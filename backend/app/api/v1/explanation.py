import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException

from app.models.schemas import (
    ApiResponse,
    UserProfile,
    ReportExplanationResponse,
    OllamaStatusResponse,
)
from app.core.security import get_current_user
from app.services.explanation_service import grounded_explanation_service
from app.services.ollama_service import ollama_service, DEFAULT_OLLAMA_MODEL, OLLAMA_BASE_URL
from app.api.v1.reports import get_report_test_results, get_report_detail

logger = logging.getLogger("medical_ocr.api.explanation")
router = APIRouter(tags=["AI Report Explanation & Ollama Grounding"])

@router.get("/ai/status", response_model=ApiResponse)
async def get_ai_status(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Checks the LLM runtime connectivity (Groq Cloud or local Ollama), active model, and downloaded model tags.
    """
    is_available, models = ollama_service.check_availability()
    provider = ollama_service.get_provider()
    active_model = ollama_service.get_active_model()
    return ApiResponse(
        success=True,
        message="AI status retrieved successfully.",
        data=OllamaStatusResponse(
            available=is_available,
            model=active_model,
            available_models=models,
            ollama_url=OLLAMA_BASE_URL,
            provider=provider,
        ).model_dump()
    )

@router.post("/reports/{report_id}/explain", response_model=ApiResponse)
async def generate_report_explanation(
    report_id: str,
    language: str = Query("en", description="Target language ('en', 'ta', 'hi')"),
    model: Optional[str] = Query(None, description="Preferred Ollama model (e.g. 'llama3:latest', 'mistral')"),
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Generates a structured, anti-hallucinatory plain-language clinical explanation for a medical report.
    Cites every biomarker value and reference interval grounded in the Phase 7 glossary.
    """
    # 1. Fetch report details
    try:
        report = await get_report_detail(report_id, current_user)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Report not found.")

    # 2. Fetch structured test results
    test_results_models = await get_report_test_results(report_id, current_user)
    test_results_dicts = [tr.model_dump() for tr in test_results_models]

    # 3. Generate grounded explanation
    explanation = grounded_explanation_service.generate_explanation(
        report_id=report_id,
        report_title=report.title,
        test_results=test_results_dicts,
        language=language,
        preferred_model=model,
    )

    return ApiResponse(
        success=True,
        message=f"Grounded clinical explanation generated successfully in '{language}'.",
        data=explanation.model_dump()
    )

@router.get("/reports/{report_id}/explanation", response_model=ApiResponse)
async def get_report_explanation(
    report_id: str,
    language: str = Query("en", description="Target language ('en', 'ta', 'hi')"),
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Retrieves the stored / cached grounded explanation for a report.
    If not yet generated, generates it on demand.
    """
    cached = grounded_explanation_service.get_cached_explanation(report_id, language=language)
    if cached:
        return ApiResponse(
            success=True,
            message="Retrieved cached report explanation.",
            data=cached.model_dump()
        )

    # Auto-generate if not cached
    return await generate_report_explanation(report_id=report_id, language=language, current_user=current_user)
