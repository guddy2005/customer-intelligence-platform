import hashlib
from typing import Dict, Any, List, Optional, Tuple
from backend.app.modules.ingestion.cleaner import clean_string, clean_amount, clean_date


def compute_record_hash(customer_id: str, txn_date: str, amount: float, source_name: str, merchant: str) -> str:
    """Computes a unique SHA-256 hash signature for deduplication."""
    raw_str = f"{customer_id.strip()}|{txn_date.strip()}|{amount:.2f}|{source_name.strip().upper()}|{merchant.strip().upper()}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def validate_customer_record(row: Dict[str, Any], row_num: int) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Validates a row intended for the master customers table."""
    errors = []
    customer_id = clean_string(row.get("customer_id"))
    full_name = clean_string(row.get("full_name"))
    email = clean_string(row.get("email"))
    phone = clean_string(row.get("phone"))
    city = clean_string(row.get("city"))
    state = clean_string(row.get("state"))

    if not customer_id:
        errors.append({
            "row": row_num,
            "field": "customer_id",
            "error": "Missing required field 'customer_id'",
            "raw_value": str(row.get("customer_id"))
        })

    if not full_name:
        errors.append({
            "row": row_num,
            "field": "full_name",
            "error": "Missing required field 'full_name'",
            "raw_value": str(row.get("full_name"))
        })

    if errors:
        return None, errors

    clean_data = {
        "customer_id": customer_id,
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "city": city,
        "state": state
    }

    return clean_data, []


def validate_transaction_record(
    row: Dict[str, Any],
    row_num: int,
    domain: str,
    source_name: str,
    txn_type: str
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Validates and prepares a transaction record for CDM storage."""
    errors = []

    # 1. Customer ID Check
    raw_cid = row.get("customer_id")
    customer_id = clean_string(raw_cid)
    if not customer_id:
        errors.append({
            "row": row_num,
            "field": "customer_id",
            "error": "Missing required customer_id",
            "raw_value": str(raw_cid)
        })

    # 2. Date Check
    raw_date = row.get("txn_date") or row.get("order_date") or row.get("date") or row.get("bill_date")
    cleaned_date = clean_date(raw_date)
    if not cleaned_date:
        errors.append({
            "row": row_num,
            "field": "transaction_date",
            "error": f"Invalid or missing transaction date format: '{raw_date}'",
            "raw_value": str(raw_date)
        })

    # 3. Amount Check
    raw_amt = row.get("amount") or row.get("order_amount") or row.get("total_paid") or row.get("amount_paid")
    amount, is_negative = clean_amount(raw_amt)
    if amount is None or amount == 0:
        errors.append({
            "row": row_num,
            "field": "amount",
            "error": f"Invalid transaction amount: '{raw_amt}'",
            "raw_value": str(raw_amt)
        })

    if errors:
        return None, errors

    # Extract merchant/provider & category
    merchant = clean_string(
        row.get("channel_or_merchant")
        or row.get("restaurant")
        or row.get("platform")
        or row.get("provider")
        or row.get("scheme_name")
        or source_name
    ) or source_name

    category = clean_string(
        row.get("category")
        or row.get("item_category")
        or row.get("utility_type")
        or row.get("investment_type")
        or domain
    ) or domain

    subcategory = clean_string(row.get("subcategory"))
    location = clean_string(row.get("location") or row.get("city") or row.get("delivery_city"))
    payment_method = clean_string(row.get("payment_mode") or row.get("payment_method") or row.get("payment_channel"))

    # Compute record hash
    record_hash = compute_record_hash(
        customer_id=customer_id,
        txn_date=cleaned_date,
        amount=amount,
        source_name=source_name,
        merchant=merchant
    )

    txn_id = clean_string(
        row.get("txn_id")
        or row.get("order_id")
        or row.get("bill_id")
        or row.get("trade_id")
    ) or f"TXN_{record_hash[:12].upper()}"

    cleaned_record = {
        "transaction_id": txn_id,
        "customer_id": customer_id,
        "source_domain": domain,
        "source_name": source_name,
        "transaction_type": txn_type,
        "category": category,
        "subcategory": subcategory,
        "transaction_date": cleaned_date,
        "amount": amount,
        "currency": "INR",
        "payment_method": payment_method,
        "merchant_or_provider": merchant,
        "location": location,
        "status": "COMPLETED",
        "record_hash": record_hash
    }

    return cleaned_record, []
