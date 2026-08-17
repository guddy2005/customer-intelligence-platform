from typing import Dict, Any, Tuple, Optional
from backend.app.modules.ingestion.cleaner import clean_string, clean_amount, clean_date
from backend.app.modules.ingestion.validator import compute_record_hash
from backend.app.core.constants import DomainEnum, TransactionTypeEnum


class Normalizer:
    """
    Translates heterogeneous raw records from various source domains
    (BANKING, E_COMMERCE, FOOD_DELIVERY, INVESTMENT, UTILITIES, CUSTOMER)
    into a standardized Common Data Model (CDM) structure.
    """

    @staticmethod
    def normalize_transaction(
        row: Dict[str, Any],
        domain: str,
        source_name: str,
        txn_type: str
    ) -> Dict[str, Any]:
        """
        Extracts, cleans, and standardizes source-specific fields into the CDM representation.
        """
        # 1. Customer ID
        customer_id = clean_string(
            row.get("customer_id")
            or row.get("customerId")
            or row.get("cust_id")
            or row.get("user_id")
        )

        # 2. Transaction Date
        raw_date = (
            row.get("txn_date")
            or row.get("transaction_date")
            or row.get("order_date")
            or row.get("date")
            or row.get("bill_date")
            or row.get("created_at")
            or row.get("timestamp")
        )
        cleaned_date = clean_date(raw_date)

        # 3. Amount & Currency
        raw_amt = (
            row.get("amount")
            or row.get("order_amount")
            or row.get("total_paid")
            or row.get("amount_paid")
            or row.get("price")
            or row.get("total_amount")
        )
        amount, _ = clean_amount(raw_amt)
        currency = clean_string(row.get("currency")) or "INR"

        # 4. Merchant / Provider / Counterparty
        merchant = clean_string(
            row.get("channel_or_merchant")
            or row.get("restaurant")
            or row.get("platform")
            or row.get("provider")
            or row.get("scheme_name")
            or row.get("merchant")
            or row.get("vendor")
            or source_name
        ) or source_name

        # 5. Category & Subcategory mapping based on domain
        raw_category = (
            row.get("category")
            or row.get("item_category")
            or row.get("utility_type")
            or row.get("investment_type")
            or domain
        )
        category = clean_string(raw_category) or domain

        raw_subcategory = (
            row.get("subcategory")
            or row.get("cuisine")
            or row.get("product_name")
            or row.get("scheme_name")
        )
        subcategory = clean_string(raw_subcategory)

        # 6. Location / Delivery City
        location = clean_string(
            row.get("location")
            or row.get("city")
            or row.get("delivery_city")
            or row.get("state")
        )

        # 7. Payment Mode / Method
        payment_method = clean_string(
            row.get("payment_mode")
            or row.get("payment_method")
            or row.get("payment_channel")
            or row.get("payment_type")
        )

        # 8. Status
        raw_status = clean_string(
            row.get("status")
            or row.get("delivery_status")
            or row.get("order_status")
            or "COMPLETED"
        )
        status = raw_status.upper() if raw_status else "COMPLETED"
        if status in ("SUCCESS", "PAID", "DELIVERED", "EXECUTED"):
            status = "COMPLETED"

        # 9. Deduplication Hash & Transaction Identifier
        record_hash = ""
        if customer_id and cleaned_date and amount is not None:
            record_hash = compute_record_hash(
                customer_id=customer_id,
                txn_date=cleaned_date,
                amount=amount,
                source_name=source_name,
                merchant=merchant
            )

        raw_txn_id = clean_string(
            row.get("txn_id")
            or row.get("transaction_id")
            or row.get("order_id")
            or row.get("bill_id")
            or row.get("trade_id")
        )
        txn_id = raw_txn_id or (f"TXN_{record_hash[:12].upper()}" if record_hash else None)

        return {
            "transaction_id": txn_id,
            "customer_id": customer_id,
            "source_domain": domain,
            "source_name": source_name,
            "transaction_type": txn_type,
            "category": category,
            "subcategory": subcategory,
            "transaction_date": cleaned_date,
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "merchant_or_provider": merchant,
            "location": location,
            "status": status,
            "record_hash": record_hash
        }

    @staticmethod
    def normalize_customer(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardizes customer master entity attributes.
        """
        return {
            "customer_id": clean_string(row.get("customer_id") or row.get("id")),
            "full_name": clean_string(row.get("full_name") or row.get("name")),
            "email": clean_string(row.get("email")),
            "phone": clean_string(row.get("phone") or row.get("mobile")),
            "city": clean_string(row.get("city")),
            "state": clean_string(row.get("state"))
        }
