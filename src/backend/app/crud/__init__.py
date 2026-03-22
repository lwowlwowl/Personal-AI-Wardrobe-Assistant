"""CRUD 聚合；請使用 `import app.crud as crud` 或 `from app.crud import ...`。"""
from app.core.security import create_access_token, verify_access_token

from app.crud.ai_conversation import AIConversationCRUD
from app.crud.batch import BatchCRUD
from app.crud.clothing import ClothingCRUD
from app.crud.model_photo import ModelPhotoCRUD
from app.crud.outfit import OutfitCRUD
from app.crud.user import (
    authenticate_user,
    change_password,
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    update_user,
    update_user_password,
)
from app.crud.wear_history import WearHistoryCRUD

model_photo_crud = ModelPhotoCRUD()
ai_conversation_crud = AIConversationCRUD()
clothing_crud = ClothingCRUD()
wear_history_crud = WearHistoryCRUD()
outfit_crud = OutfitCRUD()
batch_crud = BatchCRUD()

__all__ = [
    "create_access_token",
    "verify_access_token",
    "get_user_by_username",
    "get_user_by_email",
    "get_user_by_id",
    "update_user",
    "change_password",
    "create_user",
    "authenticate_user",
    "update_user_password",
    "ClothingCRUD",
    "WearHistoryCRUD",
    "OutfitCRUD",
    "BatchCRUD",
    "ModelPhotoCRUD",
    "AIConversationCRUD",
    "model_photo_crud",
    "ai_conversation_crud",
    "clothing_crud",
    "wear_history_crud",
    "outfit_crud",
    "batch_crud",
]
