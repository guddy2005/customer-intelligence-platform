# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, status, Query, Body
from typing import Optional, List, Dict, Any

from backend.app.modules.analytics.schemas import (
    CustomerProfileDTO,
    CustomerSummaryDTO,
    CustomerProfileDetailDTO,
    BatchProfileGenerateResponse,
    GlobalAnalyticsSummaryDTO,
    CustomerIdentityDTO,
    LinkIdentityRequest,
    CustomerAttributeDTO,
    SetAttributeRequest,
    FeatureDefinitionDTO,
    RegisterFeatureRequest,
    CustomerFeatureValueDTO,
    BatchFeatureCalculateRequest,
    BatchFeatureCalculateResponse,
)

from backend.app.modules.analytics.service import (
    get_customer_profile,
    get_customer_summary,
    get_customer_profile_details,
    generate_customer_profile,
    generate_customer_profiles,
    list_customer_profiles,
    get_global_analytics_summary,
    list_all_customers,
)

router = APIRouter(
    tags=["Analytics & Customer Intelligence"]
)


@router.get("/api/analytics/summary", response_model=GlobalAnalyticsSummaryDTO)
@router.get("/analytics/summary", response_model=GlobalAnalyticsSummaryDTO)
def get_platform_summary():
    """
    Returns platform-wide summary analytics (total customers, total spending/credit volume, top categories & merchants).
    """
    try:
        return get_global_analytics_summary()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics summary: {str(e)}"
        )


@router.get("/api/analytics/domain-breakdown")
@router.get("/analytics/domain-breakdown")
def get_domain_breakdown():
    """
    Returns per-domain aggregated statistics (transaction count, total volume, unique customers)
    for use in Analytics, Insights, and Reports pages.
    """
    from backend.app.database.connection import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                COALESCE(NULLIF(`source_domain`, ''), 'UNKNOWN') as domain,
                COUNT(*) as transaction_count,
                COALESCE(SUM(`amount`), 0) as total_volume,
                COUNT(DISTINCT `customer_id`) as unique_customers,
                COALESCE(AVG(`amount`), 0) as avg_transaction_value,
                COALESCE(SUM(CASE WHEN `transaction_type` = 'CREDIT' THEN `amount` ELSE 0 END), 0) as credit_volume,
                COALESCE(SUM(CASE WHEN `transaction_type` IN ('DEBIT','PURCHASE','BILL_PAYMENT') THEN `amount` ELSE 0 END), 0) as debit_volume
            FROM `unified_transactions`
            GROUP BY `source_domain`
            ORDER BY total_volume DESC
            """
        )
        rows = cursor.fetchall()
        total_vol = sum(float(r.get("total_volume") or 0) for r in rows)
        result = []
        for r in rows:
            vol = float(r.get("total_volume") or 0)
            result.append({
                "domain": r["domain"],
                "transaction_count": int(r.get("transaction_count") or 0),
                "total_volume": round(vol, 2),
                "unique_customers": int(r.get("unique_customers") or 0),
                "avg_transaction_value": round(float(r.get("avg_transaction_value") or 0), 2),
                "credit_volume": round(float(r.get("credit_volume") or 0), 2),
                "debit_volume": round(float(r.get("debit_volume") or 0), 2),
                "percentage_of_total": round((vol / total_vol * 100), 2) if total_vol > 0 else 0.0,
            })
        return result
    finally:
        cursor.close()
        conn.close()


@router.get("/api/customers/profiles", response_model=List[CustomerProfileDetailDTO])
@router.get("/customers/profiles", response_model=List[CustomerProfileDetailDTO])
def list_profiles(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Returns paginated list of generated customer profiles.
    """
    try:
        return list_customer_profiles(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list customer profiles: {str(e)}"
        )


