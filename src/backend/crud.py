"""
数据库CRUD操作模块
该模块包含所有与数据库交互的增删改查操作，包括：
1. 用户认证与授权
2. 服装管理
3. 穿着记录管理
4. 搭配管理
5. 模特照片管理
6. 批量操作
"""

import traceback
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, asc, or_
from typing import Tuple, Optional, List, Dict, Any
from datetime import datetime, timedelta, date
import jwt
import secrets

# PyJWT 2.8+ 使用 PyJWTError，舊版使用 JWTError，統一用此別名捕獲
_JWTError = getattr(jwt, "PyJWTError", getattr(jwt, "JWTError", Exception))
from passlib.context import CryptContext

# 导入模型和模式
import models
from models import (
    ClothingItem, ClothingTag, Outfit, OutfitItem, WearHistory,
    ModelPhoto
)
from schemas import (
    ClothingItemCreate, ClothingItemUpdate, WearHistoryCreate,
    OutfitCreate, OutfitUpdate
)

# ============ 密码加密配置 ============
# 使用pbkdf2_sha256进行密码哈希，避免bcrypt后端兼容问题
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# ============ JWT配置 ============
# 生产环境应该从环境变量读取
SECRET_KEY = secrets.token_urlsafe(32)  # 生成32字节的安全密钥
ALGORITHM = "HS256"  # JWT签名算法
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # 访问令牌过期时间（2小时）
RESET_TOKEN_EXPIRE_MINUTES = 30  # 重置令牌过期时间（30分钟）


# ============ 通用工具函数 ============

def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


