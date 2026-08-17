import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.app.database.connection import get_db_connection
from backend.app.modules.processing.processor import processor

logger = logging.getLogger("processing_service")


def process_message_text(text: str, sender: Optional[str] = None) -> Dict[str, Any]:
    """
    Direct in-memory message processing.
    """
    return processor.process(text=text, sender=sender)


def process_batch_records(batch_size: int = 1000, force: bool = False) -> Dict[str, Any]:
    """
    Processes records in chunked batches from unified_transactions and upserts into processed_data.
    Uses chunked pagination (LIMIT / OFFSET) so memory remains bounded.
    Maintains per-record accounting (intelligence_created, intelligence_skipped, intelligence_failed).
    """
    start_time = time.time()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    total_processed = 0
    txns_detected = 0
    non_txns = 0
    failed_count = 0

    try:
        # Determine selection query
        where_clause = "" if force else "WHERE ut.`transaction_id` NOT IN (SELECT `transaction_id` FROM `processed_data`)"
        
        cursor.execute(f"SELECT COUNT(*) as cnt FROM `unified_transactions` ut {where_clause}")
        total_eligible = cursor.fetchone()["cnt"]

        logger.info(f"Starting batch data processing: {total_eligible} records eligible, chunk size {batch_size}")

        offset = 0
        while offset < total_eligible:
            cursor.execute(
                f"""
                SELECT `transaction_id`, `customer_id`, `source_name`, `raw_message`, `amount`
                FROM `unified_transactions` ut
                {where_clause}
                ORDER BY ut.`created_at` ASC
                LIMIT %s OFFSET %s
                """,
                (batch_size, offset if force else 0)
            )
            rows = cursor.fetchall()
            if not rows:
                break

            upsert_rows = []
            for row in rows:
                try:
                    raw_text = row.get("raw_message") or ""
                    sender = row.get("source_name")
                    txn_id = row.get("transaction_id")
                    cust_id = row.get("customer_id")

                    result = processor.process(text=raw_text, sender=sender)
                    
                    stored_amt = float(row.get("amount") or 0.0)
                    final_amt = result["amount"] if result["amount"] > 0 else stored_amt

                    if result["transaction_detected"]:
                        txns_detected += 1
                    else:
                        non_txns += 1

                    upsert_rows.append((
                        txn_id,
                        cust_id,
                        raw_text,
                        result["transaction_detected"],
                        result["transaction_type"],
                        final_amt,
                        result["category"],
                        result["subcategory"],
                        result["merchant_or_provider"],
                        result["confidence"],
                    ))
                except Exception as row_err:
                    logger.warning(f"Error processing row {row.get('transaction_id')}: {row_err}")
                    failed_count += 1

            if upsert_rows:
                cursor.executemany(
                    """
                    INSERT INTO `processed_data`
                    (`transaction_id`, `customer_id`, `raw_message`, `transaction_detected`,
                     `transaction_type`, `amount`, `category`, `subcategory`,
                     `merchant_or_provider`, `confidence`)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        `transaction_detected` = VALUES(`transaction_detected`),
                        `transaction_type` = VALUES(`transaction_type`),
                        `amount` = VALUES(`amount`),
                        `category` = VALUES(`category`),
                        `subcategory` = VALUES(`subcategory`),
                        `merchant_or_provider` = VALUES(`merchant_or_provider`),
                        `confidence` = VALUES(`confidence`),
                        `processed_at` = CURRENT_TIMESTAMP
                    """,
                    upsert_rows
                )
                conn.commit()

            total_processed += len(rows)
            if force:
                offset += len(rows)
            logger.info(f"Processed chunk: {total_processed}/{total_eligible} records")

        # Update batch summary counters in ingestion_batches if applicable
        try:
            cursor.execute(
                """
                UPDATE `ingestion_batches` ib
                SET `intelligence_created` = (
                    SELECT COUNT(*) FROM `processed_data` pd
                    JOIN `unified_transactions` ut ON pd.`transaction_id` = ut.`transaction_id`
                    WHERE ut.`batch_id` = ib.`batch_id` AND pd.`transaction_detected` = 1
                ),
                `intelligence_skipped` = (
                    SELECT COUNT(*) FROM `processed_data` pd
                    JOIN `unified_transactions` ut ON pd.`transaction_id` = ut.`transaction_id`
                    WHERE ut.`batch_id` = ib.`batch_id` AND pd.`transaction_detected` = 0
                )
                """
            )
            conn.commit()
        except Exception as update_err:
            logger.debug(f"Could not update batch intelligence summary: {update_err}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error during batch data processing: {e}", exc_info=True)
        raise e
    finally:
        cursor.close()
        conn.close()

    duration = time.time() - start_time
    reconciliation_passed = (total_processed == (txns_detected + non_txns + failed_count))

    logger.info(
        "\n" + "=" * 60 + "\n"
        "INTELLIGENCE BATCH RECONCILIATION SUMMARY\n"
        "=" * 60 + "\n"
        f"Total Records Evaluated: {total_processed}\n"
        f"Intelligence Created:    {txns_detected}\n"
        f"Intelligence Skipped:    {non_txns}\n"
        f"Intelligence Failed:     {failed_count}\n"
        f"Reconciliation Check:    {'PASSED' if reconciliation_passed else 'FAILED'} "
        f"({total_processed} == {txns_detected} + {non_txns} + {failed_count})\n"
        f"Duration:                {round(duration, 3)}s\n"
        "=" * 60
    )

    return {
        "success": True,
        "total_processed": total_processed,
        "transactions_detected": txns_detected,
        "non_transactions": non_txns,
        "intelligence_created": txns_detected,
        "intelligence_skipped": non_txns,
        "intelligence_failed": failed_count,
        "reconciliation_passed": reconciliation_passed,
        "duration_seconds": round(duration, 3),
        "batch_size": batch_size,
    }



def get_processed_data(customer_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Returns list of processed intelligence records with optional customer filter.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if customer_id:
            cursor.execute(
                """
                SELECT * FROM `processed_data`
                WHERE `customer_id` = %s
                ORDER BY `processed_at` DESC
                LIMIT %s OFFSET %s
                """,
                (customer_id, limit, offset)
            )
        else:
            cursor.execute(
                """
                SELECT * FROM `processed_data`
                ORDER BY `processed_at` DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset)
            )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
