"""Recommendation AI: conversation persistence and streaming (legacy-compatible paths)."""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

import app.crud as crud
import app.schemas as schemas
from app.api.deps import get_current_user
from app.core.database import get_db
from app.services.ai_message_service import build_ai_message
from app.utils.language_policy import decide_reply_language

router = APIRouter(tags=["ai"])


# ============ Recommendation AI conversations (Your conversations) ============


@router.get("/api/ai/conversations")
async def list_ai_conversations(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """List current user's Recommendation AI conversations, newest first."""
    current_user = get_current_user(token, db)
    items, total, error = crud.ai_conversation_crud.list_by_user(db, user_id=current_user.id)
    if error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error)
    return {
        "success": True,
        "data": [
            {"id": c.id, "title": c.title, "messages": c.messages or [], "created_at": c.created_at.isoformat() if c.created_at else None, "updated_at": c.updated_at.isoformat() if c.updated_at else None}
            for c in items
        ],
        "total": total
    }


@router.get("/api/ai/conversations/{conversation_id}")
async def get_ai_conversation(
        conversation_id: int,
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """Get one conversation by id."""
    current_user = get_current_user(token, db)
    conv, error = crud.ai_conversation_crud.get_by_id_and_user(db, conversation_id=conversation_id, user_id=current_user.id)
    if error or not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied.",
        )
    return {
        "success": True,
        "data": {"id": conv.id, "title": conv.title, "messages": conv.messages or [], "created_at": conv.created_at.isoformat() if conv.created_at else None, "updated_at": conv.updated_at.isoformat() if conv.updated_at else None}
    }


@router.post("/api/ai/conversations")
async def create_ai_conversation(
        body: schemas.AIConversationCreate,
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """Create a new conversation."""
    current_user = get_current_user(token, db)
    conv, error = crud.ai_conversation_crud.create(db, user_id=current_user.id, title=body.title, messages=body.messages)
    if error or not conv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Could not create conversation.",
        )
    return {
        "success": True,
        "data": {"id": conv.id, "title": conv.title, "messages": conv.messages or [], "created_at": conv.created_at.isoformat() if conv.created_at else None, "updated_at": conv.updated_at.isoformat() if conv.updated_at else None}
    }


@router.put("/api/ai/conversations/{conversation_id}")
async def update_ai_conversation(
        conversation_id: int,
        body: schemas.AIConversationUpdate,
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """Update conversation title and/or messages."""
    current_user = get_current_user(token, db)
    conv, error = crud.ai_conversation_crud.update(
        db, conversation_id=conversation_id, user_id=current_user.id,
        title=body.title, messages=body.messages
    )
    if error or not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if not conv else status.HTTP_400_BAD_REQUEST,
            detail=error or "Could not update conversation.",
        )
    return {
        "success": True,
        "data": {"id": conv.id, "title": conv.title, "messages": conv.messages or [], "created_at": conv.created_at.isoformat() if conv.created_at else None, "updated_at": conv.updated_at.isoformat() if conv.updated_at else None}
    }


@router.delete("/api/ai/conversations/{conversation_id}")
async def delete_ai_conversation(
        conversation_id: int,
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """Delete a conversation."""
    current_user = get_current_user(token, db)
    ok, error = crud.ai_conversation_crud.delete(db, conversation_id=conversation_id, user_id=current_user.id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error or "Could not delete conversation.",
        )
    return {"success": True, "message": "Deleted."}


@router.post("/api/ai/chat/stream")
async def ai_chat_stream(
        req: schemas.ChatReq,
        token: Optional[str] = Query(None, description="Auth token"),
        db: Session = Depends(get_db)
):
    current_user = None
    if token:
        current_user = get_current_user(token, db)

    async def event_stream():
        from AIwardrobe.agent.tools.agent_tools import (
            reset_agent_request_user_id,
            set_agent_request_user_id,
        )

        context_token = set_agent_request_user_id(current_user.id if current_user else None)
        try:
            query_stripped = (req.query or "").strip()
            if not query_stripped:
                error_payload = json.dumps(
                    {"type": "error", "message": "Message cannot be empty."},
                    ensure_ascii=False,
                )
                yield f"data: {error_payload}\n\n"
                return
            from AIwardrobe.agent.react_agent import ReactAgent

            react_agent = ReactAgent()
            # Reply language from current message + history (default English)
            lang = decide_reply_language(req.query or "", req.history or [])

            # ReactAgent only takes query; fold recent history into a text prefix.
            history_lines = []
            for item in req.history or []:
                role = item.get("role")
                content = (item.get("content") or "").strip()
                if not content:
                    continue
                if role == "user":
                    history_lines.append(f"User: {content}")
                elif role == "ai":
                    history_lines.append(f"Assistant: {content}")

            full_query = req.query or ""
            if history_lines:
                history_text = "\n".join(history_lines[-10:])
                full_query = (
                    f"Conversation history (use context when answering):\n{history_text}\n\n"
                    f"Current question: {req.query}"
                )

            previous_text = ""
            final_full_text = ""
            async for chunk_text in react_agent.execute_stream(full_query, lang=lang):
                if not chunk_text:
                    continue
                if chunk_text.startswith(previous_text):
                    delta = chunk_text[len(previous_text):]
                else:
                    delta = chunk_text
                previous_text = chunk_text
                final_full_text = chunk_text
                if not delta:
                    continue
                payload = json.dumps({"type": "delta", "content": delta}, ensure_ascii=False)
                yield f"data: {payload}\n\n"

            # End of stream: final structured message, then done (legacy clients)
            final_message = build_ai_message(final_full_text)
            # Force locale to match server-side language decision
            final_message["locale"] = lang
            try:
                print("=== [ai_chat_stream] final_full_text ===")
                print(final_full_text)
                print("=== [ai_chat_stream] final_message ===")
                print(json.dumps(final_message, ensure_ascii=False))
            except Exception:
                # Debug logging must not break the stream
                pass
            final_payload = json.dumps({"type": "final", "message": final_message}, ensure_ascii=False)
            yield f"data: {final_payload}\n\n"
            yield 'data: {"type":"done"}\n\n'
        except Exception as e:
            error_payload = json.dumps(
                {"type": "error", "message": str(e)}, ensure_ascii=False
            )
            yield f"data: {error_payload}\n\n"
        finally:
            reset_agent_request_user_id(context_token)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
