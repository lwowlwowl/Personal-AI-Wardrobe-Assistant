from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, validator


class ClothingCategory(str, Enum):
    """衣物主分类枚举"""
    TOP = "top"  # 上衣
    BOTTOM = "bottom"  # 下装
    DRESS = "dress"  # 连衣裙
    OUTERWEAR = "outerwear"  # 外套
    FOOTWEAR = "footwear"  # 鞋履
    ACCESSORY = "accessory"  # 配饰
    BAG = "bag"  # 包袋
    UNDERWEAR = "underwear"  # 内衣
    OTHER = "other"  # 其他


class ClothingSeason(str, Enum):
    """衣物适用季节枚举"""
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"
    ALL_SEASON = "all_season"  # 四季通用


class ClothingCondition(str, Enum):
    """衣物新旧程度枚举"""
    NEW = "new"  # 全新
    GOOD = "good"  # 良好
    FAIR = "fair"  # 一般
    POOR = "poor"  # 较差


class ClothingFitType(str, Enum):
    """衣物版型枚举"""
    SLIM = "slim"  # 修身
    REGULAR = "regular"  # 常规
    LOOSE = "loose"  # 宽松
    OVERSIZED = "oversized"  # 超大


class ClothingPattern(str, Enum):
    """衣物图案枚举"""
    SOLID = "solid"  # 纯色
    STRIPED = "striped"  # 条纹
    CHECKED = "checked"  # 格子
    PRINTED = "printed"  # 印花
    PLAID = "plaid"  # 格子呢
    DOTTED = "dotted"  # 波点
    OTHER = "other"  # 其他


class ClothingTagBase(BaseModel):
    """衣物标签基础模型"""
    tag: str = Field(..., max_length=50)
    tag_type: str = Field("custom", max_length=20)  # 标签类型：custom, system等


class ClothingTagCreate(ClothingTagBase):
    """创建衣物标签请求模型"""
    pass


class ClothingTag(ClothingTagBase):
    """衣物标签完整模型（包含数据库字段）"""
    id: int
    clothing_id: int  # 关联的衣物ID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClothingItemBase(BaseModel):
    """衣物基础模型，定义通用属性"""
    name: str = Field(..., max_length=200, description="衣物名称")
    description: Optional[str] = Field(None, description="描述")
    category: ClothingCategory = Field(..., description="主分类")
    subcategory: Optional[str] = Field(None, max_length=100, description="子分类")
    style: Optional[str] = Field(None, max_length=100, description="风格")
    color: Optional[str] = Field(None, max_length=50, description="颜色")
    color_code: Optional[str] = Field(
        None,
        pattern="^#[0-9A-Fa-f]{6}$",  # 十六进制颜色代码正则
        description="颜色代码，如#FFFFFF"
    )
    pattern: Optional[ClothingPattern] = Field(None, description="图案")
    brand: Optional[str] = Field(None, max_length=100, description="品牌")
    material: Optional[str] = Field(None, max_length=100, description="材质")
    size: Optional[str] = Field(None, max_length=20, description="尺码")
    fit_type: Optional[ClothingFitType] = Field(None, description="版型")
    season: Optional[List[ClothingSeason]] = Field(None, description="季节列表")
    occasion: Optional[str] = Field(None, max_length=100, description="场合")
    purchase_date: Optional[date] = Field(None, description="购买日期")
    price: Optional[float] = Field(None, ge=0, description="价格")  # ge=0表示大于等于0
    purchase_location: Optional[str] = Field(
        None, max_length=200, description="购买地点"
    )
    is_public: bool = Field(False, description="是否公开")
    is_favorite: int = Field(0, ge=0, le=3, description="收藏等级 0-3")
    condition: ClothingCondition = Field(
        ClothingCondition.NEW, description="状态"
    )
    custom_metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")

    @validator('color_code')
    def validate_color_code(cls, v):
        """确保颜色代码以#开头"""
        if v and not v.startswith('#'):
            v = '#' + v
        return v


class ClothingItemCreate(ClothingItemBase):
    """创建衣物请求模型"""
    tags: Optional[List[str]] = Field([], description="标签列表")  # 字符串标签列表


class ClothingItemUpdate(BaseModel):
    """更新衣物请求模型（所有字段可选）"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category: Optional[ClothingCategory] = None
    subcategory: Optional[str] = Field(None, max_length=100)
    style: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    color_code: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    pattern: Optional[ClothingPattern] = None
    brand: Optional[str] = Field(None, max_length=100)
    material: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, max_length=20)
    fit_type: Optional[ClothingFitType] = None
    season: Optional[List[ClothingSeason]] = Field(None, description="季节列表")
    occasion: Optional[str] = Field(None, max_length=100)
    purchase_date: Optional[date] = None
    price: Optional[float] = Field(None, ge=0)
    purchase_location: Optional[str] = Field(None, max_length=200)
    is_public: Optional[bool] = None
    is_favorite: Optional[int] = Field(None, ge=0, le=3, description="收藏等级 0-3")
    condition: Optional[ClothingCondition] = None
    wear_count: Optional[int] = Field(None, ge=0)  # 穿着次数
    last_worn_date: Optional[date] = None  # 最后穿着日期
    custom_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None  # 更新标签列表

    @validator('color_code')
    def validate_color_code(cls, v):
        """确保颜色代码以#开头"""
        if v and not v.startswith('#'):
            v = '#' + v
        return v


