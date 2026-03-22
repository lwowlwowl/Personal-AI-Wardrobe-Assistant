from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """
    用户表
    存储系统用户的基本信息、认证凭证及偏好设置
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)  # 用户名，唯一且必填
    email = Column(String(100), unique=True, index=True, nullable=True)     # 邮箱，唯一，可选
    hashed_password = Column(String(255), nullable=False)                   # 加密后的密码
    is_active = Column(Boolean, default=True)                               # 账户是否激活
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())       # 最后更新时间

    # 用户个人资料字段
    full_name = Column(String(100), nullable=True)                          # 用户全名
    avatar_url = Column(String(255), nullable=True)                         # 头像URL

    # 定义关系（一对多）
    clothing_items = relationship("ClothingItem", back_populates="user", cascade="all, delete-orphan")  # 用户拥有的衣物
    outfits = relationship("Outfit", back_populates="user", cascade="all, delete-orphan")               # 用户创建的搭配
    wear_history = relationship("WearHistory", back_populates="user", cascade="all, delete-orphan")     # 用户的穿着记录
    model_photos = relationship("ModelPhoto", back_populates="user", cascade="all, delete-orphan")      # 用户的模特照片
    ai_conversations = relationship("AIConversation", back_populates="user", cascade="all, delete-orphan")  # 推荐 AI 对话记录
