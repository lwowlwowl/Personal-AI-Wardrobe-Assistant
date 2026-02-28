"""
schemas.py - Pydantic 数据模型定义文件

该文件定义了整个衣橱管理应用所需的所有Pydantic数据模型（Schema），
用于请求/响应数据验证、序列化和文档生成。包括用户管理、衣物管理、
搭配管理、穿着记录等核心业务模型。

主要功能：
1. 定义API请求/响应的数据结构
2. 提供数据验证规则
3. 支持ORM对象与Pydantic模型的转换
4. 为FastAPI自动生成API文档

"""

from pydantic import BaseModel, EmailStr, validator, Field, ConfigDict
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from enum import Enum


# ==================== 用户相关模型 ====================

class UserBase(BaseModel):
    """用户基础模型，包含用户基本信息"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    """用户创建请求模型，包含密码验证逻辑"""
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    confirm_password: str = Field(..., description="确认密码")

    @validator('username')
    def username_alphanumeric(cls, v):
        """验证用户名只包含字母和数字"""
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """验证两次输入的密码是否一致"""
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不一致')
        return v

    @validator('password')
    def password_strength(cls, v):
        """验证密码强度"""
        if len(v) < 6:
            raise ValueError('密码至少需要6个字符')
        # 可以添加更多密码强度验证
        # if not any(char.isdigit() for char in v):
        #     raise ValueError('密码必须包含至少一个数字')
        return v


class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str
    password: str
    remember: bool = False  # 是否记住登录状态

    @validator('username')
    def username_not_empty(cls, v):
        """验证用户名不为空"""
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()

    @validator('password')
    def password_not_empty(cls, v):
        """验证密码不为空"""
        if not v:
            raise ValueError('密码不能为空')
        return v


class UserResponse(BaseModel):
    """用户信息响应模型（返回给客户端的数据）"""
    id: int
    username: str
    email: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # 允许从ORM对象转换


class LoginResponse(BaseModel):
    """登录响应模型，包含认证令牌和用户信息"""
    success: bool
    message: str
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    expires_in: Optional[int] = None  # 令牌过期时间（秒）
    remember: Optional[bool] = None


# ==================== Token相关模型 ====================

class TokenData(BaseModel):
    """Token中存储的数据结构"""
    user_id: Optional[int] = None
    username: Optional[str] = None


class TokenResponse(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str = "bearer"  # 令牌类型，默认为bearer
    expires_in: int  # 过期时间（秒）
    user_id: int
    username: str


class UserUpdate(BaseModel):
    """用户信息更新模型"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None  # 全名
    avatar_url: Optional[str] = None  # 头像URL
    preferences: Optional[str] = None  # 用户偏好设置


# ==================== 衣物相关枚举 ====================

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


# ==================== 衣物标签模型 ====================

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


# ==================== 衣物管理模型 ====================

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
    season: Optional[ClothingSeason] = Field(None, description="季节")
    occasion: Optional[str] = Field(None, max_length=100, description="场合")
    purchase_date: Optional[date] = Field(None, description="购买日期")
    price: Optional[float] = Field(None, ge=0, description="价格")  # ge=0表示大于等于0
    purchase_location: Optional[str] = Field(
        None, max_length=200, description="购买地点"
    )
    is_public: bool = Field(False, description="是否公开")
    is_favorite: bool = Field(False, description="是否收藏")
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
    season: Optional[ClothingSeason] = None
    occasion: Optional[str] = Field(None, max_length=100)
    purchase_date: Optional[date] = None
    price: Optional[float] = Field(None, ge=0)
    purchase_location: Optional[str] = Field(None, max_length=200)
    is_public: Optional[bool] = None
    is_favorite: Optional[bool] = None
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


# ==================== 穿着记录模型 ====================

class WearHistoryBase(BaseModel):
    """穿着记录基础模型"""
    wear_date: date = Field(..., description="穿着日期")
    weather: Optional[str] = Field(None, max_length=100, description="天气")
    temperature: Optional[int] = Field(None, description="温度")
    location: Optional[str] = Field(None, max_length=200, description="地点")
    occasion: Optional[str] = Field(None, max_length=100, description="场合")
    notes: Optional[str] = Field(None, description="备注")
    rating: Optional[int] = Field(None, ge=1, le=5, description="满意度评分")  # 1-5分

    @validator('wear_date')
    def wear_date_not_future(cls, v):
        """验证穿着日期不是未来日期"""
        if v > date.today():
            raise ValueError('穿着日期不能是未来日期')
        return v


