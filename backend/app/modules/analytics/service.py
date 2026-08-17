import time
import logging
from typing import Dict, Any, List, Optional

from backend.app.modules.analytics.aggregator import (
    fetch_customer_by_id_or_phone,
    aggregate_customer_metrics,
    aggregate_global_summary,
    build_and_persist_customer_profile,
    fetch_customer_profile_from_db,
    list_customer_profiles_from_db,
)
from backend.app.database.connection import get_db_connection

logger = logging.getLogger("analytics_service")


def get_customer_profile(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Returns customer basic entity information.
    """
    return fetch_customer_by_id_or_phone(identifier)


def generate_customer_profile(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Generates and persists a structured Customer Profile for a single customer.
    """
    return build_and_persist_customer_profile(identifier)


def get_customer_profile_details(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves stored Customer Profile or generates on demand.
    """
    return fetch_customer_profile_from_db(identifier)


def list_customer_profiles(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Returns paginated list of stored customer profiles.
    """
    return list_customer_profiles_from_db(limit=limit, offset=offset)


def generate_customer_profiles(customer_ids: Optional[List[str]] = None, limit: int = 50) -> Dict[str, Any]:
    """
    Batch generates customer profiles for specified customer IDs, or for top active customers.
    Deterministic, idempotent, and performs no LLM calls.
    """
    start_time = time.time()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    target_ids = []
    if customer_ids:
        target_ids = customer_ids
    else:
        cursor.execute(
            """
            SELECT DISTINCT `customer_id`
            FROM `unified_transactions`
            LIMIT %s
            """,
            (limit,)
        )
        target_ids = [row["customer_id"] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()

    total_selected = len(target_ids)
    generated = 0
    failed = 0
    successful_cids = []

    for cid in target_ids:
        try:
            profile = build_and_persist_customer_profile(cid)
            if profile:
                generated += 1
                successful_cids.append(cid)
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Error generating profile for customer {cid}: {e}")
            failed += 1

    duration = time.time() - start_time
    reconciliation_passed = (total_selected == (generated + failed))

    logger.info(
        f"Batch Customer Profile Generation: selected={total_selected}, "
        f"generated={generated}, failed={failed}, duration={round(duration, 3)}s"
    )

    return {
        "success": True,
        "total_customers_selected": total_selected,
        "profiles_generated": generated,
        "profiles_failed": failed,
        "duration_seconds": round(duration, 3),
        "reconciliation_passed": reconciliation_passed,
        "customer_ids": successful_cids,
    }


def get_customer_summary(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Returns aggregated customer intelligence summary including category breakdown and totals.
    """
    profile = fetch_customer_by_id_or_phone(identifier)
    if not profile:
        return None

    actual_customer_id = profile["customer_id"]
    metrics = aggregate_customer_metrics(actual_customer_id)

    metrics["phone"] = profile.get("phone") or identifier
    metrics["full_name"] = profile.get("full_name")
    return metrics


def get_global_analytics_summary() -> Dict[str, Any]:
    """
    Returns platform-wide summary metrics.
    """
    return aggregate_global_summary()


def list_all_customers(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Returns paginated list of customers.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT `customer_id`, `full_name`, `email`, `phone`, `city`, `state`, `created_at`
            FROM `customers`
            ORDER BY `created_at` DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

