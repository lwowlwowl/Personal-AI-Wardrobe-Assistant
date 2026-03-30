from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ModelPhoto(Base):
    """
    User-uploaded model photos for virtual try-on or outfit previews.
    """
    __tablename__ = "model_photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # owner
    photo_name = Column(String(200), nullable=False)  # display name
    description = Column(Text, nullable=True)  # optional notes

    # Stored file metadata
    image_url = Column(String(500), nullable=False)  # full image URL
    thumbnail_url = Column(String(500), nullable=True)  # thumbnail URL
    file_size = Column(Integer, nullable=True)  # bytes
    file_format = Column(String(10), nullable=True)  # e.g. jpg, png

    # Status
    is_active = Column(Boolean, default=True)  # soft-delete flag
    is_primary = Column(Boolean, default=False)  # default model for the user

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="model_photos")

    def __repr__(self):
        """Short repr for debugging."""
        return f"<ModelPhoto(id={self.id}, user_id={self.user_id}, name={self.photo_name})>"