# ============ 用户CRUD操作 ============

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """根据用户名获取用户"""
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """根据邮箱获取用户"""
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """根据ID获取用户"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user_data: dict) -> Tuple[Optional[models.User], Optional[str]]:
    """
    创建新用户

    参数:
        db: 数据库会话
        user_data: 用户数据字典，包含username、password、email等

    返回:
        Tuple[用户对象, 错误信息] - 成功时返回用户对象，失败时返回错误信息
    """
    try:
        print(f"创建用户: {user_data}")

        # 检查用户名是否已存在
        if get_user_by_username(db, user_data["username"]):
            return None, "用户名已被注册"

        # 检查邮箱是否已存在（如果提供了邮箱）
        if user_data.get("email"):
            if get_user_by_email(db, user_data["email"]):
                return None, "邮箱已被注册"

        # 加密密码
        hashed_password = hash_password(user_data["password"])

        # 创建用户对象
        db_user = models.User(
            username=user_data["username"],
            email=user_data.get("email"),
            hashed_password=hashed_password,
            is_active=True,
            created_at=datetime.now()
        )

        # 保存到数据库
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        print(f"用户创建成功: {db_user.username}")
        return db_user, None

    except Exception as e:
        db.rollback()
        print(f"创建用户错误: {e}")
        return None, f"创建用户失败: {str(e)}"


def authenticate_user(db: Session, username: str, password: str) -> Tuple[Optional[models.User], Optional[str]]:
    """
    验证用户登录信息

    参数:
        db: 数据库会话
        username: 用户名或邮箱
        password: 密码

    返回:
        Tuple[用户对象, 错误信息] - 认证成功返回用户对象，失败返回错误信息
    """
    try:
        from sqlalchemy import or_

        print(f"[DEBUG] 开始验证用户: {username}")

        # 通过用户名或邮箱查找用户
        user = db.query(models.User).filter(
            or_(
                models.User.username == username,
                models.User.email == username
            )
        ).first()

        if not user:
            print(f"[DEBUG] 用户不存在: {username}")
            return None, "用户名或密码错误"

        print(f"[DEBUG] 找到用户: {user.username}, ID: {user.id}")
        print(f"[DEBUG] 数据库密码哈希: {user.hashed_password[:30]}...")

        # 使用正确的密码验证方法
        if not verify_password(password, user.hashed_password):
            print(f"[DEBUG] 密码验证失败: {username}")
            return None, "用户名或密码错误"

        print(f"[DEBUG] 认证成功: {user.username}")
        return user, None

    except Exception as e:
        print(f"[ERROR] authenticate_user错误: {traceback.format_exc()}")
        return None, f"认证过程中发生错误: {str(e)}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌

    参数:
        data: 要编码的数据字典
        expires_delta: 可选的过期时间差

    返回:
        JWT令牌字符串
    """
    try:
        to_encode = data.copy()

        # 设置过期时间
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        # 添加标准声明
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})

        # 编码生成JWT
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        print(f"创建token: {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        print(f"create_access_token错误: {e}")
        raise


def verify_access_token(token: str) -> Optional[dict]:
    """
    验证访问令牌

    参数:
        token: JWT令牌字符串

    返回:
        解码后的payload字典，验证失败返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"验证token成功: {payload.get('sub')}")
        return payload
    except jwt.ExpiredSignatureError:
        print("Token已过期")
        return None
    except _JWTError as e:
        print(f"Token验证失败: {e}")
        return None


def create_password_reset_token(email: str) -> str:
    """
    创建密码重置令牌

    参数:
        email: 用户邮箱

    返回:
        重置令牌字符串
    """
    try:
        expire = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
        to_encode = {"email": email, "exp": expire, "type": "reset"}
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        print(f"创建重置token错误: {e}")
        raise


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    验证密码重置令牌

    参数:
        token: 重置令牌字符串

    返回:
        用户邮箱，验证失败返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "reset":
            return None
        return payload.get("email")
    except jwt.ExpiredSignatureError:
        return None
    except _JWTError:
        return None


def update_user_password(db: Session, email: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    更新用户密码（用于忘记密码功能）

    参数:
        db: 数据库会话
        email: 用户邮箱
        new_password: 新密码

    返回:
        Tuple[是否成功, 错误信息]
    """
    try:
        user = get_user_by_email(db, email)
        if not user:
            return False, "用户不存在"

        # 更新密码和修改时间
        user.hashed_password = hash_password(new_password)
        user.updated_at = datetime.now()

        db.commit()
        print(f"密码更新成功: {email}")
        return True, None

    except Exception as e:
        db.rollback()
        print(f"更新密码错误: {e}")
        return False, f"更新密码失败: {str(e)}"


# ============ 服装相关CRUD操作 ============

class ClothingCRUD:
    """服装相关CRUD操作类"""

    @staticmethod
    def get_clothing_item(db: Session, clothing_id: int) -> Optional[ClothingItem]:
        """获取单个衣物（不检查用户权限）"""
        return db.query(ClothingItem).filter(ClothingItem.id == clothing_id).first()

    @staticmethod
    def get_clothing_item_by_user(
            db: Session,
            user_id: int,
            clothing_id: int
    ) -> Optional[ClothingItem]:
        """
        获取用户的单个衣物

        参数:
            db: 数据库会话
            user_id: 用户ID
            clothing_id: 衣物ID

        返回:
            衣物对象，如果不存在或不属于用户则返回None
        """
        return db.query(ClothingItem).filter(
            ClothingItem.id == clothing_id,
            ClothingItem.user_id == user_id
        ).first()

    @staticmethod
    def get_clothing_items(
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 100,
            category: Optional[str] = None,
            season: Optional[str] = None,
            color: Optional[str] = None,
            brand: Optional[str] = None,
            is_favorite: Optional[bool] = None,
            min_price: Optional[float] = None,
            max_price: Optional[float] = None,
            search: Optional[str] = None,
            order_by: str = "created_at",
            order_desc: bool = True
    ) -> Tuple[List[ClothingItem], int]:
        """
        获取衣物列表（支持过滤、搜索、排序、分页）

        参数:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过的记录数（用于分页）
            limit: 每页记录数
            category: 分类筛选
            season: 季节筛选
            color: 颜色筛选
            brand: 品牌筛选
            is_favorite: 是否收藏
            min_price: 最低价格
            max_price: 最高价格
            search: 搜索关键词
            order_by: 排序字段
            order_desc: 是否降序

        返回:
            Tuple[衣物列表, 总记录数]
        """
        # 基础查询：只查询当前用户的衣物
        query = db.query(ClothingItem).filter(ClothingItem.user_id == user_id)

        # 应用过滤器
        if category:
            query = query.filter(ClothingItem.category == category)
        if season:
            query = query.filter(ClothingItem.season == season)
        if color:
            query = query.filter(ClothingItem.color == color)
        if brand:
            query = query.filter(ClothingItem.brand == brand)
        if is_favorite is not None:
            query = query.filter(ClothingItem.is_favorite == is_favorite)
        if min_price is not None:
            query = query.filter(ClothingItem.price >= min_price)
        if max_price is not None:
            query = query.filter(ClothingItem.price <= max_price)

        # 搜索功能：支持名称、描述、品牌、风格的模糊搜索
        if search:
            search_filter = or_(
                ClothingItem.name.ilike(f"%{search}%"),
                ClothingItem.description.ilike(f"%{search}%"),
                ClothingItem.brand.ilike(f"%{search}%"),
                ClothingItem.style.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        # 获取总数（用于分页计算）
        total = query.count()

        # 排序
        order_column = getattr(ClothingItem, order_by, ClothingItem.created_at)
        if order_desc:
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        # 分页
        items = query.offset(skip).limit(limit).all()

        return items, total

    @staticmethod
    def create_clothing_item(
            db: Session,
            user_id: int,
            item_in: ClothingItemCreate,
            image_url: str,
            thumbnail_url: Optional[str] = None
    ) -> Tuple[Optional[ClothingItem], Optional[str]]:
        """
        创建衣物

        参数:
            db: 数据库会话
            user_id: 用户ID
            item_in: 衣物创建数据
            image_url: 图片URL
            thumbnail_url: 缩略图URL（可选）

        返回:
            Tuple[创建的衣物对象, 错误信息]
        """
        try:
            # 创建衣物对象，排除tags字段（后续单独处理）
            db_item = ClothingItem(
                user_id=user_id,
                image_url=image_url,
                thumbnail_url=thumbnail_url,
                **item_in.model_dump(exclude={"tags"})
            )
            db.add(db_item)
            db.commit()
            db.refresh(db_item)

            # 添加标签
            if item_in.tags:
                for tag_name in item_in.tags:
                    tag = ClothingTag(clothing_id=db_item.id, tag=tag_name)
                    db.add(tag)
                db.commit()
                db.refresh(db_item)

            return db_item, None

        except Exception as e:
            db.rollback()
            print(f"创建衣物错误: {e}")
            return None, f"创建衣物失败: {str(e)}"

    @staticmethod
    def update_clothing_item(
            db: Session,
            db_item: ClothingItem,
            item_in: ClothingItemUpdate
    ) -> Tuple[Optional[ClothingItem], Optional[str]]:
        """
        更新衣物

        参数:
            db: 数据库会话
            db_item: 要更新的衣物对象
            item_in: 更新数据

        返回:
            Tuple[更新后的衣物对象, 错误信息]
        """
        try:
            # 获取更新数据，排除未设置的字段和tags字段
            update_data = item_in.model_dump(exclude_unset=True, exclude={"tags"})

            # 更新衣物属性
            for field, value in update_data.items():
                if value is not None:
                    setattr(db_item, field, value)

            # 更新标签（如果提供了）
            if item_in.tags is not None:
                # 删除现有标签
                db.query(ClothingTag).filter(
                    ClothingTag.clothing_id == db_item.id
                ).delete()

                # 添加新标签
                if item_in.tags:
                    for tag_name in item_in.tags:
                        tag = ClothingTag(clothing_id=db_item.id, tag=tag_name)
                        db.add(tag)

            db.add(db_item)
            db.commit()
            db.refresh(db_item)

            return db_item, None

        except Exception as e:
            db.rollback()
            print(f"更新衣物错误: {e}")
            return None, f"更新衣物失败: {str(e)}"

    @staticmethod
    def delete_clothing_item(db: Session, clothing_id: int) -> Tuple[bool, Optional[str]]:
        """
        删除衣物

        参数:
            db: 数据库会话
            clothing_id: 衣物ID

        返回:
            Tuple[是否成功, 错误信息]
        """
        try:
            item = db.query(ClothingItem).filter(ClothingItem.id == clothing_id).first()
            if not item:
                return False, "衣物不存在"

            db.delete(item)
            db.commit()
            return True, None

        except Exception as e:
            db.rollback()
            print(f"删除衣物错误: {e}")
            return False, f"删除衣物失败: {str(e)}"

    @staticmethod
    def record_clothing_wear(
            db: Session,
            clothing_id: int
    ) -> Tuple[Optional[ClothingItem], Optional[str]]:
        """
        记录衣物穿着（增加穿着次数并更新最后穿着日期）

        参数:
            db: 数据库会话
            clothing_id: 衣物ID

        返回:
            Tuple[更新后的衣物对象, 错误信息]
        """
        try:
            item = db.query(ClothingItem).filter(ClothingItem.id == clothing_id).first()
            if not item:
                return None, "衣物不存在"

            # 更新穿着统计
            item.wear_count += 1
            item.last_worn_date = date.today()
            db.add(item)
            db.commit()
            db.refresh(item)

            return item, None

        except Exception as e:
            db.rollback()
            print(f"记录穿着错误: {e}")
            return None, f"记录穿着失败: {str(e)}"

    @staticmethod
    def get_clothing_stats(db: Session, user_id: int) -> Dict[str, Any]:
        """
        获取衣物统计信息

        参数:
            db: 数据库会话
            user_id: 用户ID

        返回:
            包含各种统计信息的字典
        """
        try:
            # 基本统计：总数、总花费、平均价格
            total_query = db.query(
                func.count(ClothingItem.id).label('total_items'),
                func.coalesce(func.sum(ClothingItem.price), 0).label('total_cost'),
                func.coalesce(func.avg(ClothingItem.price), 0).label('avg_price')
            ).filter(ClothingItem.user_id == user_id).first()

            # 分类统计
            category_stats = db.query(
                ClothingItem.category,
                func.count(ClothingItem.id).label('count')
            ).filter(ClothingItem.user_id == user_id).group_by(ClothingItem.category).all()

            # 季节统计
            season_stats = db.query(
                ClothingItem.season,
                func.count(ClothingItem.id).label('count')
            ).filter(ClothingItem.user_id == user_id).group_by(ClothingItem.season).all()

            # 颜色统计
            color_stats = db.query(
                ClothingItem.color,
                func.count(ClothingItem.id).label('count')
            ).filter(
                ClothingItem.user_id == user_id,
                ClothingItem.color.isnot(None)
            ).group_by(ClothingItem.color).all()

            # 最常穿着（前5件）
            most_worn = db.query(ClothingItem).filter(
                ClothingItem.user_id == user_id,
                ClothingItem.wear_count > 0
            ).order_by(desc(ClothingItem.wear_count)).limit(5).all()

            # 最近添加（前5件）
            recently_added = db.query(ClothingItem).filter(
                ClothingItem.user_id == user_id
            ).order_by(desc(ClothingItem.created_at)).limit(5).all()

            # 穿着频率（最近30天）
            thirty_days_ago = date.today() - timedelta(days=30)
            wear_frequency = db.query(
                WearHistory.wear_date,
                func.count(WearHistory.id).label('count')
            ).filter(
                WearHistory.user_id == user_id,
                WearHistory.wear_date >= thirty_days_ago
            ).group_by(WearHistory.wear_date).all()

            # 组织返回数据
            return {
                "total_items": total_query.total_items or 0,
                "total_cost": float(total_query.total_cost or 0),
                "avg_price": float(total_query.avg_price or 0),
                "by_category": {stat.category.value: stat.count for stat in category_stats},
                "by_season": {stat.season.value: stat.count for stat in season_stats if stat.season},
                "by_color": {stat.color: stat.count for stat in color_stats if stat.color},
                "most_worn": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "image_url": item.image_url,
                        "wear_count": item.wear_count
                    }
                    for item in most_worn
                ],
                "recently_added": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "image_url": item.image_url,
                        "created_at": item.created_at
                    }
                    for item in recently_added
                ],
                "wear_frequency": {str(stat.wear_date): stat.count for stat in wear_frequency}
            }

        except Exception as e:
            print(f"获取统计信息错误: {e}")
            return {}

    @staticmethod
    def get_filter_options(db: Session, user_id: int) -> Dict[str, List[str]]:
        """
        获取筛选选项（用于前端下拉框等）

        参数:
            db: 数据库会话
            user_id: 用户ID

        返回:
            包含各种筛选选项的字典
        """
        try:
            # 分类选项
            categories = db.query(ClothingItem.category).filter(
                ClothingItem.user_id == user_id
            ).distinct().all()

            # 季节选项
            seasons = db.query(ClothingItem.season).filter(
                ClothingItem.user_id == user_id,
                ClothingItem.season.isnot(None)
            ).distinct().all()

            # 颜色选项
            colors = db.query(ClothingItem.color).filter(
                ClothingItem.user_id == user_id,
                ClothingItem.color.isnot(None)
            ).distinct().all()

            # 品牌选项
            brands = db.query(ClothingItem.brand).filter(
                ClothingItem.user_id == user_id,
                ClothingItem.brand.isnot(None)
            ).distinct().all()

            # 尺码选项
            sizes = db.query(ClothingItem.size).filter(
                ClothingItem.user_id == user_id,
                ClothingItem.size.isnot(None)
            ).distinct().all()

            # 材质选项
            materials = db.query(ClothingItem.material).filter(
                ClothingItem.user_id == user_id,
                ClothingItem.material.isnot(None)
            ).distinct().all()

            return {
                "categories": [c.category.value for c in categories if c.category],
                "seasons": [s.season.value for s in seasons if s.season],
                "colors": [c.color for c in colors if c.color],
                "brands": [b.brand for b in brands if b.brand],
                "sizes": [s.size for s in sizes if s.size],
                "materials": [m.material for m in materials if m.material]
            }

        except Exception as e:
            print(f"获取筛选选项错误: {e}")
            return {}


