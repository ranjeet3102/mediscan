import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException

from app.models.schemas import (
    ApiResponse,
    UserProfile,
    DoctorSummaryResponse,
)
from app.core.security import get_current_user
from app.services.doctor_service import doctor_service
from app.api.v1.reports import get_report_detail, get_report_test_results

logger = logging.getLogger("medical_ocr.api.doctor")
router = APIRouter(tags=["Doctor Support Suite & Multilingual Brief (Phase 12)"])

@router.get("/reports/{report_id}/doctor-summary", response_model=ApiResponse)
async def get_report_doctor_summary(
    report_id: str,
    language: str = Query("en", description="Target language ('en', 'ta', 'hi')"),
    model: Optional[str] = Query(None, description="Preferred Ollama model (e.g. 'llama3:latest')"),
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Generates a structured, print-ready 1-Page Doctor Consultation Brief.
    Includes clinical overview, out-of-range parameters table, longitudinal shifts,
    and prioritized patient discussion questions.
    """
    # 1. Fetch report details
    try:
        report = await get_report_detail(report_id, current_user)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Medical report not found.")

    # 2. Fetch structured test results
    test_results_models = await get_report_test_results(report_id, current_user)
    test_results_dicts = [tr.model_dump() for tr in test_results_models]

    # 3. Generate summary
    try:
        summary = doctor_service.generate_doctor_summary(
            report_id=report_id,
            user_id=current_user.id,
            report_title=report.title or "Medical Diagnostic Report",
            report_date=report.report_date,
            test_results=test_results_dicts,
            patient_email=current_user.email,
            language=language,
            preferred_model=model,
        )
    except Exception as e:
        logger.error(f"Error generating doctor summary for report {report_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate doctor summary: {str(e)}")

    return ApiResponse(
        success=True,
        message="Doctor consultation summary generated successfully.",
        data=summary.model_dump(),
    )

@router.get("/reports/{report_id}/doctor-questions", response_model=ApiResponse)
async def get_report_doctor_questions(
    report_id: str,
    language: str = Query("en", description="Target language ('en', 'ta', 'hi')"),
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Retrieves prioritized consultation questions for the patient to ask their physician.
    """
    try:
        report = await get_report_detail(report_id, current_user)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Medical report not found.")

    test_results_models = await get_report_test_results(report_id, current_user)
    test_results_dicts = [tr.model_dump() for tr in test_results_models]

    summary = doctor_service.generate_doctor_summary(
        report_id=report_id,
        user_id=current_user.id,
        report_title=report.title or "Medical Diagnostic Report",
        report_date=report.report_date,
        test_results=test_results_dicts,
        patient_email=current_user.email,
        language=language,
    )

    return ApiResponse(
        success=True,
        message="Doctor discussion questions retrieved successfully.",
        data=[q.model_dump() for q in summary.doctor_questions],
    )
