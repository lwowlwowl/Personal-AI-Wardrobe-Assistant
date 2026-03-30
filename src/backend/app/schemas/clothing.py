from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, validator


class ClothingCategory(str, Enum):
    """Primary clothing category."""
    TOP = "top"  # tops
    BOTTOM = "bottom"  # bottoms
    DRESS = "dress"  # dresses
    OUTERWEAR = "outerwear"  # outerwear
    FOOTWEAR = "footwear"  # shoes
    ACCESSORY = "accessory"  # accessories
    BAG = "bag"  # bags
    UNDERWEAR = "underwear"  # underwear
    OTHER = "other"  # other


class ClothingSeason(str, Enum):
    """Season tag."""
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"
    ALL_SEASON = "all_season"  # year-round


class ClothingCondition(str, Enum):
    """Wear condition."""
    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class ClothingFitType(str, Enum):
    """Fit / silhouette."""
    SLIM = "slim"
    REGULAR = "regular"
    LOOSE = "loose"
    OVERSIZED = "oversized"


class ClothingPattern(str, Enum):
    """Pattern / print."""
    SOLID = "solid"
    STRIPED = "striped"
    CHECKED = "checked"
    PRINTED = "printed"
    PLAID = "plaid"
    DOTTED = "dotted"
    OTHER = "other"


class ClothingTagBase(BaseModel):
    """Tag on a clothing item."""
    tag: str = Field(..., max_length=50)
    tag_type: str = Field("custom", max_length=20)  # e.g. custom, system


class ClothingTagCreate(ClothingTagBase):
    """Create tag."""
    pass


class ClothingTag(ClothingTagBase):
    """Tag with DB fields."""
    id: int
    clothing_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClothingItemBase(BaseModel):
    """Shared clothing fields."""
    name: str = Field(..., max_length=200, description="Name")
    description: Optional[str] = Field(None, description="Description")
    category: ClothingCategory = Field(..., description="Primary category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Subcategory")
    style: Optional[str] = Field(None, max_length=100, description="Style")
    color: Optional[str] = Field(None, max_length=50, description="Color")
    color_code: Optional[str] = Field(
        None,
        pattern="^#[0-9A-Fa-f]{6}$",
        description="Hex color e.g. #FFFFFF",
    )
    pattern: Optional[ClothingPattern] = Field(None, description="Pattern")
    brand: Optional[str] = Field(None, max_length=100, description="Brand")
    material: Optional[str] = Field(None, max_length=100, description="Material")
    size: Optional[str] = Field(None, max_length=20, description="Size")
    fit_type: Optional[ClothingFitType] = Field(None, description="Fit")
    season: Optional[List[ClothingSeason]] = Field(None, description="Seasons")
    occasion: Optional[str] = Field(None, max_length=100, description="Occasion")
    purchase_date: Optional[date] = Field(None, description="Purchase date")
    price: Optional[float] = Field(None, ge=0, description="Price")  # ge=0
    purchase_location: Optional[str] = Field(
        None, max_length=200, description="Purchase location"
    )
    is_public: bool = Field(False, description="Public flag")
    is_favorite: int = Field(0, ge=0, le=3, description="Favorite level 0-3")
    condition: ClothingCondition = Field(
        ClothingCondition.NEW, description="Condition"
    )
    custom_metadata: Optional[Dict[str, Any]] = Field(None, description="Extra metadata")

    @validator('color_code')
    def validate_color_code(cls, v):
        """Normalize leading # on hex colors."""
        if v and not v.startswith('#'):
            v = '#' + v
        return v


class ClothingItemCreate(ClothingItemBase):
    """Create clothing."""
    tags: Optional[List[str]] = Field([], description="Tag strings")


class ClothingItemUpdate(BaseModel):
    """Update clothing (all optional)."""
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
    season: Optional[List[ClothingSeason]] = Field(None, description="Seasons")
    occasion: Optional[str] = Field(None, max_length=100)
    purchase_date: Optional[date] = None
    price: Optional[float] = Field(None, ge=0)
    purchase_location: Optional[str] = Field(None, max_length=200)
    is_public: Optional[bool] = None
    is_favorite: Optional[int] = Field(None, ge=0, le=3, description="Favorite 0-3")
    condition: Optional[ClothingCondition] = None
    wear_count: Optional[int] = Field(None, ge=0)
    last_worn_date: Optional[date] = None
    custom_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

    @validator('color_code')
    def validate_color_code(cls, v):
        if v and not v.startswith('#'):
            v = '#' + v
        return v


