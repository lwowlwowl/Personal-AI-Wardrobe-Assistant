"""
ORM entities; use `from app.models import User, ...`.
"""
from app.core.database import Base

from app.models.ai_conversation import AIConversation
from app.models.clothing import (
    ClothingCategory,
    ClothingCondition,
    ClothingFitType,
    ClothingItem,
    ClothingPattern,
    ClothingSeason,
    ClothingTag,
)
from app.models.model_photo import ModelPhoto
from app.models.outfit import Outfit, OutfitItem
from app.models.user import User
from app.models.wear_history import WearHistory

__all__ = [
    "Base",
    "User",
    "ClothingCategory",
    "ClothingSeason",
    "ClothingCondition",
    "ClothingFitType",
    "ClothingPattern",
    "ClothingItem",
    "ClothingTag",
    "ModelPhoto",
    "Outfit",
    "OutfitItem",
    "AIConversation",
    "WearHistory",
]
