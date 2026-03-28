"""Outfit CRUD edge paths with mocked Session (app.crud.outfit.OutfitCRUD)."""
from unittest.mock import MagicMock

from app.crud.outfit import OutfitCRUD
from app.schemas.outfit import OutfitCreate, OutfitItemCreate


def test_create_outfit_rollback_when_clothing_not_owned():
    outfit_in = OutfitCreate(
        name="Test outfit",
        clothing_items=[OutfitItemCreate(clothing_id=404, position="top", order_index=0)],
    )
    db = MagicMock()

    def refresh_side_effect(obj):
        obj.id = 1

    db.refresh.side_effect = refresh_side_effect
    db.query.return_value.filter.return_value.first.return_value = None

    created, err = OutfitCRUD.create_outfit(db, user_id=1, outfit_in=outfit_in)
    assert created is None
    assert err is not None
    assert "404" in err or "does not exist" in err
    db.rollback.assert_called()