# ============ 穿着记录CRUD操作 ============

class WearHistoryCRUD:
    """穿着记录CRUD操作类"""

    @staticmethod
    def create_wear_history(
            db: Session,
            user_id: int,
            history_in: WearHistoryCreate
    ) -> Tuple[Optional[WearHistory], Optional[str]]:
        """
        创建穿着记录

        参数:
            db: 数据库会话
            user_id: 用户ID
            history_in: 穿着记录数据

        返回:
            Tuple[创建的穿着记录对象, 错误信息]
        """
        try:
            # 创建穿着记录
            db_history = WearHistory(
                user_id=user_id,
                **history_in.model_dump()
            )
            db.add(db_history)

            # 更新衣物的穿着记录
            if history_in.clothing_id:
                clothing = db.query(ClothingItem).filter(
                    ClothingItem.id == history_in.clothing_id,
                    ClothingItem.user_id == user_id
                ).first()
                if clothing:
                    clothing.wear_count += 1
                    clothing.last_worn_date = history_in.wear_date

            # 更新搭配的穿着记录
            if history_in.outfit_id:
                outfit = db.query(Outfit).filter(
                    Outfit.id == history_in.outfit_id,
                    Outfit.user_id == user_id
                ).first()
                if outfit:
                    outfit.wear_count += 1
                    outfit.last_worn_date = history_in.wear_date

            db.commit()
            db.refresh(db_history)

            return db_history, None

        except Exception as e:
            db.rollback()
            print(f"创建穿着记录错误: {e}")
            return None, f"创建穿着记录失败: {str(e)}"

    @staticmethod
    def get_wear_history(
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[WearHistory], int]:
        """
        获取穿着记录列表

        参数:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 每页记录数

        返回:
            Tuple[穿着记录列表, 总记录数]
        """
        query = db.query(WearHistory).filter(WearHistory.user_id == user_id)

        total = query.count()
        items = query.order_by(desc(WearHistory.wear_date)).offset(skip).limit(limit).all()

        return items, total

    @staticmethod
    def delete_wear_history(db: Session, history_id: int) -> Tuple[bool, Optional[str]]:
        """
        删除穿着记录

        参数:
            db: 数据库会话
            history_id: 穿着记录ID

        返回:
            Tuple[是否成功, 错误信息]
        """
        try:
            history = db.query(WearHistory).filter(WearHistory.id == history_id).first()
            if not history:
                return False, "记录不存在"

            db.delete(history)
            db.commit()
            return True, None

        except Exception as e:
            db.rollback()
            print(f"删除穿着记录错误: {e}")
            return False, f"删除穿着记录失败: {str(e)}"


