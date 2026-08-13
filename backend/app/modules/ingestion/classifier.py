from typing import Dict, Any, Tuple
from backend.app.core.constants import DomainEnum, TransactionTypeEnum


def classify_record(row: Dict[str, Any], domain_hint: str = "AUTO_DETECT") -> Tuple[str, str, str]:
    """
    Classifies a data row into (source_domain, source_name, transaction_type).
    """
    # 1. Determine Source Domain
    domain_str = domain_hint.upper() if domain_hint else "AUTO_DETECT"
    
    if domain_str not in ("AUTO_DETECT", "UNKNOWN", ""):
        try:
            domain = DomainEnum[domain_str].value
        except KeyError:
            domain = DomainEnum.UNKNOWN.value
    else:
        # Auto-detect domain based on keys/fields present in raw row
        row_keys = set(k.lower() for k in row.keys())
        
        if "app_name" in row_keys or "restaurant" in row_keys:
            domain = DomainEnum.FOOD_DELIVERY.value
        elif "platform" in row_keys and ("order_id" in row_keys or "delivery_city" in row_keys):
            domain = DomainEnum.E_COMMERCE.value
        elif "investment_type" in row_keys or "scheme_name" in row_keys or "folio_or_trade_id" in row_keys:
            domain = DomainEnum.INVESTMENT.value
        elif "utility_type" in row_keys or "provider" in row_keys or "bill_id" in row_keys:
            domain = DomainEnum.UTILITIES.value
        elif "full_name" in row_keys or "email" in row_keys:
            domain = DomainEnum.CUSTOMER.value
        elif "txn_type" in row_keys or "channel_or_merchant" in row_keys or "txn_id" in row_keys:
            domain = DomainEnum.BANKING.value
        else:
            domain = DomainEnum.BANKING.value

    # 2. Determine Source Name
    source_name = (
        row.get("source_name")
        or row.get("platform")
        or row.get("app_name")
        or row.get("provider")
        or row.get("channel_or_merchant")
        or row.get("source")
        or "GENERIC_SOURCE"
    )
    source_name = str(source_name).strip().upper()

    # 3. Determine Transaction Type
    raw_type = str(
        row.get("transaction_type")
        or row.get("txn_type")
        or row.get("investment_type")
        or row.get("utility_type")
        or ""
    ).strip().upper()

    if "PURCHASE" in raw_type or domain == DomainEnum.E_COMMERCE.value or domain == DomainEnum.FOOD_DELIVERY.value:
        txn_type = TransactionTypeEnum.PURCHASE.value
    elif "REFUND" in raw_type:
        txn_type = TransactionTypeEnum.REFUND.value
    elif "INVEST" in raw_type or "SIP" in raw_type or "MUTUAL" in raw_type or domain == DomainEnum.INVESTMENT.value:
        txn_type = TransactionTypeEnum.INVESTMENT.value
    elif "BILL" in raw_type or domain == DomainEnum.UTILITIES.value:
        txn_type = TransactionTypeEnum.BILL_PAYMENT.value
    elif "ATM" in raw_type or "CASH" in raw_type:
        txn_type = TransactionTypeEnum.CASH_WITHDRAWAL.value
    elif "CREDIT" in raw_type or "SALARY" in raw_type:
        txn_type = TransactionTypeEnum.CREDIT.value
    elif "DEBIT" in raw_type:
        txn_type = TransactionTypeEnum.DEBIT.value
    else:
        txn_type = TransactionTypeEnum.DEBIT.value

    return domain, source_name, txn_type
