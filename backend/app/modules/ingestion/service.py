import json
import uuid
import logging
from typing import Dict, Any, List
from backend.app.database.connection import get_db_connection
from backend.app.modules.ingestion.parsers.csv_parser import CSVParser
from backend.app.modules.ingestion.classifier import classify_record
from backend.app.modules.ingestion.validator import validate_customer_record, validate_transaction_record
from backend.app.core.constants import DomainEnum

logger = logging.getLogger("ingestion_service")


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


def process_csv_ingestion(file_content: str, filename: str, domain_hint: str = "AUTO_DETECT") -> Dict[str, Any]:
    batch_id = f"batch_{uuid.uuid4().hex[:10]}"
    parser = CSVParser()
    
    total_records = 0
    valid_records = 0
    rejected_records = 0
    duplicate_records = 0
    inserted_records = 0
    errors_list = []

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    detected_domain = domain_hint.upper() if domain_hint else "AUTO_DETECT"

    try:
        # 1. Insert Initial Batch Record
        cursor.execute(
            """
            INSERT INTO `ingestion_batches`
            (`batch_id`, `filename`, `source_domain`, `total_records`, `valid_records`, `rejected_records`, `duplicate_records`, `inserted_records`, `status`)
            VALUES (%s, %s, %s, 0, 0, 0, 0, 0, 'PROCESSING')
            """,
            (batch_id, filename, detected_domain)
        )
        conn.commit()

        # Parse CSV rows generator
        rows = list(parser.parse(file_content))
        total_records = len(rows)

        for idx, row in enumerate(rows, start=1):
            # Record raw row snapshot
            raw_json = json.dumps(row, ensure_ascii=False)
            cursor.execute(
                """
                INSERT INTO `raw_ingestion_records` (`batch_id`, `row_number`, `raw_data`)
                VALUES (%s, %s, %s)
                """,
                (batch_id, idx, raw_json)
            )
            raw_record_id = cursor.lastrowid

            # Classify record
            domain, source_name, txn_type = classify_record(row, domain_hint=domain_hint)
            if detected_domain == "AUTO_DETECT" and domain != DomainEnum.UNKNOWN.value:
                detected_domain = domain

            # Handle Customer Master File vs Transaction File
            if domain == DomainEnum.CUSTOMER.value or "full_name" in row:
                clean_cust, cust_errors = validate_customer_record(row, idx)
                if cust_errors:
                    rejected_records += 1
                    for err in cust_errors:
                        errors_list.append(err)
                        cursor.execute(
                            """
                            INSERT INTO `ingestion_errors` (`batch_id`, `row_number`, `field_name`, `error_reason`, `raw_value`)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (batch_id, idx, err["field"], err["error"], err["raw_value"])
                        )
                else:
                    valid_records += 1
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
            else:
                # Transaction Record Pipeline
                clean_txn, txn_errors = validate_transaction_record(row, idx, domain, source_name, txn_type)
                
                if txn_errors:
                    rejected_records += 1
                    for err in txn_errors:
                        errors_list.append(err)
                        cursor.execute(
                            """
                            INSERT INTO `ingestion_errors` (`batch_id`, `row_number`, `field_name`, `error_reason`, `raw_value`)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (batch_id, idx, err["field"], err["error"], err["raw_value"])
                        )
                else:
                    valid_records += 1
                    # Ensure customer exists in customers master table to maintain FK integrity
                    cursor.execute("SELECT `customer_id` FROM `customers` WHERE `customer_id` = %s", (clean_txn["customer_id"],))
                    if not cursor.fetchone():
                        cursor.execute(
                            """
                            INSERT INTO `customers` (`customer_id`, `full_name`)
                            VALUES (%s, %s)
                            """,
                            (clean_txn["customer_id"], f"Customer {clean_txn['customer_id']}")
                        )

                    # Deduplication check by transaction_id or record_hash
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
                             `payment_method`, `merchant_or_provider`, `location`, `status`, `record_hash`)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                                clean_txn["record_hash"],
                            )
                        )
                        inserted_records += 1

        # Update Final Batch Status
        cursor.execute(
            """
            UPDATE `ingestion_batches`
            SET `source_domain` = %s,
                `total_records` = %s,
                `valid_records` = %s,
                `rejected_records` = %s,
                `duplicate_records` = %s,
                `inserted_records` = %s,
                `status` = 'COMPLETED'
            WHERE `batch_id` = %s
            """,
            (detected_domain, total_records, valid_records, rejected_records, duplicate_records, inserted_records, batch_id)
        )
        conn.commit()

        return {
            "success": True,
            "batch_id": batch_id,
            "filename": filename,
            "domain": detected_domain,
            "summary": {
                "total_records": total_records,
                "valid_records": valid_records,
                "rejected_records": rejected_records,
                "duplicate_records": duplicate_records,
                "inserted_records": inserted_records
            },
            "errors": errors_list
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Error during ingestion processing: {e}")
        cursor.execute("UPDATE `ingestion_batches` SET `status` = 'FAILED' WHERE `batch_id` = %s", (batch_id,))
        conn.commit()
        raise e
    finally:
        cursor.close()
        conn.close()


def get_all_batches() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `ingestion_batches` ORDER BY `created_at` DESC LIMIT 50")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_batch_details(batch_id: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `ingestion_batches` WHERE `batch_id` = %s", (batch_id,))
        batch = cursor.fetchone()
        if not batch:
            return None

        cursor.execute("SELECT `row_number` as `row`, `field_name` as `field`, `error_reason` as `error`, `raw_value` FROM `ingestion_errors` WHERE `batch_id` = %s ORDER BY `row_number` ASC", (batch_id,))
        errors = cursor.fetchall()

        batch["errors"] = errors
        return batch
    finally:
        cursor.close()
        conn.close()