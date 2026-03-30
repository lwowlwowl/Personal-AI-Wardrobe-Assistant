"""CRUD for user model photos (virtual try-on / display)."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ModelPhoto


class ModelPhotoCRUD:
    """CRUD helpers for model photo rows."""

    @staticmethod
    def create_model_photo(db: Session, user_id: int, photo_name: str,
                           image_url: str, thumbnail_url: str = None,
                           description: str = None, file_size: int = None,
                           file_format: str = None, is_primary: bool = False):
        """
        Insert a model photo row.

        Args:
            db: DB session.
            user_id: owner user id.
            photo_name: display name.
            image_url: main image URL.
            thumbnail_url: thumbnail URL (optional).
            description: text description (optional).
            file_size: size in bytes (optional).
            file_format: file extension / MIME hint (optional).
            is_primary: when True, this row becomes the default model photo.

        Returns:
            (model_photo, error_message) — error_message is None on success.
        """
        try:
            # If this photo is primary, clear primary on all other rows for this user first.
            if is_primary:
                db.query(ModelPhoto).filter(
                    ModelPhoto.user_id == user_id,
                    ModelPhoto.is_primary == True
                ).update({"is_primary": False})

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
        List model photos for a user with pagination.

        Args:
            db: DB session.
            user_id: owner user id.
            skip: offset (number of rows to skip).
            limit: max rows to return.
            is_active: when True, only rows with is_active=True.

        Returns:
            (photos, total_count, error_message).
        """
        try:
            query = db.query(ModelPhoto).filter(
                ModelPhoto.user_id == user_id,
                ModelPhoto.is_active == is_active
            )

            total = query.count()
            # Sort: primary photo first, then newest first by created_at.
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
        Fetch one model photo by id, scoped to the user.

        Args:
            db: DB session.
            user_id: owner user id.
            photo_id: row id.

        Returns:
            (photo, error_message).
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
        Return the user's current primary (default) model photo, if any.

        Args:
            db: DB session.
            user_id: owner user id.

        Returns:
            (photo, error_message).
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
        Update fields on an existing model photo row.

        Args:
            db: DB session.
            db_photo: loaded ModelPhoto instance.
            update_data: dict of field names to new values.

        Returns:
            (photo, error_message).
        """
        try:
            # Promoting this row to primary: demote other primaries for the same user.
            if update_data.get('is_primary') is True:
                db.query(ModelPhoto).filter(
                    ModelPhoto.user_id == db_photo.user_id,
                    ModelPhoto.id != db_photo.id,
                    ModelPhoto.is_primary == True
                ).update({"is_primary": False})

            for field, value in update_data.items():
                if value is not None:
                    setattr(db_photo, field, value)

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
        Soft-delete a model photo (sets is_active to False).

        Args:
            db: DB session.
            photo_id: row id.

        Returns:
            (success, error_message).
        """
        try:
            photo = db.query(ModelPhoto).filter(ModelPhoto.id == photo_id).first()
            if not photo:
                return False, "Model photo does not exist"

            photo.is_active = False
            db.commit()

            return True, None
        except Exception as e:
            db.rollback()
            return False, f"Failed to delete model photo: {str(e)}"

    @staticmethod
    def hard_delete_model_photo(db: Session, photo_id: int):
        """
        Permanently delete a model photo row from the database.

        Args:
            db: DB session.
            photo_id: row id.

        Returns:
            (success, error_message).
        """
        try:
            photo = db.query(ModelPhoto).filter(ModelPhoto.id == photo_id).first()
            if not photo:
                return False, "Model photo does not exist"

            db.delete(photo)
            db.commit()

            return True, None
        except Exception as e:
            db.rollback()
            return False, f"Failed to permanently delete model photo: {str(e)}"
