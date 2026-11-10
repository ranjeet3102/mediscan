import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_user
from app.core.supabase_client import get_supabase_client, get_supabase_admin_client, is_supabase_configured
from app.models.schemas import (
    UserSignupRequest,
    UserLoginRequest,
    UserProfile,
    TokenResponse,
    ProfileUpdateRequest,
    ApiResponse,
)

logger = logging.getLogger("medical_ocr.api.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=ApiResponse)
async def signup(request: UserSignupRequest):
    """
    Register a new user account with full name and language preference.
    Security policy: Public registration exclusively creates standard 'user' accounts.
    Administrator accounts can only be provisioned directly by executing SQL queries in Supabase.
    """
    email = request.email.strip().lower()
    password = request.password
    full_name = (request.full_name or "").strip() or None
    # Force 'user' role for public signups (admin creation is restricted to direct SQL queries)
    role = "user"
    lang = request.preferred_language or "en"

    if is_supabase_configured():
        admin_client = get_supabase_admin_client()
        supabase = get_supabase_client()
        
        user_id = None
        created_user = None

        # Try auto-confirmed creation using admin client first
        if admin_client:
            try:
                auth_resp = admin_client.auth.admin.create_user({
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {
                        "full_name": full_name,
                        "role": role,
                        "preferred_language": lang,
                    }
                })
                if auth_resp and auth_resp.user:
                    created_user = auth_resp.user
                    user_id = created_user.id
            except Exception as e:
                err_msg = str(e)
                if "already registered" in err_msg.lower() or "already exists" in err_msg.lower():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="An account with this email address already exists. Please log in."
                    )
                logger.warning(f"Admin create_user fallback triggered: {e}")

        # Fallback to standard client sign up if not created via admin
        if not user_id:
            try:
                auth_resp = supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "full_name": full_name,
                            "role": role,
                            "preferred_language": lang,
                        }
                    }
                })
                if not auth_resp or not auth_resp.user:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create user account.")
                created_user = auth_resp.user
                user_id = created_user.id
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Signup error: {e}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
        # Ensure profile record exists in public.profiles
        try:
            db_client = admin_client or supabase
            db_client.table("profiles").upsert({
                "id": user_id,
                "email": email,
                "role": role,
                "preferred_language": lang,
            }).execute()
        except Exception as pe:
            logger.warning(f"Failed to upsert profile record for {user_id}: {pe}")

        return ApiResponse(
            success=True,
            message="Account successfully registered.",
            data={"user_id": user_id, "email": email, "full_name": full_name, "role": role}
        )
    else:
        # Development fallback mode
        return ApiResponse(
            success=True,
            message="Development Mock Mode: Account created successfully.",
            data={
                "user_id": "00000000-0000-0000-0000-000000000001",
                "email": email,
                "full_name": full_name or "Demo Patient",
                "role": role,
                "preferred_language": lang
            }
        )

