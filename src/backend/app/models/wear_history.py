from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class WearHistory(Base):
    """
    穿着记录表
    记录用户穿着某件衣物或某个搭配的历史记录
    """
    __tablename__ = "wear_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # 用户ID
    clothing_id = Column(Integer, ForeignKey("clothing_items.id", ondelete="SET NULL"), nullable=True)  # 衣物ID（可为空，表示仅记录搭配）
    outfit_id = Column(Integer, ForeignKey("outfits.id", ondelete="SET NULL"), nullable=True)  # 搭配ID（可为空，表示仅记录单件衣物）

    wear_date = Column(Date, nullable=False)       # 穿着日期
    weather = Column(String(100), nullable=True)   # 天气情况
    temperature = Column(Integer, nullable=True)   # 温度（摄氏度）
    location = Column(String(200), nullable=True)  # 地点
    occasion = Column(String(100), nullable=True)  # 场合
    notes = Column(Text, nullable=True)            # 备注
    rating = Column(Integer, nullable=True)        # 本次穿着评分（1-5分）
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 记录创建时间

    # 关系
    user = relationship("User", back_populates="wear_history")        # 所属用户
    clothing_item = relationship("ClothingItem", back_populates="wear_history")  # 对应的衣物（可选）
    outfit = relationship("Outfit", back_populates="wear_history")    # 对应的搭配（可选）

    # 表级约束与索引
    __table_args__ = (
        CheckConstraint('rating IS NULL OR (rating >= 1 AND rating <= 5)', name='ck_wear_history_rating'),  # 评分范围约束
        Index('idx_wear_history_user_date', 'user_id', 'wear_date'),  # 按用户和穿着日期查询
        Index('idx_wear_history_clothing', 'clothing_id'),            # 按衣物查询
        Index('idx_wear_history_outfit', 'outfit_id'),                # 按搭配查询
        Index('idx_wear_history_date', 'wear_date'),                  # 按日期查询
    )