class WearHistoryCreate(WearHistoryBase):
    """创建穿着记录请求模型"""
    clothing_id: Optional[int] = Field(None, description="衣物ID")
    outfit_id: Optional[int] = Field(None, description="搭配ID")  # 如果记录的是整套搭配


class WearHistory(WearHistoryBase):
    """穿着记录完整模型"""
    id: int
    user_id: int  # 用户ID
    clothing_id: Optional[int] = None
    outfit_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 日历穿搭（MyCalendar）模型 ====================


class CalendarOutfitItem(BaseModel):
    """日历中的单个穿搭单品（与前端 MyCalendar 保持字段一致）"""
    id: int = Field(..., description="单品 id（对应衣橱中的 clothing_id）")
    name: Optional[str] = Field(None, description="单品名称（可选）")
    image: Optional[str] = Field(None, description="图片 URL（可选）")
    accentColor: Optional[str] = Field(None, description="主题色（前端展示用，可选）")


class CalendarOutfitSave(BaseModel):
    """保存 / 更新某天日历穿搭记录的请求体"""
    date: str = Field(..., description="日期（YYYY-MM-DD）")
    items: List[CalendarOutfitItem] = Field(default_factory=list, description="当日穿搭单品数组（可为空数组表示清空）")


# ==================== 搭配管理模型 ====================

class OutfitItemBase(BaseModel):
    """搭配中的单件衣物模型"""
    clothing_id: int = Field(..., description="衣物ID")
    position: str = Field(..., max_length=20, description="位置：top, bottom等")
    order_index: int = Field(0, description="显示顺序")


class OutfitItemCreate(OutfitItemBase):
    """创建搭配衣物请求模型"""
    pass


class OutfitItem(OutfitItemBase):
    """搭配衣物完整模型"""
    id: int
    outfit_id: int  # 所属搭配ID

    model_config = ConfigDict(from_attributes=True)


class OutfitBase(BaseModel):
    """搭配基础模型"""
    name: str = Field(..., max_length=200, description="搭配名称")
    description: Optional[str] = Field(None, description="描述")
    occasion: Optional[str] = Field(None, max_length=100, description="场合")
    season: Optional[str] = Field(None, max_length=20, description="季节")
    style: Optional[str] = Field(None, max_length=100, description="风格")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分")
    is_public: bool = Field(False, description="是否公开")


class OutfitCreate(OutfitBase):
    """创建搭配请求模型"""
    clothing_items: List[OutfitItemCreate] = Field([], description="衣物列表")
    cover_image_url: Optional[str] = Field(None, description="封面图URL")


