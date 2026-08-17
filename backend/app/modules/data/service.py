import logging
from typing import Dict, Any, List, Optional
from backend.app.database.connection import get_db_connection
from backend.app.modules.ingestion.service import get_batch_details

logger = logging.getLogger("data_service")


def get_transaction_by_id(transaction_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a single transaction record by ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT `transaction_id`, `raw_record_id`, `batch_id`, `customer_id`, `source_domain`,
                   `source_name`, `transaction_type`, `category`, `subcategory`, `transaction_date`,
                   `amount`, `currency`, `payment_method`, `merchant_or_provider`, `location`,
                   `status`, `raw_message`, `classification_confidence`, `classified_at`, `created_at`
            FROM `unified_transactions`
            WHERE `transaction_id` = %s
            """,
            (transaction_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def list_transactions(
    customer_id: Optional[str] = None,
    category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Lists paginated transactions with optional filters.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conditions = []
        params: List[Any] = []

        if customer_id:
            conditions.append("`customer_id` = %s")
            params.append(customer_id)
        if category:
            conditions.append("`category` = %s")
            params.append(category.upper())
        if transaction_type:
            conditions.append("`transaction_type` = %s")
            params.append(transaction_type.upper())

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Total count query
        cursor.execute(f"SELECT COUNT(*) as total FROM `unified_transactions` {where_clause}", tuple(params))
        total_count = cursor.fetchone()["total"]

        # Fetch records
        fetch_sql = f"""
            SELECT `transaction_id`, `raw_record_id`, `batch_id`, `customer_id`, `source_domain`,
                   `source_name`, `transaction_type`, `category`, `subcategory`, `transaction_date`,
                   `amount`, `currency`, `payment_method`, `merchant_or_provider`, `location`,
                   `status`, `raw_message`, `classification_confidence`, `classified_at`, `created_at`
            FROM `unified_transactions`
            {where_clause}
            ORDER BY `transaction_date` DESC
            LIMIT %s OFFSET %s
        """
        fetch_params = params + [limit, offset]
        cursor.execute(fetch_sql, tuple(fetch_params))
        records = cursor.fetchall()

        return {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "records": records,
        }
    finally:
        cursor.close()
        conn.close()


def get_import_job_status(import_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches import job status and progress by batch/import ID.
    """
    return get_batch_details(import_id)
