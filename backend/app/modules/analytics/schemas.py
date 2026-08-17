# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CustomerProfileDTO(BaseModel):
    customer_id: str
    phone: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    created_at: Optional[datetime] = None


class CategorySpendingDTO(BaseModel):
    category: str
    total_amount: float
    transaction_count: int
    percentage_of_total: float = 0.0


class MerchantSpendingDTO(BaseModel):
    merchant: str
    total_amount: float
    transaction_count: int
    percentage_of_total: float = 0.0


class CustomerSummaryDTO(BaseModel):
    customer_id: str
    phone: Optional[str] = None
    full_name: Optional[str] = None
    total_transactions: int
    total_spending: float
    total_credited_amount: float
    total_debited_amount: float
    category_spending: Dict[str, float] = {}
    category_breakdown: List[CategorySpendingDTO] = []
    first_activity: Optional[datetime] = None
    last_activity: Optional[datetime] = None


class CustomerIdentityDTO(BaseModel):
    identity_type: str
    identity_value: str
    is_primary: bool = False
    confidence: float = 1.0
    verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class LinkIdentityRequest(BaseModel):
    identity_type: str = Field(..., description="Identity type, e.g., PHONE, EMAIL, UPI_VPA, LOYALTY_ID, DEVICE_ID")
    identity_value: str = Field(..., description="Unique identifier value, e.g. +919876543210 or user@example.com")
    is_primary: bool = Field(False, description="Whether this is the primary identifier")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Resolution confidence score")


class CustomerAttributeDTO(BaseModel):
    attribute_name: str
    attribute_value: Any
    data_type: str = "STRING"
    source: str = "SYSTEM"
    updated_at: Optional[datetime] = None


class SetAttributeRequest(BaseModel):
    attribute_name: str = Field(..., description="Attribute key, e.g. demographics.age_group or kyc_tier")
    attribute_value: Any = Field(..., description="Value of the attribute")
    data_type: str = Field("STRING", description="Data type: STRING, NUMBER, BOOLEAN, JSON, DATE")
    source: str = Field("SYSTEM", description="Source provider or subsystem")


class FeatureDefinitionDTO(BaseModel):
    feature_id: str
    display_name: str
    description: Optional[str] = None
    category: str = "FINANCIAL"
    data_type: str = "CURRENCY"
    aggregation_type: str = "SUM"
    time_window: str = "ALL_TIME"
    unit: str = "INR"
    status: str = "ACTIVE"
    version: str = "v1"
    parameters_json: Optional[Dict[str, Any]] = None


class RegisterFeatureRequest(BaseModel):
    feature_id: str = Field(..., description="Unique machine identifier, e.g. travel_frequency, food_share_pct")
    display_name: str = Field(..., description="Human-readable title for UI rendering")
    description: Optional[str] = Field(None, description="Detailed explanation of the feature")
    category: str = Field("FINANCIAL", description="FINANCIAL, BEHAVIORAL, LIFESTYLE, RISK, AFFINITY, GOVERNANCE")
    data_type: str = Field("CURRENCY", description="CURRENCY, NUMBER, PERCENTAGE, STRING, BOOLEAN, JSON")
    aggregation_type: str = Field("SUM", description="SUM, AVG, COUNT, RATIO, RECENCY, RULE, MODEL")
    time_window: str = Field("ALL_TIME", description="ALL_TIME, 30_DAYS, 90_DAYS, 365_DAYS")
    unit: str = Field("INR", description="Unit of measurement: INR, USD, COUNT, PERCENT, SCORE, CADENCE")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Optional custom formula parameters")


class CustomerFeatureValueDTO(BaseModel):
    feature_id: str
    display_name: str
    category: str
    data_type: str
    unit: str
    value_numeric: Optional[float] = None
    value_string: Optional[str] = None
    value_json: Optional[Any] = None
    formatted_value: Optional[str] = None
    confidence: float = 1.0
    version: str = "v1"
    calculated_at: Optional[datetime] = None


class BatchFeatureCalculateRequest(BaseModel):
    customer_ids: Optional[List[str]] = Field(None, description="Target customer IDs (if empty, processes top active customers)")
    feature_ids: Optional[List[str]] = Field(None, description="Specific feature IDs to recalculate (if empty, calculates all active features)")
    limit: int = Field(50, ge=1, le=500, description="Max number of customers to evaluate")


class BatchFeatureCalculateResponse(BaseModel):
    success: bool
    total_customers: int
    features_calculated_count: int
    duration_seconds: float
    reconciliation_passed: bool = True
    customer_ids: List[str] = []


class CustomerProfileDetailDTO(BaseModel):
    customer_id: str
    phone_number: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    total_events: int = 0
    total_transactions: int = 0
    total_spend: float = 0.0
    total_income: float = 0.0
    income_count: int = 0
    expense_count: int = 0
    average_transaction_amount: float = 0.0
    largest_transaction_amount: float = 0.0
    smallest_transaction_amount: float = 0.0
    top_category: Optional[str] = None
    top_categories: List[CategorySpendingDTO] = []
    top_merchants: List[MerchantSpendingDTO] = []
    spending_categories: Dict[str, float] = {}
    merchant_count: int = 0
    recurring_payment_count: int = 0
    transaction_frequency: str = "Low"
    recent_activity: str = "Active"
    first_activity_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None
    financial_activity_summary: Optional[str] = None
    data_quality: str = "MEDIUM"
    confidence: float = 1.0
    # Common Customer Model Extensible Components
    identities: List[CustomerIdentityDTO] = []
    attributes: Dict[str, Any] = {}
    features: List[CustomerFeatureValueDTO] = []
    feature_map: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BatchProfileGenerateResponse(BaseModel):
    success: bool
    total_customers_selected: int
    profiles_generated: int
    profiles_failed: int
    duration_seconds: float
    reconciliation_passed: bool = True
    customer_ids: List[str] = []


class GlobalAnalyticsSummaryDTO(BaseModel):
    total_customers: int
    total_transactions: int
    total_volume_inr: float
    total_credit_volume: float
    total_debit_volume: float
    average_transaction_value: float
    top_categories: List[CategorySpendingDTO] = []
    top_merchants: List[Dict[str, Any]] = []
    recent_activity_count: int = 0


