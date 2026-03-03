# AIwardrobe 模块说明

## 一、是什么、用来做什么

**AIwardrobe** 是后端里的一个 **AI 智能衣橱穿搭助手** 模块，基于 **LangChain** 实现，主要负责：

- **理解用户的穿搭需求**（场景、风格、天气、衣橱等）
- **调用工具** 获取天气、用户位置、RAG 检索资料、外部使用数据等
- **生成专业、可执行的穿搭建议**，并支持 **流式输出**

也就是说：用户在前端（RecommendationAI）输入问题 → 后端把问题交给 AIwardrobe → Agent 按需调用工具（天气、RAG 等）→ 大模型生成回答 → 以流式或一次性返回给前端。

---

## 二、目录结构与职责

| 路径 | 职责 |
|------|------|
| `agent/react_agent.py` | ReAct Agent 入口：组装模型、提示词、工具，提供 `execute_stream(query)` 流式生成 |
| `agent/tools/agent_tools.py` | 工具定义：`rag_summarize`、`get_weather`、`get_user_location`、`get_user_id`、`fetch_external_data`、`fill_context_for_report` 等 |
| `agent/tools/middleware.py` | 工具与模型调用的中间件（监控、日志、报告用提示词切换） |
| `rag/rag_service.py` | RAG 总结服务：根据问题检索向量库并生成总结 |
| `rag/vector_store.py` | 向量存储（Chroma）与检索 |
| `model/factory.py` | 大模型与 Embedding 的工厂（如 ChatOpenAI、DashScopeEmbeddings） |
| `config/` | `rag.yml`、`prompts.yml`、`chroma.yml` 等配置 |
| `prompts/` | 系统提示词（如 `main_prompt_zh.txt`）、RAG 提示词 |
| `utils/` | 路径、日志、配置加载、天气 JSON 读取等 |

**重要**：AIwardrobe 内部的 import 是 **相对于 AIwardrobe 包** 的（例如 `from model.factory import chat_model`、`from rag.rag_service import RagSummarizeService`），因此要么在 **AIwardrobe 目录下** 运行，要么把 **AIwardrobe 目录加入 `sys.path`** 后再 import。

---

## 三、在后端（main.py）中的使用

**main.py 已接入 AIwardrobe**，通过 `sys.path` 引入 AIwardrobe 目录，并对外提供流式接口。

### 3.1 现有接口

| 接口 | 说明 |
|------|------|
| `POST /api/ai/chat/stream` | AI 穿搭建议流式接口，SSE 格式 |

**请求体**（`ChatReq`）：

```json
{
  "query": "用户输入文本",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "ai", "content": "..." }
  ]
}
```

**响应**：SSE 流式，每行 `data: {"type":"delta","content":"..."}`，结束 `data: {"type":"done"}`，错误 `data: {"type":"error","message":"..."}`。

### 3.2 若需自行接入（参考）

AIwardrobe 内部用相对 import（`model`、`rag`、`agent` 等），需把 **AIwardrobe 目录加入 `sys.path`** 后再 `from agent.react_agent import ReactAgent`。main.py 已按此方式配置。

---

## 四、与前端 RecommendationAI 联调

### 4.1 联调状态

- **后端**：已提供 `POST /api/ai/chat/stream`，接收 `{ query, history }`，返回 SSE 流式。
- **前端**：`api/recommendationApi.js` 的 `chatRecommendation(query, history)` 已对接该接口，解析 SSE 并累积为完整 `content`。
- **Mock 开关**：`RecommendationAI/mockData.js` 中 `USE_RECOMMENDATION_MOCK = true` 时用本地 Mock，设为 `false` 时请求后端。

### 4.2 使用真实接口

1. 确保 **gpt-oss**（或配置的 chat 模型）在 `rag.yml` 的 `base_url` 所指地址运行（如 `http://localhost:8080/v1`）。
2. 启动后端 `main.py`（端口 8000）。
3. 将 `mockData.js` 中 `USE_RECOMMENDATION_MOCK` 设为 `false`。
4. 前端 `recommendationApi.js` 的 `API_BASE_URL` 为 `http://localhost:8000`，与后端一致。

### 4.3 数据格式

- **目前 Agent 输出**：`execute_stream` 只 yield **纯文字**，前端以 `{ role: 'ai', content: '...' }` 展示。
- **未来扩展**：若后端返回结构化 `{ content, recommendations: [...] }`，前端 `normalizeChatResponse` 已支持，可直接赋给 `msg.recommendations` 展示推荐卡片。

---

## 五、小结

| 问题 | 说明 |
|------|------|
| **AIwardrobe 是什么** | 后端的 AI 智能衣橱模块：LangChain ReAct Agent + RAG + 天气等工具，用于生成穿搭建议。 |
| **在后端怎么用** | main.py 已接入，对外提供 `POST /api/ai/chat/stream`，请求体 `{ query, history }`，返回 SSE 流式。 |
| **与 RecommendationAI 联调** | 已对接。前端 `chatRecommendation(query, history)` 调用该接口；`USE_RECOMMENDATION_MOCK = false` 时使用真实后端。 |
