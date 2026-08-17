from enum import Enum


class ClassificationDomainEnum(str, Enum):
    FINANCIAL = "FINANCIAL"
    BANKING = "BANKING"
    COMMERCE = "COMMERCE"
    E_COMMERCE = "E_COMMERCE"
    RETAIL = "RETAIL"
    FOOD_DELIVERY = "FOOD_DELIVERY"
    QUICK_COMMERCE = "QUICK_COMMERCE"
    TRAVEL = "TRAVEL"
    LIFESTYLE = "LIFESTYLE"
    HEALTHCARE = "HEALTHCARE"
    EDUCATION = "EDUCATION"
    AUTOMOTIVE = "AUTOMOTIVE"
    REAL_ESTATE = "REAL_ESTATE"
    UTILITIES = "UTILITIES"
    INVESTMENTS = "INVESTMENTS"
    INSURANCE = "INSURANCE"
    TELECOM = "TELECOM"
    ENTERTAINMENT = "ENTERTAINMENT"
    UNKNOWN = "UNKNOWN"


class ConfidenceLevel:
    EXACT_MATCH = 1.00    # Direct match on known merchant/platform dictionary
    STRONG_KEYWORD = 0.85 # Strong keyword or pattern in merchant name/description
    INFERRED = 0.70       # Inferred from transaction_type + source_domain combination
    WEAK_MATCH = 0.40     # Partial/weak token match
    UNKNOWN = 0.00        # Unrecognized record
