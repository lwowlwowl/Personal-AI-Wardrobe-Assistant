from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ModelPhoto(Base):
    """
    模特照片表
    存储用户的模特照片，可用于虚拟试衣或搭配展示
    """
    __tablename__ = "model_photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # 所属用户ID
    photo_name = Column(String(200), nullable=False)   # 照片名称
    description = Column(Text, nullable=True)          # 描述

    # ---- 照片存储信息 ----
    image_url = Column(String(500), nullable=False)    # 原图URL
    thumbnail_url = Column(String(500), nullable=True) # 缩略图URL
    file_size = Column(Integer, nullable=True)         # 文件大小（字节）
    file_format = Column(String(10), nullable=True)    # 文件格式（如jpg, png）

    # ---- 状态标记 ----
    is_active = Column(Boolean, default=True)          # 是否可用
    is_primary = Column(Boolean, default=False)        # 是否为主模特照片（用于默认展示）

    # ---- 时间戳 ----
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # 最后更新时间

    # 关系
    user = relationship("User", back_populates="model_photos")  # 所属用户

    def __repr__(self):
        """友好的字符串表示，便于调试"""
        return f"<ModelPhoto(id={self.id}, user_id={self.user_id}, name={self.photo_name})>"