@router.post("/api/customers/profiles/generate-batch", response_model=BatchProfileGenerateResponse)
@router.post("/customers/profiles/generate-batch", response_model=BatchProfileGenerateResponse)
def generate_profiles_batch(
    customer_ids: Optional[List[str]] = Body(None, description="Optional list of specific customer IDs to generate profiles for"),
    limit: int = Body(50, ge=1, le=500, description="Max number of customers to process if customer_ids not provided")
):
    """
    Batch generates customer profiles for top active customers deterministically with no AI calls.
    """
    try:
        return generate_customer_profiles(customer_ids=customer_ids, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch generate profiles: {str(e)}"
        )


@router.get("/api/customers/{customerId}/profile", response_model=CustomerProfileDetailDTO)
@router.get("/customers/{customerId}/profile", response_model=CustomerProfileDetailDTO)
def get_customer_profile_endpoint(customerId: str):
    """
    Returns full structured Customer Profile containing events, spend, top categories/merchants,
    recurring patterns, frequency, data quality, and financial activity summary.
    """
    try:
        profile = get_customer_profile_details(customerId)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with identifier '{customerId}' not found."
            )
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch customer profile: {str(e)}"
        )


@router.post("/api/customers/{customerId}/profile/generate", response_model=CustomerProfileDetailDTO)
@router.post("/customers/{customerId}/profile/generate", response_model=CustomerProfileDetailDTO)
def generate_customer_profile_endpoint(customerId: str):
    """
    Forces recalculation and idempotent update of customer profile.
    """
    try:
        profile = generate_customer_profile(customerId)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with identifier '{customerId}' not found."
            )
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate customer profile: {str(e)}"
        )


@router.get("/api/customers/{phoneNumber}/summary", response_model=CustomerSummaryDTO)
@router.get("/customers/{phoneNumber}/summary", response_model=CustomerSummaryDTO)
def get_customer_intelligence_summary(phoneNumber: str):
    """
    Returns customer-level aggregated metrics (total transactions, credit vs debit, category-wise spending).
    """
    try:
        summary = get_customer_summary(phoneNumber)
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with identifier '{phoneNumber}' not found."
            )
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate customer summary: {str(e)}"
        )


@router.get("/api/customers/{phoneNumber}", response_model=CustomerProfileDTO)
@router.get("/customers/{phoneNumber}", response_model=CustomerProfileDTO)
def get_customer(phoneNumber: str):
    """
    Fetches customer basic metadata by phoneNumber or customerId.
    """
    try:
        cust = get_customer_profile(phoneNumber)
        if not cust:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with identifier '{phoneNumber}' not found."
            )
        return cust
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch customer: {str(e)}"
        )


@router.get("/api/features/catalog", response_model=List[FeatureDefinitionDTO])
@router.get("/features/catalog", response_model=List[FeatureDefinitionDTO])
def get_features_catalog(
    category: Optional[str] = Query(None, description="Optional filter by feature category")
):
    """
    Returns the metadata catalog of all registered dynamic features, metrics, and KPIs.
    """
    from backend.app.modules.analytics.feature_engine import get_registered_features
    try:
        return get_registered_features(category=category)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch feature catalog: {str(e)}"
        )


@router.post("/api/features/register", response_model=FeatureDefinitionDTO)
@router.post("/features/register", response_model=FeatureDefinitionDTO)
def register_feature_endpoint(request: RegisterFeatureRequest):
    """
    Dynamically registers a new metric / KPI definition into the platform without code deployment.
    """
    from backend.app.modules.analytics.feature_engine import register_feature_definition
    try:
        return register_feature_definition(
            feature_id=request.feature_id,
            display_name=request.display_name,
            description=request.description,
            category=request.category,
            data_type=request.data_type,
            aggregation_type=request.aggregation_type,
            time_window=request.time_window,
            unit=request.unit,
            parameters=request.parameters
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register feature: {str(e)}"
        )


@router.get("/api/customers/{customerId}/features", response_model=List[CustomerFeatureValueDTO])
@router.get("/customers/{customerId}/features", response_model=List[CustomerFeatureValueDTO])
def get_customer_features_endpoint(customerId: str):
    """
    Returns all materialized or on-demand dynamic feature values for a specific customer.
    """
    from backend.app.modules.analytics.feature_engine import get_customer_materialized_features
    try:
        return get_customer_materialized_features(customerId)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch customer features: {str(e)}"
        )


