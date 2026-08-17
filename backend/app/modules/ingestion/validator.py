import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from backend.app.modules.ingestion.cleaner import clean_string, clean_amount, clean_date


def compute_record_hash(customer_id: Any, txn_date: Any, amount: Any, source_name: Any, merchant: Any) -> str:
    """Computes a unique SHA-256 hash signature for deduplication."""
    cid = str(customer_id or "").strip()
    dt = str(txn_date or "").strip()
    src = str(source_name or "GENERIC_SOURCE").strip().upper()
    merch = str(merchant or "GENERIC_MERCHANT").strip().upper()
    try:
        amt_float = float(amount) if amount is not None else 0.0
    except (ValueError, TypeError):
        amt_float = 0.0
    raw_str = f"{cid}|{dt}|{amt_float:.2f}|{src}|{merch}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def compute_sms_record_hash(
    phone: Any,
    sender: Any,
    message: Any,
    timestamp: Any
) -> str:
    """
    Deterministic hash for SMS records using phone + sender + message text + timestamp.
    Used for deduplication of SMS/communication records.
    """
    ph = str(phone or "").strip()
    snd = str(sender or "").strip().upper()
    # Use first 200 chars of message to avoid excessive hashing cost
    msg = str(message or "")[:200].strip()
    ts = str(timestamp or "").strip()
    raw_str = f"{ph}|{snd}|{msg}|{ts}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def validate_customer_record(row: Dict[str, Any], row_num: int) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Validates a row intended for the master customers table."""
    errors = []
    customer_id = clean_string(row.get("customer_id"))
    full_name = clean_string(row.get("full_name") or row.get("name"))
    email = clean_string(row.get("email"))
    phone = clean_string(row.get("phone") or row.get("mobile"))
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


