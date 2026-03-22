"""推荐 AI 对话 CRUD。"""
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import AIConversation

class AIConversationCRUD:
    """推荐 AI 对话持久化（Your conversations）"""

    @staticmethod
    def list_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 200):
        """按用户获取对话列表，按 updated_at 降序"""
        try:
            query = db.query(AIConversation).filter(AIConversation.user_id == user_id)
            total = query.count()
            items = query.order_by(desc(AIConversation.updated_at)).offset(skip).limit(limit).all()
            return items, total, None
        except Exception as e:
            return [], 0, str(e)

    @staticmethod
    def get_by_id_and_user(db: Session, conversation_id: int, user_id: int):
        """按 id 和 user_id 获取单条对话"""
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
        """创建一条对话"""
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
        """更新对话的 title 和/或 messages"""
        try:
            conv = db.query(AIConversation).filter(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user_id
            ).first()
            if not conv:
                return None, "对话不存在"
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
        """删除一条对话"""
        try:
            conv = db.query(AIConversation).filter(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user_id
            ).first()
            if not conv:
                return False, "对话不存在"
            db.delete(conv)
            db.commit()
            return True, None
        except Exception as e:
            db.rollback()
            return False, str(e)
