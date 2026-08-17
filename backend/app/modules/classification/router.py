# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
from backend.app.modules.classification.schemas import (
    SingleClassificationRequest,
    ClassificationResultDTO,
    BatchClassificationRequest,
    BatchClassificationResponse,
)
from backend.app.modules.classification.service import (
    classify_record_data,
    classify_single_transaction,
    classify_batch_transactions,
)
from backend.app.modules.classification.constants import ClassificationDomainEnum

router = APIRouter(
    prefix="/classification",
    tags=["Classification Engine"]
)


@router.post("/classify", response_model=ClassificationResultDTO)
def classify_record(payload: SingleClassificationRequest):
    """
    Classifies a single in-memory normalized CDM record and returns domain, category,
    subcategory, and rule-based confidence score.
    """
    try:
        record_dict = payload.model_dump()
        result = classify_record_data(record_dict)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification error: {str(e)}"
        )


@router.post("/classify-batch", response_model=BatchClassificationResponse)
def classify_batch(payload: BatchClassificationRequest = BatchClassificationRequest()):
    """
    Fetches unclassified transactions from the database, classifies them,
    and updates database records idempotently.
    """
    try:
        stats = classify_batch_transactions(limit=payload.limit, force=payload.force)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch classification failed: {str(e)}"
        )


@router.post("/classify/{transaction_id}", response_model=ClassificationResultDTO)
def classify_transaction_by_id(transaction_id: str):
    """
    Classifies a specific stored transaction by ID and updates its classification in the database.
    """
    try:
        result = classify_single_transaction(transaction_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID '{transaction_id}' not found."
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to classify transaction: {str(e)}"
        )


@router.get("/domains", response_model=List[str])
def list_supported_domains():
    """
    Returns list of all supported classification domains.
    """
    return [d.value for d in ClassificationDomainEnum]