def validate_sms_record(
    parsed: Dict[str, Any],
    row_num: int,
    domain: str,
    source_name: str,
    txn_type: str,
    confidence: Optional[float] = None
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validates and prepares an already-parsed SMS record for CDM storage.

    IMPORTANT: This validator is LENIENT for SMS records.
    - Records are only rejected if they are completely empty / unprocessable.
    - Missing amount → defaults to 0.0 (informational SMS is valid).
    - Missing date → defaults to current UTC.
    - Missing customer_id → uses CUST_UNKNOWN (never rejects on this alone).
    - Raw message is preserved regardless.
    """
    errors = []

    # 1. Customer ID — use fallback, never reject for this alone on SMS
    customer_id = clean_string(
        parsed.get("customer_id")
        or parsed.get("phone")
        or parsed.get("phoneNumber")
    ) or "CUST_UNKNOWN"

    # 2. Raw message — must have SOME content to be processable
    raw_message = clean_string(parsed.get("raw_message") or parsed.get("text") or parsed.get("message")) or ""

    # 3. Reject ONLY if both sender and message are completely absent
    raw_sender = clean_string(parsed.get("raw_sender") or parsed.get("source_name") or "")
    if not raw_message and not raw_sender:
        errors.append({
            "row": row_num,
            "field": "text",
            "error": "SMS record has no message text and no sender — cannot process",
            "raw_value": str(parsed)[:200]
        })
        return None, errors

    # 4. Date — fallback to current UTC, never reject
    raw_date = (
        parsed.get("transaction_date")
        or parsed.get("updateAt")
        or parsed.get("timestamp")
        or parsed.get("date")
    )
    if raw_date:
        cleaned_date = clean_date(str(raw_date))
    else:
        cleaned_date = None

    if not cleaned_date:
        cleaned_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # 5. Amount — default 0.0 for informational SMS (OTP, alerts, promotions)
    raw_amt = parsed.get("amount")
    if raw_amt is not None and str(raw_amt).strip() not in ("", "None"):
        amount, _ = clean_amount(raw_amt)
        if amount is None:
            amount = 0.0  # Unparseable amount → default, not rejection
    else:
        amount = 0.0

    # 6. Source name and merchant
    final_source_name = clean_string(
        source_name
        or parsed.get("source_name")
        or parsed.get("sender")
        or "UNKNOWN_SENDER"
    ) or "UNKNOWN_SENDER"

    merchant = clean_string(
        parsed.get("merchant_or_provider")
        or parsed.get("channel_or_merchant")
        or final_source_name
    ) or final_source_name

    # 7. Category
    category = clean_string(
        parsed.get("category")
        or domain
    ) or domain or "UNKNOWN"

    subcategory = clean_string(parsed.get("subcategory"))
    location = clean_string(parsed.get("location") or parsed.get("city"))
    payment_method = clean_string(parsed.get("payment_method"))

    # 8. Deduplication hash — SMS-specific: phone + sender + message + timestamp
    record_hash = compute_sms_record_hash(
        phone=customer_id,
        sender=final_source_name,
        message=raw_message,
        timestamp=cleaned_date
    )

    # 9. Transaction ID — use existing ID from raw record or generate from hash
    txn_id = clean_string(
        parsed.get("transaction_id")
        or parsed.get("id")
        or parsed.get("txn_id")
    ) or f"SMS_{record_hash[:12].upper()}"

    cleaned_record = {
        "transaction_id": txn_id,
        "customer_id": customer_id,
        "source_domain": domain or "UNKNOWN",
        "source_name": final_source_name,
        "transaction_type": txn_type or "PURCHASE",
        "category": category,
        "subcategory": subcategory,
        "transaction_date": cleaned_date,
        "amount": amount,
        "currency": "INR",
        "payment_method": payment_method,
        "merchant_or_provider": merchant,
        "location": location,
        "status": "COMPLETED",
        "raw_message": raw_message,
        "classification_confidence": confidence if confidence is not None else 1.0,
        "record_hash": record_hash
    }

    return cleaned_record, []


def validate_transaction_record(
    row: Dict[str, Any],
    row_num: int,
    domain: str,
    source_name: str,
    txn_type: str,
    confidence: Optional[float] = None
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validates and standardizes a structured transaction record into CDM structure.
    Used for structured CSVs (banking, e-commerce, food delivery etc.).
    """
    errors = []

    # 1. Customer ID Check
    raw_cid = row.get("customer_id") or row.get("customerId") or row.get("cust_id") or row.get("phone")
    customer_id = clean_string(raw_cid)
    if not customer_id:
        errors.append({
            "row": row_num,
            "field": "customer_id",
            "error": "Missing required customer_id",
            "raw_value": str(raw_cid)
        })

    # 2. Date Check
    raw_date = (
        row.get("transaction_date")
        or row.get("txn_date")
        or row.get("order_date")
        or row.get("date")
        or row.get("bill_date")
        or row.get("timestamp")
        or row.get("created_at")
    )

    if raw_date:
        cleaned_date = clean_date(raw_date)
        if not cleaned_date:
            errors.append({
                "row": row_num,
                "field": "transaction_date",
                "error": f"Invalid or missing transaction date format: '{raw_date}'",
                "raw_value": str(raw_date)
            })
    else:
        # Fallback to current UTC datetime for records without date
        cleaned_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # 3. Amount Check
    raw_amt = (
        row.get("amount")
        or row.get("order_amount")
        or row.get("total_paid")
        or row.get("amount_paid")
        or row.get("total")
    )
    if raw_amt is not None and str(raw_amt).strip() != "":
        amount, _ = clean_amount(raw_amt)
        if amount is None:
            errors.append({
                "row": row_num,
                "field": "amount",
                "error": f"Invalid transaction amount: '{raw_amt}'",
                "raw_value": str(raw_amt)
            })
    else:
        amount = 0.0

    if errors:
        return None, errors

    # Extract merchant/provider & source name
    final_source_name = clean_string(
        source_name
        or row.get("source_name")
        or row.get("platform")
        or row.get("app_name")
        or row.get("provider")
        or row.get("sender")
        or "GENERIC_SOURCE"
    ) or "GENERIC_SOURCE"

    merchant = clean_string(
        row.get("merchant_or_provider")
        or row.get("channel_or_merchant")
        or row.get("restaurant")
        or row.get("platform")
        or row.get("provider")
        or row.get("scheme_name")
        or final_source_name
    ) or final_source_name

    category = clean_string(
        row.get("category")
        or row.get("item_category")
        or row.get("utility_type")
        or row.get("investment_type")
        or domain
    ) or domain

    subcategory = clean_string(row.get("subcategory") or row.get("cuisine") or row.get("product_name"))
    location = clean_string(row.get("location") or row.get("city") or row.get("delivery_city"))
    payment_method = clean_string(row.get("payment_mode") or row.get("payment_method") or row.get("payment_channel"))

    # Compute record hash
    record_hash = compute_record_hash(
        customer_id=customer_id,
        txn_date=cleaned_date,
        amount=amount,
        source_name=final_source_name,
        merchant=merchant
    )

    txn_id = clean_string(
        row.get("transaction_id")
        or row.get("txn_id")
        or row.get("order_id")
        or row.get("bill_id")
        or row.get("trade_id")
    ) or f"TXN_{record_hash[:12].upper()}"

    cleaned_record = {
        "transaction_id": txn_id,
        "customer_id": customer_id,
        "source_domain": domain or "UNKNOWN",
        "source_name": final_source_name,
        "transaction_type": txn_type or "PURCHASE",
        "category": category,
        "subcategory": subcategory,
        "transaction_date": cleaned_date,
        "amount": amount,
        "currency": "INR",
        "payment_method": payment_method,
        "merchant_or_provider": merchant,
        "location": location,
        "status": "COMPLETED",
        "raw_message": None,  # No raw_message for structured records
        "classification_confidence": confidence if confidence is not None else 1.0,
        "record_hash": record_hash
    }

    return cleaned_record, []
