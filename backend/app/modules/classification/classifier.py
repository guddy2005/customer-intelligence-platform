import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from backend.app.modules.classification.constants import (
    ClassificationDomainEnum as Domain,
    ConfidenceLevel,
)
from backend.app.modules.classification.rules import (
    EXACT_MERCHANT_RULES,
    KEYWORD_RULES,
    DOMAIN_FALLBACKS,
)

logger = logging.getLogger("classification_engine")


class BaseClassifier(ABC):
    """
    Abstract classifier interface allowing rule-based or future ML models
    to be plugged in seamlessly.
    """

    @abstractmethod
    def classify(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies a single normalized CDM record.
        """
        pass


class RuleBasedClassificationEngine(BaseClassifier):
    """
    Extensible rule-based engine that infers domain, category, subcategory,
    and a confidence score from multi-dimensional CDM signals.
    """

    def __init__(self):
        self.exact_rules = EXACT_MERCHANT_RULES
        self.keyword_rules = KEYWORD_RULES
        self.domain_fallbacks = DOMAIN_FALLBACKS

    def classify(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes hierarchical classification pipeline on a normalized record:
        1. Exact Merchant / Platform Match (Score: 1.00)
        2. Strong Keyword / Pattern Match in text & merchant (Score: 0.85)
        3. Domain / Transaction Type Fallback (Score: 0.70)
        4. Unknown Signal Handling (Score: 0.00)
        """
        if not isinstance(record, dict):
            return self._unknown_result(record)

        # Extract normalized signals safely
        merchant = str(
            record.get("merchant_or_provider")
            or record.get("channel_or_merchant")
            or record.get("restaurant")
            or record.get("provider")
            or record.get("scheme_name")
            or record.get("platform")
            or ""
        ).strip()

        source_name = str(
            record.get("source_name")
            or record.get("platform")
            or record.get("app_name")
            or record.get("provider")
            or record.get("sender")
            or ""
        ).strip()

        category = str(
            record.get("category")
            or record.get("investment_type")
            or record.get("utility_type")
            or record.get("item_category")
            or ""
        ).strip()

        subcategory = str(
            record.get("subcategory")
            or record.get("scheme_name")
            or record.get("cuisine")
            or record.get("product_name")
            or ""
        ).strip()

        source_domain = str(record.get("source_domain") or "").strip().upper()
        txn_type = str(
            record.get("transaction_type")
            or record.get("txn_type")
            or record.get("investment_type")
            or record.get("utility_type")
            or ""
        ).strip().upper()

        merchant_upper = merchant.upper()
        source_upper = source_name.upper()


        # Concatenate text tokens for pattern evaluation
        search_text = f"{merchant_upper} {source_upper} {category.upper()} {subcategory.upper()} {txn_type}".strip()

        # ----------------------------------------------------
        # Stage 1: Exact Merchant / Known Brand Lookup
        # ----------------------------------------------------
        for target_key in (merchant_upper, source_upper):
            if not target_key:
                continue

            # A. Exact Match
            if target_key in self.exact_rules:
                domain, cat, subcat, conf = self.exact_rules[target_key]
                refined_cat, refined_subcat = self._refine_category(cat, subcat, category, subcategory)
                return {
                    "transaction_id": record.get("transaction_id"),
                    "customer_id": record.get("customer_id"),
                    "source_domain": domain,
                    "source_name": source_name or target_key,
                    "transaction_type": txn_type or "PURCHASE",
                    "category": refined_cat,
                    "subcategory": refined_subcat,
                    "confidence": conf
                }

            # B. Known Brand Substring / Prefix Match (e.g., 'IndiGo Flight Booking' -> INDIGO)
            for brand_key, (domain, cat, subcat, conf) in self.exact_rules.items():
                if len(brand_key) >= 3 and (target_key == brand_key or target_key.startswith(brand_key + " ") or f" {brand_key} " in f" {target_key} "):
                    refined_cat, refined_subcat = self._refine_category(cat, subcat, category, subcategory)
                    return {
                        "transaction_id": record.get("transaction_id"),
                        "customer_id": record.get("customer_id"),
                        "source_domain": domain,
                        "source_name": source_name or brand_key,
                        "transaction_type": txn_type or "PURCHASE",
                        "category": refined_cat,
                        "subcategory": refined_subcat,
                        "confidence": conf
                    }

        # ----------------------------------------------------
        # Stage 2: Keyword / Regex Pattern Matching
        # ----------------------------------------------------
        if search_text:
            for pattern, domain, cat, subcat, conf in self.keyword_rules:
                if re.search(pattern, search_text, re.IGNORECASE):
                    refined_cat, refined_subcat = self._refine_category(cat, subcat, category, subcategory)
                    return {
                        "transaction_id": record.get("transaction_id"),
                        "customer_id": record.get("customer_id"),
                        "source_domain": domain,
                        "source_name": source_name or merchant or "KEYWORD_DETECTED",
                        "transaction_type": txn_type or "TRANSACTION",
                        "category": refined_cat,
                        "subcategory": refined_subcat,
                        "confidence": conf
                    }

        # ----------------------------------------------------
        # Stage 3: Source Domain Fallback Inference
        # ----------------------------------------------------
        if source_domain in self.domain_fallbacks:
            domain, cat, subcat, conf = self.domain_fallbacks[source_domain]
            refined_cat = category.upper() if category and category.upper() != "UNKNOWN" else cat
            refined_subcat = subcategory.upper() if subcategory else subcat
            return {
                "transaction_id": record.get("transaction_id"),
                "customer_id": record.get("customer_id"),
                "source_domain": domain,
                "source_name": source_name or "DOMAIN_INFERRED",
                "transaction_type": txn_type or "TRANSACTION",
                "category": refined_cat,
                "subcategory": refined_subcat,
                "confidence": conf
            }

        # ----------------------------------------------------
        # Stage 4: Safe Unknown Fallback
        # ----------------------------------------------------
        return self._unknown_result(record)

    def _refine_category(
        self,
        base_cat: str,
        base_subcat: str,
        in_cat: str,
        in_subcat: str
    ) -> Tuple[str, Optional[str]]:
        """
        Preserves fine-grained categories/subcategories from data when available.
        """
        final_cat = base_cat
        final_subcat = base_subcat

        in_cat_upper = in_cat.upper() if in_cat else ""
        in_subcat_upper = in_subcat.upper() if in_subcat else ""

        if in_cat_upper and in_cat_upper not in ("GENERIC", "UNKNOWN", base_cat):
            if base_cat == "INVESTMENT":
                final_subcat = in_cat_upper
            elif base_subcat in ("E_COMMERCE", "FOOD_DELIVERY", "GENERAL", ""):
                final_subcat = in_cat_upper
            else:
                final_cat = in_cat_upper

        if in_subcat_upper:
            final_subcat = in_subcat_upper

        return final_cat, final_subcat

    def _unknown_result(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "transaction_id": record.get("transaction_id") if isinstance(record, dict) else None,
            "customer_id": record.get("customer_id") if isinstance(record, dict) else None,
            "source_domain": Domain.UNKNOWN.value,
            "source_name": record.get("source_name") if isinstance(record, dict) else "UNKNOWN",
            "transaction_type": record.get("transaction_type") if isinstance(record, dict) else "UNKNOWN",
            "category": "UNKNOWN",
            "subcategory": None,
            "confidence": ConfidenceLevel.UNKNOWN
        }


# Singleton engine instance
classification_engine = RuleBasedClassificationEngine()
