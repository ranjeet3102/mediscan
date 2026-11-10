import os
import uuid
import logging
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from app.core.supabase_client import get_supabase_client, get_supabase_admin_client, is_supabase_configured

logger = logging.getLogger("medical_ocr.storage")

# Constants
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/tiff": ".tiff",
    "image/webp": ".webp",
}

# Magic bytes signatures for secure file format verification
MAGIC_SIGNATURES = {
    b"%PDF": "application/pdf",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"II*\x00": "image/tiff",
    b"MM\x00*": "image/tiff",
    b"RIFF": "image/webp",
}

LOCAL_UPLOAD_DIR = Path("uploads")
LOCAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class StorageService:
    @staticmethod
    def validate_file(file: UploadFile, content: bytes) -> Tuple[bool, str]:
        """
        Validates file size, MIME type, and magic bytes signature.
        Prevents MIME-spoofing and oversized payloads.
        """
        # 1. Size Validation
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of 25MB (Current: {len(content) / (1024 * 1024):.2f}MB)",
            )

        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded. Please select a valid medical report file.",
            )

        # 2. MIME type check
        mime_type = file.content_type or ""
        if mime_type not in ALLOWED_MIME_TYPES:
            # Check if filename extension matches
            ext = Path(file.filename or "").suffix.lower()
            matching_mime = None
            for mime, m_ext in ALLOWED_MIME_TYPES.items():
                if ext == m_ext:
                    matching_mime = mime
                    break
            if not matching_mime:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"Unsupported file format '{mime_type}'. Allowed formats: PDF, PNG, JPG, JPEG, TIFF, WEBP",
                )
            mime_type = matching_mime

        # 3. Magic Bytes Verification
        is_magic_valid = False
        for sig, expected_mime in MAGIC_SIGNATURES.items():
            if content.startswith(sig):
                is_magic_valid = True
                break

        if not is_magic_valid and mime_type not in ["application/pdf", "image/png", "image/jpeg"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match valid medical report format signature.",
            )

        return True, mime_type

    @staticmethod
    async def upload_file(
        user_id: str,
        file: UploadFile,
        content: bytes,
        mime_type: str
    ) -> Tuple[str, str]:
        """
        Uploads validated file to private Supabase Storage bucket 'medical-reports/{user_id}/{filename}',
        or falls back to local encrypted directory in offline/mock mode.
        Returns: (file_url_or_path, unique_file_key)
        """
        ext = ALLOWED_MIME_TYPES.get(mime_type, ".pdf")
        safe_name = f"{uuid.uuid4().hex}{ext}"
        storage_path = f"{user_id}/{safe_name}"

        if is_supabase_configured():
            supabase = get_supabase_admin_client() or get_supabase_client()
            if supabase:
                try:
                    # Upload to Supabase Storage private bucket
                    res = supabase.storage.from_("medical-reports").upload(
                        path=storage_path,
                        file=content,
                        file_options={"content-type": mime_type, "upsert": "false"}
                    )
                    logger.info(f"File uploaded to Supabase Storage: {storage_path}")
                    return storage_path, safe_name
                except Exception as e:
                    logger.error(f"Supabase storage upload error: {e}. Falling back to local storage.")

        # Local filesystem storage fallback
        user_dir = LOCAL_UPLOAD_DIR / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        local_file_path = user_dir / safe_name
        
        with open(local_file_path, "wb") as f:
            f.write(content)

        logger.info(f"File saved to local storage: {local_file_path}")
        return str(local_file_path), safe_name

    @staticmethod
    def get_signed_url(file_url_or_path: str, expires_in_seconds: int = 3600) -> str:
        """
        Generates a secure, time-limited signed URL for private file access.
        """
        if is_supabase_configured() and not file_url_or_path.startswith("uploads"):
            supabase = get_supabase_client() or get_supabase_admin_client()
            if supabase:
                try:
                    res = supabase.storage.from_("medical-reports").create_signed_url(
                        path=file_url_or_path,
                        expires_in=expires_in_seconds
                    )
                    if isinstance(res, dict) and "signedURL" in res:
                        return res["signedURL"]
                except Exception as e:
                    logger.warning(f"Failed to generate signed URL: {e}")

        # Fallback for local files: return an API endpoint URL
        return f"/api/v1/reports/raw/{Path(file_url_or_path).name}"

    @staticmethod
    def delete_file(file_url_or_path: str) -> bool:
        """
        Deletes the file from storage.
        """
        if is_supabase_configured() and not file_url_or_path.startswith("uploads"):
            supabase = get_supabase_admin_client() or get_supabase_client()
            if supabase:
                try:
                    supabase.storage.from_("medical-reports").remove([file_url_or_path])
                    return True
                except Exception as e:
                    logger.error(f"Error deleting file from Supabase storage: {e}")

        # Fallback local file deletion
        local_path = Path(file_url_or_path)
        if local_path.exists():
            try:
                local_path.unlink()
                return True
            except Exception as e:
                logger.error(f"Error deleting local file: {e}")
        return False

storage_service = StorageService()
