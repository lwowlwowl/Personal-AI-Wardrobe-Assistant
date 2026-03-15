# 推荐 AI 与后端联调说明

推荐 AI 与后端 **AIwardrobe** 模块联调，后端说明见：**`src/backend/AIwardrobe/README.md`**。

## 接口约定（与后端 main.py 一致）

| 项目 | 说明 |
|------|------|
| 接口 | `POST /api/ai/chat/stream` |
| 请求体 | `{ "query": "用户输入文本", "history": [{ "role": "user"\|"ai", "content": "..." }] }` |
| 响应 | SSE 流式：`data: {"type":"delta","content":"..."}` 逐块推送，结束 `data: {"type":"done"}` |
| 前端处理 | 累积 delta 得到完整 `content`，经 **`chatContentAdapter.js`** 的 `normalizeChatResponse` 解析为聊天消息（方案、单品、警示等） |

单条 `recommendation` 结构：`title`、`temperature`、`styleTags`、`content`、`items`、`whyThisWorks`、`cautions`、`images`（与 `RecommendationCard.vue` 的 props 一致）。

## 前端文件职责

| 文件 | 职责 |
|------|------|
| `chatContentAdapter.js` | 聊天内容适配层：加载文案常量 `LOADING_STEPS`、`normalizeChatResponse`（将后端返回的 Markdown 解析为结构化 recommendations） |
| `RecommendationAI.vue` | 发送逻辑：调用 `chatRecommendation` 请求 `/api/ai/chat/stream`，将返回的 `content` 经 `normalizeChatResponse` 后 push 到 chatHistory |
| `api/recommendationApi.js` | 封装 `chatRecommendation(query, history)` 调用 `POST /api/ai/chat/stream`，解析 SSE 流 |

联调时确保后端已提供 `/api/ai/chat/stream`，前端默认即请求该接口。
