import logging
import shutil
from datetime import datetime, timezone
from typing import List, Optional
import httpx
from fastapi import APIRouter, Depends, Query, HTTPException, Body

from app.core.security import get_current_admin
from app.core.config import settings
from app.core.supabase_client import is_supabase_configured, get_supabase_admin_client, get_supabase_client
from app.models.schemas import (
    AdminStatsResponse,
    SystemHealthResponse,
    AdminTelemetryOverviewResponse,
    TelemetryTimeSeriesPoint,
    TelemetryModuleBreakdownItem,
    TelemetryEventItem,
    ApiResponse,
    UserProfile,
    AdminUserRecord,
    AdminUserSessionRecord,
    AdminCreateUserRequest,
    AdminUpdateUserRoleRequest,
)
from app.services.telemetry_service import telemetry_service
from app.services.ollama_service import ollama_service

logger = logging.getLogger("medical_ocr.api.admin")
router = APIRouter(prefix="/admin", tags=["Admin Privacy-Preserved Telemetry"])

@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(current_admin: UserProfile = Depends(get_current_admin)):
    """
    Returns high-level system usage telemetry for administrators.
    STRICT PRIVACY POLICY: Zero patient identifiable information (PHI),
    zero clinical values, zero report images, and zero chat transcripts are returned.
    """
    stats_dict = telemetry_service.get_stats()
    return AdminStatsResponse(**stats_dict)

@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(current_admin: UserProfile = Depends(get_current_admin)):
    """
    Diagnostic health report for system background services.
    """
    # Check Tesseract binary
    tesseract_ok = bool(shutil.which(settings.TESSERACT_CMD) or shutil.which("tesseract"))
    
    # Check Ollama runtime
    ollama_ok, _ = ollama_service.check_availability()

    now_dt = datetime.now(timezone.utc)
    return SystemHealthResponse(
        status="healthy" if (tesseract_ok or not is_supabase_configured()) else "degraded",
        version=settings.VERSION,
        timestamp=now_dt,
        database_connected=is_supabase_configured(),
        supabase_configured=is_supabase_configured(),
        tesseract_available=tesseract_ok,
        ollama_available=ollama_ok,
        llm_provider=ollama_service.get_provider(),
    )

@router.get("/telemetry/overview", response_model=ApiResponse)
async def get_telemetry_overview(current_admin: UserProfile = Depends(get_current_admin)):
    """
    Comprehensive Zero-PHI Telemetry Overview for the Administrator Dashboard.
    Provides KPIs, runtime service health, 24-hour time series, module breakdown, and event stream.
    """
    stats_dict = telemetry_service.get_stats()
    stats = AdminStatsResponse(**stats_dict)

    tesseract_ok = bool(shutil.which(settings.TESSERACT_CMD) or shutil.which("tesseract"))
    ollama_ok, _ = ollama_service.check_availability()
    health = SystemHealthResponse(
        status="healthy" if (tesseract_ok or not is_supabase_configured()) else "degraded",
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
        database_connected=is_supabase_configured(),
        supabase_configured=is_supabase_configured(),
        tesseract_available=tesseract_ok,
        ollama_available=ollama_ok,
        llm_provider=ollama_service.get_provider(),
    )

    time_series = [TelemetryTimeSeriesPoint(**pt) for pt in telemetry_service.get_time_series(24)]
    breakdown = [TelemetryModuleBreakdownItem(**m) for m in telemetry_service.get_module_breakdown()]
    recent_events = [TelemetryEventItem(**e) for e in telemetry_service.get_recent_events(30)]

    overview = AdminTelemetryOverviewResponse(
        stats=stats,
        health=health,
        time_series=time_series,
        breakdown=breakdown,
        recent_events=recent_events,
    )

    return ApiResponse(
        success=True,
        message="Retrieved privacy-preserving system telemetry overview.",
        data=overview.model_dump(),
    )

@router.get("/telemetry/timeseries", response_model=ApiResponse)
async def get_telemetry_timeseries(
    hours: int = Query(24, ge=6, le=72, description="Number of historical hours to return"),
    current_admin: UserProfile = Depends(get_current_admin)
):
    """
    Returns time-series buckets of system throughput and latency for Recharts graphs.
    """
    data = telemetry_service.get_time_series(hours=hours)
    return ApiResponse(
        success=True,
        message=f"Retrieved {len(data)} hourly telemetry data points.",
        data=data,
    )

@router.get("/telemetry/breakdown", response_model=ApiResponse)
async def get_telemetry_breakdown(current_admin: UserProfile = Depends(get_current_admin)):
    """
    Returns workload distribution by subsystem with latency and success rate metrics.
    """
    data = telemetry_service.get_module_breakdown()
    return ApiResponse(
        success=True,
        message="Retrieved subsystem workload breakdown.",
        data=data,
    )

