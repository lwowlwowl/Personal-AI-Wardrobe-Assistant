from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Numeric, Date, \
    Enum as SQLEnum, Index, UniqueConstraint, CheckConstraint, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

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
    preferences = Column(String(500), nullable=True)                        # 用户偏好设置（JSON格式）

    # 定义关系（一对多）
    clothing_items = relationship("ClothingItem", back_populates="user", cascade="all, delete-orphan")  # 用户拥有的衣物
    outfits = relationship("Outfit", back_populates="user", cascade="all, delete-orphan")               # 用户创建的搭配
    wear_history = relationship("WearHistory", back_populates="user", cascade="all, delete-orphan")     # 用户的穿着记录
    model_photos = relationship("ModelPhoto", back_populates="user", cascade="all, delete-orphan")      # 用户的模特照片

# ========== 枚举定义 ==========
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