class ClothingItem(ClothingItemBase):
    """Full clothing row."""
    id: int
    user_id: int
    image_url: str = Field(..., description="Image URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    wear_count: int = Field(0, description="Times worn")
    last_worn_date: Optional[date] = Field(None, description="Last worn date")
    created_at: datetime
    updated_at: datetime
    tags: List[ClothingTag] = Field([], description="Tags")
    avg_rating: Optional[float] = Field(None, ge=0, le=5, description="Avg rating 0-5")

    model_config = ConfigDict(from_attributes=True)


class ClothingItemList(BaseModel):
    """Paginated list."""
    items: List[ClothingItem]
    total: int
    page: int
    size: int
    pages: int


class ClothingStats(BaseModel):
    """Wardrobe stats."""
    total_items: int = Field(0, description="Total items")
    total_cost: float = Field(0, description="Total spend")
    avg_price: float = Field(0, description="Average price")
    by_category: Dict[str, int] = Field({}, description="Count by category")
    by_season: Dict[str, int] = Field({}, description="Count by season")
    most_worn: List[Dict[str, Any]] = Field([], description="Most worn")
    recently_added: List[Dict[str, Any]] = Field([], description="Recently added")
    wear_frequency: Dict[str, int] = Field({}, description="Wear frequency")


class UploadResponse(BaseModel):
    """Upload result."""
    success: bool
    message: str
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    clothing_id: Optional[int] = None


class BatchUpdateClothing(BaseModel):
    """Bulk update body."""
    clothing_ids: List[int] = Field(..., description="Clothing ids")
    update_data: Dict[str, Any] = Field(..., description="Fields to set")


class BatchDeleteClothing(BaseModel):
    """Bulk delete body."""
    clothing_ids: List[int] = Field(..., description="Clothing ids")


class FilterOptions(BaseModel):
    """Filter dropdown data."""
    categories: List[str] = Field([], description="Categories")
    season: Optional[List[ClothingSeason]] = Field(None, description="Seasons")
    colors: List[str] = Field([], description="Colors")
    brands: List[str] = Field([], description="Brands")
    sizes: List[str] = Field([], description="Sizes")
    materials: List[str] = Field([], description="Materials")


class SearchRequest(BaseModel):
    """Search / list query."""
    query: Optional[str] = Field(None, description="Search text")
    category: Optional[str] = Field(None, description="Category")
    season: Optional[List[ClothingSeason]] = Field(None, description="Seasons")
    color: Optional[str] = Field(None, description="Color")
    brand: Optional[str] = Field(None, description="Brand")
    min_price: Optional[float] = Field(None, ge=0, description="Min price")
    max_price: Optional[float] = Field(None, ge=0, description="Max price")
    is_favorite: Optional[int] = Field(None, ge=0, le=3, description="Favorite 0-3")
    page: int = Field(1, ge=1, description="Page")  # min 1
    size: int = Field(20, ge=1, le=100, description="Page size")  # max 100
    order_by: str = Field("created_at", description="Sort field")
    order_desc: bool = Field(True, description="Descending sort")


class ClothingTypeResponse(BaseModel):
    """Taxonomy for UI."""
    categories: List[Dict[str, str]] = Field(..., description="Primary categories")
    subcategories: Dict[str, List[Dict[str, str]]] = Field(
        ..., description="Subcategory map"
    )


class ClothingAnalysis(BaseModel):
    """Analytics snapshot."""
    color_distribution: Dict[str, int] = Field({}, description="By color")
    brand_distribution: Dict[str, int] = Field({}, description="By brand")
    category_distribution: Dict[str, int] = Field({}, description="By category")
    most_expensive: Optional[ClothingItem] = Field(None, description="Most expensive")
    least_worn: Optional[ClothingItem] = Field(None, description="Least worn")
    total_investment: float = Field(0, description="Total invested")
    cost_per_wear: Dict[int, float] = Field({}, description="Cost per wear by id")
