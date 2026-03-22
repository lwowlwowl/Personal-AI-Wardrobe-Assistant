"""推薦 AI 對話持久化與串流（路徑與行為與重構前 main 一致）。"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

import app.crud as crud
import app.schemas as schemas
from AIwardrobe.agent.react_agent import ReactAgent
from AIwardrobe.agent.tools.agent_tools import (
    set_agent_request_user_id,
    reset_agent_request_user_id,
)
from app.api.deps import get_current_user
from app.core.database import get_db
from app.services.ai_message_service import build_ai_message
from app.utils.language_policy import decide_reply_language

router = APIRouter(tags=["ai"])

react_agent = ReactAgent()


# ============ 推荐 AI 对话持久化（Your conversations） ============


@router.get("/api/ai/conversations")
async def list_ai_conversations(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """获取当前用户的推荐 AI 对话列表，按更新时间降序"""
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
    """获取单条对话详情"""
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
    """创建一条新对话"""
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
    """更新对话标题和/或消息列表"""
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
    """删除一条对话"""
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
        token: Optional[str] = Query(None, description="用户认证令牌"),
        db: Session = Depends(get_db)
):
    current_user = None
    if token:
        current_user = get_current_user(token, db)

    async def event_stream():
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
            # 先根据当前消息与历史判定回复语言（默认英语）
            lang = decide_reply_language(req.query or "", req.history or [])

            # ReactAgent 当前接口仅接收 query；将历史上下文压成文本前缀传入。
            history_lines = []
            for item in req.history or []:
                role = item.get("role")
                content = (item.get("content") or "").strip()
                if not content:
                    continue
                if role == "user":
                    history_lines.append(f"用户: {content}")
                elif role == "ai":
                    history_lines.append(f"助手: {content}")

            full_query = req.query or ""
            if history_lines:
                history_text = "\n".join(history_lines[-10:])
                full_query = f"以下是历史对话，请结合上下文回答：\n{history_text}\n\n当前问题：{req.query}"

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

            # 流式结束：先发 final（结构化 message），再发 done（兼容旧前端）
            final_message = build_ai_message(final_full_text)
            # 强制把最终 locale 同步成后端判定语言（防止模型偶尔写错）
            final_message["locale"] = lang
            try:
                print("=== [ai_chat_stream] final_full_text ===")
                print(final_full_text)
                print("=== [ai_chat_stream] final_message ===")
                print(json.dumps(final_message, ensure_ascii=False))
            except Exception:
                # 调试日志失败不影响主流程
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
