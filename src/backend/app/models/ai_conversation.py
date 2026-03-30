from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AIConversation(Base):
    """
    Recommendation AI chat threads; persisted for restore after re-login.
    """
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(200), nullable=False, default="New conversation")
    messages = Column(JSON, nullable=False, default=list)  # [{ role, content }, ...]

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="ai_conversations")

    __table_args__ = (
        Index("idx_ai_conversations_user_updated", "user_id", "updated_at"),
    )
