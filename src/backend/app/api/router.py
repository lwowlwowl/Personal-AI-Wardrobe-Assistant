from fastapi import APIRouter

from app.api.v1 import ai_chat, analysis, auth, calendar, clothing, model_photos, system, users, virtual_tryon, weather

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(weather.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(clothing.router)
api_router.include_router(calendar.router)
api_router.include_router(model_photos.router)
api_router.include_router(analysis.router)
api_router.include_router(ai_chat.router)
api_router.include_router(virtual_tryon.router)
