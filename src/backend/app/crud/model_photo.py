"""模特照片 CRUD。"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ModelPhoto

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
            return None, f"Failed to create model photo: {str(e)}"

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
            return [], 0, f"Failed to get model photo list: {str(e)}"

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
            return None, f"Failed to get model photo: {str(e)}"

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
            return None, f"Failed to get primary model photo: {str(e)}"

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
            return None, f"Failed to update model photo: {str(e)}"

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
                return False, "Model photo does not exist"

            # 软删除：设置is_active为False
            photo.is_active = False
            db.commit()

            return True, None
        except Exception as e:
            db.rollback()
            return False, f"Failed to delete model photo: {str(e)}"

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
                return False, "Model photo does not exist"

            # 硬删除：从数据库彻底删除
            db.delete(photo)
            db.commit()

            return True, None
        except Exception as e:
            db.rollback()
            return False, f"Failed to permanently delete model photo: {str(e)}"