class ClothingItem(ClothingItemBase):
    """衣物完整模型（包含所有数据库字段）"""
    id: int
    user_id: int  # 所属用户ID
    image_url: str = Field(..., description="图片URL")
    thumbnail_url: Optional[str] = Field(None, description="缩略图URL")
    wear_count: int = Field(0, description="穿着次数")
    last_worn_date: Optional[date] = Field(None, description="最后穿着日期")
    created_at: datetime
    updated_at: datetime
    tags: List[ClothingTag] = Field([], description="标签列表")  # 完整的标签对象列表
    avg_rating: Optional[float] = Field(None, ge=0, le=5, description="平均评分")  # 0-5分

    model_config = ConfigDict(from_attributes=True)


class ClothingItemList(BaseModel):
    """衣物列表分页响应模型"""
    items: List[ClothingItem]  # 当前页的衣物列表
    total: int  # 总记录数
    page: int  # 当前页码
    size: int  # 每页数量
    pages: int  # 总页数


class ClothingStats(BaseModel):
    """衣物统计信息模型"""
    total_items: int = Field(0, description="总衣物数")
    total_cost: float = Field(0, description="总花费")
    avg_price: float = Field(0, description="平均价格")
    by_category: Dict[str, int] = Field({}, description="按分类统计")
    by_season: Dict[str, int] = Field({}, description="按季节统计")
    most_worn: List[Dict[str, Any]] = Field([], description="最常穿着")
    recently_added: List[Dict[str, Any]] = Field([], description="最近添加")
    wear_frequency: Dict[str, int] = Field({}, description="穿着频率")


class UploadResponse(BaseModel):
    """文件上传响应模型"""
    success: bool
    message: str
    image_url: Optional[str] = None  # 原图URL
    thumbnail_url: Optional[str] = None  # 缩略图URL
    clothing_id: Optional[int] = None  # 关联的衣物ID


class BatchUpdateClothing(BaseModel):
    """批量更新衣物请求模型"""
    clothing_ids: List[int] = Field(..., description="衣物ID列表")
    update_data: Dict[str, Any] = Field(..., description="更新数据")


class BatchDeleteClothing(BaseModel):
    """批量删除衣物请求模型"""
    clothing_ids: List[int] = Field(..., description="衣物ID列表")


class FilterOptions(BaseModel):
    """筛选选项模型"""
    categories: List[str] = Field([], description="分类列表")
    season: Optional[List[ClothingSeason]] = Field(None, description="季节列表")
    colors: List[str] = Field([], description="颜色列表")
    brands: List[str] = Field([], description="品牌列表")
    sizes: List[str] = Field([], description="尺码列表")
    materials: List[str] = Field([], description="材质列表")


class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: Optional[str] = Field(None, description="搜索关键词")
    category: Optional[str] = Field(None, description="分类")
    season: Optional[List[ClothingSeason]] = Field(None, description="季节列表")
    color: Optional[str] = Field(None, description="颜色")
    brand: Optional[str] = Field(None, description="品牌")
    min_price: Optional[float] = Field(None, ge=0, description="最低价格")
    max_price: Optional[float] = Field(None, ge=0, description="最高价格")
    is_favorite: Optional[int] = Field(None, ge=0, le=3, description="收藏等级 0-3")
    page: int = Field(1, ge=1, description="页码")  # ge=1表示最小为1
    size: int = Field(20, ge=1, le=100, description="每页数量")  # le=100表示最大100
    order_by: str = Field("created_at", description="排序字段")
    order_desc: bool = Field(True, description="是否降序")


class ClothingTypeResponse(BaseModel):
    """衣物类型配置响应模型"""
    categories: List[Dict[str, str]] = Field(..., description="主分类")
    subcategories: Dict[str, List[Dict[str, str]]] = Field(
        ..., description="子分类映射"
    )


class ClothingAnalysis(BaseModel):
    """衣物数据分析模型"""
    color_distribution: Dict[str, int] = Field({}, description="颜色分布")
    brand_distribution: Dict[str, int] = Field({}, description="品牌分布")
    category_distribution: Dict[str, int] = Field({}, description="分类分布")
    most_expensive: Optional[ClothingItem] = Field(None, description="最贵衣物")
    least_worn: Optional[ClothingItem] = Field(None, description="最少穿着")
    total_investment: float = Field(0, description="总投资")
    cost_per_wear: Dict[int, float] = Field({}, description="每次穿着成本")
