from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatReq(BaseModel):
    query: str
    history: list[dict] = Field(default_factory=list)


class AIConversationCreate(BaseModel):
    title: str = "New conversation"
    messages: List[Dict[str, Any]] = Field(default_factory=list)


class AIConversationUpdate(BaseModel):
    title: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None


class AIConversationResponse(BaseModel):
    id: int
    title: str
    messages: List[Dict[str, Any]]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
