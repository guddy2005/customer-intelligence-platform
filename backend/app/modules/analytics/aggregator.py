import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.app.database.connection import get_db_connection

logger = logging.getLogger("analytics_aggregator")


def fetch_customer_by_id_or_phone(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Finds a customer record by customer_id or phone number.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT `customer_id`, `full_name`, `email`, `phone`, `city`, `state`, `created_at`
            FROM `customers`
            WHERE `customer_id` = %s OR `phone` = %s
            LIMIT 1
            """,
            (identifier, identifier)
        )
        row = cursor.fetchone()
        if not row:
            # If not in customers table directly, check if any transactions exist for this ID/phone
            cursor.execute(
                """
                SELECT `customer_id`, MIN(`transaction_date`) as `first_seen`
                FROM `unified_transactions`
                WHERE `customer_id` = %s
                GROUP BY `customer_id`
                """,
                (identifier,)
            )
            txn_row = cursor.fetchone()
            if txn_row:
                return {
                    "customer_id": identifier,
                    "full_name": f"Customer {identifier}",
                    "email": None,
                    "phone": identifier,
                    "city": None,
                    "state": None,
                    "created_at": txn_row.get("first_seen")
                }
        return row
    finally:
        cursor.close()
        conn.close()


def aggregate_customer_metrics(customer_id: str) -> Dict[str, Any]:
    """
    Computes customer-level metrics:
    - total transactions
    - total credited amount
    - total debited amount
    - total spending (purchases + debits)
    - category-wise breakdown
    - first & last activity timestamp
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Overall stats
        cursor.execute(
            """
            SELECT
                COUNT(*) as total_transactions,
                COALESCE(SUM(CASE WHEN `transaction_type` = 'CREDIT' THEN `amount` ELSE 0 END), 0) as total_credited,
                COALESCE(SUM(CASE WHEN `transaction_type` IN ('DEBIT', 'PURCHASE', 'BILL_PAYMENT') THEN `amount` ELSE 0 END), 0) as total_debited,
                COALESCE(SUM(CASE WHEN `transaction_type` IN ('DEBIT', 'PURCHASE', 'BILL_PAYMENT', 'INVESTMENT') THEN `amount` ELSE 0 END), 0) as total_spending,
                MIN(`transaction_date`) as first_activity,
                MAX(`transaction_date`) as last_activity
            FROM `unified_transactions`
            WHERE `customer_id` = %s
            """,
            (customer_id,)
        )
        stats = cursor.fetchone() or {
            "total_transactions": 0,
            "total_credited": 0.0,
            "total_debited": 0.0,
            "total_spending": 0.0,
            "first_activity": None,
            "last_activity": None,
        }

        # 2. Category breakdown
        cursor.execute(
            """
            SELECT
                COALESCE(NULLIF(`category`, ''), 'UNKNOWN') as category,
                COALESCE(SUM(`amount`), 0) as total_amount,
                COUNT(*) as txn_count
            FROM `unified_transactions`
            WHERE `customer_id` = %s
            GROUP BY `category`
            ORDER BY total_amount DESC
            """,
            (customer_id,)
        )
        cat_rows = cursor.fetchall()

        total_spent = float(stats["total_spending"] or 0.0)
        category_spending_dict = {}
        category_breakdown_list = []

        for cr in cat_rows:
            cat_name = cr["category"]
            amt = float(cr["total_amount"] or 0.0)
            cnt = int(cr["txn_count"] or 0)
            pct = round((amt / total_spent * 100), 2) if total_spent > 0 else 0.0

            category_spending_dict[cat_name] = amt
            category_breakdown_list.append({
                "category": cat_name,
                "total_amount": amt,
                "transaction_count": cnt,
                "percentage_of_total": pct,
            })

        return {
            "customer_id": customer_id,
            "total_transactions": int(stats["total_transactions"] or 0),
            "total_credited_amount": float(stats["total_credited"] or 0.0),
            "total_debited_amount": float(stats["total_debited"] or 0.0),
            "total_spending": total_spent,
            "category_spending": category_spending_dict,
            "category_breakdown": category_breakdown_list,
            "first_activity": stats["first_activity"],
            "last_activity": stats["last_activity"],
        }
    finally:
        cursor.close()
        conn.close()


def aggregate_global_summary() -> Dict[str, Any]:
    """
    Computes global platform-wide intelligence metrics:
    - total customers
    - total transactions
    - total volume (credits + debits)
    - average transaction size
    - top categories
    - top merchants
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Customers count
        cursor.execute("SELECT COUNT(DISTINCT `customer_id`) as cust_cnt FROM `unified_transactions`")
        total_customers = cursor.fetchone()["cust_cnt"]

        # Transaction totals
        cursor.execute(
            """
            SELECT
                COUNT(*) as total_txns,
                COALESCE(SUM(`amount`), 0) as total_volume,
                COALESCE(SUM(CASE WHEN `transaction_type` = 'CREDIT' THEN `amount` ELSE 0 END), 0) as credit_vol,
                COALESCE(SUM(CASE WHEN `transaction_type` IN ('DEBIT', 'PURCHASE', 'BILL_PAYMENT') THEN `amount` ELSE 0 END), 0) as debit_vol,
                COALESCE(AVG(`amount`), 0) as avg_txn_value
            FROM `unified_transactions`
            """
        )
        totals = cursor.fetchone()

        total_txns = int(totals["total_txns"] or 0)
        total_vol = float(totals["total_volume"] or 0.0)

        # Top categories
        cursor.execute(
            """
            SELECT
                COALESCE(NULLIF(`category`, ''), 'UNKNOWN') as category,
                COALESCE(SUM(`amount`), 0) as total_amount,
                COUNT(*) as txn_count
            FROM `unified_transactions`
            GROUP BY `category`
            ORDER BY total_amount DESC
            LIMIT 10
            """
        )
        top_cats = cursor.fetchall()
        category_breakdown = []
        for tc in top_cats:
            amt = float(tc["total_amount"] or 0.0)
            category_breakdown.append({
                "category": tc["category"],
                "total_amount": amt,
                "transaction_count": int(tc["txn_count"] or 0),
                "percentage_of_total": round((amt / total_vol * 100), 2) if total_vol > 0 else 0.0,
            })

        # Top merchants / providers
        cursor.execute(
            """
            SELECT
                COALESCE(NULLIF(`merchant_or_provider`, ''), `source_name`) as merchant,
                COALESCE(SUM(`amount`), 0) as total_amount,
                COUNT(*) as txn_count
            FROM `unified_transactions`
            GROUP BY `merchant`
            ORDER BY total_amount DESC
            LIMIT 10
            """
        )
        top_merchants = cursor.fetchall()

        return {
            "total_customers": total_customers,
            "total_transactions": total_txns,
            "total_volume_inr": total_vol,
            "total_credit_volume": float(totals["credit_vol"] or 0.0),
            "total_debit_volume": float(totals["debit_vol"] or 0.0),
            "average_transaction_value": round(float(totals["avg_txn_value"] or 0.0), 2),
            "top_categories": category_breakdown,
            "top_merchants": [
                {
                    "merchant": m["merchant"],
                    "total_amount": float(m["total_amount"] or 0.0),
                    "transaction_count": int(m["txn_count"] or 0),
                }
                for m in top_merchants
            ],
            "recent_activity_count": total_txns,
        }
    finally:
        cursor.close()
        conn.close()


def build_and_persist_customer_profile(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Generates a deterministic Customer Profile from stored transactions,
    computes behavioral and financial metrics, and persists to customer_profiles table idempotently.
    """
    profile_info = fetch_customer_by_id_or_phone(identifier)
    if not profile_info:
        return None

    actual_customer_id = profile_info["customer_id"]
    phone_number = profile_info.get("phone") or identifier

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Fetch all unified transactions for customer
        cursor.execute(
            """
            SELECT `transaction_id`, `source_name`, `transaction_type`, `category`,
                   `subcategory`, `transaction_date`, `amount`, `currency`,
                   `payment_method`, `merchant_or_provider`, `classification_confidence`,
                   `raw_message`
            FROM `unified_transactions`
            WHERE `customer_id` = %s
            ORDER BY `transaction_date` ASC
            """,
            (actual_customer_id,)
        )
        txns = cursor.fetchall()
        total_events = len(txns)

        # 2. Segregate Income vs Expense
        income_txns = [t for t in txns if (t.get("transaction_type") or "").upper() == "CREDIT"]
        expense_txns = [t for t in txns if (t.get("transaction_type") or "").upper() in ("DEBIT", "PURCHASE", "BILL_PAYMENT", "INVESTMENT")]
        all_txns_with_amount = [t for t in txns if float(t.get("amount") or 0.0) > 0]

        total_transactions = len(all_txns_with_amount) if all_txns_with_amount else (len(income_txns) + len(expense_txns))
        total_spend = sum(float(t.get("amount") or 0.0) for t in expense_txns)
        total_income = sum(float(t.get("amount") or 0.0) for t in income_txns)
        income_count = len(income_txns)
        expense_count = len(expense_txns)

        expense_amounts = [float(t.get("amount") or 0.0) for t in expense_txns if float(t.get("amount") or 0.0) > 0]
        all_positive_amounts = [float(t.get("amount") or 0.0) for t in txns if float(t.get("amount") or 0.0) > 0]

        avg_txn_amount = round(sum(expense_amounts) / len(expense_amounts), 2) if expense_amounts else 0.00
        largest_txn = max(all_positive_amounts) if all_positive_amounts else 0.00
        smallest_txn = min(all_positive_amounts) if all_positive_amounts else 0.00

        # 3. Category Intelligence
        category_spending_dict = {}
        category_counts = {}
        for t in expense_txns:
            cat = t.get("category") or "UNKNOWN"
            amt = float(t.get("amount") or 0.0)
            category_spending_dict[cat] = category_spending_dict.get(cat, 0.0) + amt
            category_counts[cat] = category_counts.get(cat, 0) + 1

        top_categories = []
        for cat, amt in sorted(category_spending_dict.items(), key=lambda x: x[1], reverse=True):
            pct = round((amt / total_spend * 100), 2) if total_spend > 0 else 0.0
            top_categories.append({
                "category": cat,
                "total_amount": round(amt, 2),
                "transaction_count": category_counts.get(cat, 0),
                "percentage_of_total": pct
            })

        top_category_name = top_categories[0]["category"] if top_categories else (
            txns[0].get("category") if txns else "UNKNOWN"
        )

        # 4. Merchant Intelligence
        merchant_spending = {}
        merchant_counts = {}
        for t in txns:
            m = t.get("merchant_or_provider") or t.get("source_name") or "UNKNOWN"
            amt = float(t.get("amount") or 0.0)
            merchant_spending[m] = merchant_spending.get(m, 0.0) + amt
            merchant_counts[m] = merchant_counts.get(m, 0) + 1

        top_merchants = []
        for m, amt in sorted(merchant_spending.items(), key=lambda x: x[1], reverse=True):
            pct = round((amt / total_spend * 100), 2) if total_spend > 0 else 0.0
            top_merchants.append({
                "merchant": m,
                "total_amount": round(amt, 2),
                "transaction_count": merchant_counts.get(m, 0),
                "percentage_of_total": pct
            })
        merchant_count = len(merchant_spending)

        # 5. Recurring Payment Pattern Detection
        recurring_patterns = {}
        for t in txns:
            m = t.get("merchant_or_provider") or t.get("source_name")
            amt = round(float(t.get("amount") or 0.0), 0)
            if m and amt > 0:
                key = (m, amt)
                recurring_patterns[key] = recurring_patterns.get(key, 0) + 1

        recurring_payment_count = sum(1 for count in recurring_patterns.values() if count >= 2)

        # 6. Activity & Frequency
        dates = [t["transaction_date"] for t in txns if t.get("transaction_date")]
        first_date = min(dates) if dates else None
        last_date = max(dates) if dates else None

        if total_transactions >= 10:
            frequency = "High"
        elif total_transactions >= 3:
            frequency = "Moderate"
        elif total_transactions >= 1:
            frequency = "Low"
        else:
            frequency = "Inactive"

        recent_activity = "Active" if total_transactions > 0 else "Inactive"

        # 7. Data Quality & Confidence Scoring
        quality_score = 0.0
        if total_events >= 5:
            quality_score += 0.4
        elif total_events >= 2:
            quality_score += 0.2
        else:
            quality_score += 0.1

        known_amounts = sum(1 for t in txns if float(t.get("amount") or 0.0) > 0)
        if total_events > 0 and (known_amounts / total_events) >= 0.7:
            quality_score += 0.3
        elif total_events > 0:
            quality_score += 0.1

        known_categories = sum(1 for t in txns if t.get("category") and t.get("category") != "UNKNOWN")
        if total_events > 0 and (known_categories / total_events) >= 0.7:
            quality_score += 0.2

        if first_date is not None:
            quality_score += 0.1

        if quality_score >= 0.75:
            data_quality = "HIGH"
        elif quality_score >= 0.45:
            data_quality = "MEDIUM"
        else:
            data_quality = "LOW"

        conf_scores = [float(t.get("classification_confidence") or 1.0) for t in txns if t.get("classification_confidence") is not None]
        avg_confidence = round(sum(conf_scores) / len(conf_scores), 2) if conf_scores else 1.00

        # 8. Deterministic Financial Summary Text
        if total_transactions > 0:
            top_cat_str = f" Highest spending category is {top_category_name} (₹{category_spending_dict.get(top_category_name, 0.0):,.2f})." if top_category_name != "UNKNOWN" else ""
            rec_str = f" Detected {recurring_payment_count} recurring payment patterns." if recurring_payment_count > 0 else ""
            summary_text = (
                f"Customer has {total_transactions} detected transactions across {merchant_count} merchants "
                f"with total spending of ₹{total_spend:,.2f} (average ₹{avg_txn_amount:,.2f}).{top_cat_str}{rec_str} "
                f"Activity status: {recent_activity} ({frequency} frequency)."
            )
        else:
            summary_text = f"Customer has {total_events} informational alerts and no active financial debits recorded."

        # 9. Save / Upsert to customer_profiles table (Idempotent)
        import json
        top_cats_json = json.dumps(top_categories[:10])
        top_merch_json = json.dumps(top_merchants[:10])
        spending_cats_json = json.dumps(category_spending_dict)

        cursor.execute(
            """
            INSERT INTO `customer_profiles`
            (`customer_id`, `phone_number`, `total_events`, `total_transactions`,
             `total_spend`, `total_income`, `income_count`, `expense_count`,
             `average_transaction_amount`, `largest_transaction_amount`, `smallest_transaction_amount`,
             `top_category`, `top_categories_json`, `top_merchants_json`, `spending_categories_json`,
             `merchant_count`, `recurring_payment_count`, `transaction_frequency`, `recent_activity`,
             `first_activity_date`, `last_activity_date`, `financial_activity_summary`,
             `data_quality`, `confidence`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                `phone_number` = VALUES(`phone_number`),
                `total_events` = VALUES(`total_events`),
                `total_transactions` = VALUES(`total_transactions`),
                `total_spend` = VALUES(`total_spend`),
                `total_income` = VALUES(`total_income`),
                `income_count` = VALUES(`income_count`),
                `expense_count` = VALUES(`expense_count`),
                `average_transaction_amount` = VALUES(`average_transaction_amount`),
                `largest_transaction_amount` = VALUES(`largest_transaction_amount`),
                `smallest_transaction_amount` = VALUES(`smallest_transaction_amount`),
                `top_category` = VALUES(`top_category`),
                `top_categories_json` = VALUES(`top_categories_json`),
                `top_merchants_json` = VALUES(`top_merchants_json`),
                `spending_categories_json` = VALUES(`spending_categories_json`),
                `merchant_count` = VALUES(`merchant_count`),
                `recurring_payment_count` = VALUES(`recurring_payment_count`),
                `transaction_frequency` = VALUES(`transaction_frequency`),
                `recent_activity` = VALUES(`recent_activity`),
                `first_activity_date` = VALUES(`first_activity_date`),
                `last_activity_date` = VALUES(`last_activity_date`),
                `financial_activity_summary` = VALUES(`financial_activity_summary`),
                `data_quality` = VALUES(`data_quality`),
                `confidence` = VALUES(`confidence`),
                `updated_at` = CURRENT_TIMESTAMP
            """,
            (
                actual_customer_id, phone_number, total_events, total_transactions,
                total_spend, total_income, income_count, expense_count,
                avg_txn_amount, largest_txn, smallest_txn,
                top_category_name, top_cats_json, top_merch_json, spending_cats_json,
                merchant_count, recurring_payment_count, frequency, recent_activity,
                first_date, last_date, summary_text,
                data_quality, avg_confidence
            )
        )
        conn.commit()

        # 10. Fetch Extensible Common Customer Model Components
        from backend.app.modules.analytics.identity_service import get_customer_identities, get_customer_attributes
        from backend.app.modules.analytics.feature_engine import get_customer_materialized_features

        identities = get_customer_identities(actual_customer_id, cursor=cursor, conn=conn)
        attributes = get_customer_attributes(actual_customer_id, cursor=cursor, conn=conn)
        features = get_customer_materialized_features(actual_customer_id, cursor=cursor, conn=conn)
        feature_map = {f["feature_id"]: f["value_numeric"] if f["value_numeric"] is not None else f["value_string"] for f in features}


        # Build response DTO format
        return {
            "customer_id": actual_customer_id,
            "phone_number": phone_number,
            "full_name": profile_info.get("full_name"),
            "email": profile_info.get("email"),
            "city": profile_info.get("city"),
            "state": profile_info.get("state"),
            "total_events": total_events,
            "total_transactions": total_transactions,
            "total_spend": float(total_spend),
            "total_income": float(total_income),
            "income_count": income_count,
            "expense_count": expense_count,
            "average_transaction_amount": float(avg_txn_amount),
            "largest_transaction_amount": float(largest_txn),
            "smallest_transaction_amount": float(smallest_txn),
            "top_category": top_category_name,
            "top_categories": top_categories,
            "top_merchants": top_merchants,
            "spending_categories": category_spending_dict,
            "merchant_count": merchant_count,
            "recurring_payment_count": recurring_payment_count,
            "transaction_frequency": frequency,
            "recent_activity": recent_activity,
            "first_activity_date": first_date,
            "last_activity_date": last_date,
            "financial_activity_summary": summary_text,
            "data_quality": data_quality,
            "confidence": float(avg_confidence),
            "identities": identities,
            "attributes": attributes,
            "features": features,
            "feature_map": feature_map,
            "created_at": profile_info.get("created_at"),
            "updated_at": datetime.now(),
        }

    finally:
        cursor.close()
        conn.close()


def fetch_customer_profile_from_db(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves stored profile from customer_profiles table, or generates on demand if not present.
    """
    profile_info = fetch_customer_by_id_or_phone(identifier)
    if not profile_info:
        return None

    actual_customer_id = profile_info["customer_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT * FROM `customer_profiles`
            WHERE `customer_id` = %s
            """,
            (actual_customer_id,)
        )
        row = cursor.fetchone()
        if not row:
            # Generate and persist on-demand
            return build_and_persist_customer_profile(actual_customer_id)

        import json
        top_cats = json.loads(row.get("top_categories_json") or "[]") if isinstance(row.get("top_categories_json"), str) else (row.get("top_categories_json") or [])
        top_merch = json.loads(row.get("top_merchants_json") or "[]") if isinstance(row.get("top_merchants_json"), str) else (row.get("top_merchants_json") or [])
        spending_cats = json.loads(row.get("spending_categories_json") or "{}") if isinstance(row.get("spending_categories_json"), str) else (row.get("spending_categories_json") or {})

        from backend.app.modules.analytics.identity_service import get_customer_identities, get_customer_attributes
        from backend.app.modules.analytics.feature_engine import get_customer_materialized_features

        identities = get_customer_identities(actual_customer_id, cursor=cursor, conn=conn)
        attributes = get_customer_attributes(actual_customer_id, cursor=cursor, conn=conn)
        features = get_customer_materialized_features(actual_customer_id, cursor=cursor, conn=conn)
        feature_map = {f["feature_id"]: f["value_numeric"] if f["value_numeric"] is not None else f["value_string"] for f in features}


        return {
            "customer_id": row["customer_id"],
            "phone_number": row.get("phone_number") or profile_info.get("phone"),
            "full_name": profile_info.get("full_name"),
            "email": profile_info.get("email"),
            "city": profile_info.get("city"),
            "state": profile_info.get("state"),
            "total_events": int(row.get("total_events") or 0),
            "total_transactions": int(row.get("total_transactions") or 0),
            "total_spend": float(row.get("total_spend") or 0.0),
            "total_income": float(row.get("total_income") or 0.0),
            "income_count": int(row.get("income_count") or 0),
            "expense_count": int(row.get("expense_count") or 0),
            "average_transaction_amount": float(row.get("average_transaction_amount") or 0.0),
            "largest_transaction_amount": float(row.get("largest_transaction_amount") or 0.0),
            "smallest_transaction_amount": float(row.get("smallest_transaction_amount") or 0.0),
            "top_category": row.get("top_category"),
            "top_categories": top_cats,
            "top_merchants": top_merch,
            "spending_categories": spending_cats,
            "merchant_count": int(row.get("merchant_count") or 0),
            "recurring_payment_count": int(row.get("recurring_payment_count") or 0),
            "transaction_frequency": row.get("transaction_frequency") or "Low",
            "recent_activity": row.get("recent_activity") or "Active",
            "first_activity_date": row.get("first_activity_date"),
            "last_activity_date": row.get("last_activity_date"),
            "financial_activity_summary": row.get("financial_activity_summary"),
            "data_quality": row.get("data_quality") or "MEDIUM",
            "confidence": float(row.get("confidence") or 1.0),
            "identities": identities,
            "attributes": attributes,
            "features": features,
            "feature_map": feature_map,
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }

    finally:
        cursor.close()
        conn.close()


def list_customer_profiles_from_db(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Returns paginated list of generated customer profiles from DB.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT cp.*, c.`full_name`, c.`email`, c.`city`, c.`state`
            FROM `customer_profiles` cp
            LEFT JOIN `customers` c ON cp.`customer_id` = c.`customer_id`
            ORDER BY cp.`total_spend` DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset)
        )
        rows = cursor.fetchall()
        import json
        profiles = []
        for row in rows:
            top_cats = json.loads(row.get("top_categories_json") or "[]") if isinstance(row.get("top_categories_json"), str) else (row.get("top_categories_json") or [])
            top_merch = json.loads(row.get("top_merchants_json") or "[]") if isinstance(row.get("top_merchants_json"), str) else (row.get("top_merchants_json") or [])
            spending_cats = json.loads(row.get("spending_categories_json") or "{}") if isinstance(row.get("spending_categories_json"), str) else (row.get("spending_categories_json") or {})

            profiles.append({
                "customer_id": row["customer_id"],
                "phone_number": row.get("phone_number"),
                "full_name": row.get("full_name"),
                "email": row.get("email"),
                "city": row.get("city"),
                "state": row.get("state"),
                "total_events": int(row.get("total_events") or 0),
                "total_transactions": int(row.get("total_transactions") or 0),
                "total_spend": float(row.get("total_spend") or 0.0),
                "total_income": float(row.get("total_income") or 0.0),
                "income_count": int(row.get("income_count") or 0),
                "expense_count": int(row.get("expense_count") or 0),
                "average_transaction_amount": float(row.get("average_transaction_amount") or 0.0),
                "largest_transaction_amount": float(row.get("largest_transaction_amount") or 0.0),
                "smallest_transaction_amount": float(row.get("smallest_transaction_amount") or 0.0),
                "top_category": row.get("top_category"),
                "top_categories": top_cats,
                "top_merchants": top_merch,
                "spending_categories": spending_cats,
                "merchant_count": int(row.get("merchant_count") or 0),
                "recurring_payment_count": int(row.get("recurring_payment_count") or 0),
                "transaction_frequency": row.get("transaction_frequency") or "Low",
                "recent_activity": row.get("recent_activity") or "Active",
                "first_activity_date": row.get("first_activity_date"),
                "last_activity_date": row.get("last_activity_date"),
                "financial_activity_summary": row.get("financial_activity_summary"),
                "data_quality": row.get("data_quality") or "MEDIUM",
                "confidence": float(row.get("confidence") or 1.0),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
            })
        return profiles
    finally:
        cursor.close()
        conn.close()