# ============ 搭配CRUD操作 ============

class OutfitCRUD:
    """搭配CRUD操作类"""

    @staticmethod
    def get_outfit(db: Session, outfit_id: int) -> Optional[Outfit]:
        """获取单个搭配（包含关联的衣物）"""
        return db.query(Outfit).options(
            joinedload(Outfit.outfit_items).joinedload(OutfitItem.clothing_item)
        ).filter(Outfit.id == outfit_id).first()

    @staticmethod
    def get_outfit_by_user(
            db: Session,
            user_id: int,
            outfit_id: int
    ) -> Optional[Outfit]:
        """
        获取用户的单个搭配

        参数:
            db: 数据库会话
            user_id: 用户ID
            outfit_id: 搭配ID

        返回:
            搭配对象，包含关联的衣物信息
        """
        return db.query(Outfit).options(
            joinedload(Outfit.outfit_items).joinedload(OutfitItem.clothing_item)
        ).filter(
            Outfit.id == outfit_id,
            Outfit.user_id == user_id
        ).first()

    @staticmethod
    def get_outfits(
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 100,
            occasion: Optional[str] = None,
            season: Optional[str] = None,
            is_public: Optional[bool] = None,
            order_by: str = "created_at",
            order_desc: bool = True
    ) -> Tuple[List[Outfit], int]:
        """
        获取搭配列表（支持过滤、排序、分页）

        参数:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 每页记录数
            occasion: 场合筛选
            season: 季节筛选
            is_public: 是否公开
            order_by: 排序字段
            order_desc: 是否降序

        返回:
            Tuple[搭配列表, 总记录数]
        """
        query = db.query(Outfit).filter(Outfit.user_id == user_id)

        # 应用过滤器
        if occasion:
            query = query.filter(Outfit.occasion == occasion)
        if season:
            query = query.filter(Outfit.season == season)
        if is_public is not None:
            query = query.filter(Outfit.is_public == is_public)

        # 获取总数
        total = query.count()

        # 排序
        order_column = getattr(Outfit, order_by, Outfit.created_at)
        if order_desc:
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        # 分页并加载关联（预加载搭配项和衣物信息）
        items = query.options(
            joinedload(Outfit.outfit_items).joinedload(OutfitItem.clothing_item)
        ).offset(skip).limit(limit).all()

        return items, total

    @staticmethod
    def create_outfit(
            db: Session,
            user_id: int,
            outfit_in: OutfitCreate
    ) -> Tuple[Optional[Outfit], Optional[str]]:
        """
        创建搭配

        参数:
            db: 数据库会话
            user_id: 用户ID
            outfit_in: 搭配创建数据

        返回:
            Tuple[创建的搭配对象, 错误信息]
        """
        try:
            # 创建搭配
            db_outfit = Outfit(
                user_id=user_id,
                **outfit_in.model_dump(exclude={"clothing_items"})
            )
            db.add(db_outfit)
            db.commit()
            db.refresh(db_outfit)

            # 添加搭配物品
            for item_in in outfit_in.clothing_items:
                # 验证衣物属于该用户
                clothing = db.query(ClothingItem).filter(
                    ClothingItem.id == item_in.clothing_id,
                    ClothingItem.user_id == user_id
                ).first()

                if not clothing:
                    db.rollback()
                    return None, f"衣物 {item_in.clothing_id} 不存在或不属于当前用户"

                # 创建搭配项
                outfit_item = OutfitItem(
                    outfit_id=db_outfit.id,
                    clothing_id=item_in.clothing_id,
                    position=item_in.position,
                    order_index=item_in.order_index
                )
                db.add(outfit_item)

            db.commit()
            db.refresh(db_outfit)

            return db_outfit, None

        except Exception as e:
            db.rollback()
            print(f"创建搭配错误: {e}")
            return None, f"创建搭配失败: {str(e)}"

    @staticmethod
    def update_outfit(
            db: Session,
            db_outfit: Outfit,
            outfit_in: OutfitUpdate
    ) -> Tuple[Optional[Outfit], Optional[str]]:
        """
        更新搭配

        参数:
            db: 数据库会话
            db_outfit: 要更新的搭配对象
            outfit_in: 更新数据

        返回:
            Tuple[更新后的搭配对象, 错误信息]
        """
        try:
            # 获取更新数据，排除未设置的字段
            update_data = outfit_in.model_dump(exclude_unset=True)

            # 更新搭配属性
            for field, value in update_data.items():
                if value is not None:
                    setattr(db_outfit, field, value)

            db.add(db_outfit)
            db.commit()
            db.refresh(db_outfit)

            return db_outfit, None

        except Exception as e:
            db.rollback()
            print(f"更新搭配错误: {e}")
            return None, f"更新搭配失败: {str(e)}"

    @staticmethod
    def delete_outfit(db: Session, outfit_id: int) -> Tuple[bool, Optional[str]]:
        """
        删除搭配

        参数:
            db: 数据库会话
            outfit_id: 搭配ID

        返回:
            Tuple[是否成功, 错误信息]
        """
        try:
            outfit = db.query(Outfit).filter(Outfit.id == outfit_id).first()
            if not outfit:
                return False, "搭配不存在"

            db.delete(outfit)
            db.commit()
            return True, None

        except Exception as e:
            db.rollback()
            print(f"删除搭配错误: {e}")
            return False, f"删除搭配失败: {str(e)}"

    @staticmethod
    def record_outfit_wear(
            db: Session,
            outfit_id: int
    ) -> Tuple[Optional[Outfit], Optional[str]]:
        """
        记录搭配穿着（增加穿着次数并更新最后穿着日期）

        参数:
            db: 数据库会话
            outfit_id: 搭配ID

        返回:
            Tuple[更新后的搭配对象, 错误信息]
        """
        try:
            outfit = db.query(Outfit).filter(Outfit.id == outfit_id).first()
            if not outfit:
                return None, "搭配不存在"

            # 更新穿着统计
            outfit.wear_count += 1
            outfit.last_worn_date = date.today()
            db.add(outfit)
            db.commit()
            db.refresh(outfit)

            return outfit, None

        except Exception as e:
            db.rollback()
            print(f"记录搭配穿着错误: {e}")
            return None, f"记录搭配穿着失败: {str(e)}"