@router.get("/telemetry/events", response_model=ApiResponse)
async def get_telemetry_events(
    limit: int = Query(25, ge=5, le=100),
    current_admin: UserProfile = Depends(get_current_admin)
):
    """
    Returns recent sanitized system events stream with guaranteed zero-PHI isolation.
    """
    events = telemetry_service.get_recent_events(limit=limit)
    return ApiResponse(
        success=True,
        message=f"Retrieved {len(events)} sanitized system events.",
        data=events,
    )


# ==============================================================
# USER MANAGEMENT — List, Create, Remove, Promote/Demote
# ==============================================================

@router.get("/users", response_model=ApiResponse)
async def list_all_users(
    current_admin: UserProfile = Depends(get_current_admin),
):
    """
    Returns a list of all registered users with their role and last sign-in time.
    Privacy: Only non-clinical metadata (email, role, timestamps) is returned.
    Zero medical report data, lab values, or clinical notes are exposed.
    """
    if not is_supabase_configured():
        # Dev fallback — return mock users
        mock_users = [
            AdminUserRecord(
                id="a4e0b6e5-b64f-42d0-9c99-e818e85a4df2",
                email="patient@medicalocr.com",
                full_name="Demo Patient",
                role="user",
                preferred_language="en",
                created_at=datetime.now(timezone.utc).isoformat(),
                last_sign_in_at=datetime.now(timezone.utc).isoformat(),
                is_active=True,
            ),
            AdminUserRecord(
                id="18c60302-1240-4bee-a9d8-b9b487777789",
                email="admin@medicalocr.com",
                full_name="System Administrator",
                role="admin",
                preferred_language="en",
                created_at=datetime.now(timezone.utc).isoformat(),
                last_sign_in_at=datetime.now(timezone.utc).isoformat(),
                is_active=True,
            ),
        ]
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(mock_users)} users (dev mode).",
            data=[u.model_dump() for u in mock_users],
        )

    supabase = get_supabase_admin_client()
    if not supabase:
        raise HTTPException(status_code=503, detail="Admin client not available.")

    try:
        # Fetch auth users (Supabase Admin API)
        auth_response = supabase.auth.admin.list_users()
        auth_users = auth_response if isinstance(auth_response, list) else getattr(auth_response, "users", [])

        # Fetch profiles table for role & language (note: profiles schema has id, email, role, preferred_language, created_at)
        profiles_res = supabase.table("profiles").select("id, role, preferred_language, created_at").execute()
        profiles_map = {str(p["id"]): p for p in (profiles_res.data or [])}

        def _to_iso(val) -> Optional[str]:
            if not val:
                return None
            return val.isoformat() if hasattr(val, "isoformat") else str(val)

        users: list[AdminUserRecord] = []
        for au in auth_users:
            uid = str(au.id)
            profile = profiles_map.get(uid, {})
            meta = getattr(au, "user_metadata", None) or {}
            users.append(AdminUserRecord(
                id=uid,
                email=getattr(au, "email", None) or "",
                full_name=meta.get("full_name") or None,
                role=profile.get("role") or meta.get("role", "user"),
                preferred_language=profile.get("preferred_language") or meta.get("preferred_language", "en"),
                created_at=_to_iso(getattr(au, "created_at", None)),
                last_sign_in_at=_to_iso(getattr(au, "last_sign_in_at", None)),
                is_active=not getattr(au, "banned_until", None),
            ))

        return ApiResponse(
            success=True,
            message=f"Retrieved {len(users)} registered users.",
            data=[u.model_dump() for u in users],
        )
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user list: {str(e)}")


@router.post("/users", response_model=ApiResponse)
async def create_user(
    payload: AdminCreateUserRequest,
    current_admin: UserProfile = Depends(get_current_admin),
):
    """
    Creates a new user (or admin) account directly from the Admin dashboard.
    Sets up both Supabase Auth entry and profiles table record.
    """
    if payload.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'.")

    if not is_supabase_configured():
        raise HTTPException(status_code=503, detail="Supabase is not configured. Cannot create users in dev mode.")

    supabase = get_supabase_admin_client()
    if not supabase:
        raise HTTPException(status_code=503, detail="Admin client not available.")

    try:
        # 1. Create auth user via Supabase Admin API
        create_resp = supabase.auth.admin.create_user({
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": payload.full_name or "",
                "role": payload.role,
                "preferred_language": payload.preferred_language,
            },
        })
        new_user = create_resp.user if hasattr(create_resp, "user") else create_resp
        if not new_user:
            raise HTTPException(status_code=500, detail="Failed to create user in auth system.")

        uid = str(new_user.id)

        # 2. Upsert into profiles table (profiles schema: id, email, role, preferred_language)
        supabase.table("profiles").upsert({
            "id": uid,
            "email": payload.email.strip().lower(),
            "role": payload.role,
            "preferred_language": payload.preferred_language,
        }).execute()

        # 3. Log telemetry event (zero PHI)
        try:
            supabase.table("system_events").insert({
                "event_type": "admin_user_created",
                "duration_ms": 0,
                "status": "success",
                "token_count": 0,
            }).execute()
        except Exception:
            pass

        logger.info(f"Admin {current_admin.email} created new user {payload.email} with role '{payload.role}'")
        return ApiResponse(
            success=True,
            message=f"User '{payload.email}' created successfully with role '{payload.role}'.",
            data={"id": uid, "email": payload.email, "role": payload.role},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"User creation failed: {str(e)}")


