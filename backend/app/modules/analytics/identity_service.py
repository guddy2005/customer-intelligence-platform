import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.app.database.connection import get_db_connection

logger = logging.getLogger("identity_service")


def resolve_or_create_customer(
    identity_type: str,
    identity_value: str,
    default_name: Optional[str] = None
) -> str:
    """
    Resolves an identity (phone, email, UPI VPA, loyalty ID, etc.) to a canonical customer_id.
    If the identity is unknown, automatically registers a new customer and identity link.
    """
    id_type = identity_type.strip().upper()
    id_val = identity_value.strip()
    if not id_val:
        return "CUST_UNKNOWN"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Check Identity Graph
        cursor.execute(
            """
            SELECT `customer_id` FROM `customer_identities`
            WHERE `identity_type` = %s AND `identity_value` = %s
            LIMIT 1
            """,
            (id_type, id_val)
        )
        row = cursor.fetchone()
        if row:
            return row["customer_id"]

        # 2. Check if customer_id directly matches in customers table
        cursor.execute(
            """
            SELECT `customer_id` FROM `customers`
            WHERE `customer_id` = %s OR `phone` = %s
            LIMIT 1
            """,
            (id_val, id_val)
        )
        cust_row = cursor.fetchone()
        if cust_row:
            resolved_id = cust_row["customer_id"]
        else:
            # 3. Create new customer master row
            resolved_id = id_val if id_type == "PHONE" else f"CUST_{abs(hash(id_val)) % 1000000:06d}"
            name = default_name or f"Customer {id_val[-6:] if len(id_val) >= 6 else id_val}"
            phone = id_val if id_type == "PHONE" else None
            email = id_val if id_type == "EMAIL" else None

            cursor.execute(
                """
                INSERT INTO `customers` (`customer_id`, `full_name`, `phone`, `email`)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE `full_name` = COALESCE(VALUES(`full_name`), `full_name`)
                """,
                (resolved_id, name, phone, email)
            )

        # 4. Link identity in Identity Graph
        cursor.execute(
            """
            INSERT INTO `customer_identities`
            (`customer_id`, `identity_type`, `identity_value`, `is_primary`, `confidence`)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                `customer_id` = VALUES(`customer_id`),
                `confidence` = VALUES(`confidence`),
                `updated_at` = CURRENT_TIMESTAMP
            """,
            (resolved_id, id_type, id_val, True if id_type == "PHONE" else False, 1.00)
        )
        conn.commit()
        return resolved_id

    finally:
        cursor.close()
        conn.close()


