import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException

from app.services.glossary_service import medical_glossary_service
from app.models.schemas import ApiResponse, UserProfile
from app.core.security import get_current_user

logger = logging.getLogger("medical_ocr.api.glossary")
router = APIRouter(prefix="/glossary", tags=["Medical Knowledge Base & Glossary"])

@router.get("/search", response_model=ApiResponse)
async def search_glossary(
    q: str = Query("", description="Biomarker name, symptom, or plain-language question"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of search results to return"),
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Performs semantic vector similarity search against the curated medical knowledge base.
    Returns matched clinical biomarkers, organ involvement, and patient-friendly explanations.
    """
    results = medical_glossary_service.search(query=q, limit=limit)
    return ApiResponse(
        success=True,
        message=f"Found {len(results)} matching medical biomarker entries.",
        data={
            "query": q,
            "total_matches": len(results),
            "results": results,
        }
    )

@router.get("/item/{canonical_name}", response_model=ApiResponse)
async def get_glossary_item(
    canonical_name: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Retrieves full clinical and patient-friendly education card for a specific biomarker.
    """
    entry = medical_glossary_service.get_by_name(canonical_name)
    if not entry:
        raise HTTPException(
            status_code=404,
            detail=f"Biomarker '{canonical_name}' not found in medical knowledge base."
        )

    return ApiResponse(
        success=True,
        message=f"Retrieved clinical knowledge card for {entry.canonical_name}.",
        data=medical_glossary_service._entry_to_dict(entry)
    )

@router.get("/categories/all", response_model=ApiResponse)
async def get_glossary_categories(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Returns all standard diagnostic categories and biomarker counts.
    """
    categories = medical_glossary_service.get_all_categories()
    return ApiResponse(
        success=True,
        message="Retrieved all medical knowledge base diagnostic categories.",
        data={
            "total_categories": len(categories),
            "categories": categories,
        }
    )

@router.post("/seed", response_model=ApiResponse)
async def seed_glossary_database(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Seeds / synchronizes the curated medical glossary into PostgreSQL pgvector table.
    """
    count = medical_glossary_service.seed_supabase()
    return ApiResponse(
        success=True,
        message=f"Successfully initialized and indexed {count} medical biomarkers with vector embeddings.",
        data={"seeded_count": count}
    )
