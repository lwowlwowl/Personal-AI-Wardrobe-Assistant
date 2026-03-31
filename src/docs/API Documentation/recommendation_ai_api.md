# Recommendation AI — module API & integration reference

**Document scope:** **Current implementation reference** that covers **three areas in one module**: (1) **streaming chat** (`POST /api/ai/chat/stream`), (2) **conversation persistence** CRUD, (3) **supporting weather** (`GET /api/weather/now`) used on the recommendation screen. It includes **HTTP / SSE behavior** and **client integration**. Not an OpenAPI export.

**Base URL:** `http://localhost:8000` (`frontend/utils/request.js`).

**Auth:** Stream: query **`token`** optional (valid token binds wardrobe tools; invalid → **401** before body streams). Conversations: **`token`** required.

---

## Endpoint overview

| # | Kind | Path |
|---|------|------|
| 1 | SSE stream | `POST /api/ai/chat/stream` |
| 2 | REST | `GET /api/ai/conversations` |
| 3 | REST | `GET /api/ai/conversations/{id}` |
| 4 | REST | `POST /api/ai/conversations` |
| 5 | REST | `PUT /api/ai/conversations/{id}` |
| 6 | REST | `DELETE /api/ai/conversations/{id}` |
| 7 | REST | `GET /api/weather/now` |

---

## 1. Streaming chat

- **Method:** `POST`
- **Path:** `/api/ai/chat/stream`
- **Auth:** Query `token` **optional**
- **Content-Type:** `application/json`
- **Response:** `text/event-stream` (not JSON document body)

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | No | Query |
| `query` | string | Yes | Body; whitespace-only → SSE `error` event |
| `history` | array | No | Body; items `{ "role": "user" \| "ai", "content": "..." }` |

#### Success response

Stream of lines `data: <JSON>\n\n`:

| Event `type` | Payload |
|--------------|---------|
| `delta` | `{ "type": "delta", "content": "<chunk>" }` |
| `final` | `{ "type": "final", "message": { ... } }` — `build_ai_message`, `locale` forced server-side |
| `done` | `{ "type": "done" }` |

Example final message may include `renderType`: `text` | `recommendation` | `plan` (if `plan.days` present it wins over `recommendations` in normalization).

#### Error response

| Form | Meaning |
|------|---------|
| SSE `type: "error"` | `{ "type": "error", "message": "..." }` |
| HTTP 401 | Invalid `token` when provided, before stream |

#### Notes

Server uses last **10** history lines, `ReactAgent.execute_stream`, `decide_reply_language`. Client `chatRecommendation` uses `fetch` + stream reader; prefers `final.message`, else deltas or JSON parse of full text.

---

## 2. List conversations

- **Method:** `GET`
- **Path:** `/api/ai/conversations`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |

#### Success response

`HTTP 200`

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "New conversation",
      "messages": [],
      "created_at": "2025-01-01T12:00:00+00:00",
      "updated_at": "2025-01-01T12:00:00+00:00"
    }
  ],
  "total": 1
}
```

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 | Invalid token |

---

## 3. Get one conversation

- **Method:** `GET`
- **Path:** `/api/ai/conversations/{conversation_id}`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |
| `conversation_id` | integer | Yes | Path |

#### Success response

`HTTP 200`

```json
{
  "success": true,
  "data": {
    "id": 5,
    "title": "Outfit for rainy day",
    "messages": [
      { "role": "user", "content": "What should I wear?" },
      { "role": "assistant", "content": "Consider a waterproof jacket…" }
    ],
    "created_at": "2025-02-01T10:00:00",
    "updated_at": "2025-02-01T10:02:00"
  }
}
```

#### Error response

| HTTP | Meaning |
|------|---------|
| 404 | Not found or not owned |

---

## 4. Create conversation

- **Method:** `POST`
- **Path:** `/api/ai/conversations`
- **Auth:** Query `token` (required)
- **Content-Type:** `application/json`

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | Query |
| `title` | string | No | Body; default `"New conversation"` |
| `messages` | array | No | Body; default `[]` |

#### Success response

`HTTP 200` — `{ "success": true, "data": { ...created } }`

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 400 | |

---

## 5. Update conversation

- **Method:** `PUT`
- **Path:** `/api/ai/conversations/{conversation_id}`
- **Auth:** Query `token` (required)
- **Content-Type:** `application/json`

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | Query |
| `conversation_id` | integer | Yes | Path |
| `title` | string | No | Body |
| `messages` | array | No | Body |

#### Success response

`HTTP 200` — `{ "success": true, "data": { ... } }`

#### Error response

| HTTP | Meaning |
|------|---------|
| 404 / 400 | |

---

## 6. Delete conversation

- **Method:** `DELETE`
- **Path:** `/api/ai/conversations/{conversation_id}`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |
| `conversation_id` | integer | Yes | Path |

#### Success response

`HTTP 200`

```json
{
  "success": true,
  "message": "Deleted."
}
```

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 404 | |

---

## 7. Weather now

- **Method:** `GET`
- **Path:** `/api/weather/now`
- **Auth:** Query `token` **optional** (per-user geo cache on server)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `lat` | float | Yes | Query |
| `lon` | float | Yes | Query |
| `token` | string | No | Query |

#### Success response

`HTTP 200` — payload from `weather_service` (e.g. fields such as `temp`, `text`, `windDesc` depending on implementation).

#### Error response

| HTTP | Meaning |
|------|---------|
| 4xx / 5xx | AppError / server |

#### Notes

`getWeatherNow` throttles to ~**60s** per client session. Implemented in `backend/app/api/v1/weather.py`.

---

## Known inconsistencies / implementation notes

| Topic | Detail |
|-------|--------|
| Mixed protocols | One module doc covers **SSE** and **REST JSON**. |
| Stream token | Optional on stream; required on conversations. |
| `recommendationApi.js` | Also exports `getSuggestions` / `updateSuggestion` targeting paths **not** implemented in `ai_chat` router — **unused** by current UI. |

---

## Code map

| Layer | Path |
|-------|------|
| AI + conversations | `backend/app/api/v1/ai_chat.py` |
| Weather | `backend/app/api/v1/weather.py`, `app/services/weather_service.py` |
| Schemas | `backend/app/schemas/ai.py` |
| Message shape | `backend/app/services/ai_message_service.py` |
| Agent | `backend/AIwardrobe/agent/react_agent.py` |
| Frontend | `frontend/api/recommendationApi.js` |

---

## Frontend integration

| `recommendationApi.js` | HTTP |
|------------------------|------|
| `chatRecommendation` | §1 |
| `getWeatherNow` | §7 |
| `listConversations`, `createConversation`, `updateConversation`, `deleteConversation` | §2–§6 |
| `getAuthToken` | Storage helper |

| UI |
|----|
| `RecommendationAI.vue` — chat, weather, wardrobe/calendar for cards |
| `ConversationSidebar.vue` — conversation CRUD |
| `InputBar.vue` — local `custom_ai_prompts` only for chips |

---

**Document version:** 2.1  
**Last updated:** 2026-03-28
