import re
from typing import Dict, Any, Optional, Tuple, List

# Transaction detection indicator keywords
TRANSACTION_KEYWORDS = [
    r"\bcredited\b", r"\bdebited\b", r"\bspent\b", r"\bpaid\b",
    r"\btransferred\b", r"\bwithdrawn\b", r"\border placed\b",
    r"\border confirmed\b", r"\bbill payment\b", r"\brecharge\b",
    r"\bsip\b", r"\brefund\b", r"\bcashback\b", r"\bpurchase\b",
    r"\bcharged\b", r"\bfare\b", r"\binvested\b", r"\bmutual fund\b",
    r"\baccount ending\b", r"\ba/c\b", r"\bbal:\b", r"\bbalance\b"
]

NON_TRANSACTION_KEYWORDS = [
    r"\botp\b", r"\bverification code\b", r"\bpassword\b",
    r"\blogin\b", r"\bdo not share\b", r"\bcongratulations\b",
    r"\boffer\b", r"\bdiscount\b", r"\bwin\b", r"\bclaim now\b"
]

# Category and entity extraction patterns
CATEGORY_RULES: List[Tuple[str, str, Optional[str]]] = [
    # (regex_pattern, category, subcategory)
    (r"\b(amazon|flipkart|myntra|ajio|meesho|nykaa|tatacliq)\b", "ECOMMERCE", "SHOPPING"),
    (r"\b(swiggy|zomato|domino|mcdonald|kfc|pizza hut|eatclub)\b", "FOOD_DELIVERY", "RESTAURANT"),
    (r"\b(zepto|blinkit|instamart|bbnow|bigbasket)\b", "QUICK_COMMERCE", "GROCERIES"),
    (r"\b(uber|ola|rapido|irctc|indigo|air india|makemytrip|goibibo|redbus)\b", "TRAVEL", "TRANSPORT"),
    (r"\b(electricity|bses|tatapower|cesc|bescom|uppcl|dhbvn|tneb)\b", "UTILITIES", "ELECTRICITY"),
    (r"\b(airtel|jio|vi|vodafone|bsnl|broadband|recharge)\b", "UTILITIES", "TELECOM"),
    (r"\b(indane|bharat gas|hp gas|png|lpg|gas bill)\b", "UTILITIES", "GAS"),
    (r"\b(zerodha|groww|angelone|upstox|kuvera|coin|mutual fund|sip|nifty|sensex)\b", "INVESTMENT", "EQUITY_MF"),
    (r"\b(apollo|pharmeasy|1mg|netmeds|medplus|hospital|pharmacy)\b", "HEALTHCARE", "PHARMACY"),
    (r"\b(petrol|diesel|hpcl|bpcl|iocl|fuel)\b", "AUTOMOBILE", "FUEL"),
    (r"\b(hdfc|sbi|icici|axis|kotak|pnb|bob|canara|yes bank|indusind)\b", "BANKING", "ACCOUNT"),
]


def is_transaction_message(text: str) -> bool:
    """
    Determines whether a message is an actionable financial or commercial transaction.
    """
    if not text:
        return False

    t = text.lower()

    # If it contains clear non-transactional/OTP indicators without monetary context
    has_otp = any(re.search(pat, t) for pat in NON_TRANSACTION_KEYWORDS)
    has_txn = any(re.search(pat, t) for pat in TRANSACTION_KEYWORDS)
    has_currency = bool(re.search(r"(?:rs\.?|inr|₹)\s*[0-9]+", t))

    if has_otp and not has_currency:
        return False

    return has_txn or has_currency


def extract_category_and_subcategory(text: str, sender: Optional[str] = None) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Infers category, subcategory, and merchant entity from text and sender.
    """
    combined = f"{sender or ''} {text or ''}".strip().lower()

    for pattern, cat, subcat in CATEGORY_RULES:
        match = re.search(pattern, combined)
        if match:
            merchant = match.group(1).upper()
            return cat, subcat, merchant

    # Fallbacks
    if any(k in combined for k in ["salary", "credited", "debited", "a/c", "atm"]):
        return "BANKING", "ACCOUNT", sender.upper() if sender else None

    return "GENERAL", None, sender.upper() if sender else None
