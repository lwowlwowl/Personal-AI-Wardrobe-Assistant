"""ClothingCRUD read helpers with mocked Session."""
from unittest.mock import MagicMock

from app.crud.clothing import ClothingCRUD


def test_get_clothing_item_by_user_returns_row():
    db = MagicMock()
    item = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = item
    assert ClothingCRUD.get_clothing_item_by_user(db, user_id=3, clothing_id=9) is item


def test_get_clothing_item_by_user_returns_none():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    assert ClothingCRUD.get_clothing_item_by_user(db, user_id=3, clothing_id=9) is None
