from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from backend.app.modules.audience.schemas import (
    AttributeDefinitionDTO,
    AudienceCreateRequest,
    AudienceCustomersResponseDTO,
    AudienceDetailDTO,
    AudienceListResponseDTO,
    AudiencePreviewResponseDTO,
    AudienceSummaryDTO,
    AudienceAnalyticsDTO,
    AudienceUpdateRequest,
    MLTrainSegmentationRequest,
    MLTrainSegmentationResponse,
    MLSegmentationResultsResponse,
    MLSegmentationStatusResponse,
)
from backend.app.modules.audience.service import (
    archive_audience,
    create_audience,
    duplicate_audience,
    get_audience,
    get_audience_analytics,
    get_audience_attributes,
    get_audience_customers,
    get_segmentation_results,
    get_segmentation_status,
    list_audiences,
    preview_audience,
    train_segmentation_model,
    update_audience,
)

router = APIRouter(tags=["Audience Segmentation"])


@router.get("/api/audience-attributes", response_model=list[AttributeDefinitionDTO])
@router.get("/audience-attributes", response_model=list[AttributeDefinitionDTO])
def list_attribute_definitions():
    return get_audience_attributes()


@router.get("/api/audiences", response_model=AudienceListResponseDTO)
@router.get("/audiences", response_model=AudienceListResponseDTO)
def list_audiences_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    audience_type: Optional[str] = Query(None),
    sort_by: str = Query("updated_at"),
    sort_order: str = Query("desc"),
):
    return list_audiences(page=page, page_size=page_size, search=search, status=status_filter, audience_type=audience_type, sort_by=sort_by, sort_order=sort_order)


@router.post("/api/audiences", response_model=AudienceDetailDTO, status_code=status.HTTP_201_CREATED)
@router.post("/audiences", response_model=AudienceDetailDTO, status_code=status.HTTP_201_CREATED)
def create_audience_endpoint(request: AudienceCreateRequest):
    return create_audience(request.model_dump())


@router.post("/api/audiences/preview", response_model=AudiencePreviewResponseDTO)
@router.post("/audiences/preview", response_model=AudiencePreviewResponseDTO)
def preview_audience_endpoint(request: AudienceCreateRequest):
    return preview_audience(request.rule_definition.model_dump() if request.rule_definition else None, request.audience_type, request.ml_config)


@router.get("/api/audiences/{audience_id}", response_model=AudienceDetailDTO)
@router.get("/audiences/{audience_id}", response_model=AudienceDetailDTO)
def get_audience_endpoint(audience_id: str):
    audience = get_audience(audience_id)
    if not audience:
        raise HTTPException(status_code=404, detail="Audience not found")
    return audience


@router.put("/api/audiences/{audience_id}", response_model=AudienceDetailDTO)
@router.put("/audiences/{audience_id}", response_model=AudienceDetailDTO)
def update_audience_endpoint(audience_id: str, request: AudienceUpdateRequest):
    audience = update_audience(audience_id, request.model_dump(exclude_unset=True))
    if not audience:
        raise HTTPException(status_code=404, detail="Audience not found")
    return audience


@router.delete("/api/audiences/{audience_id}")
@router.delete("/audiences/{audience_id}")
def archive_audience_endpoint(audience_id: str):
    success = archive_audience(audience_id)
    if not success:
        raise HTTPException(status_code=404, detail="Audience not found")
    return {"success": True}


@router.post("/api/audiences/{audience_id}/duplicate", response_model=AudienceDetailDTO)
@router.post("/audiences/{audience_id}/duplicate", response_model=AudienceDetailDTO)
def duplicate_audience_endpoint(audience_id: str):
    audience = duplicate_audience(audience_id)
    if not audience:
        raise HTTPException(status_code=404, detail="Audience not found")
    return audience


@router.get("/api/audiences/{audience_id}/customers", response_model=AudienceCustomersResponseDTO)
@router.get("/audiences/{audience_id}/customers", response_model=AudienceCustomersResponseDTO)
def get_audience_customers_endpoint(audience_id: str, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100)):
    result = get_audience_customers(audience_id, page=page, page_size=page_size)
    if not result:
        raise HTTPException(status_code=404, detail="Audience not found")
    return result


@router.get("/api/audiences/{audience_id}/analytics", response_model=AudienceAnalyticsDTO)
@router.get("/audiences/{audience_id}/analytics", response_model=AudienceAnalyticsDTO)
def get_audience_analytics_endpoint(audience_id: str):
    result = get_audience_analytics(audience_id)
    if not result:
        raise HTTPException(status_code=404, detail="Audience not found")
    return result


@router.post("/api/ml/segmentation/train", response_model=MLTrainSegmentationResponse)
@router.post("/ml/segmentation/train", response_model=MLTrainSegmentationResponse)
def train_segmentation_endpoint(request: MLTrainSegmentationRequest):
    return train_segmentation_model(k=request.k, feature_ids=request.feature_ids, source_population=request.source_population)


@router.get("/api/ml/segmentation/status", response_model=MLSegmentationStatusResponse)
@router.get("/ml/segmentation/status", response_model=MLSegmentationStatusResponse)
def get_segmentation_status_endpoint():
    return get_segmentation_status()


@router.get("/api/ml/segmentation/results", response_model=MLSegmentationResultsResponse)
@router.get("/ml/segmentation/results", response_model=MLSegmentationResultsResponse)
def get_segmentation_results_endpoint():
    return get_segmentation_results()
