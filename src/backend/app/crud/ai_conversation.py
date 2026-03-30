"""CRUD for Recommendation AI conversations."""
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import AIConversation

class AIConversationCRUD:
    """Persist Recommendation AI conversations (Your conversations)."""

    @staticmethod
    def list_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 200):
        """
        List conversations for a user.

        Sort: most recently updated first (`updated_at` descending).
        """
        try:
            query = db.query(AIConversation).filter(AIConversation.user_id == user_id)
            total = query.count()
            items = query.order_by(desc(AIConversation.updated_at)).offset(skip).limit(limit).all()
            return items, total, None
        except Exception as e:
            return [], 0, str(e)

    @staticmethod
    def get_by_id_and_user(db: Session, conversation_id: int, user_id: int):
        """Fetch one conversation by primary key, scoped to `user_id`."""
        try:
            conv = db.query(AIConversation).filter(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user_id
            ).first()
            return conv, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def create(db: Session, user_id: int, title: str = "New conversation", messages: list = None):
        """Insert a new conversation row (empty `messages` if omitted)."""
        try:
            conv = AIConversation(
                user_id=user_id,
                title=title or "New conversation",
                messages=messages if messages is not None else []
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)
            return conv, None
        except Exception as e:
            db.rollback()
            return None, str(e)

    @staticmethod
    def update(db: Session, conversation_id: int, user_id: int, title: str = None, messages: list = None):
        """Update `title` and/or `messages`; pass None to leave a field unchanged."""
        try:
            conv = db.query(AIConversation).filter(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user_id
            ).first()
            if not conv:
                return None, "Conversation not found."
            if title is not None:
                conv.title = title[:200] if len(title) > 200 else title
            if messages is not None:
                conv.messages = messages
            db.commit()
            db.refresh(conv)
            return conv, None
        except Exception as e:
            db.rollback()
            return None, str(e)

    @staticmethod
    def delete(db: Session, conversation_id: int, user_id: int):
        """Delete a conversation row after verifying ownership."""
        try:
            conv = db.query(AIConversation).filter(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user_id
            ).first()
            if not conv:
                return False, "Conversation not found."
            db.delete(conv)
            db.commit()
            return True, None
        except Exception as e:
            db.rollback()
            return False, str(e)
