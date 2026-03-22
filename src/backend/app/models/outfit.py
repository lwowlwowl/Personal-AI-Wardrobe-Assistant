from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Outfit(Base):
    """
    搭配表
    存储用户创建的衣物搭配方案
    """
    __tablename__ = "outfits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # 所属用户ID

    name = Column(String(200), nullable=False)         # 搭配名称
    description = Column(Text, nullable=True)          # 搭配描述
    cover_image_url = Column(String(500), nullable=True)  # 封面图片URL
    occasion = Column(String(100), nullable=True)      # 适用场合
    season = Column(String(20), nullable=True)         # 适用季节
    style = Column(String(100), nullable=True)         # 风格
    rating = Column(Integer, nullable=True)            # 评分（1-5分）
    is_public = Column(Boolean, default=False)         # 是否公开
    wear_count = Column(Integer, default=0)            # 穿着次数
    last_worn_date = Column(Date, nullable=True)       # 最后穿着日期
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())        # 最后更新时间

    # 关系
    user = relationship("User", back_populates="outfits")  # 所属用户
    outfit_items = relationship("OutfitItem", back_populates="outfit", cascade="all, delete-orphan")  # 包含的衣物项
    wear_history = relationship("WearHistory", back_populates="outfit")  # 穿着记录

    # 表级约束与索引
    __table_args__ = (
        CheckConstraint('rating IS NULL OR (rating >= 1 AND rating <= 5)', name='ck_outfit_rating'),  # 评分范围约束
        Index('idx_outfits_user_created', 'user_id', 'created_at'),  # 按用户和创建时间查询
        Index('idx_outfits_occasion', 'occasion'),                   # 按场合查询
        Index('idx_outfits_season', 'season'),                       # 按季节查询
    )


class OutfitItem(Base):
    """
    搭配-衣物关联表
    记录搭配中包含的衣物及其顺序/位置
    """
    __tablename__ = "outfit_items"

    id = Column(Integer, primary_key=True, index=True)
    outfit_id = Column(Integer, ForeignKey("outfits.id", ondelete="CASCADE"), nullable=False)  # 所属搭配ID
    clothing_id = Column(Integer, ForeignKey("clothing_items.id", ondelete="CASCADE"), nullable=False)  # 衣物ID
    position = Column(String(20), nullable=False)  # 位置描述（如top, bottom, accessory等）
    order_index = Column(Integer, default=0)       # 显示顺序（用于排序）

    # 关系
    outfit = relationship("Outfit", back_populates="outfit_items")          # 所属搭配
    clothing_item = relationship("ClothingItem", back_populates="outfit_items")  # 对应的衣物

    # 表级约束与索引
    __table_args__ = (
        UniqueConstraint('outfit_id', 'clothing_id', name='uq_outfit_clothing'),  # 同一搭配中同一衣物只能出现一次
        Index('idx_outfit_items_outfit', 'outfit_id', 'order_index'),      # 按搭配和顺序查询
        Index('idx_outfit_items_clothing', 'clothing_id'),                 # 按衣物查询
    )
