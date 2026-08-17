import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.app.database.connection import get_db_connection
from backend.app.modules.classification.classifier import classification_engine
from backend.app.modules.classification.constants import (
    ClassificationDomainEnum as Domain,
    ConfidenceLevel,
)

logger = logging.getLogger("classification_service")


def classify_record_data(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes rule-based classification on an in-memory normalized CDM dictionary.
    """
    return classification_engine.classify(record)


def classify_single_transaction(transaction_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a transaction from the database by ID, classifies it,
    updates the record in-place idempotently, and returns the classification result.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT `transaction_id`, `customer_id`, `source_domain`, `source_name`,
                   `transaction_type`, `category`, `subcategory`, `merchant_or_provider`,
                   `amount`, `currency`, `payment_method`, `location`
            FROM `unified_transactions`
            WHERE `transaction_id` = %s
            """,
            (transaction_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None

        result = classification_engine.classify(row)

        # Update database with classified metadata idempotently
        cursor.execute(
            """
            UPDATE `unified_transactions`
            SET `source_domain` = %s,
                `category` = %s,
                `subcategory` = %s,
                `classification_confidence` = %s,
                `classified_at` = %s
            WHERE `transaction_id` = %s
            """,
            (
                result["source_domain"],
                result["category"],
                result["subcategory"],
                result["confidence"],
                datetime.utcnow(),
                transaction_id
            )
        )
        conn.commit()
        return result

    except Exception as e:
        conn.rollback()
        logger.error(f"Error classifying transaction {transaction_id}: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()


def classify_batch_transactions(limit: int = 100, force: bool = False) -> Dict[str, Any]:
    """
    Fetches unclassified transactions from MySQL, applies classification,
    and updates records in batch.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    total_records = 0
    classified_records = 0
    unknown_records = 0
    failed_records = 0

    try:
        # Fetch unclassified or all (if force is requested)
        if force:
            cursor.execute(
                """
                SELECT `transaction_id`, `customer_id`, `source_domain`, `source_name`,
                       `transaction_type`, `category`, `subcategory`, `merchant_or_provider`,
                       `amount`, `currency`, `payment_method`, `location`
                FROM `unified_transactions`
                ORDER BY `created_at` DESC
                LIMIT %s
                """,
                (limit,)
            )
        else:
            cursor.execute(
                """
                SELECT `transaction_id`, `customer_id`, `source_domain`, `source_name`,
                       `transaction_type`, `category`, `subcategory`, `merchant_or_provider`,
                       `amount`, `currency`, `payment_method`, `location`
                FROM `unified_transactions`
                WHERE `classified_at` IS NULL
                ORDER BY `created_at` DESC
                LIMIT %s
                """,
                (limit,)
            )

        rows = cursor.fetchall()
        total_records = len(rows)

        for row in rows:
            txn_id = row["transaction_id"]
            try:
                result = classification_engine.classify(row)
                
                cursor.execute(
                    """
                    UPDATE `unified_transactions`
                    SET `source_domain` = %s,
                        `category` = %s,
                        `subcategory` = %s,
                        `classification_confidence` = %s,
                        `classified_at` = %s
                    WHERE `transaction_id` = %s
                    """,
                    (
                        result["source_domain"],
                        result["category"],
                        result["subcategory"],
                        result["confidence"],
                        datetime.utcnow(),
                        txn_id
                    )
                )

                if result["source_domain"] == Domain.UNKNOWN.value or result["confidence"] == 0.0:
                    unknown_records += 1
                else:
                    classified_records += 1

            except Exception as row_err:
                logger.warning(f"Failed to classify row {txn_id}: {row_err}")
                failed_records += 1

        conn.commit()

        return {
            "success": True,
            "total_records": total_records,
            "classified_records": classified_records,
            "unknown_records": unknown_records,
            "failed_records": failed_records
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Error during batch classification: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()
