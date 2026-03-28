"""build_agent_context: validation and aggregated payload shape (DB reads mocked)."""
from unittest.mock import patch

import pytest

from AIwardrobe.utils.database_retriever import build_agent_context


@patch("AIwardrobe.utils.database_retriever.get_wear_history")
@patch("AIwardrobe.utils.database_retriever.get_outfits")
@patch("AIwardrobe.utils.database_retriever.get_clothing_items")
@patch("AIwardrobe.utils.database_retriever._fetch_all")
def test_build_agent_context_success_structure(
    mock_fetch, mock_clothing, mock_outfits, mock_wear,
):
    mock_fetch.return_value = [
        {"id": 3, "username": "u1", "is_active": True, "created_at": "2026-01-01T00:00:00"},
    ]
    mock_clothing.return_value = [{"id": 10, "name": "coat"}]
    mock_outfits.return_value = []
    mock_wear.return_value = []

    ctx = build_agent_context(
        3,
        db=None,
        closet_limit=50,
        closet_offset=5,
        constraints={"city": "Ningbo"},
    )

    assert ctx["user"]["id"] == 3
    assert ctx["user"]["username"] == "u1"
    assert ctx["closet_items"] == [{"id": 10, "name": "coat"}]
    assert ctx["constraints"] == {"city": "Ningbo"}
    assert ctx["pagination"]["closet_items"] == {"limit": 50, "offset": 5, "count": 1}
    assert "summary" in ctx
    assert ctx["summary"]["counts"]["closet_items"] == 1


def test_build_agent_context_invalid_user_id():
    with pytest.raises(ValueError, match="positive"):
        build_agent_context(0)


@patch("AIwardrobe.utils.database_retriever._fetch_all")
def test_build_agent_context_user_not_found(mock_fetch):
    mock_fetch.return_value = []
    with pytest.raises(ValueError, match="not found"):
        build_agent_context(999)