@router.post("/api/customers/{customerId}/features/calculate", response_model=List[CustomerFeatureValueDTO])
@router.post("/customers/{customerId}/features/calculate", response_model=List[CustomerFeatureValueDTO])
def calculate_customer_features_endpoint(
    customerId: str,
    feature_ids: Optional[List[str]] = Body(None, description="Optional specific features to calculate")
):
    """
    Forces recalculation and materialization of dynamic features for a single customer.
    """
    from backend.app.modules.analytics.feature_engine import calculate_customer_features
    try:
        return calculate_customer_features(customerId, feature_ids=feature_ids)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate customer features: {str(e)}"
        )


@router.post("/api/features/calculate-batch", response_model=BatchFeatureCalculateResponse)
@router.post("/features/calculate-batch", response_model=BatchFeatureCalculateResponse)
def batch_calculate_features_endpoint(request: BatchFeatureCalculateRequest):
    """
    Batch calculates dynamic feature sets across multiple customers.
    """
    from backend.app.modules.analytics.feature_engine import batch_calculate_features
    try:
        return batch_calculate_features(
            customer_ids=request.customer_ids,
            feature_ids=request.feature_ids,
            limit=request.limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute batch feature calculation: {str(e)}"
        )


@router.get("/api/customers/{customerId}/identities", response_model=List[CustomerIdentityDTO])
@router.get("/customers/{customerId}/identities", response_model=List[CustomerIdentityDTO])
def get_customer_identities_endpoint(customerId: str):
    """
    Returns all linked identities (phone numbers, emails, external IDs) for a customer.
    """
    from backend.app.modules.analytics.identity_service import get_customer_identities
    try:
        return get_customer_identities(customerId)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch customer identities: {str(e)}"
        )


@router.post("/api/customers/{customerId}/identities", response_model=Dict[str, Any])
@router.post("/customers/{customerId}/identities", response_model=Dict[str, Any])
def link_customer_identity_endpoint(customerId: str, request: LinkIdentityRequest):
    """
    Links a new identity (e.g. secondary phone, email, external user ID) to a customer.
    """
    from backend.app.modules.analytics.identity_service import link_customer_identity
    try:
        return link_customer_identity(
            customer_id=customerId,
            identity_type=request.identity_type,
            identity_value=request.identity_value,
            confidence=request.confidence,
            is_primary=request.is_primary
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link customer identity: {str(e)}"
        )


@router.get("/api/customers/{customerId}/attributes", response_model=Dict[str, Any])
@router.get("/customers/{customerId}/attributes", response_model=Dict[str, Any])
def get_customer_attributes_endpoint(customerId: str):
    """
    Returns all dynamic extensible attributes for a customer.
    """
    from backend.app.modules.analytics.identity_service import get_customer_attributes
    try:
        return get_customer_attributes(customerId)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch customer attributes: {str(e)}"
        )


@router.post("/api/customers/{customerId}/attributes", response_model=Dict[str, Any])
@router.post("/customers/{customerId}/attributes", response_model=Dict[str, Any])
def set_customer_attribute_endpoint(customerId: str, request: SetAttributeRequest):
    """
    Sets or updates a dynamic extensible attribute for a customer.
    """
    from backend.app.modules.analytics.identity_service import set_customer_attribute
    try:
        return set_customer_attribute(
            customer_id=customerId,
            attribute_name=request.attribute_name,
            attribute_value=request.attribute_value,
            data_type=request.data_type,
            source=request.source
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set customer attribute: {str(e)}"
        )


@router.get("/api/customers", response_model=List[CustomerProfileDTO])
@router.get("/customers", response_model=List[CustomerProfileDTO])
def list_customers(

    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Returns paginated list of customers.
    """
    try:
        return list_all_customers(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list customers: {str(e)}"
        )



