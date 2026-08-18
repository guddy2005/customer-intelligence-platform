import json
import math
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from backend.app.database.connection import get_db_connection
from backend.app.modules.analytics.feature_engine import get_registered_features


DEFAULT_ATTRIBUTE_DEFINITIONS = [
    {"key": "city", "label": "City", "category": "geographic", "data_type": "string", "operators": ["=", "!=", "contains"], "unit": None, "control_type": "searchable_select", "searchable": True},
    {"key": "state", "label": "State", "category": "geographic", "data_type": "string", "operators": ["=", "!=", "contains"], "unit": None, "control_type": "searchable_select", "searchable": True},
    {"key": "total_spend", "label": "Total Spend", "category": "financial", "data_type": "number", "operators": [">", "<", "=", ">=", "<=", "between"], "unit": "INR", "control_type": "number", "searchable": False},
    {"key": "total_income", "label": "Total Income", "category": "financial", "data_type": "number", "operators": [">", "<", "=", ">=", "<=", "between"], "unit": "INR", "control_type": "number", "searchable": False},
    {"key": "avg_ticket_size", "label": "Average Transaction Value", "category": "transactional", "data_type": "number", "operators": [">", "<", "=", ">=", "<=", "between"], "unit": "INR", "control_type": "number", "searchable": False},
    {"key": "transaction_count", "label": "Transaction Count", "category": "transactional", "data_type": "number", "operators": [">", "<", "=", ">=", "<=", "between"], "unit": "COUNT", "control_type": "number", "searchable": False},
    {"key": "transaction_frequency", "label": "Transaction Frequency", "category": "behavioral", "data_type": "string", "operators": ["=", "!=", "in"], "unit": None, "control_type": "select", "searchable": False, "options": [{"label": "High", "value": "High"}, {"label": "Moderate", "value": "Moderate"}, {"label": "Low", "value": "Low"}, {"label": "Inactive", "value": "Inactive"}]},
    {"key": "top_spending_category", "label": "Top Spending Category", "category": "category", "data_type": "string", "operators": ["=", "!=", "in", "contains"], "unit": None, "control_type": "searchable_select", "searchable": True},
    {"key": "recurring_subscription_count", "label": "Recurring Subscription Count", "category": "engagement", "data_type": "number", "operators": [">", "<", "=", ">=", "<=", "between"], "unit": "COUNT", "control_type": "number", "searchable": False},
    {"key": "food_spend_share", "label": "Food Spend Share", "category": "category", "data_type": "percentage", "operators": [">", "<", "=", ">=", "<=", "between"], "unit": "%", "control_type": "percentage", "searchable": False},
    {"key": "travel_spend_share", "label": "Travel Spend Share", "category": "category", "data_type": "percentage", "operators": [">", "<", "=", ">=", "<=", "between"], "unit": "%", "control_type": "percentage", "searchable": False},
    {"key": "shopping_spend_share", "label": "Shopping Spend Share", "category": "category", "data_type": "percentage", "operators": [">", "<", "=", ">=", "<=", "between"], "unit": "%", "control_type": "percentage", "searchable": False},
    {"key": "data_quality_grade", "label": "Data Quality Grade", "category": "custom", "data_type": "string", "operators": ["=", "!=", "in"], "unit": None, "control_type": "select", "searchable": False, "options": [{"label": "HIGH", "value": "HIGH"}, {"label": "MEDIUM", "value": "MEDIUM"}, {"label": "LOW", "value": "LOW"}]},
]


FEATURE_TO_CATEGORY = {
    "FINANCIAL": "financial",
    "BEHAVIORAL": "behavioral",
    "LIFESTYLE": "ml_generated",
    "RISK": "ml_generated",
    "AFFINITY": "ml_generated",
    "GOVERNANCE": "custom",
    "TRANSACTIONAL": "transactional",
}


DATA_TYPE_TO_CONTROL = {
    "CURRENCY": ("number", "number", [">", "<", "=", ">=", "<=", "between"]),
    "NUMBER": ("number", "number", [">", "<", "=", ">=", "<=", "between"]),
    "PERCENTAGE": ("percentage", "percentage", [">", "<", "=", ">=", "<=", "between"]),
    "STRING": ("string", "text", ["=", "!=", "contains", "in"]),
    "BOOLEAN": ("boolean", "boolean", ["=", "!="]),
    "JSON": ("json", "searchable_select", ["contains"]),
}


def _json_load(raw: Any, fallback: Any):
    if raw is None:
        return fallback
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return fallback


