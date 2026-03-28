"""
Shared fixtures: pin JWT secret so tests do not depend on a random config SECRET_KEY.
"""
import sys
import types
from unittest.mock import MagicMock

import pytest

import app.core.security as security

# Allow importing app.services.clothing_service without pulling langchain (unit + integration).
_cm_stub = MagicMock()
_cm_stub.ClassificationModel = MagicMock()
sys.modules.setdefault("AIwardrobe.agent.classify_model", _cm_stub)


def _stub_aiwardrobe_agent_modules_for_pytest():
    """Lightweight stubs so app.api.v1.ai_chat can load without LangChain/RAG (pytest only)."""
    tools_key = "AIwardrobe.agent.tools.agent_tools"
    if tools_key not in sys.modules:
        tm = types.ModuleType(tools_key)

        def _set_uid(_uid):
            return object()

        def _reset(_tok):
            return None

        tm.set_agent_request_user_id = _set_uid
        tm.reset_agent_request_user_id = _reset
        sys.modules[tools_key] = tm

    ra_key = "AIwardrobe.agent.react_agent"
    if ra_key not in sys.modules:
        rm = types.ModuleType(ra_key)

        class ReactAgent:
            async def execute_stream(self, query: str, lang: str = "en"):
                if False:
                    yield
                yield ""

        rm.ReactAgent = ReactAgent
        sys.modules[ra_key] = rm


_stub_aiwardrobe_agent_modules_for_pytest()


@pytest.fixture(autouse=True)
def fixed_jwt_secret():
    prev = security.SECRET_KEY
    security.SECRET_KEY = "unit-test-jwt-secret-key-do-not-use-in-prod"
    yield
    security.SECRET_KEY = prev
