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

## 三、在后端（main.py）中如何使用

目前 **main.py 尚未引用 AIwardrobe**。要接入，需做两件事：

### 3.1 让 main.py 能 import AIwardrobe 内的模块

因为 AIwardrobe 内部用相对 import（`model`、`rag`、`agent` 等），有两种常见做法：

**方式 A：把 AIwardrobe 目录加入 sys.path（推荐）**

在 `main.py` 顶部（在 import 业务代码之后、在 import AIwardrobe 之前）加入：

```python
import sys
from pathlib import Path as PathLib

# 项目 backend 目录
BACKEND_DIR = PathLib(__file__).resolve().parent
AIWARDROBE_DIR = BACKEND_DIR / "AIwardrobe"
if str(AIWARDROBE_DIR) not in sys.path:
    sys.path.insert(0, str(AIWARDROBE_DIR))
```

之后即可：

```python
from agent.react_agent import ReactAgent
```

**方式 B：以包形式 import（需改 AIwardrobe 内部为相对包路径）**

若希望用 `from backend.AIwardrobe.agent.react_agent import ReactAgent`，需要把 AIwardrobe 内所有 `from model.xxx`、`from rag.xxx` 等改为 `from AIwardrobe.model.xxx` 或使用相对 import（`from ..model import xxx`）。改动较多，一般先用方式 A 即可。

### 3.2 新增一个聊天/推荐接口

例如 **流式接口**（与 `execute_stream` 对应）：

```python
from fastapi.responses import StreamingResponse

@app.post("/api/chat/stream")
async def chat_stream(query: str = Body(..., embed=True)):
    """AI 穿搭建议流式；请求体: {"query": "用户输入"}"""
    try:
        agent = ReactAgent(lang="zh")
        def generate():
            for chunk in agent.execute_stream(query):
                yield chunk
        return StreamingResponse(
            generate(),
            media_type="text/plain; charset=utf-8",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

若希望 **一次性返回**（不流式），可以先把流式结果拼成字符串再返回：

```python
@app.post("/api/chat")
async def chat(query: str = Body(..., embed=True)):
    try:
        agent = ReactAgent(lang="zh")
        full = "".join(agent.execute_stream(query))
        return {"content": full}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

按需选择流式或一次性；前端 RecommendationAI 可依此对接。

---

## 四、与前端 RecommendationAI 联调

### 4.1 前端现状

- **RecommendationAI.vue**：用户发送消息后，目前用 **setTimeout 2.5 秒** 模拟延迟，然后 push 一笔 **写死的推荐**（`msg.recommendations`），**没有调用后端 API**。
- 后端 **main.py 目前没有** `/api/chat` 或 `/api/recommend` 这类 AI 接口。

### 4.2 联调要做的事

1. **后端**  
   - 按上面「三」在 main.py 中加入 `sys.path` 与 `ReactAgent` 的 import。  
   - 新增一个接口，例如：  
     - `POST /api/chat/stream`（流式），或  
     - `POST /api/chat`（一次性 JSON，如 `{"content": "..."}`）。  

2. **前端**  
   - 在 **RecommendationAI.vue** 的发送逻辑里（目前是 `setTimeout` 那段），改为调用上述 API：  
     - 用 `uni.request` 或项目里的 `request`（`utils/request.js`）发 `POST`，body 为 `{ query: 用户输入 }`。  
   - 若后端返回的是 **纯文字**：  
     - 可先把整段文字当成一条 AI 消息的 `content` 显示（不带 `recommendations`），或  
     - 等后端日后改为返回结构化 `recommendations` 再对接卡片。  
   - 若后端日后改为返回 **结构化推荐**（例如 `{ content, recommendations: [...] }`），前端只要把 `recommendations` 赋给 `msg.recommendations`，现有 `RecommendationCard` 与 swiper 即可复用。

3. **端口与 BASE_URL**  
   - 后端：main.py 使用 **8000** 端口。  
   - 前端：`api/wardrobe.js` 使用 `API_BASE_URL = 'http://localhost:8000'`；`utils/request.js` 的 `BASE_URL` 为 `http://localhost:3000`。  
   - 若 RecommendationAI 通过 `request.js` 调用后端，请把 **request.js 的 BASE_URL 改为 `http://localhost:8000`**，或改为使用 `wardrobe.js` 的 `API_BASE_URL`，避免请求打到错误的端口。

### 4.3 数据格式对齐

- **目前 Agent 输出**：`execute_stream` 只会 yield **纯文字**（模型最终回复内容），没有 JSON。  
- **前端 RecommendationAI**：期望一条 AI 消息带 `recommendations` 数组，每项有 `title`、`temperature`、`styleTags`、`content`、`items`、`whyThisWorks`、`images` 等。  
- **联调建议**：  
  - **第一阶段**：后端先只返回文字，前端先以「纯文字 AI 消息」显示，确认打通。  
  - **第二阶段**：再在后端加一层（例如提示词 + 解析），让模型输出结构化 JSON，或后端用正则/解析从文字中抽出推荐结构，返回 `{ content, recommendations }`，前端再赋给 `msg.recommendations`。

---

## 五、小结

| 问题 | 说明 |
|------|------|
| **AIwardrobe 是什么** | 后端的 AI 智能衣橱模块：LangChain ReAct Agent + RAG + 天气等工具，用于生成穿搭建议。 |
| **在后端怎么用** | 把 AIwardrobe 目录加入 `sys.path`，`from agent.react_agent import ReactAgent`，在 FastAPI 中新增路由调用 `agent.execute_stream(query)`，用 StreamingResponse 或拼成字符串返回。 |
| **与 RecommendationAI 联调** | 后端新增 `/api/chat` 或 `/api/chat/stream`；前端把现有 setTimeout 改为调用该 API；注意 BASE_URL 用 8000；先对接纯文字，再考虑结构化 `recommendations`。 |

若你希望，我可以再根据你当前的 main.py 和 RecommendationAI.vue 写出具体补丁（含 sys.path、路由和前端 request 范例）。