def ensure_audience_tables() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    statements = [
        """
        CREATE TABLE IF NOT EXISTS `audiences` (
            `audience_id` VARCHAR(64) PRIMARY KEY,
            `name` VARCHAR(255) NOT NULL,
            `description` TEXT NULL,
            `audience_type` VARCHAR(32) NOT NULL,
            `source_population` VARCHAR(100) NOT NULL DEFAULT 'ALL_CUSTOMERS',
            `status` VARCHAR(32) NOT NULL DEFAULT 'DRAFT',
            `rule_definition_json` LONGTEXT NULL,
            `ml_config_json` LONGTEXT NULL,
            `estimated_customer_count` INT NOT NULL DEFAULT 0,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            `last_refreshed_at` DATETIME NULL,
            INDEX `idx_audience_status` (`status`),
            INDEX `idx_audience_type` (`audience_type`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS `audience_snapshots` (
            `snapshot_id` BIGINT AUTO_INCREMENT PRIMARY KEY,
            `audience_id` VARCHAR(64) NOT NULL,
            `snapshot_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            `customer_count` INT NOT NULL DEFAULT 0,
            `analytics_json` LONGTEXT NULL,
            CONSTRAINT `fk_audience_snapshot_audience` FOREIGN KEY (`audience_id`) REFERENCES `audiences`(`audience_id`) ON DELETE CASCADE,
            INDEX `idx_snapshot_audience_date` (`audience_id`, `snapshot_date`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS `ml_segmentation_jobs` (
            `job_id` VARCHAR(64) PRIMARY KEY,
            `algorithm` VARCHAR(32) NOT NULL DEFAULT 'K_MEANS',
            `status` VARCHAR(32) NOT NULL DEFAULT 'COMPLETED',
            `config_json` LONGTEXT NULL,
            `results_json` LONGTEXT NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            `completed_at` DATETIME NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
    ]
    try:
        for stmt in statements:
            cursor.execute(stmt)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def _build_customer_feature_map() -> Dict[str, Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT c.`customer_id`, c.`full_name`, c.`city`, c.`state`,
                   MAX(CASE WHEN cfv.`feature_id` = 'total_spend' THEN cfv.`value_numeric` END) AS total_spend,
                   MAX(CASE WHEN cfv.`feature_id` = 'total_income' THEN cfv.`value_numeric` END) AS total_income,
                   MAX(CASE WHEN cfv.`feature_id` = 'avg_ticket_size' THEN cfv.`value_numeric` END) AS avg_ticket_size,
                   MAX(CASE WHEN cfv.`feature_id` = 'transaction_frequency' THEN cfv.`value_string` END) AS transaction_frequency,
                   MAX(CASE WHEN cfv.`feature_id` = 'top_spending_category' THEN cfv.`value_string` END) AS top_spending_category,
                   MAX(CASE WHEN cfv.`feature_id` = 'recurring_subscription_count' THEN cfv.`value_numeric` END) AS recurring_subscription_count,
                   MAX(CASE WHEN cfv.`feature_id` = 'food_spend_share' THEN cfv.`value_numeric` END) AS food_spend_share,
                   MAX(CASE WHEN cfv.`feature_id` = 'travel_spend_share' THEN cfv.`value_numeric` END) AS travel_spend_share,
                   MAX(CASE WHEN cfv.`feature_id` = 'shopping_spend_share' THEN cfv.`value_numeric` END) AS shopping_spend_share,
                   MAX(CASE WHEN cfv.`feature_id` = 'data_quality_grade' THEN cfv.`value_string` END) AS data_quality_grade,
                   COUNT(DISTINCT ut.`transaction_id`) AS transaction_count,
                   COALESCE(AVG(ut.`amount`), 0) AS average_monthly_spend
            FROM `customers` c
            LEFT JOIN `customer_feature_values` cfv ON c.`customer_id` = cfv.`customer_id`
            LEFT JOIN `unified_transactions` ut ON c.`customer_id` = ut.`customer_id`
            GROUP BY c.`customer_id`, c.`full_name`, c.`city`, c.`state`
            ORDER BY c.`customer_id` ASC
            """
        )
        rows = cursor.fetchall() or []
        result = {}
        for row in rows:
            result[row["customer_id"]] = {
                "customer_id": row["customer_id"],
                "full_name": row.get("full_name"),
                "city": row.get("city"),
                "state": row.get("state"),
                "total_spend": float(row.get("total_spend") or 0.0),
                "total_income": float(row.get("total_income") or 0.0),
                "avg_ticket_size": float(row.get("avg_ticket_size") or 0.0),
                "transaction_frequency": row.get("transaction_frequency") or "Inactive",
                "top_spending_category": row.get("top_spending_category") or "UNKNOWN",
                "recurring_subscription_count": float(row.get("recurring_subscription_count") or 0.0),
                "food_spend_share": float(row.get("food_spend_share") or 0.0),
                "travel_spend_share": float(row.get("travel_spend_share") or 0.0),
                "shopping_spend_share": float(row.get("shopping_spend_share") or 0.0),
                "data_quality_grade": row.get("data_quality_grade") or "LOW",
                "transaction_count": int(row.get("transaction_count") or 0),
                "average_monthly_spend": float(row.get("average_monthly_spend") or 0.0),
                "engagement_score": _derive_engagement_score(row),
                "customer_value_score": _derive_customer_value_score(row),
                "churn_probability": _derive_churn_probability(row),
                "purchase_propensity": _derive_purchase_propensity(row),
                "predicted_customer_value": _derive_predicted_customer_value(row),
                "customer_segment": _derive_customer_segment(row),
                "category_affinity": row.get("top_spending_category") or "UNKNOWN",
                "product_affinity": row.get("top_spending_category") or "UNKNOWN",
                "lifestyle_cluster": _derive_lifestyle_cluster(row),
                "spending_behavior": _derive_spending_behavior(row),
            }
        return result
    finally:
        cursor.close()
        conn.close()


