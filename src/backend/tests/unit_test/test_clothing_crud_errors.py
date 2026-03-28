"""Clothing CRUD error paths (no PostgreSQL; builds ORM models only)."""
from unittest.mock import MagicMock

from app.crud.clothing import ClothingCRUD
from app.schemas.clothing import ClothingCategory, ClothingItemCreate


def test_create_clothing_item_rollback_on_commit_failure():
    db = MagicMock()
    db.flush = MagicMock()
    db.add = MagicMock()
    db.commit.side_effect = RuntimeError("disk full")
    db.rollback = MagicMock()
    db.refresh = MagicMock()

    item = ClothingItemCreate(
        name="測試上衣",
        category=ClothingCategory.TOP,
        tags=["  a ", "A", ""],
    )
    created, err = ClothingCRUD.create_clothing_item(
        db, user_id=1, item_in=item, image_url="https://example.com/x.jpg",
    )
    assert created is None
    assert err is not None
    assert "disk full" in err
    db.rollback.assert_called()
