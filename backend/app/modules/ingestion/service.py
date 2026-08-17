import os
import json
import uuid
import logging
import tempfile
import shutil
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set
from collections import Counter

from backend.app.database.connection import get_db_connection
from backend.app.modules.ingestion.connectors import (
    CSVConnector,
    APIConnector,
    DBConnector,
    ConnectorError,
)
from backend.app.modules.ingestion.parsers.sms_parser import SMSParser
from backend.app.modules.classification.classifier import classification_engine
from backend.app.modules.ingestion.validator import (
    validate_customer_record,
    validate_transaction_record,
    validate_sms_record,
)
from backend.app.core.constants import DomainEnum

logger = logging.getLogger("ingestion_service")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_BATCH_SIZE = 1000  # Records processed per DB commit cycle
MAX_ERRORS_STORED = 500    # Cap on in-response error list (DB stores all)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def save_message(data: Any):
    """Legacy helper function preserved for backward compatibility."""
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO `raw_messages`
            (`customer_id`, `source`, `message`, `received_at`)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (data.customer_id, data.source, data.message, data.received_at))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()


def ensure_schema_columns(cursor):
    """Ensures optional columns exist in unified_transactions table."""
    optional_cols = [
        "ALTER TABLE `unified_transactions` ADD COLUMN `classification_confidence` DECIMAL(4, 2) DEFAULT NULL",
        "ALTER TABLE `unified_transactions` ADD COLUMN `classified_at` DATETIME DEFAULT NULL",
        "ALTER TABLE `unified_transactions` ADD COLUMN `raw_message` LONGTEXT DEFAULT NULL",
    ]
    for stmt in optional_cols:
        try:
            cursor.execute(stmt)
        except Exception:
            pass  # Column already exists


def _insert_batch_record(cursor, batch_id: str, filename: str, input_type: str, total_records: int):
    """Creates the initial ingestion_batches tracking row."""
    cursor.execute(
        """
        INSERT INTO `ingestion_batches`
        (`batch_id`, `filename`, `input_type`, `source_domain`, `total_records`,
         `valid_records`, `rejected_records`, `duplicate_records`, `inserted_records`, `status`)
        VALUES (%s, %s, %s, %s, %s, 0, 0, 0, 0, 'PROCESSING')
        """,
        (batch_id, filename, input_type.upper(), "PROCESSING", total_records)
    )


def _update_batch_progress(cursor, batch_id: str, valid: int, rejected: int, dupes: int, inserted: int):
    """Incrementally updates batch counters — called after each chunk commit."""
    cursor.execute(
        """
        UPDATE `ingestion_batches`
        SET `valid_records` = `valid_records` + %s,
            `rejected_records` = `rejected_records` + %s,
            `duplicate_records` = `duplicate_records` + %s,
            `inserted_records` = `inserted_records` + %s
        WHERE `batch_id` = %s
        """,
        (valid, rejected, dupes, inserted, batch_id)
    )


def _finalize_batch(cursor, batch_id: str, domain_counter: Counter, status: str = "COMPLETED"):
    """Updates batch status and computes domain summary at the end."""
    unique_domains = [d for d in domain_counter.keys() if d != "CUSTOMER"]
    if len(unique_domains) == 1:
        batch_domain = unique_domains[0]
    elif len(unique_domains) > 1:
        batch_domain = "MULTI_SOURCE"
    else:
        batch_domain = "UNKNOWN"

    cursor.execute(
        """
        UPDATE `ingestion_batches`
        SET `source_domain` = %s,
            `status` = %s,
            `completed_at` = %s
        WHERE `batch_id` = %s
        """,
        (batch_domain, status, datetime.now(timezone.utc), batch_id)
    )