def _derive_engagement_score(row: Dict[str, Any]) -> float:
    txn_count = float(row.get("transaction_count") or 0)
    recurring = float(row.get("recurring_subscription_count") or 0)
    freq = row.get("transaction_frequency") or "Inactive"
    freq_boost = {"High": 32, "Moderate": 22, "Low": 10, "Inactive": 2}.get(freq, 5)
    score = min(100.0, round(freq_boost + min(txn_count, 40) * 1.1 + recurring * 3.5, 2))
    return score


def _derive_customer_value_score(row: Dict[str, Any]) -> float:
    spend = float(row.get("total_spend") or 0)
    income = float(row.get("total_income") or 0)
    avg_ticket = float(row.get("avg_ticket_size") or 0)
    score = min(100.0, round((spend / 10000.0) * 8 + (income / 15000.0) * 4 + (avg_ticket / 3000.0) * 20, 2))
    return score


def _derive_churn_probability(row: Dict[str, Any]) -> float:
    freq = row.get("transaction_frequency") or "Inactive"
    base = {"High": 15, "Moderate": 30, "Low": 55, "Inactive": 80}.get(freq, 60)
    spend = float(row.get("total_spend") or 0)
    modifier = -12 if spend > 100000 else -6 if spend > 50000 else 0
    return float(max(1, min(99, base + modifier)))


def _derive_purchase_propensity(row: Dict[str, Any]) -> float:
    engagement = _derive_engagement_score(row)
    spend = float(row.get("total_spend") or 0)
    return float(min(100, round(engagement * 0.55 + min(spend / 1500.0, 45), 2)))


def _derive_predicted_customer_value(row: Dict[str, Any]) -> float:
    spend = float(row.get("total_spend") or 0)
    propensity = _derive_purchase_propensity(row)
    return round(spend * (1 + propensity / 200.0), 2)


def _derive_customer_segment(row: Dict[str, Any]) -> str:
    spend = float(row.get("total_spend") or 0)
    freq = row.get("transaction_frequency") or "Inactive"
    if spend >= 150000 and freq == "High":
        return "High Value"
    if spend >= 80000:
        return "Growth"
    if freq in ("Low", "Inactive"):
        return "Dormant"
    return "Core"


def _derive_lifestyle_cluster(row: Dict[str, Any]) -> str:
    top_cat = (row.get("top_spending_category") or "UNKNOWN").upper()
    if top_cat in ("TRAVEL", "AUTOMOTIVE", "TRANSIT"):
        return "Mobility Focused"
    if top_cat in ("FOOD", "FOOD_DELIVERY", "DINING"):
        return "Food Lifestyle"
    if top_cat in ("SHOPPING", "ECOMMERCE", "COMMERCE"):
        return "Retail Lifestyle"
    return "General Lifestyle"


def _derive_spending_behavior(row: Dict[str, Any]) -> str:
    spend = float(row.get("total_spend") or 0)
    avg_ticket = float(row.get("avg_ticket_size") or 0)
    if spend > 120000 and avg_ticket > 3000:
        return "Premium"
    if spend > 50000:
        return "Steady"
    return "Value Conscious"


def get_audience_attributes() -> List[Dict[str, Any]]:
    ensure_audience_tables()
    attributes = list(DEFAULT_ATTRIBUTE_DEFINITIONS)
    for feature in get_registered_features():
        data_type, control_type, operators = DATA_TYPE_TO_CONTROL.get(
            feature.get("data_type", "STRING"),
            ("string", "text", ["=", "!=", "contains"]),
        )
        attributes.append({
            "key": feature["feature_id"],
            "label": feature["display_name"],
            "category": FEATURE_TO_CATEGORY.get(feature.get("category", "CUSTOM"), "custom"),
            "data_type": data_type,
            "operators": operators,
            "unit": feature.get("unit"),
            "control_type": control_type,
            "options": [],
            "searchable": control_type in ("searchable_select", "text"),
            "description": feature.get("description"),
            "source": "FEATURE_CATALOG",
        })
    deduped = {}
    for attr in attributes:
        deduped[attr["key"]] = attr
    return sorted(deduped.values(), key=lambda item: (item["category"], item["label"]))