# ============ 批量操作 ============

class BatchCRUD:
    """批量操作CRUD类"""

    @staticmethod
    def batch_update_clothing(
            db: Session,
            user_id: int,
            clothing_ids: List[int],
            update_data: Dict[str, Any]
    ) -> Tuple[int, Optional[str]]:
        """
        批量更新衣物

        参数:
            db: 数据库会话
            user_id: 用户ID
            clothing_ids: 衣物ID列表
            update_data: 更新数据字典

        返回:
            Tuple[更新的记录数, 错误信息]
        """
        try:
            # 验证所有衣物都属于该用户
            items = db.query(ClothingItem).filter(
                ClothingItem.id.in_(clothing_ids),
                ClothingItem.user_id == user_id
            ).all()

            if len(items) != len(clothing_ids):
                return 0, "部分衣物不存在或不属于当前用户"

            # 批量更新（使用synchronize_session=False提高性能）
            updated_count = db.query(ClothingItem).filter(
                ClothingItem.id.in_(clothing_ids)
            ).update(update_data, synchronize_session=False)

            db.commit()
            return updated_count, None

        except Exception as e:
            db.rollback()
            print(f"批量更新错误: {e}")
            return 0, f"批量更新失败: {str(e)}"

    @staticmethod
    def batch_delete_clothing(
            db: Session,
            user_id: int,
            clothing_ids: List[int]
    ) -> Tuple[int, Optional[str]]:
        """
        批量删除衣物

        参数:
            db: 数据库会话
            user_id: 用户ID
            clothing_ids: 衣物ID列表

        返回:
            Tuple[删除的记录数, 错误信息]
        """
        try:
            # 验证所有衣物都属于该用户
            items = db.query(ClothingItem).filter(
                ClothingItem.id.in_(clothing_ids),
                ClothingItem.user_id == user_id
            ).all()

            if len(items) != len(clothing_ids):
                return 0, "部分衣物不存在或不属于当前用户"

            # 批量删除（使用synchronize_session=False提高性能）
            deleted_count = db.query(ClothingItem).filter(
                ClothingItem.id.in_(clothing_ids)
            ).delete(synchronize_session=False)

            db.commit()
            return deleted_count, None

        except Exception as e:
            db.rollback()
            print(f"批量删除错误: {e}")
            return 0, f"批量删除失败: {str(e)}"