class OutfitUpdate(BaseModel):
    """更新搭配请求模型"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    occasion: Optional[str] = Field(None, max_length=100)
    season: Optional[str] = Field(None, max_length=20)
    style: Optional[str] = Field(None, max_length=100)
    rating: Optional[int] = Field(None, ge=1, le=5)
    is_public: Optional[bool] = None
    cover_image_url: Optional[str] = None
    wear_count: Optional[int] = Field(None, ge=0)  # 穿着次数
    last_worn_date: Optional[date] = None  # 最后穿着日期


class Outfit(OutfitBase):
    """搭配完整模型"""
    id: int
    user_id: int  # 所属用户ID
    cover_image_url: Optional[str] = None
    wear_count: int = Field(0, description="穿着次数")
    last_worn_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    clothing_items: List[OutfitItem] = Field([], description="衣物列表")

    model_config = ConfigDict(from_attributes=True)


# ==================== 文件上传相关模型 ====================

class UploadResponse(BaseModel):
    """文件上传响应模型"""
    success: bool
    message: str
    image_url: Optional[str] = None  # 原图URL
    thumbnail_url: Optional[str] = None  # 缩略图URL
    clothing_id: Optional[int] = None  # 关联的衣物ID


# ==================== 批量操作模型 ====================

class BatchUpdateClothing(BaseModel):
    """批量更新衣物请求模型"""
    clothing_ids: List[int] = Field(..., description="衣物ID列表")
    update_data: Dict[str, Any] = Field(..., description="更新数据")


class BatchDeleteClothing(BaseModel):
    """批量删除衣物请求模型"""
    clothing_ids: List[int] = Field(..., description="衣物ID列表")


# ==================== 筛选和搜索模型 ====================

class FilterOptions(BaseModel):
    """筛选选项模型"""
    categories: List[str] = Field([], description="分类列表")
    seasons: List[str] = Field([], description="季节列表")
    colors: List[str] = Field([], description="颜色列表")
    brands: List[str] = Field([], description="品牌列表")
    sizes: List[str] = Field([], description="尺码列表")
    materials: List[str] = Field([], description="材质列表")


class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: Optional[str] = Field(None, description="搜索关键词")
    category: Optional[str] = Field(None, description="分类")
    season: Optional[str] = Field(None, description="季节")
    color: Optional[str] = Field(None, description="颜色")
    brand: Optional[str] = Field(None, description="品牌")
    min_price: Optional[float] = Field(None, ge=0, description="最低价格")
    max_price: Optional[float] = Field(None, ge=0, description="最高价格")
    is_favorite: Optional[bool] = Field(None, description="是否收藏")
    page: int = Field(1, ge=1, description="页码")  # ge=1表示最小为1
    size: int = Field(20, ge=1, le=100, description="每页数量")  # le=100表示最大100
    order_by: str = Field("created_at", description="排序字段")
    order_desc: bool = Field(True, description="是否降序")


# ==================== 衣物类型配置模型 ====================

class ClothingTypeResponse(BaseModel):
    """衣物类型配置响应模型"""
    categories: List[Dict[str, str]] = Field(..., description="主分类")
    subcategories: Dict[str, List[Dict[str, str]]] = Field(
        ..., description="子分类映射"
    )


# ==================== 通用响应模型 ====================

class SuccessResponse(BaseModel):
    """成功响应通用模型"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None  # 响应数据


class ErrorResponse(BaseModel):
    """错误响应通用模型"""
    success: bool = False
    message: str
    error_code: Optional[str] = None  # 错误代码
    details: Optional[Dict[str, Any]] = None  # 错误详情


# ==================== 数据分析模型 ====================

class ClothingAnalysis(BaseModel):
    """衣物数据分析模型"""
    color_distribution: Dict[str, int] = Field({}, description="颜色分布")
    brand_distribution: Dict[str, int] = Field({}, description="品牌分布")
    category_distribution: Dict[str, int] = Field({}, description="分类分布")
    most_expensive: Optional[ClothingItem] = Field(None, description="最贵衣物")
    least_worn: Optional[ClothingItem] = Field(None, description="最少穿着")
    total_investment: float = Field(0, description="总投资")
    cost_per_wear: Dict[int, float] = Field({}, description="每次穿着成本")


# ==================== 模特照片模型 ====================

class ModelPhotoBase(BaseModel):
    """模特照片基础模型"""
    photo_name: str  # 照片名称
    description: Optional[str] = None  # 描述
    is_primary: Optional[bool] = False  # 是否为主照片


class ModelPhotoCreate(ModelPhotoBase):
    """创建模特照片请求模型"""
    pass


class ModelPhotoUpdate(BaseModel):
    """更新模特照片请求模型"""
    photo_name: Optional[str] = None
    description: Optional[str] = None
    is_primary: Optional[bool] = None


class ModelPhotoInDB(ModelPhotoBase):
    """模特照片数据库模型"""
    id: int
    user_id: int  # 所属用户ID
    image_url: str  # 图片URL
    thumbnail_url: Optional[str] = None  # 缩略图URL
    file_size: Optional[int] = None  # 文件大小（字节）
    file_format: Optional[str] = None  # 文件格式
    is_active: bool  # 是否激活
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True  # 兼容旧版Pydantic


class ModelPhotoResponse(BaseModel):
    """模特照片响应模型"""
    success: bool
    message: Optional[str] = None
    data: Optional[Union[ModelPhotoInDB, List[ModelPhotoInDB], dict]] = None


# ==================== 数据导出模型 ====================

class ExportData(BaseModel):
    """数据导出模型"""
    clothing_items: List[ClothingItem]  # 衣物列表
    outfits: List[Outfit]  # 搭配列表
    wear_history: List[WearHistory]  # 穿着记录
    export_date: datetime = Field(default_factory=datetime.now)  # 导出时间
    total_items: int  # 总衣物数
    total_outfits: int  # 总搭配数
    total_wears: int  # 总穿着次数
