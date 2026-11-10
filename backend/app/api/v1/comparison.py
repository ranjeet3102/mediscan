import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException

from app.models.schemas import (
    ApiResponse,
    UserProfile,
    BiomarkerTrendSeries,
    ReportComparisonRequest,
    ReportComparisonResponse,
)
from app.core.security import get_current_user
from app.services.comparison_service import comparison_service
from app.api.v1.reports import get_report_detail

logger = logging.getLogger("medical_ocr.api.comparison")
router = APIRouter(tags=["Longitudinal Trends & Multi-Report Comparison"])

@router.get("/trends/biomarkers", response_model=ApiResponse)
async def get_biomarker_trends(
    biomarker_name: Optional[str] = Query(None, description="Optional canonical or normalized biomarker name to filter"),
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Retrieves chronological time-series data points and range trajectory bounds
    for all or specific normalized biomarkers across the user's historical reports.
    """
    trends = comparison_service.get_biomarker_trends(
        user_id=current_user.id,
        biomarker_name=biomarker_name,
    )
    return ApiResponse(
        success=True,
        message=f"Retrieved {len(trends)} biomarker trend series.",
        data=[t.model_dump() for t in trends],
    )

@router.get("/trends/biomarker-names", response_model=ApiResponse)
async def get_available_biomarker_names(
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Lists all distinct normalized biomarker names available for time-series trending
    in the authenticated user's profile.
    """
    names = comparison_service.get_available_biomarkers(user_id=current_user.id)
    return ApiResponse(
        success=True,
        message="Available biomarker names retrieved successfully.",
        data={"names": names, "total": len(names)},
    )

@router.post("/reports/compare", response_model=ApiResponse)
async def compare_reports(
    payload: ReportComparisonRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Performs precision side-by-side comparative diff analysis between Report A (Baseline)
    and Report B (Follow-up), computing numeric and percentage deltas (Δ), category shifts,
    and grounded AI trajectory insights.
    """
    # 1. Verify user ownership of both reports
    try:
        await get_report_detail(payload.report_a_id, current_user)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Baseline Report (Report A) not found.")

    try:
        await get_report_detail(payload.report_b_id, current_user)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Follow-up Report (Report B) not found.")

    # 2. Perform comparison
    try:
        comparison_res = comparison_service.compare_two_reports(
            report_a_id=payload.report_a_id,
            report_b_id=payload.report_b_id,
            user_id=current_user.id,
            language=payload.language or "en",
            preferred_model=payload.preferred_model,
        )
    except Exception as e:
        logger.error(f"Error comparing reports {payload.report_a_id} vs {payload.report_b_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report comparison failed: {str(e)}")

    return ApiResponse(
        success=True,
        message="Report comparison generated successfully.",
        data=comparison_res.model_dump(),
    )