def _compare_value(actual: Any, operator: str, expected: Any) -> bool:
    if operator == "contains":
        return str(expected).lower() in str(actual or "").lower()
    if operator == "in":
        if not isinstance(expected, list):
            expected = [expected]
        return str(actual) in [str(v) for v in expected]
    if operator == "between":
        if not isinstance(expected, list) or len(expected) != 2:
            return False
        low, high = expected
        try:
            actual_num = float(actual or 0)
            return float(low) <= actual_num <= float(high)
        except Exception:
            return False
    if operator in (">", "<", ">=", "<="):
        try:
            actual_num = float(actual or 0)
            expected_num = float(expected)
            if operator == ">":
                return actual_num > expected_num
            if operator == "<":
                return actual_num < expected_num
            if operator == ">=":
                return actual_num >= expected_num
            return actual_num <= expected_num
        except Exception:
            return False
    if operator == "!=":
        return str(actual) != str(expected)
    return str(actual) == str(expected)


def _matches_group(customer: Dict[str, Any], group: Optional[Dict[str, Any]]) -> bool:
    if not group:
        return True
    combinator = (group.get("combinator") or "AND").upper()
    results = []
    for condition in group.get("conditions", []):
        results.append(_compare_value(customer.get(condition.get("field")), condition.get("operator", "="), condition.get("value")))
    for nested in group.get("groups", []):
        results.append(_matches_group(customer, nested))
    if not results:
        return True
    return all(results) if combinator == "AND" else any(results)


def _segment_distribution(customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for customer in customers:
        segment = customer.get("customer_segment") or "Unclassified"
        counts[segment] = counts.get(segment, 0) + 1
    total = len(customers) or 1
    return [
        {"segment": name, "customer_count": count, "percentage": round((count / total) * 100, 2)}
        for name, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)
    ]


def preview_audience(rule_definition: Optional[Dict[str, Any]], audience_type: str = "RULE_BASED", ml_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    customer_map = _build_customer_feature_map()
    customers = list(customer_map.values())
    total_customers = len(customers) or 1

    if audience_type == "ML_SEGMENT":
        target_segments = (ml_config or {}).get("segment_labels") or []
        filtered = [c for c in customers if not target_segments or c.get("customer_segment") in target_segments]
    elif audience_type == "HYBRID":
        target_segments = (ml_config or {}).get("segment_labels") or []
        filtered = [c for c in customers if _matches_group(c, rule_definition) and (not target_segments or c.get("customer_segment") in target_segments)]
    else:
        filtered = [c for c in customers if _matches_group(c, rule_definition)]

    count = len(filtered)
    avg_value = round(sum(c.get("predicted_customer_value", 0.0) for c in filtered) / count, 2) if count else 0.0
    avg_monthly_spend = round(sum(c.get("average_monthly_spend", 0.0) for c in filtered) / count, 2) if count else 0.0
    avg_txn_freq = round(sum(c.get("transaction_count", 0) for c in filtered) / count, 2) if count else 0.0
    avg_engagement = round(sum(c.get("engagement_score", 0.0) for c in filtered) / count, 2) if count else 0.0

    sample_customers = [
        {
            "customer_id": c["customer_id"],
            "full_name": c.get("full_name"),
            "city": c.get("city"),
            "state": c.get("state"),
            "total_spend": c.get("total_spend", 0.0),
            "total_income": c.get("total_income", 0.0),
            "transaction_count": c.get("transaction_count", 0),
            "avg_transaction_value": c.get("avg_ticket_size", 0.0),
            "top_category": c.get("top_spending_category"),
            "transaction_frequency": c.get("transaction_frequency"),
        }
        for c in filtered[:10]
    ]

    return {
        "estimated_customer_count": count,
        "percentage_of_total_customers": round((count / total_customers) * 100, 2) if total_customers else 0.0,
        "segment_distribution": _segment_distribution(filtered),
        "average_customer_value": avg_value,
        "average_monthly_spend": avg_monthly_spend,
        "average_transaction_frequency": avg_txn_freq,
        "average_engagement_score": avg_engagement,
        "sample_customers": sample_customers,
    }


def create_audience(payload: Dict[str, Any]) -> Dict[str, Any]:
    ensure_audience_tables()
    audience_id = f"AUD-{uuid.uuid4().hex[:10].upper()}"
    preview = preview_audience(payload.get("rule_definition"), payload.get("audience_type", "RULE_BASED"), payload.get("ml_config"))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            INSERT INTO `audiences`
            (`audience_id`, `name`, `description`, `audience_type`, `source_population`, `status`, `rule_definition_json`, `ml_config_json`, `estimated_customer_count`, `last_refreshed_at`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                audience_id,
                payload["name"],
                payload.get("description"),
                payload.get("audience_type", "RULE_BASED"),
                payload.get("source_population", "ALL_CUSTOMERS"),
                payload.get("status", "DRAFT"),
                json.dumps(payload.get("rule_definition")) if payload.get("rule_definition") is not None else None,
                json.dumps(payload.get("ml_config")) if payload.get("ml_config") is not None else None,
                int(preview["estimated_customer_count"]),
            ),
        )
        cursor.execute(
            "INSERT INTO `audience_snapshots` (`audience_id`, `customer_count`, `analytics_json`) VALUES (%s, %s, %s)",
            (audience_id, int(preview["estimated_customer_count"]), json.dumps(preview)),
        )
        conn.commit()
        return get_audience(audience_id)
    finally:
        cursor.close()
        conn.close()


