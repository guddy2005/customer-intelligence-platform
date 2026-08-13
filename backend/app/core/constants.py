from enum import Enum


class DomainEnum(str, Enum):
    BANKING = "BANKING"
    INVESTMENT = "INVESTMENT"
    E_COMMERCE = "E_COMMERCE"
    FOOD_DELIVERY = "FOOD_DELIVERY"
    TRAVEL = "TRAVEL"
    AUTOMOBILE = "AUTOMOBILE"
    REAL_ESTATE = "REAL_ESTATE"
    UTILITIES = "UTILITIES"
    HEALTHCARE = "HEALTHCARE"
    EDUCATION = "EDUCATION"
    RETAIL_LIFESTYLE = "RETAIL_LIFESTYLE"
    CUSTOMER = "CUSTOMER"
    UNKNOWN = "UNKNOWN"


class TransactionTypeEnum(str, Enum):
    DEBIT = "DEBIT"            # Money out
    CREDIT = "CREDIT"          # Money in
    PURCHASE = "PURCHASE"      # Spending
    REFUND = "REFUND"          # Money returned
    INVESTMENT = "INVESTMENT"  # Money invested
    BILL_PAYMENT = "BILL_PAYMENT"
    CASH_WITHDRAWAL = "CASH_WITHDRAWAL"
    UNKNOWN = "UNKNOWN"


class BatchStatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
