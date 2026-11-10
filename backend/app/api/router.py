from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.reports import router as reports_router
from app.api.v1.ocr import router as ocr_router
from app.api.v1.glossary import router as glossary_router
from app.api.v1.explanation import router as explanation_router
from app.api.v1.chat import router as chat_router
from app.api.v1.comparison import router as comparison_router
from app.api.v1.doctor import router as doctor_router
from app.api.v1.prescriptions import router as prescriptions_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(reports_router)
api_router.include_router(ocr_router)
api_router.include_router(glossary_router)
api_router.include_router(explanation_router)
api_router.include_router(chat_router)
api_router.include_router(comparison_router)
api_router.include_router(doctor_router)
api_router.include_router(prescriptions_router)



