import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from backend.app.modules.ingestion.cleaner import clean_string, clean_date, clean_amount

# Sender prefix cleaner: Indian telecom routing codes like AD-HDFCBK, VM-AMAZON, BP-SWIGGY, JK-SmplPL
SENDER_PREFIX_PATTERN = re.compile(r"^[A-Za-z]{2}-", re.IGNORECASE)

# Known sender aliases mapping to canonical provider/source names
SENDER_CANONICAL_MAP = {
    "HDFCBK": "HDFC",
    "HDFCBANK": "HDFC",
    "SBIBNK": "SBI",
    "SBIN": "SBI",
    "ICICIB": "ICICI",
    "ICICIBK": "ICICI",
    "AXISBK": "AXIS",
    "KOTAKB": "KOTAK",
    "PNBSMS": "PNB",
    "PUNBNK": "PNB",
    "YESBNK": "YES BANK",
    "INDBNK": "INDUSIND",
    "AMAZON": "AMAZON",
    "AMZN": "AMAZON",
    "FLIPKT": "FLIPKART",
    "FLIPKART": "FLIPKART",
    "MYNTRA": "MYNTRA",
    "AJIO": "AJIO",
    "NYKAA": "NYKAA",
    "SWIGGY": "SWIGGY",
    "ZOMATO": "ZOMATO",
    "BLINKT": "BLINKIT",
    "BLINKIT": "BLINKIT",
    "ZEPTO": "ZEPTO",
    "SMPLPL": "SIMPL",
    "SIMPL": "SIMPL",
    "VICARE": "VI",
    "VIL": "VI",
    "IRCTC": "IRCTC",
    "INDIGO": "INDIGO",
    "UBER": "UBER",
    "OLACAB": "OLA",
    "RAPIDO": "RAPIDO",
    "BSES": "BSES RAJDHANI",
    "AIRTEL": "AIRTEL",
    "JIO": "JIO",
    "TATAPOWER": "TATA POWER",
    "INDANE": "INDANE GAS",
    "ZERODHA": "ZERODHA",
    "GROWW": "GROWW",
    "ANGELONE": "ANGELONE",
    "APOLLO": "APOLLO PHARMACY",
    "PHARMEASY": "PHARMEASY",
    "1MG": "TATA 1MG",
}


