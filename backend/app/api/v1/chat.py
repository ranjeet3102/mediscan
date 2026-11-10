import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.models.schemas import (
    ApiResponse,
    UserProfile,
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
)
from app.core.security import get_current_user
from app.services.chat_service import chat_service
from app.api.v1.reports import get_report_detail, get_report_test_results

logger = logging.getLogger("medical_ocr.api.chat")
router = APIRouter(tags=["'Ask My Report' Conversational Q&A (RAG)"])

@router.post("/reports/{report_id}/chat", response_model=ApiResponse)
async def post_report_chat_message(
    report_id: str,
    payload: ChatRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Submits a conversational question about a specific medical report.
    Answers are strictly grounded in verified lab findings and medical glossary facts.
    """
    # 1. Verify report existence and user ownership
    try:
        report = await get_report_detail(report_id, current_user)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Medical report not found.")

    # 2. Retrieve extracted structured test results
    test_results_models = await get_report_test_results(report_id, current_user)
    test_results_dicts = [tr.model_dump() for tr in test_results_models]

    report_title = report.title or "Medical Report"

    # 3. Generate grounded chat reply
    try:
        chat_response = chat_service.generate_chat_reply(
            report_id=report_id,
            user_id=current_user.id,
            report_title=report_title,
            test_results=test_results_dicts,
            user_message=payload.message,
            language=payload.language or "en",
            conversation_id=payload.conversation_id,
            preferred_model=payload.preferred_model,
        )
    except Exception as e:
        logger.error(f"Error generating chat reply for report {report_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate chat response: {str(e)}")

    return ApiResponse(
        success=True,
        message="Chat response generated successfully.",
        data=chat_response.model_dump(),
    )

@router.get("/reports/{report_id}/chat", response_model=ApiResponse)
async def get_report_chat_history(
    report_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Retrieves the full multi-turn conversation history for a given report.
    """
    # 1. Verify report existence and ownership
    try:
        await get_report_detail(report_id, current_user)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Medical report not found.")

    history = chat_service.get_conversation_history(report_id, current_user.id)

    return ApiResponse(
        success=True,
        message="Conversation history retrieved successfully.",
        data=history.model_dump(),
    )

@router.delete("/reports/{report_id}/chat", response_model=ApiResponse)
async def clear_report_chat(
    report_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Clears all saved messages in the conversation for this report.
    """
    try:
        await get_report_detail(report_id, current_user)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Medical report not found.")

    success = chat_service.clear_conversation(report_id, current_user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear conversation history.")

    return ApiResponse(
        success=True,
        message="Conversation history cleared successfully.",
        data={"cleared": True, "report_id": report_id},
    )