@router.post("/login", response_model=TokenResponse)
async def login(request: UserLoginRequest):
    """
    Authenticate user against Supabase Auth and return session token with role, full name & profile.
    """
    email = request.email.strip().lower()
    password = request.password

    if is_supabase_configured():
        supabase = get_supabase_client()
        admin_client = get_supabase_admin_client() or supabase
        try:
            auth_resp = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })
            if not auth_resp or not auth_resp.session:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
            
            session = auth_resp.session
            user = auth_resp.user
            
            # Fetch profile details from public.profiles
            role = "user"
            lang = "en"
            full_name = user.user_metadata.get("full_name") if user.user_metadata else None
            try:
                profile_res = admin_client.table("profiles").select("*").eq("id", user.id).maybe_single().execute()
                if profile_res and profile_res.data:
                    role = profile_res.data.get("role", "user")
                    lang = profile_res.data.get("preferred_language", "en")
                elif user.user_metadata:
                    role = user.user_metadata.get("role", "user")
                    lang = user.user_metadata.get("preferred_language", "en")
                    # Auto-persist missing profile
                    admin_client.table("profiles").upsert({
                        "id": user.id,
                        "email": user.email,
                        "role": role,
                        "preferred_language": lang,
                    }).execute()
            except Exception as pe:
                logger.warning(f"Profile fetch warning during login: {pe}")
                if user.user_metadata:
                    role = user.user_metadata.get("role", "user")
                    lang = user.user_metadata.get("preferred_language", "en")
                    full_name = user.user_metadata.get("full_name")

            user_profile = UserProfile(
                id=user.id,
                email=user.email,
                full_name=full_name,
                role=role,
                preferred_language=lang,
                created_at=str(user.created_at) if user.created_at else None,
            )

            # Record login session event (Zero-PHI: stores email for admin visibility only)
            try:
                admin_client.table("system_events").insert({
                    "event_type": "user_login",
                    "duration_ms": 0,
                    "status": "success",
                    "token_count": 0,
                    "user_email": user.email,
                    "user_id_ref": str(user.id),
                }).execute()
            except Exception:
                try:
                    admin_client.table("system_events").insert({
                        "event_type": "user_login",
                        "duration_ms": 0,
                        "status": "success",
                        "token_count": 0,
                    }).execute()
                except Exception:
                    pass  # Telemetry failure must never block login

            return TokenResponse(
                access_token=session.access_token,
                token_type="bearer",
                user=user_profile,
                expires_in=session.expires_in or 3600,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    else:
        # Development fallback
        is_admin = "admin" in email.lower()
        role = "admin" if is_admin else "user"
        token = "dev-admin-token" if is_admin else "dev-user-token"
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserProfile(
                id="18c60302-1240-4bee-a9d8-b9b487777789" if is_admin else "a4e0b6e5-b64f-42d0-9c99-e818e85a4df2",
                email=email,
                full_name="System Administrator" if is_admin else "Demo Patient",
                role=role,
                preferred_language="en",
            ),
            expires_in=3600,
        )

@router.get("/me", response_model=UserProfile)
async def get_me(current_user: UserProfile = Depends(get_current_user)):
    """
    Get the currently logged-in user's profile and role.
    """
    return current_user

@router.put("/profile", response_model=ApiResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Update full name, preferred language or user settings.
    """
    if is_supabase_configured():
        supabase = get_supabase_client()
        update_data = {}
        if request.full_name is not None:
            update_data["full_name"] = request.full_name
        if request.preferred_language:
            update_data["preferred_language"] = request.preferred_language
        if request.role:
            update_data["role"] = request.role
            
        if update_data:
            supabase.table("profiles").update(update_data).eq("id", current_user.id).execute()

    return ApiResponse(
        success=True,
        message="Profile updated successfully.",
        data={
            "id": current_user.id,
            "full_name": request.full_name or current_user.full_name,
            "preferred_language": request.preferred_language or current_user.preferred_language,
            "role": request.role or current_user.role,
        }
    )

@router.post("/logout", response_model=ApiResponse)
async def logout(current_user: UserProfile = Depends(get_current_user)):
    """
    Sign out user from active session. Records logout event for admin session log.
    """
    if is_supabase_configured():
        supabase = get_supabase_client()
        admin_client = get_supabase_admin_client() or supabase
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        # Record logout event
        try:
            admin_client.table("system_events").insert({
                "event_type": "user_logout",
                "duration_ms": 0,
                "status": "success",
                "token_count": 0,
                "user_email": current_user.email,
                "user_id_ref": current_user.id,
            }).execute()
        except Exception:
            try:
                admin_client.table("system_events").insert({
                    "event_type": "user_logout",
                    "duration_ms": 0,
                    "status": "success",
                    "token_count": 0,
                }).execute()
            except Exception:
                pass
    return ApiResponse(success=True, message="Successfully logged out.")