def link_customer_identity(
    customer_id: str,
    identity_type: str,
    identity_value: str,
    confidence: float = 1.0,
    is_primary: bool = False
) -> Dict[str, Any]:
    """
    Explicitly links a new identity (e.g. email, phone, bank account) to a customer.
    """
    id_type = identity_type.strip().upper()
    id_val = identity_value.strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            INSERT INTO `customer_identities`
            (`customer_id`, `identity_type`, `identity_value`, `is_primary`, `confidence`)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                `customer_id` = VALUES(`customer_id`),
                `is_primary` = VALUES(`is_primary`),
                `confidence` = VALUES(`confidence`),
                `updated_at` = CURRENT_TIMESTAMP
            """,
            (customer_id, id_type, id_val, is_primary, confidence)
        )
        conn.commit()
        return {
            "customer_id": customer_id,
            "identity_type": id_type,
            "identity_value": id_val,
            "is_primary": is_primary,
            "confidence": confidence,
            "status": "LINKED"
        }
    finally:
        cursor.close()
        conn.close()


def get_customer_identities(customer_id: str, cursor = None, conn = None) -> List[Dict[str, Any]]:
    """
    Fetches all linked identities for a customer from the Identity Graph.
    """
    should_close = False
    if cursor is None or conn is None:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        should_close = True
    try:
        cursor.execute(
            """
            SELECT `identity_type`, `identity_value`, `is_primary`, `confidence`, `verified_at`, `created_at`
            FROM `customer_identities`
            WHERE `customer_id` = %s
            ORDER BY `is_primary` DESC, `created_at` ASC
            """,
            (customer_id,)
        )
        raw_rows = cursor.fetchall() or []
        identities = [r for r in raw_rows if isinstance(r, dict) and "identity_type" in r]
        if not identities:
            # Fallback to customer table
            cursor.execute(
                "SELECT `phone`, `email` FROM `customers` WHERE `customer_id` = %s",
                (customer_id,)
            )
            c_row = cursor.fetchone()
            if c_row and isinstance(c_row, dict):
                if c_row.get("phone"):
                    identities.append({
                        "identity_type": "PHONE",
                        "identity_value": c_row["phone"],
                        "is_primary": True,
                        "confidence": 1.0,
                        "verified_at": None,
                        "created_at": None
                    })
                if c_row.get("email"):
                    identities.append({
                        "identity_type": "EMAIL",
                        "identity_value": c_row["email"],
                        "is_primary": False,
                        "confidence": 1.0,
                        "verified_at": None,
                        "created_at": None
                    })
        return identities
    finally:
        if should_close:
            cursor.close()
            conn.close()


def set_customer_attribute(
    customer_id: str,
    attribute_name: str,
    attribute_value: Any,
    data_type: str = "STRING",
    source: str = "SYSTEM",
    cursor = None,
    conn = None
) -> Dict[str, Any]:
    """
    Sets a dynamic attribute for a customer in the extensible customer_attributes store.
    """
    val_str = json.dumps(attribute_value) if isinstance(attribute_value, (dict, list)) else str(attribute_value)

    should_close = False
    if cursor is None or conn is None:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        should_close = True
    try:
        cursor.execute(
            """
            INSERT INTO `customer_attributes`
            (`customer_id`, `attribute_name`, `attribute_value`, `data_type`, `source`)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                `attribute_value` = VALUES(`attribute_value`),
                `data_type` = VALUES(`data_type`),
                `source` = VALUES(`source`),
                `updated_at` = CURRENT_TIMESTAMP
            """,
            (customer_id, attribute_name, val_str, data_type.upper(), source)
        )
        if should_close:
            conn.commit()
        return {
            "customer_id": customer_id,
            "attribute_name": attribute_name,
            "attribute_value": attribute_value,
            "data_type": data_type.upper(),
            "source": source
        }
    finally:
        if should_close:
            cursor.close()
            conn.close()


def get_customer_attributes(customer_id: str, cursor = None, conn = None) -> Dict[str, Any]:
    """
    Retrieves all dynamic attributes for a customer as a clean key-value dictionary.
    """
    should_close = False
    if cursor is None or conn is None:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        should_close = True
    try:
        cursor.execute(
            """
            SELECT `attribute_name`, `attribute_value`, `data_type`
            FROM `customer_attributes`
            WHERE `customer_id` = %s
            """,
            (customer_id,)
        )
        raw_rows = cursor.fetchall() or []
        rows = [r for r in raw_rows if isinstance(r, dict) and "attribute_name" in r]
        attributes = {}
        for r in rows:
            name = r["attribute_name"]
            val_raw = r.get("attribute_value")
            dtype = r.get("data_type", "STRING")

            if dtype == "NUMBER":
                try:
                    attributes[name] = float(val_raw) if "." in str(val_raw) else int(val_raw)
                except Exception:
                    attributes[name] = val_raw
            elif dtype == "BOOLEAN":
                attributes[name] = str(val_raw).lower() in ("true", "1", "yes")
            elif dtype == "JSON":
                try:
                    attributes[name] = json.loads(val_raw)
                except Exception:
                    attributes[name] = val_raw
            else:
                attributes[name] = val_raw
        return attributes
    finally:
        if should_close:
            cursor.close()
            conn.close()