# ============ 模特照片CRUD操作 ============

class ModelPhotoCRUD:
    """模特照片CRUD操作类"""

    @staticmethod
    def create_model_photo(db: Session, user_id: int, photo_name: str,
                           image_url: str, thumbnail_url: str = None,
                           description: str = None, file_size: int = None,
                           file_format: str = None, is_primary: bool = False):
        """
        创建模特照片记录

        参数:
            db: 数据库会话
            user_id: 用户ID
            photo_name: 照片名称
            image_url: 图片URL
            thumbnail_url: 缩略图URL（可选）
            description: 描述（可选）
            file_size: 文件大小（可选）
            file_format: 文件格式（可选）
            is_primary: 是否为主要照片

        返回:
            Tuple[创建的模特照片对象, 错误信息]
        """
        try:
            # 如果设置为主要照片，先取消其他主要照片
            if is_primary:
                db.query(ModelPhoto).filter(
                    ModelPhoto.user_id == user_id,
                    ModelPhoto.is_primary == True
                ).update({"is_primary": False})

            # 创建新照片记录
            model_photo = ModelPhoto(
                user_id=user_id,
                photo_name=photo_name,
                description=description,
                image_url=image_url,
                thumbnail_url=thumbnail_url,
                file_size=file_size,
                file_format=file_format,
                is_primary=is_primary
            )

            db.add(model_photo)
            db.commit()
            db.refresh(model_photo)

            return model_photo, None
        except Exception as e:
            db.rollback()
            return None, f"创建模特照片失败: {str(e)}"

    @staticmethod
    def get_model_photos_by_user(db: Session, user_id: int,
                                 skip: int = 0, limit: int = 100,
                                 is_active: bool = True):
        """
        获取用户的模特照片列表

        参数:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 每页记录数
            is_active: 是否只获取活跃照片

        返回:
            Tuple[照片列表, 总记录数, 错误信息]
        """
        try:
            query = db.query(ModelPhoto).filter(
                ModelPhoto.user_id == user_id,
                ModelPhoto.is_active == is_active
            )

            total = query.count()
            # 排序：主要照片优先，然后按创建时间降序
            photos = query.order_by(
                ModelPhoto.is_primary.desc(),
                ModelPhoto.created_at.desc()
            ).offset(skip).limit(limit).all()

            return photos, total, None
        except Exception as e:
            return [], 0, f"获取模特照片列表失败: {str(e)}"

    @staticmethod
    def get_model_photo_by_id(db: Session, user_id: int, photo_id: int):
        """
        根据ID获取模特照片

        参数:
            db: 数据库会话
            user_id: 用户ID
            photo_id: 照片ID

        返回:
            Tuple[照片对象, 错误信息]
        """
        try:
            photo = db.query(ModelPhoto).filter(
                ModelPhoto.id == photo_id,
                ModelPhoto.user_id == user_id,
                ModelPhoto.is_active == True
            ).first()

            return photo, None
        except Exception as e:
            return None, f"获取模特照片失败: {str(e)}"

    @staticmethod
    def get_primary_model_photo(db: Session, user_id: int):
        """
        获取用户的主要模特照片

        参数:
            db: 数据库会话
            user_id: 用户ID

        返回:
            Tuple[主要照片对象, 错误信息]
        """
        try:
            photo = db.query(ModelPhoto).filter(
                ModelPhoto.user_id == user_id,
                ModelPhoto.is_primary == True,
                ModelPhoto.is_active == True
            ).first()

            return photo, None
        except Exception as e:
            return None, f"获取主要模特照片失败: {str(e)}"

    @staticmethod
    def update_model_photo(db: Session, db_photo: ModelPhoto,
                           update_data: dict):
        """
        更新模特照片信息

        参数:
            db: 数据库会话
            db_photo: 要更新的照片对象
            update_data: 更新数据字典

        返回:
            Tuple[更新后的照片对象, 错误信息]
        """
        try:
            # 如果设置为主要照片，先取消其他主要照片
            if update_data.get('is_primary') is True:
                db.query(ModelPhoto).filter(
                    ModelPhoto.user_id == db_photo.user_id,
                    ModelPhoto.id != db_photo.id,
                    ModelPhoto.is_primary == True
                ).update({"is_primary": False})

            # 更新字段
            for field, value in update_data.items():
                if value is not None:
                    setattr(db_photo, field, value)

            # 更新修改时间
            db_photo.updated_at = func.now()
            db.commit()
            db.refresh(db_photo)

            return db_photo, None
        except Exception as e:
            db.rollback()
            return None, f"更新模特照片失败: {str(e)}"

    @staticmethod
    def delete_model_photo(db: Session, photo_id: int):
        """
        删除模特照片（软删除）

        参数:
            db: 数据库会话
            photo_id: 照片ID

        返回:
            Tuple[是否成功, 错误信息]
        """
        try:
            photo = db.query(ModelPhoto).filter(ModelPhoto.id == photo_id).first()
            if not photo:
                return False, "模特照片不存在"

            # 软删除：设置is_active为False
            photo.is_active = False
            db.commit()

            return True, None
        except Exception as e:
            db.rollback()
            return False, f"删除模特照片失败: {str(e)}"

    @staticmethod
    def hard_delete_model_photo(db: Session, photo_id: int):
        """
        永久删除模特照片

        参数:
            db: 数据库会话
            photo_id: 照片ID

        返回:
            Tuple[是否成功, 错误信息]
        """
        try:
            photo = db.query(ModelPhoto).filter(ModelPhoto.id == photo_id).first()
            if not photo:
                return False, "模特照片不存在"

            # 硬删除：从数据库彻底删除
            db.delete(photo)
            db.commit()

            return True, None
        except Exception as e:
            db.rollback()
            return False, f"永久删除模特照片失败: {str(e)}"


# ============ 模块实例化 ============
# 创建各个CRUD类的实例，方便在其他模块中导入使用

model_photo_crud = ModelPhotoCRUD()
clothing_crud = ClothingCRUD()
wear_history_crud = WearHistoryCRUD()
outfit_crud = OutfitCRUD()
batch_crud = BatchCRUD()