class SMSParser:
    """
    Intelligent communication extractor that parses raw SMS/Message text,
    normalizing unstructured message bodies into structured financial/commerce signals.
    """

    @staticmethod
    def is_sms_record(row: Dict[str, Any]) -> bool:
        """
        Determines if a raw data row represents an SMS/communication message
        rather than an already structured transaction schema.
        """
        if not isinstance(row, dict):
            return False

        keys = set(k.lower().strip() for k in row.keys() if k)
        has_message = any(k in keys for k in ("message", "msg", "sms_text", "body", "text", "sms", "smstext"))
        has_sender = any(k in keys for k in ("sender", "senderaddress", "header", "source", "from"))
        has_txn_structure = all(k in keys for k in ("amount", "transaction_type", "category"))
        
        return (has_message or has_sender) and not has_txn_structure

    @staticmethod
    def clean_sender(raw_sender: Optional[str]) -> str:
        """
        Strips SMS header routing prefixes (e.g., 'AD-HDFCBK' -> 'HDFCBK')
        and maps to canonical source names.
        """
        if not raw_sender:
            return "UNKNOWN_SENDER"

        s = str(raw_sender).strip()
        # Remove routing prefix (e.g. VK-, AD-, BZ-, VM-, JK-)
        s_clean = SENDER_PREFIX_PATTERN.sub("", s).strip().upper()

        return SENDER_CANONICAL_MAP.get(s_clean, s_clean)

    @staticmethod
    def extract_amount(text: str) -> Optional[float]:
        """
        Extracts monetary amounts from various Indian & international SMS patterns.
        Examples:
          'Rs.95.15 on Zomato' -> 95.15
          'Rs 50,000' -> 50000.0
          'Rs. 2,499.00' -> 2499.0
          'INR 650.00' -> 650.0
          '₹ 1,20,000.00' -> 120000.0
          'amount of 800.00' -> 800.0
        """
        if not text:
            return None

        # Regex for currency patterns
        patterns = [
            r"(?:Rs\.?|INR|₹)\s*([0-9,]+(?:\.[0-9]{1,2})?)",
            r"(?:amount(?: of)?|paid|spent|debited by|credited with|fare:?|total:?)\s*(?:Rs\.?|INR|₹)?\s*([0-9,]+(?:\.[0-9]{1,2})?)",
            r"(?:worth|for)\s*(?:Rs\.?|INR|₹)\s*([0-9,]+(?:\.[0-9]{1,2})?)",
        ]

        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                raw_val = match.group(1)
                amt, _ = clean_amount(raw_val)
                if amt is not None and amt > 0:
                    return amt

        return None

    @staticmethod
    def extract_transaction_type(text: str) -> str:
        """
        Detects transaction type from SMS action verbs.
        """
        t = text.lower() if text else ""

        if any(w in t for w in ("credited", "received", "refund", "salary", "cashback", "deposited")):
            return "CREDIT"
        elif any(w in t for w in ("debited", "spent", "withdrawn", "atm wdl", "transferred", "charged")):
            return "DEBIT"
        elif any(w in t for w in ("order placed", "order confirmed", "delivered", "booked", "ticket booked", "bought")):
            return "PURCHASE"
        elif any(w in t for w in ("bill payment", "bill received", "recharge successful", "bill paid")):
            return "BILL_PAYMENT"
        elif any(w in t for w in ("sip executed", "units allocated", "invested", "mutual fund", "shares bought")):
            return "INVESTMENT"
        else:
            return "PURCHASE"

    @staticmethod
    def extract_payment_method(text: str) -> Optional[str]:
        """
        Extracts payment channel from message text.
        """
        t = text.upper() if text else ""
        if "UPI" in t or "VPAY" in t or "GPAY" in t or "GOOGLEPAY" in t or "PHONEPE" in t or "PAYTM" in t:
            return "UPI"
        elif "SIMPL" in t:
            return "BNPL_SIMPL"
        elif "CREDIT CARD" in t or "CC" in t:
            return "CREDIT_CARD"
        elif "DEBIT CARD" in t or "DC" in t or "ATM" in t:
            return "DEBIT_CARD"
        elif "NET BANKING" in t or "NETBANKING" in t or "IMPS" in t or "NEFT" in t or "RTGS" in t:
            return "NET_BANKING"
        elif "AUTO DEBIT" in t or "AUTO-DEBIT" in t or "ACH" in t or "NACH" in t:
            return "AUTO_DEBIT"
        return "DIGITAL"

    @staticmethod
    def extract_merchant_or_provider(sender: str, text: str) -> str:
        """
        Extracts counterparty/merchant name from sender or message context.
        """
        t = text if text else ""
        # Search for patterns like 'on Zomato', 'at <Merchant>', 'from <Merchant>', 'to <Merchant>'
        merchant_match = re.search(r"\b(?:on|at|from|to|with)\s+([A-Z][A-Za-z0-9'\s]{2,25}?)(?:\s+(?:charged|paid|via|on|ref|for|amount|using|dated|\.|\,))", t, re.IGNORECASE)
        if merchant_match:
            cand = merchant_match.group(1).strip()
            if cand.upper() not in ("YOUR", "THE", "AN", "A", "RS", "INR", "ACCOUNT", "A/C", "WHATSAPP"):
                return cand

        # Fallback to cleaned sender
        return sender or "GENERIC_MERCHANT"

    @classmethod
    def parse_sms_record(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms a raw SMS row into a pre-normalized structure ready for Record-Level Classification & CDM storage.
        """
        # 1. Customer ID / Phone
        customer_id = clean_string(
            row.get("customer_id")
            or row.get("customerId")
            or row.get("cust_id")
            or row.get("phoneNumber")
            or row.get("phonenumber")
            or row.get("phone")
            or row.get("user_id")
        ) or "CUST_UNKNOWN"

        # 2. Raw message text and sender
        raw_message = clean_string(
            row.get("message")
            or row.get("text")
            or row.get("msg")
            or row.get("sms_text")
            or row.get("body")
            or ""
        ) or ""

        raw_sender = (
            row.get("sender")
            or row.get("senderAddress")
            or row.get("senderaddress")
            or row.get("header")
            or row.get("source")
            or ""
        )
        canonical_sender = cls.clean_sender(raw_sender)

        # 3. Extract Amount
        amount = cls.extract_amount(raw_message)
        if amount is None:
            explicit_amt = row.get("amount") or row.get("total")
            if explicit_amt is not None:
                amt_val, _ = clean_amount(explicit_amt)
                amount = amt_val
        # Default to 0.0 for informational alerts without amount
        if amount is None:
            amount = 0.0

        # 4. Extract Transaction Type
        txn_type = cls.extract_transaction_type(raw_message)

        # 5. Extract Payment Method
        payment_method = cls.extract_payment_method(raw_message)

        # 6. Extract Merchant / Provider
        merchant = cls.extract_merchant_or_provider(canonical_sender, raw_message)

        # 7. Extract Date / Timestamp
        raw_date = (
            row.get("updateAt")
            or row.get("updateat")
            or row.get("timestamp")
            or row.get("date")
            or row.get("txn_date")
            or row.get("created_at")
        )
        cleaned_date = clean_date(raw_date) if raw_date else None
        if not cleaned_date:
            cleaned_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # 8. Transaction ID / Reference
        raw_txn_id = row.get("id") or row.get("txn_id") or row.get("order_id")

        return {
            "transaction_id": str(raw_txn_id) if raw_txn_id else None,
            "customer_id": customer_id,
            "source_name": canonical_sender,
            "merchant_or_provider": merchant,
            "transaction_type": txn_type,
            "amount": amount,
            "currency": "INR",
            "transaction_date": cleaned_date,
            "payment_method": payment_method,
            "raw_message": raw_message,
            "raw_sender": str(raw_sender),
            "status": "COMPLETED"
        }
