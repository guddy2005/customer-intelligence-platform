from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field


AudienceType = Literal["RULE_BASED", "ML_SEGMENT", "HYBRID"]
AudienceStatus = Literal["DRAFT", "ACTIVE", "ARCHIVED"]
LogicalOperator = Literal["AND", "OR"]


class AttributeDefinitionDTO(BaseModel):
    key: str
    label: str
    category: str
    data_type: str
    operators: List[str] = []
    unit: Optional[str] = None
    control_type: str
    options: List[Dict[str, Any]] = []
    searchable: bool = False
    description: Optional[str] = None
    source: str = "FEATURE_CATALOG"


class AudienceConditionDTO(BaseModel):
    field: str
    operator: str
    value: Any = None


class AudienceRuleGroupDTO(BaseModel):
    combinator: LogicalOperator = "AND"
    conditions: List[AudienceConditionDTO] = Field(default_factory=list)
    groups: List["AudienceRuleGroupDTO"] = Field(default_factory=list)


class AudienceCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    audience_type: AudienceType
    source_population: str = Field(default="ALL_CUSTOMERS")
    status: AudienceStatus = "DRAFT"
    rule_definition: Optional[AudienceRuleGroupDTO] = None
    ml_config: Optional[Dict[str, Any]] = None


class AudienceUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    audience_type: Optional[AudienceType] = None
    source_population: Optional[str] = None
    status: Optional[AudienceStatus] = None
    rule_definition: Optional[AudienceRuleGroupDTO] = None
    ml_config: Optional[Dict[str, Any]] = None


class AudienceSummaryDTO(BaseModel):
    audience_id: str
    name: str
    description: Optional[str] = None
    audience_type: AudienceType
    source_population: str
    status: AudienceStatus
    customer_count: int = 0
    created_at: datetime
    updated_at: datetime
    last_refreshed_at: Optional[datetime] = None


class AudienceListResponseDTO(BaseModel):
    items: List[AudienceSummaryDTO]
    total: int
    page: int
    page_size: int
    summary: Dict[str, Any]


class PreviewSampleCustomerDTO(BaseModel):
    customer_id: str
    full_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    total_spend: float = 0.0
    total_income: float = 0.0
    transaction_count: int = 0
    avg_transaction_value: float = 0.0
    top_category: Optional[str] = None
    transaction_frequency: Optional[str] = None


class AudiencePreviewResponseDTO(BaseModel):
    estimated_customer_count: int
    percentage_of_total_customers: float
    segment_distribution: List[Dict[str, Any]]
    average_customer_value: float
    average_monthly_spend: float
    average_transaction_frequency: float
    average_engagement_score: float
    sample_customers: List[PreviewSampleCustomerDTO]


class AudienceDetailDTO(BaseModel):
    audience: AudienceSummaryDTO
    rule_definition: Optional[Dict[str, Any]] = None
    ml_config: Optional[Dict[str, Any]] = None
    preview: Optional[AudiencePreviewResponseDTO] = None


class AudienceCustomersResponseDTO(BaseModel):
    items: List[PreviewSampleCustomerDTO]
    total: int
    page: int
    page_size: int


class AudienceAnalyticsDTO(BaseModel):
    overview: Dict[str, Any]
    customer_profile: Dict[str, Any]
    ml_insights: Dict[str, Any]
    behavioral_analysis: Dict[str, Any]
    segment_distribution: List[Dict[str, Any]]


class MLTrainSegmentationRequest(BaseModel):
    k: int = Field(default=4, ge=2, le=12)
    feature_ids: Optional[List[str]] = None
    source_population: str = Field(default="ALL_CUSTOMERS")


class MLTrainSegmentationResponse(BaseModel):
    job_id: str
    status: str
    started_at: datetime
    k: int


class MLSegmentationStatusResponse(BaseModel):
    status: str
    last_trained_at: Optional[datetime] = None
    latest_job_id: Optional[str] = None
    cluster_count: int = 0


class MLSegmentationResultDTO(BaseModel):
    segment_id: str
    label: str
    customer_count: int
    characteristics: List[str]
    centroid_metrics: Dict[str, float]


class MLSegmentationResultsResponse(BaseModel):
    status: str
    trained_at: Optional[datetime] = None
    algorithm: str = "K_MEANS"
    segments: List[MLSegmentationResultDTO]


AudienceRuleGroupDTO.model_rebuild()
