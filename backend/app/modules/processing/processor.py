from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from backend.app.modules.ingestion.parsers.sms_parser import SMSParser
from backend.app.modules.processing.rules import (
    is_transaction_message,
    extract_category_and_subcategory,
)


class BaseProcessor(ABC):
    """
    Abstract interface for data processing and intelligence extraction.
    Allows rule-based processing to be replaced or augmented by ML/NLP models seamlessly.
    """

    @abstractmethod
    def process(self, text: str, sender: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes raw message text and returns extracted signals.
        """
        pass


class RuleBasedProcessor(BaseProcessor):
    """
    Deterministic rule-based processor for baseline processing.
    Extracts transaction detection, transaction type, amount, category, and merchant.
    """

    def process(self, text: str, sender: Optional[str] = None) -> Dict[str, Any]:
        if not text:
            return {
                "transaction_detected": False,
                "transaction_type": "UNKNOWN",
                "amount": 0.0,
                "category": "UNKNOWN",
                "subcategory": None,
                "merchant_or_provider": None,
                "confidence": 0.0,
                "raw_message": text,
            }

        # 1. Detect if it's a transaction
        is_txn = is_transaction_message(text)

        # 2. Extract monetary amount
        amount = SMSParser.extract_amount(text) or 0.0

        # If an amount was extracted > 0, it's very likely a transaction
        if amount > 0:
            is_txn = True

        # 3. Detect transaction type (CREDIT / DEBIT / PURCHASE / etc.)
        txn_type = SMSParser.extract_transaction_type(text) if is_txn else "NON_TRANSACTION"

        # 4. Extract Category and Merchant
        category, subcategory, merchant = extract_category_and_subcategory(text, sender)

        # 5. Extract payment method
        payment_method = SMSParser.extract_payment_method(text)

        # Confidence heuristic
        confidence = 1.0 if (is_txn and amount > 0 and category != "GENERAL") else (0.8 if is_txn else 0.9)

        return {
            "transaction_detected": is_txn,
            "transaction_type": txn_type,
            "amount": amount,
            "category": category,
            "subcategory": subcategory,
            "merchant_or_provider": merchant or (sender.upper() if sender else None),
            "payment_method": payment_method,
            "confidence": confidence,
            "raw_message": text,
        }


# Singleton processor instance
processor = RuleBasedProcessor()