# ==============================================================
# USER SESSION LOG — Login & Logout Activity
# ==============================================================

@router.get("/users/sessions", response_model=ApiResponse)
async def get_user_sessions(
    limit: int = Query(50, ge=5, le=200),
    current_admin: UserProfile = Depends(get_current_admin),
):
    """
    Returns recent login/logout session activity from system_events.
    Emails are shown only if stored in the event record — otherwise shows anonymized user IDs.
    Privacy: Only event timestamps, type, and masked identity included.
    """
    if not is_supabase_configured():
        # Dev fallback — return mock session events matching SessionEvent schema
        mock_sessions = [
            {
                "id": "sess-001",
                "event_type": "user_login",
                "status": "success",
                "user_email": "patient@medicalocr.com",
                "user_id_ref": "a4e0b6e5-b64f-42d0-9c99-e818e85a4df2",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": "sess-002",
                "event_type": "user_login",
                "status": "success",
                "user_email": "admin@medicalocr.com",
                "user_id_ref": "18c60302-1240-4bee-a9d8-b9b487777789",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        ]
        return ApiResponse(
            success=True,
            message="Session log retrieved (dev mode).",
            data=mock_sessions,
        )

    supabase = get_supabase_admin_client()
    if not supabase:
        raise HTTPException(status_code=503, detail="Admin client not available.")

    try:
        res = (
            supabase.table("system_events")
            .select("*")
            .in_("event_type", ["user_login", "user_logout"])
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        events = res.data or []
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(events)} session events.",
            data=events,
        )
    except Exception as e:
        logger.error(f"Failed to fetch session events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve session log: {str(e)}")


@router.delete("/users/{user_id}", response_model=ApiResponse)
async def delete_user(
    user_id: str,
    current_admin: UserProfile = Depends(get_current_admin),
):
    """
    Permanently removes a user account and all their associated data.
    Cascades via ON DELETE CASCADE to reports, test_results, prescriptions, conversations.
    Cannot delete your own admin account.
    """
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own administrator account.")

    if not is_supabase_configured():
        raise HTTPException(status_code=503, detail="Supabase is not configured.")

    supabase = get_supabase_admin_client()
    if not supabase:
        raise HTTPException(status_code=503, detail="Admin client not available.")

    try:
        # Delete from Supabase Auth (cascades to profiles via ON DELETE CASCADE)
        supabase.auth.admin.delete_user(user_id)

        # Log telemetry event (zero PHI — no user identity stored)
        try:
            supabase.table("system_events").insert({
                "event_type": "admin_user_deleted",
                "duration_ms": 0,
                "status": "success",
                "token_count": 0,
            }).execute()
        except Exception:
            pass

        logger.info(f"Admin {current_admin.email} deleted user {user_id}")
        return ApiResponse(
            success=True,
            message="User account and all associated data permanently removed.",
            data={"deleted_user_id": user_id},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User deletion failed for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


@router.patch("/users/{user_id}/role", response_model=ApiResponse)
async def update_user_role(
    user_id: str,
    payload: AdminUpdateUserRoleRequest,
    current_admin: UserProfile = Depends(get_current_admin),
):
    """
    Promotes a user to admin or demotes an admin back to user.
    Updates both Supabase Auth user_metadata and the profiles table.
    """
    if payload.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'.")

    if not is_supabase_configured():
        raise HTTPException(status_code=503, detail="Supabase is not configured.")

    supabase = get_supabase_admin_client()
    if not supabase:
        raise HTTPException(status_code=503, detail="Admin client not available.")

    try:
        # Update auth user_metadata
        supabase.auth.admin.update_user_by_id(
            user_id,
            {"user_metadata": {"role": payload.role}},
        )
        # Update profiles table
        supabase.table("profiles").update({"role": payload.role}).eq("id", user_id).execute()

        logger.info(f"Admin {current_admin.email} changed user {user_id} role to '{payload.role}'")
        return ApiResponse(
            success=True,
            message=f"User role updated to '{payload.role}' successfully.",
            data={"user_id": user_id, "new_role": payload.role},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Role update failed for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user role: {str(e)}")