def ensure_customer_placeholder(cursor, customer_id: str, known_customers: Set[str]):
    """Ensures the customer FK placeholder exists (in-memory cache to minimize DB hits)."""
    if customer_id in known_customers or customer_id == "CUST_UNKNOWN":
        return
    cursor.execute("SELECT `customer_id` FROM `customers` WHERE `customer_id` = %s", (customer_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO `customers` (`customer_id`, `full_name`) VALUES (%s, %s)",
            (customer_id, f"Customer {customer_id}")
        )
    known_customers.add(customer_id)


def ensure_unknown_customer(cursor):
    """Ensures the CUST_UNKNOWN placeholder exists for SMS records without a real customer_id."""
    cursor.execute("SELECT `customer_id` FROM `customers` WHERE `customer_id` = 'CUST_UNKNOWN'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO `customers` (`customer_id`, `full_name`) VALUES ('CUST_UNKNOWN', 'Unknown Customer')"
        )


# ---------------------------------------------------------------------------
# Core streaming pipeline — processes one BATCH chunk at a time
# ---------------------------------------------------------------------------

def _process_batch_chunk(
    cursor,
    conn,
    batch_id: str,
    chunk: List[Dict[str, Any]],
    chunk_offset: int,
    input_type: str,
    known_customers: Set[str],
    domain_counter: Counter,
    errors_list: List[Dict[str, Any]],
) -> Dict[str, int]:
    """
    Processes a single batch chunk:
    - Detects record type (Customer / SMS / Structured Transaction)
    - Parses, classifies, validates, deduplicates
    - Inserts raw records and CDM records into DB
    - Returns per-chunk counters

    Never raises exceptions for individual record failures.
    Only propagates DB-level fatal errors.
    """
    valid_records = 0
    rejected_records = 0
    duplicate_records = 0
    inserted_records = 0

    is_sms_mode = input_type.upper() == "SMS"

    for local_idx, raw_row in enumerate(chunk):
        row_num = chunk_offset + local_idx + 1

        # --- Store raw snapshot ---
        raw_json = json.dumps(raw_row, ensure_ascii=False, default=str)
        cursor.execute(
            """
            INSERT INTO `raw_ingestion_records` (`batch_id`, `row_number`, `raw_data`)
            VALUES (%s, %s, %s)
            """,
            (batch_id, row_num, raw_json)
        )
        raw_record_id = cursor.lastrowid

        try:
            # ----------------------------------------------------------------
            # Branch A: Customer Master Profile
            # ----------------------------------------------------------------
            if "full_name" in raw_row or input_type.upper() in ("CUSTOMERS", "CUSTOMER_MASTER"):
                clean_cust, cust_errors = validate_customer_record(raw_row, row_num)
                if cust_errors:
                    rejected_records += 1
                    for err in cust_errors:
                        if len(errors_list) < MAX_ERRORS_STORED:
                            errors_list.append(err)
                        cursor.execute(
                            """
                            INSERT INTO `ingestion_errors` (`batch_id`, `row_number`, `field_name`, `error_reason`, `raw_value`)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (batch_id, row_num, err["field"], err["error"][:500], str(err["raw_value"])[:500])
                        )
                else:
                    valid_records += 1
                    domain_counter["CUSTOMER"] += 1
                    known_customers.add(clean_cust["customer_id"])
                    cursor.execute(
                        """
                        INSERT INTO `customers` (`customer_id`, `full_name`, `email`, `phone`, `city`, `state`)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            `full_name` = VALUES(`full_name`),
                            `email` = VALUES(`email`),
                            `phone` = VALUES(`phone`),
                            `city` = VALUES(`city`),
                            `state` = VALUES(`state`)
                        """,
                        (
                            clean_cust["customer_id"],
                            clean_cust["full_name"],
                            clean_cust["email"],
                            clean_cust["phone"],
                            clean_cust["city"],
                            clean_cust["state"],
                        )
                    )
                    inserted_records += 1

            # ----------------------------------------------------------------
            # Branch B: SMS / Communication Record
            # ----------------------------------------------------------------
            elif is_sms_mode or SMSParser.is_sms_record(raw_row):
                # Step 1: Parse raw SMS into structured fields
                parsed = SMSParser.parse_sms_record(raw_row)

                # Step 2: Classify at record level
                classified = classification_engine.classify(parsed)

                rec_domain = classified.get("source_domain") or "UNKNOWN"
                rec_source_name = classified.get("source_name") or parsed.get("source_name") or "UNKNOWN_SENDER"
                rec_txn_type = parsed.get("transaction_type") or classified.get("transaction_type") or "PURCHASE"
                rec_confidence = classified.get("confidence", 0.0)

                # Step 3: Validate with lenient SMS rules
                clean_txn, txn_errors = validate_sms_record(
                    parsed,
                    row_num,
                    domain=rec_domain,
                    source_name=rec_source_name,
                    txn_type=rec_txn_type,
                    confidence=rec_confidence
                )

                if txn_errors:
                    rejected_records += 1
                    for err in txn_errors:
                        if len(errors_list) < MAX_ERRORS_STORED:
                            errors_list.append(err)
                        cursor.execute(
                            """
                            INSERT INTO `ingestion_errors` (`batch_id`, `row_number`, `field_name`, `error_reason`, `raw_value`)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (batch_id, row_num, err["field"], err["error"][:500], str(err["raw_value"])[:500])
                        )
                else:
                    valid_records += 1
                    domain_counter[rec_domain] += 1
                    cid = clean_txn["customer_id"]

                    # Ensure customer FK exists
                    if cid == "CUST_UNKNOWN":
                        ensure_unknown_customer(cursor)
                        known_customers.add("CUST_UNKNOWN")
                    else:
                        ensure_customer_placeholder(cursor, cid, known_customers)

                    # Deduplication
                    cursor.execute(
                        "SELECT `transaction_id` FROM `unified_transactions` WHERE `record_hash` = %s",
                        (clean_txn["record_hash"],)
                    )
                    if cursor.fetchone():
                        duplicate_records += 1
                    else:
                        cursor.execute(
                            """
                            INSERT INTO `unified_transactions`
                            (`transaction_id`, `raw_record_id`, `batch_id`, `customer_id`, `source_domain`, `source_name`,
                             `transaction_type`, `category`, `subcategory`, `transaction_date`, `amount`, `currency`,
                             `payment_method`, `merchant_or_provider`, `location`, `status`, `raw_message`,
                             `classification_confidence`, `classified_at`, `record_hash`)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                clean_txn["transaction_id"],
                                raw_record_id,
                                batch_id,
                                clean_txn["customer_id"],
                                clean_txn["source_domain"],
                                clean_txn["source_name"],
                                clean_txn["transaction_type"],
                                clean_txn["category"],
                                clean_txn["subcategory"],
                                clean_txn["transaction_date"],
                                clean_txn["amount"],
                                clean_txn["currency"],
                                clean_txn["payment_method"],
                                clean_txn["merchant_or_provider"],
                                clean_txn["location"],
                                clean_txn["status"],
                                clean_txn.get("raw_message"),
                                clean_txn["classification_confidence"],
                                datetime.now(timezone.utc),
                                clean_txn["record_hash"],
                            )
                        )
                        inserted_records += 1

            # ----------------------------------------------------------------
            # Branch C: Structured Transaction Record
            # ----------------------------------------------------------------
            else:
                extracted_record = dict(raw_row)
                classified = classification_engine.classify(extracted_record)

                rec_domain = classified.get("source_domain") or "UNKNOWN"
                rec_source_name = classified.get("source_name") or "GENERIC_SOURCE"
                rec_txn_type = extracted_record.get("transaction_type") or classified.get("transaction_type") or "PURCHASE"
                rec_category = classified.get("category", rec_domain)
                rec_subcategory = classified.get("subcategory")
                rec_confidence = classified.get("confidence", 0.0)

                merged_row = {**extracted_record, "category": rec_category, "subcategory": rec_subcategory}
                clean_txn, txn_errors = validate_transaction_record(
                    merged_row,
                    row_num,
                    domain=rec_domain,
                    source_name=rec_source_name,
                    txn_type=rec_txn_type,
                    confidence=rec_confidence
                )

                if txn_errors:
                    rejected_records += 1
                    for err in txn_errors:
                        if len(errors_list) < MAX_ERRORS_STORED:
                            errors_list.append(err)
                        cursor.execute(
                            """
                            INSERT INTO `ingestion_errors` (`batch_id`, `row_number`, `field_name`, `error_reason`, `raw_value`)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (batch_id, row_num, err["field"], err["error"][:500], str(err["raw_value"])[:500])
                        )
                else:
                    valid_records += 1
                    domain_counter[rec_domain] += 1
                    cid = clean_txn["customer_id"]
                    ensure_customer_placeholder(cursor, cid, known_customers)

                    cursor.execute(
                        "SELECT `transaction_id` FROM `unified_transactions` WHERE `transaction_id` = %s OR `record_hash` = %s",
                        (clean_txn["transaction_id"], clean_txn["record_hash"])
                    )
                    if cursor.fetchone():
                        duplicate_records += 1
                    else:
                        cursor.execute(
                            """
                            INSERT INTO `unified_transactions`
                            (`transaction_id`, `raw_record_id`, `batch_id`, `customer_id`, `source_domain`, `source_name`,
                             `transaction_type`, `category`, `subcategory`, `transaction_date`, `amount`, `currency`,
                             `payment_method`, `merchant_or_provider`, `location`, `status`, `raw_message`,
                             `classification_confidence`, `classified_at`, `record_hash`)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                clean_txn["transaction_id"],
                                raw_record_id,
                                batch_id,
                                clean_txn["customer_id"],
                                clean_txn["source_domain"],
                                clean_txn["source_name"],
                                clean_txn["transaction_type"],
                                clean_txn["category"],
                                clean_txn["subcategory"],
                                clean_txn["transaction_date"],
                                clean_txn["amount"],
                                clean_txn["currency"],
                                clean_txn["payment_method"],
                                clean_txn["merchant_or_provider"],
                                clean_txn["location"],
                                clean_txn["status"],
                                clean_txn.get("raw_message"),
                                clean_txn["classification_confidence"],
                                datetime.now(timezone.utc),
                                clean_txn["record_hash"],
                            )
                        )
                        inserted_records += 1

        except Exception as record_err:
            # Individual record error — log it, continue processing
            logger.warning(f"Row {row_num} processing error: {record_err}")
            rejected_records += 1
            err_msg = str(record_err)[:500]
            try:
                cursor.execute(
                    """
                    INSERT INTO `ingestion_errors` (`batch_id`, `row_number`, `field_name`, `error_reason`, `raw_value`)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (batch_id, row_num, "record", err_msg, str(raw_row)[:500])
                )
            except Exception:
                pass

    return {
        "valid": valid_records,
        "rejected": rejected_records,
        "duplicate": duplicate_records,
        "inserted": inserted_records,
    }


# ---------------------------------------------------------------------------
# Main streaming pipeline entry point
# ---------------------------------------------------------------------------

def run_streaming_pipeline(
    file_path: str,
    filename: str,
    batch_id: str,
    input_type: str = "AUTO_DETECT",
    batch_size: int = DEFAULT_BATCH_SIZE,
    domain_hint: Optional[str] = None,
    cleanup_file: bool = True
) -> Dict[str, Any]:
    """
    Streaming ingestion pipeline. Reads the file in `batch_size` chunks.
    Each chunk is:
        read → parse → validate → classify → insert → commit → free memory

    This function can run as a background task.
    Returns the final summary dict.
    """
    logger.info(f"Starting streaming pipeline: batch_id={batch_id}, file={filename}, batch_size={batch_size}")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    total_valid = 0
    total_rejected = 0
    total_duplicate = 0
    total_inserted = 0
    total_processed = 0
    domain_counter: Counter = Counter()
    errors_list: List[Dict[str, Any]] = []
    known_customers: Set[str] = set()
    final_status = "COMPLETED"

    try:
        ensure_schema_columns(cursor)
        conn.commit()

        connector = CSVConnector(file_path=file_path, source_name=filename)
        connector.connect()

        # Count total rows efficiently (reads file once)
        total_records = connector.count_rows()
        logger.info(f"Total records in file: {total_records}")

        # Create batch tracking row
        _insert_batch_record(cursor, batch_id, filename, input_type, total_records)
        conn.commit()

        # Stream and process in chunks
        chunk_num = 0
        for chunk in connector.stream_batches(batch_size=batch_size):
            chunk_num += 1
            logger.info(f"Processing chunk {chunk_num}, rows {total_processed + 1}–{total_processed + len(chunk)}")

            chunk_results = _process_batch_chunk(
                cursor=cursor,
                conn=conn,
                batch_id=batch_id,
                chunk=chunk,
                chunk_offset=total_processed,
                input_type=input_type,
                known_customers=known_customers,
                domain_counter=domain_counter,
                errors_list=errors_list,
            )

            total_processed += len(chunk)
            total_valid += chunk_results["valid"]
            total_rejected += chunk_results["rejected"]
            total_duplicate += chunk_results["duplicate"]
            total_inserted += chunk_results["inserted"]

            # Update progress counters in DB
            _update_batch_progress(
                cursor, batch_id,
                chunk_results["valid"],
                chunk_results["rejected"],
                chunk_results["duplicate"],
                chunk_results["inserted"]
            )
            conn.commit()

            logger.info(
                f"Chunk {chunk_num} done: valid={chunk_results['valid']}, "
                f"rejected={chunk_results['rejected']}, dup={chunk_results['duplicate']}"
            )

        # Determine final status
        if total_valid == 0 and total_rejected > 0:
            final_status = "FAILED"
        elif total_rejected > 0:
            final_status = "PARTIAL"
        else:
            final_status = "COMPLETED"

        _finalize_batch(cursor, batch_id, domain_counter, final_status)
        conn.commit()

    except Exception as e:
        logger.error(f"Fatal error in streaming pipeline for batch {batch_id}: {e}", exc_info=True)
        try:
            cursor.execute(
                "UPDATE `ingestion_batches` SET `status` = 'FAILED', `completed_at` = %s WHERE `batch_id` = %s",
                (datetime.now(timezone.utc), batch_id)
            )
            conn.commit()
        except Exception:
            pass
        final_status = "FAILED"
        raise
    finally:
        cursor.close()
        conn.close()
        if cleanup_file and file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not delete temp file {file_path}: {e}")

    # Compute domain breakdown
    unique_domains = [d for d in domain_counter.keys() if d != "CUSTOMER"]
    batch_domain = (
        unique_domains[0] if len(unique_domains) == 1
        else "MULTI_SOURCE" if len(unique_domains) > 1
        else "UNKNOWN"
    )

    return {
        "success": final_status != "FAILED",
        "batch_id": batch_id,
        "filename": filename,
        "input_type": input_type,
        "status": final_status,
        "domain": batch_domain,
        "domain_breakdown": dict(domain_counter),
        "summary": {
            "total_records": total_processed,
            "valid_records": total_valid,
            "rejected_records": total_rejected,
            "duplicate_records": total_duplicate,
            "inserted_records": total_inserted,
        },
        "errors": errors_list
    }


def process_csv_ingestion(
    file_content: Optional[str] = None,
    filename: str = "data.csv",
    file_path: Optional[str] = None,
    input_type: str = "AUTO_DETECT",
    batch_size: int = DEFAULT_BATCH_SIZE,
    domain_hint: Optional[str] = None
) -> str:
    """
    Saves the uploaded CSV to a temp file and runs the streaming pipeline.
    Returns the batch_id immediately (pipeline runs in the background).

    If file_path is provided directly, uses that.
    If file_content is provided, saves to a temp file first.
    """
    batch_id = f"batch_{uuid.uuid4().hex[:10]}"

    if file_path is None:
        # Save content to a temporary file so streaming can work properly
        tmp_dir = tempfile.gettempdir()
        tmp_path = os.path.join(tmp_dir, f"ingestion_{batch_id}.csv")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(file_content or "")
            file_path = tmp_path
        except Exception as e:
            raise RuntimeError(f"Failed to save upload to temp file: {e}")

    return batch_id, file_path


def process_api_ingestion(
    url: str,
    source_name: str = "EXTERNAL_API",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    results_key: Optional[str] = None,
    timeout: int = 15,
    input_type: str = "API",
    domain_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetches remote JSON data via APIConnector and feeds into the CDM pipeline.
    Uses in-memory processing (API responses are typically small).
    """
    connector = APIConnector(
        url=url,
        headers=headers,
        params=params,
        timeout=timeout,
        source_name=source_name,
        results_key=results_key
    )
    connector.connect()
    records = connector.fetch()

    # For API data: write to temp file and use streaming pipeline
    batch_id = f"batch_{uuid.uuid4().hex[:10]}"
    tmp_path = os.path.join(tempfile.gettempdir(), f"ingestion_{batch_id}.json")
    try:
        # Convert records to CSV-like structure via temp file
        import csv as _csv
        if records:
            fieldnames = list(records[0].keys())
            with open(tmp_path, "w", newline="", encoding="utf-8") as f:
                writer = _csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(records)
        else:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write("")

        return run_streaming_pipeline(
            file_path=tmp_path,
            filename=f"API: {url}",
            batch_id=batch_id,
            input_type=input_type,
            domain_hint=domain_hint,
            cleanup_file=True
        )
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def process_db_ingestion(
    host: str,
    user: str,
    database: str,
    query: str,
    port: int = 3306,
    password: Optional[str] = None,
    source_name: str = "EXTERNAL_DB",
    input_type: str = "DATABASE",
    domain_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Queries external relational database via DBConnector and feeds rows into CDM pipeline.
    """
    with DBConnector(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        query=query,
        source_name=source_name
    ) as connector:
        records = connector.fetch()

    batch_id = f"batch_{uuid.uuid4().hex[:10]}"
    tmp_path = os.path.join(tempfile.gettempdir(), f"ingestion_{batch_id}.csv")
    try:
        import csv as _csv
        if records:
            fieldnames = list(records[0].keys())
            with open(tmp_path, "w", newline="", encoding="utf-8") as f:
                writer = _csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(records)
        else:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write("")

        return run_streaming_pipeline(
            file_path=tmp_path,
            filename=f"DB: {database}",
            batch_id=batch_id,
            input_type=input_type,
            domain_hint=domain_hint,
            cleanup_file=True
        )
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def get_all_batches() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT `batch_id`, `filename`, `input_type`, `source_domain`,
                   `total_records`, `valid_records`, `rejected_records`,
                   `duplicate_records`, `inserted_records`, `status`,
                   `created_at`, `completed_at`
            FROM `ingestion_batches`
            ORDER BY `created_at` DESC
            LIMIT 50
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_batch_details(batch_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT `batch_id`, `filename`, `input_type`, `source_domain`,
                   `total_records`, `valid_records`, `rejected_records`,
                   `duplicate_records`, `inserted_records`, `status`,
                   `created_at`, `completed_at`
            FROM `ingestion_batches`
            WHERE `batch_id` = %s
        """, (batch_id,))
        batch = cursor.fetchone()
        if not batch:
            return None

        cursor.execute(
            """
            SELECT `row_number` as `row`, `field_name` as `field`, `error_reason` as `error`, `raw_value`
            FROM `ingestion_errors`
            WHERE `batch_id` = %s
            ORDER BY `row_number` ASC
            LIMIT 500
            """,
            (batch_id,)
        )
        errors = cursor.fetchall()
        batch["errors"] = errors
        return batch
    finally:
        cursor.close()
        conn.close()