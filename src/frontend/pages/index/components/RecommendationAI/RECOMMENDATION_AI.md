# 推荐 AI 与后端联调说明

推荐 AI 与后端 **AIwardrobe** 模块联调，后端说明见：**`src/backend/AIwardrobe/README.md`**。

## 前端如何切换 Mock / 真实接口

- 在 **`mockData.js`** 中设置：
  - `USE_RECOMMENDATION_MOCK = true`：使用本地 Mock 数据（默认）
  - `USE_RECOMMENDATION_MOCK = false`：请求后端 `POST /api/chat`

- 请求使用 **`api/recommendationApi.js`** 的 `chatRecommendation(query)`，基址为 `http://localhost:8000`，与后端端口一致。

## 接口约定（与 AIwardrobe README 一致）

| 项目 | 说明 |
|------|------|
| 接口 | `POST /api/chat` |
| 请求体 | `{ "query": "用户输入文本" }` |
| 第一阶段 | 后端返回 `{ "content": "纯文字回复" }`，前端以纯文字 AI 消息展示 |
| 第二阶段 | 后端返回 `{ "content": "...", "recommendations": [...] }`，前端展示推荐卡片 |

单条 `recommendation` 结构需包含：`title`、`temperature`、`styleTags`、`content`、`items`、`whyThisWorks`、`images`（与 `RecommendationCard.vue` 的 props 一致）。

## 前端文件职责

| 文件 | 职责 |
|------|------|
| `mockData.js` | Mock 开关、Mock 数据、加载文案、`normalizeChatResponse`（将后端返回规范为聊天消息） |
| `RecommendationAI.vue` | 发送逻辑：根据 `USE_RECOMMENDATION_MOCK` 走 Mock 或 `chatRecommendation`，再 push 规范后的消息 |
| `api/recommendationApi.js` | 封装 `chatRecommendation(query)` 调用 `POST /api/chat` |

联调时只需将 `USE_RECOMMENDATION_MOCK` 设为 `false` 并确保后端已提供 `/api/chat` 即可。
