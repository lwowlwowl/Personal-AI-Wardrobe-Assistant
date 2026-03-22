import enum

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ClothingCategory(str, enum.Enum):
    """衣物分类枚举"""
    TOP = "top"           # 上衣
    BOTTOM = "bottom"     # 下装
    DRESS = "dress"       # 连衣裙
    OUTERWEAR = "outerwear"  # 外套
    FOOTWEAR = "footwear"    # 鞋履
    ACCESSORY = "accessory"  # 配饰
    BAG = "bag"           # 包袋
    UNDERWEAR = "underwear"  # 内衣
    OTHER = "other"       # 其他


class ClothingSeason(str, enum.Enum):
    """适用季节枚举"""
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"
    ALL_SEASON = "all_season"  # 四季皆宜


class ClothingCondition(str, enum.Enum):
    """衣物新旧程度枚举"""
    NEW = "new"   # 全新
    GOOD = "good" # 良好
    FAIR = "fair" # 一般
    POOR = "poor" # 较差


class ClothingFitType(str, enum.Enum):
    """衣物版型/合身程度枚举"""
    SLIM = "slim"       # 修身
    REGULAR = "regular" # 常规
    LOOSE = "loose"     # 宽松
    OVERSIZED = "oversized"  # 超大


class ClothingPattern(str, enum.Enum):
    """衣物图案/花纹枚举"""
    SOLID = "solid"     # 纯色
    STRIPED = "striped" # 条纹
    CHECKED = "checked" # 格子
    PRINTED = "printed" # 印花
    PLAID = "plaid"     # 格子呢
    DOTTED = "dotted"   # 波点
    OTHER = "other"     # 其他


class ClothingItem(Base):
    """
    衣物主表
    存储用户衣物的详细信息
    """
    __tablename__ = "clothing_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # 所属用户ID

    # ---- 基本信息 ----
    name = Column(String(200), nullable=False)         # 衣物名称
    description = Column(Text, nullable=True)          # 详细描述
    image_url = Column(String(500), nullable=False)    # 图片URL
    thumbnail_url = Column(String(500), nullable=True) # 缩略图URL

    # ---- 分类信息 ----
    category = Column(SQLEnum(ClothingCategory), nullable=False)  # 主分类
    subcategory = Column(String(100), nullable=True)   # 子分类（如T恤、衬衫等）
    style = Column(String(100), nullable=True)         # 风格（如休闲、商务等）

    # ---- 基本属性 ----
    color = Column(String(50), nullable=True)          # 颜色描述
    color_code = Column(String(7), nullable=True)      # 十六进制颜色码（如#FFFFFF）
    pattern = Column(SQLEnum(ClothingPattern), nullable=True)  # 图案
    brand = Column(String(100), nullable=True)         # 品牌

    # ---- 物理属性 ----
    material = Column(String(100), nullable=True)      # 材质
    size = Column(String(20), nullable=True)           # 尺寸
    fit_type = Column(SQLEnum(ClothingFitType), nullable=True)  # 版型/合身类型

    # ---- 使用信息 ----
    season = Column(ARRAY(SQLEnum(ClothingSeason)), nullable=True)     # 适用季节
    occasion = Column(String(100), nullable=True)      # 适用场合
    purchase_date = Column(Date, nullable=True)        # 购买日期
    price = Column(Numeric(10, 2), nullable=True)      # 购买价格
    purchase_location = Column(String(200), nullable=True)  # 购买地点

    # ---- 状态管理 ----
    is_public = Column(Boolean, default=False)         # 是否公开
    is_favorite = Column(Integer, default=0)            # 收藏等级 0-3（对应前端 0-3 hearts）
    wear_count = Column(Integer, default=0)            # 穿着次数
    last_worn_date = Column(Date, nullable=True)       # 最后穿着日期
    condition = Column(SQLEnum(ClothingCondition), default=ClothingCondition.NEW)  # 新旧程度

    # ---- 时间戳 ----
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())        # 最后更新时间

    # ---- 扩展字段 ----
    custom_metadata = Column(JSON, nullable=True)      # 自定义元数据（JSON格式）

    # ---- 关系定义 ----
    user = relationship("User", back_populates="clothing_items")  # 所属用户
    tags = relationship("ClothingTag", back_populates="clothing_item", cascade="all, delete-orphan")  # 标签
    outfit_items = relationship("OutfitItem", back_populates="clothing_item", cascade="all, delete-orphan")  # 所在搭配
    wear_history = relationship("WearHistory", back_populates="clothing_item")  # 穿着记录

    # ---- 表级约束与索引 ----
    __table_args__ = (
        Index('idx_clothing_user_created', 'user_id', 'created_at'),  # 按用户和创建时间查询
        Index('idx_clothing_category', 'category'),                   # 按分类查询
        Index('idx_clothing_season', 'season', postgresql_using="gin"),                       # 按季节查询
        Index('idx_clothing_brand', 'brand'),                         # 按品牌查询
        Index('idx_clothing_color', 'color'),                         # 按颜色查询
    )


class ClothingTag(Base):
    """
    衣物标签表
    为衣物打上自定义标签，支持灵活的分类与检索
    """
    __tablename__ = "clothing_tags"

    id = Column(Integer, primary_key=True, index=True)
    clothing_id = Column(Integer, ForeignKey("clothing_items.id", ondelete="CASCADE"), nullable=False)  # 所属衣物ID
    tag = Column(String(50), nullable=False)        # 标签内容
    tag_type = Column(String(20), default="custom") # 标签类型（如custom, system等）
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间

    # 关系
    clothing_item = relationship("ClothingItem", back_populates="tags")  # 所属衣物

    # 表级约束与索引
    __table_args__ = (
        UniqueConstraint('clothing_id', 'tag', name='uq_clothing_tag'),  # 同一衣物不能有重复标签
        Index('idx_clothing_tags_clothing_id', 'clothing_id'),          # 按衣物ID查询
        Index('idx_clothing_tags_tag', 'tag'),                          # 按标签内容查询
    )