def _read_audience_row(audience_id: str) -> Optional[Dict[str, Any]]:
    ensure_audience_tables()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `audiences` WHERE `audience_id` = %s LIMIT 1", (audience_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return row
    finally:
        cursor.close()
        conn.close()


def get_audience(audience_id: str) -> Optional[Dict[str, Any]]:
    row = _read_audience_row(audience_id)
    if not row:
        return None
    rule_definition = _json_load(row.get("rule_definition_json"), None)
    ml_config = _json_load(row.get("ml_config_json"), None)
    preview = preview_audience(rule_definition, row.get("audience_type", "RULE_BASED"), ml_config)
    audience = {
        "audience_id": row["audience_id"],
        "name": row["name"],
        "description": row.get("description"),
        "audience_type": row["audience_type"],
        "source_population": row.get("source_population") or "ALL_CUSTOMERS",
        "status": row.get("status") or "DRAFT",
        "customer_count": int(preview["estimated_customer_count"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "last_refreshed_at": row.get("last_refreshed_at"),
    }
    return {
        "audience": audience,
        "rule_definition": rule_definition,
        "ml_config": ml_config,
        "preview": preview,
    }


def update_audience(audience_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    row = _read_audience_row(audience_id)
    if not row:
        return None
    merged = {
        "name": payload.get("name", row["name"]),
        "description": payload.get("description", row.get("description")),
        "audience_type": payload.get("audience_type", row["audience_type"]),
        "source_population": payload.get("source_population", row.get("source_population") or "ALL_CUSTOMERS"),
        "status": payload.get("status", row.get("status") or "DRAFT"),
        "rule_definition": payload.get("rule_definition", _json_load(row.get("rule_definition_json"), None)),
        "ml_config": payload.get("ml_config", _json_load(row.get("ml_config_json"), None)),
    }
    preview = preview_audience(merged.get("rule_definition"), merged.get("audience_type", "RULE_BASED"), merged.get("ml_config"))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE `audiences`
            SET `name` = %s,
                `description` = %s,
                `audience_type` = %s,
                `source_population` = %s,
                `status` = %s,
                `rule_definition_json` = %s,
                `ml_config_json` = %s,
                `estimated_customer_count` = %s,
                `last_refreshed_at` = NOW()
            WHERE `audience_id` = %s
            """,
            (
                merged["name"],
                merged.get("description"),
                merged["audience_type"],
                merged["source_population"],
                merged["status"],
                json.dumps(merged.get("rule_definition")) if merged.get("rule_definition") is not None else None,
                json.dumps(merged.get("ml_config")) if merged.get("ml_config") is not None else None,
                int(preview["estimated_customer_count"]),
                audience_id,
            ),
        )
        cursor.execute(
            "INSERT INTO `audience_snapshots` (`audience_id`, `customer_count`, `analytics_json`) VALUES (%s, %s, %s)",
            (audience_id, int(preview["estimated_customer_count"]), json.dumps(preview)),
        )
        conn.commit()
        return get_audience(audience_id)
    finally:
        cursor.close()
        conn.close()


def archive_audience(audience_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE `audiences` SET `status` = 'ARCHIVED' WHERE `audience_id` = %s", (audience_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()


def duplicate_audience(audience_id: str) -> Optional[Dict[str, Any]]:
    existing = get_audience(audience_id)
    if not existing:
        return None
    audience = existing["audience"]
    return create_audience({
        "name": f"{audience['name']} Copy",
        "description": audience.get("description"),
        "audience_type": audience["audience_type"],
        "source_population": audience["source_population"],
        "status": "DRAFT",
        "rule_definition": existing.get("rule_definition"),
        "ml_config": existing.get("ml_config"),
    })


def list_audiences(page: int = 1, page_size: int = 10, search: Optional[str] = None, status: Optional[str] = None, audience_type: Optional[str] = None, sort_by: str = "updated_at", sort_order: str = "desc") -> Dict[str, Any]:
    ensure_audience_tables()
    allowed_sort = {"name", "created_at", "updated_at", "estimated_customer_count", "status", "audience_type"}
    if sort_by not in allowed_sort:
        sort_by = "updated_at"
    sort_order = "ASC" if str(sort_order).lower() == "asc" else "DESC"
    offset = (page - 1) * page_size

    where_parts = []
    params: List[Any] = []
    if search:
        where_parts.append("(`name` LIKE %s OR `description` LIKE %s)")
        like = f"%{search}%"
        params.extend([like, like])
    if status:
        where_parts.append("`status` = %s")
        params.append(status)
    if audience_type:
        where_parts.append("`audience_type` = %s")
        params.append(audience_type)
    where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT COUNT(*) AS total FROM `audiences` {where_sql}", tuple(params))
        total = int((cursor.fetchone() or {}).get("total") or 0)
        query_params = params + [page_size, offset]
        cursor.execute(
            f"""
            SELECT `audience_id`, `name`, `description`, `audience_type`, `source_population`, `status`,
                   `estimated_customer_count`, `created_at`, `updated_at`, `last_refreshed_at`
            FROM `audiences`
            {where_sql}
            ORDER BY `{sort_by}` {sort_order}
            LIMIT %s OFFSET %s
            """,
            tuple(query_params),
        )
        rows = cursor.fetchall() or []

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_audiences,
                SUM(CASE WHEN `status` = 'ACTIVE' THEN 1 ELSE 0 END) AS active_audiences,
                COALESCE(SUM(`estimated_customer_count`), 0) AS total_segmented_customers
            FROM `audiences`
            """
        )
        summary_row = cursor.fetchone() or {}

        cursor.execute(
            """
            SELECT DATE(`created_at`) AS created_date, COUNT(*) AS audience_count
            FROM `audiences`
            GROUP BY DATE(`created_at`)
            ORDER BY created_date DESC
            LIMIT 7
            """
        )
        growth = list(reversed(cursor.fetchall() or []))

        cursor.execute(
            """
            SELECT `name`, `estimated_customer_count`
            FROM `audiences`
            ORDER BY `estimated_customer_count` DESC, `updated_at` DESC
            LIMIT 5
            """
        )
        top_segments = cursor.fetchall() or []

        return {
            "items": [
                {
                    "audience_id": row["audience_id"],
                    "name": row["name"],
                    "description": row.get("description"),
                    "audience_type": row["audience_type"],
                    "source_population": row.get("source_population") or "ALL_CUSTOMERS",
                    "status": row.get("status") or "DRAFT",
                    "customer_count": int(row.get("estimated_customer_count") or 0),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "last_refreshed_at": row.get("last_refreshed_at"),
                }
                for row in rows
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": {
                "total_audiences": int(summary_row.get("total_audiences") or 0),
                "active_audiences": int(summary_row.get("active_audiences") or 0),
                "total_segmented_customers": int(summary_row.get("total_segmented_customers") or 0),
                "recent_growth": [
                    {"date": str(item.get("created_date")), "audience_count": int(item.get("audience_count") or 0)}
                    for item in growth
                ],
                "top_segments": [
                    {"name": item.get("name"), "customer_count": int(item.get("estimated_customer_count") or 0)}
                    for item in top_segments
                ],
            },
        }
    finally:
        cursor.close()
        conn.close()


def get_audience_customers(audience_id: str, page: int = 1, page_size: int = 25) -> Optional[Dict[str, Any]]:
    detail = get_audience(audience_id)
    if not detail:
        return None
    preview = detail["preview"]
    total = int(preview["estimated_customer_count"])
    customer_map = _build_customer_feature_map()
    customers = list(customer_map.values())
    if detail["audience"]["audience_type"] == "ML_SEGMENT":
        target_segments = (detail.get("ml_config") or {}).get("segment_labels") or []
        filtered = [c for c in customers if not target_segments or c.get("customer_segment") in target_segments]
    elif detail["audience"]["audience_type"] == "HYBRID":
        target_segments = (detail.get("ml_config") or {}).get("segment_labels") or []
        filtered = [c for c in customers if _matches_group(c, detail.get("rule_definition")) and (not target_segments or c.get("customer_segment") in target_segments)]
    else:
        filtered = [c for c in customers if _matches_group(c, detail.get("rule_definition"))]
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]
    return {
        "items": [
            {
                "customer_id": c["customer_id"],
                "full_name": c.get("full_name"),
                "city": c.get("city"),
                "state": c.get("state"),
                "total_spend": c.get("total_spend", 0.0),
                "total_income": c.get("total_income", 0.0),
                "transaction_count": c.get("transaction_count", 0),
                "avg_transaction_value": c.get("avg_ticket_size", 0.0),
                "top_category": c.get("top_spending_category"),
                "transaction_frequency": c.get("transaction_frequency"),
            }
            for c in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_audience_analytics(audience_id: str) -> Optional[Dict[str, Any]]:
    detail = get_audience(audience_id)
    if not detail:
        return None
    preview = detail["preview"]
    customer_map = _build_customer_feature_map()
    customers = list(customer_map.values())
    if detail["audience"]["audience_type"] == "ML_SEGMENT":
        target_segments = (detail.get("ml_config") or {}).get("segment_labels") or []
        filtered = [c for c in customers if not target_segments or c.get("customer_segment") in target_segments]
    elif detail["audience"]["audience_type"] == "HYBRID":
        target_segments = (detail.get("ml_config") or {}).get("segment_labels") or []
        filtered = [c for c in customers if _matches_group(c, detail.get("rule_definition")) and (not target_segments or c.get("customer_segment") in target_segments)]
    else:
        filtered = [c for c in customers if _matches_group(c, detail.get("rule_definition"))]

    count = len(filtered) or 1
    geography_counts: Dict[str, int] = {}
    category_counts: Dict[str, int] = {}
    lifecycle_counts: Dict[str, int] = {}
    spend_buckets = {"0-25K": 0, "25K-50K": 0, "50K-100K": 0, "100K+": 0}
    for c in filtered:
        geography = c.get("state") or "Unknown"
        geography_counts[geography] = geography_counts.get(geography, 0) + 1
        category = c.get("top_spending_category") or "UNKNOWN"
        category_counts[category] = category_counts.get(category, 0) + 1
        lifecycle = c.get("transaction_frequency") or "Inactive"
        lifecycle_counts[lifecycle] = lifecycle_counts.get(lifecycle, 0) + 1
        spend = c.get("total_spend", 0.0)
        if spend < 25000:
            spend_buckets["0-25K"] += 1
        elif spend < 50000:
            spend_buckets["25K-50K"] += 1
        elif spend < 100000:
            spend_buckets["50K-100K"] += 1
        else:
            spend_buckets["100K+"] += 1

    dominant_segment = max((item for item in preview["segment_distribution"]), key=lambda item: item["customer_count"], default={"segment": "Unclassified"})

    return {
        "overview": {
            "audience_size": preview["estimated_customer_count"],
            "growth": {"last_7_days": max(0, math.floor(preview["estimated_customer_count"] * 0.08)), "trend": "up" if preview["estimated_customer_count"] else "flat"},
            "customer_value": preview["average_customer_value"],
            "engagement": preview["average_engagement_score"],
            "spending": preview["average_monthly_spend"],
        },
        "customer_profile": {
            "geography": [{"label": k, "value": v} for k, v in sorted(geography_counts.items(), key=lambda item: item[1], reverse=True)[:8]],
            "behavioral_patterns": [{"label": k, "value": v} for k, v in lifecycle_counts.items()],
            "transaction_behavior": [{"label": k, "value": v} for k, v in spend_buckets.items()],
            "top_categories": [{"label": k, "value": v} for k, v in sorted(category_counts.items(), key=lambda item: item[1], reverse=True)[:8]],
        },
        "ml_insights": {
            "dominant_segment": dominant_segment.get("segment"),
            "average_churn_risk": round(sum(c.get("churn_probability", 0.0) for c in filtered) / count, 2),
            "average_purchase_propensity": round(sum(c.get("purchase_propensity", 0.0) for c in filtered) / count, 2),
            "top_affinity": max(category_counts.items(), key=lambda item: item[1])[0] if category_counts else "UNKNOWN",
            "predicted_value": preview["average_customer_value"],
        },
        "behavioral_analysis": {
            "spending_trend": [{"label": bucket, "value": value} for bucket, value in spend_buckets.items()],
            "transaction_frequency": [{"label": k, "value": v} for k, v in lifecycle_counts.items()],
            "category_distribution": [{"label": k, "value": v} for k, v in sorted(category_counts.items(), key=lambda item: item[1], reverse=True)[:8]],
            "engagement": [{"label": "Average Engagement Score", "value": preview["average_engagement_score"]}],
            "customer_lifecycle": [{"label": k, "value": v} for k, v in lifecycle_counts.items()],
        },
        "segment_distribution": preview["segment_distribution"],
    }


def _load_latest_segmentation() -> Optional[Dict[str, Any]]:
    ensure_audience_tables()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM `ml_segmentation_jobs` ORDER BY `created_at` DESC LIMIT 1")
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def _euclidean(p1: List[float], p2: List[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))


def _mean(points: List[List[float]]) -> List[float]:
    if not points:
        return []
    dims = len(points[0])
    return [sum(point[i] for point in points) / len(points) for i in range(dims)]


def _label_cluster(centroid: Dict[str, float]) -> Tuple[str, List[str]]:
    descriptors = []
    if centroid["frequency"] >= 25:
        descriptors.append("High frequency")
    elif centroid["frequency"] >= 8:
        descriptors.append("Medium frequency")
    else:
        descriptors.append("Low frequency")

    if centroid["monetary"] >= 100000:
        descriptors.append("High monetary value")
    elif centroid["monetary"] >= 40000:
        descriptors.append("Medium monetary value")
    else:
        descriptors.append("Low monetary value")

    if centroid["engagement"] >= 75:
        descriptors.append("High engagement")
    elif centroid["engagement"] >= 45:
        descriptors.append("Medium engagement")
    else:
        descriptors.append("Low engagement")

    if "High monetary value" in descriptors and "High frequency" in descriptors:
        label = "High Value Loyalists"
    elif "Low engagement" in descriptors and "Low frequency" in descriptors:
        label = "Dormant Opportunities"
    elif "Medium monetary value" in descriptors and "High engagement" in descriptors:
        label = "Engaged Growth Customers"
    else:
        label = "Behavior Cluster"
    return label, descriptors


def train_segmentation_model(k: int = 4, feature_ids: Optional[List[str]] = None, source_population: str = "ALL_CUSTOMERS") -> Dict[str, Any]:
    ensure_audience_tables()
    customer_map = _build_customer_feature_map()
    customers = list(customer_map.values())
    points = []
    refs = []
    for customer in customers:
        point = [
            float(customer.get("transaction_count", 0)),
            float(customer.get("total_spend", 0.0)),
            float(customer.get("average_monthly_spend", 0.0)),
            float(customer.get("avg_ticket_size", 0.0)),
            float(customer.get("engagement_score", 0.0)),
            float(customer.get("travel_spend_share", 0.0) + customer.get("shopping_spend_share", 0.0) + customer.get("food_spend_share", 0.0)),
        ]
        points.append(point)
        refs.append(customer)
    if not points:
        job_id = f"MLJOB-{uuid.uuid4().hex[:10].upper()}"
        return {"job_id": job_id, "status": "COMPLETED", "started_at": datetime.utcnow(), "k": k}

    k = min(k, len(points))
    centroids = [points[i][:] for i in range(k)]
    assignments = [0] * len(points)
    for _ in range(10):
        for idx, point in enumerate(points):
            distances = [_euclidean(point, centroid) for centroid in centroids]
            assignments[idx] = distances.index(min(distances))
        for cluster_idx in range(k):
            cluster_points = [point for idx, point in enumerate(points) if assignments[idx] == cluster_idx]
            if cluster_points:
                centroids[cluster_idx] = _mean(cluster_points)

    segments = []
    for cluster_idx in range(k):
        cluster_customers = [refs[idx] for idx, assignment in enumerate(assignments) if assignment == cluster_idx]
        if not cluster_customers:
            continue
        centroid_metrics = {
            "frequency": round(sum(c.get("transaction_count", 0) for c in cluster_customers) / len(cluster_customers), 2),
            "monetary": round(sum(c.get("total_spend", 0.0) for c in cluster_customers) / len(cluster_customers), 2),
            "monthly_spend": round(sum(c.get("average_monthly_spend", 0.0) for c in cluster_customers) / len(cluster_customers), 2),
            "avg_transaction_value": round(sum(c.get("avg_ticket_size", 0.0) for c in cluster_customers) / len(cluster_customers), 2),
            "engagement": round(sum(c.get("engagement_score", 0.0) for c in cluster_customers) / len(cluster_customers), 2),
            "category_diversity": round(sum(1 if c.get("top_spending_category") else 0 for c in cluster_customers) / len(cluster_customers), 2),
        }
        label, descriptors = _label_cluster(centroid_metrics)
        segments.append({
            "segment_id": f"cluster_{cluster_idx + 1}",
            "label": label if label != "Behavior Cluster" else f"Cluster {cluster_idx + 1}",
            "customer_count": len(cluster_customers),
            "characteristics": descriptors,
            "centroid_metrics": centroid_metrics,
        })

    job_id = f"MLJOB-{uuid.uuid4().hex[:10].upper()}"
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO `ml_segmentation_jobs` (`job_id`, `algorithm`, `status`, `config_json`, `results_json`, `completed_at`)
            VALUES (%s, 'K_MEANS', 'COMPLETED', %s, %s, NOW())
            """,
            (job_id, json.dumps({"k": k, "feature_ids": feature_ids or [], "source_population": source_population}), json.dumps({"segments": segments})),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return {"job_id": job_id, "status": "COMPLETED", "started_at": datetime.utcnow(), "k": k}


def get_segmentation_status() -> Dict[str, Any]:
    latest = _load_latest_segmentation()
    if not latest:
        return {"status": "NOT_TRAINED", "last_trained_at": None, "latest_job_id": None, "cluster_count": 0}
    results = _json_load(latest.get("results_json"), {"segments": []})
    return {
        "status": latest.get("status") or "COMPLETED",
        "last_trained_at": latest.get("completed_at") or latest.get("created_at"),
        "latest_job_id": latest.get("job_id"),
        "cluster_count": len(results.get("segments", [])),
    }


def get_segmentation_results() -> Dict[str, Any]:
    latest = _load_latest_segmentation()
    if not latest:
        return {"status": "NOT_TRAINED", "trained_at": None, "algorithm": "K_MEANS", "segments": []}
    results = _json_load(latest.get("results_json"), {"segments": []})
    return {
        "status": latest.get("status") or "COMPLETED",
        "trained_at": latest.get("completed_at") or latest.get("created_at"),
        "algorithm": latest.get("algorithm") or "K_MEANS",
        "segments": results.get("segments", []),
    }
