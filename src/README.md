# Personal AI Wardrobe Assistant 

This project implements a personal AI wardrobe assistant that supports outfit recommendation, virtual try-on, and wardrobe management, together with extended modules such as calendar-based outfit tracking and wardrobe analytics.

The system integrates a Vue 3 + UniApp frontend, a FastAPI backend, and an LLM-driven recommendation module (AIwardrobe). Through this architecture, the system forms a complete workflow from user input → AI processing → structured output → visual rendering.

## Project structure

Paths are relative to **`src/`**.

### Frontend (`frontend/`) — main files

Vue 3 + UniApp (Vite). Listed below are the primary entry, config, API clients, and feature modules (every `.vue` / `.js` that defines a screen, modal, or shared logic—not every asset byte-for-byte).

```
frontend/
├── App.vue
├── main.js
├── index.html
├── pages.json
├── manifest.json
├── vite.config.js
├── uni.scss
├── uni.promisify.adaptor.js
├── package.json
│
├── api/
│   ├── userApi.js
│   ├── wardrobe.js
│   ├── wardrobeMedia.js
│   ├── calendarApi.js
│   ├── analysisApi.js
│   ├── recommendationApi.js
│   └── virtualTryOnApi.js
│
├── utils/
│   ├── request.js              # API_BASE_URL + uni.request wrapper
│   ├── wardrobeEnums.js
│   └── apiErrors.js
│
├── static/
│   └── icons/                  # SVG icons (sidebar, actions, etc.)
│
├── pages/
│   ├── login/
│   │   ├── login.vue
│   │   └── ForgotPasswordModal.vue
│   └── index/
│       ├── index.vue           # shell: sidebar + module area
│       ├── SettingsModal.vue
│       └── components/
│           ├── VirtualTryOn.vue
│           ├── MyWardrobe/
│           │   ├── WardrobeView.vue
│           │   ├── DeleteConfirmModal.vue
│           │   ├── cloth-modal/
│           │   │   ├── ClothUploadModal.vue
│           │   │   └── ClothDetailModal.vue
│           │   └── model-modal/
│           │       ├── ModelUploadModal.vue
│           │       └── ModelDetailModal.vue
│           ├── MyCalendar/
│           │   ├── MyCalendar.vue
│           │   ├── MyCalendar.scss
│           │   └── AddOutfitPanel.vue
│           ├── WardrobeAnalysis/
│           │   ├── WardrobeAnalysis.vue
│           │   ├── ViewByFilter.vue
│           │   ├── bento-widgets/
│           │   │   ├── CategoryBreakdown.vue
│           │   │   ├── IdleRate.vue
│           │   │   ├── MostWorn.vue
│           │   │   ├── SuggestedAdditions.vue
│           │   │   ├── TopStats.vue
│           │   │   ├── TotalItems.vue
│           │   │   └── WardrobeActivity.vue
│           │   └── expanded-pages/
│           │       ├── ActivityReport.vue
│           │       └── IdleItemsView.vue
│           └── RecommendationAI/
│               ├── RecommendationAI.vue
│               ├── InputBar.vue
│               ├── sidebar/
│               │   ├── ConversationSidebar.vue
│               │   ├── DeleteModal.vue
│               │   └── RenameModal.vue
│               ├── chat-content/
│               │   ├── ChatMessageBubble.vue
│               │   ├── LoadingPanel.vue
│               │   ├── PlanScheduleCard.vue
│               │   └── RecommendationCard.vue
│               └── utils/
│                   ├── chat/
│                   │   ├── aiJson.js
│                   │   ├── chatContentAdapter.js
│                   │   ├── historyMsg.js
│                   │   ├── msgRender.js
│                   │   └── wardrobeImages.js
│                   ├── rec/
│                   │   ├── outfitOrder.js
│                   │   ├── recItem.js
│                   │   └── textDisplay.js
│                   └── common/
│                       ├── dates.js
│                       └── regenerate.js
```

### Backend (`backend/`) — main folders

FastAPI app lives under **`app/`**; **`AIwardrobe/`** is the LangChain agent subtree. Under `app/`, **`api/v1/`** is listed **file-by-file**; other directories (`core`, `models`, `schemas`, `crud`, `services`, `utils`, `resources`) are shown as **folders only**.

```
backend/
├── app/
│   ├── main.py                 # FastAPI entry, middleware, router mount
│   ├── runtime.py              # app-wide runtime hooks if used
│   ├── api/                    # HTTP layer: shared deps + v1 routers
│   │   ├── deps.py
│   │   ├── router.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── ai_chat.py      # conversations, streaming chat
│   │       ├── analysis.py     # wardrobe analytics
│   │       ├── auth.py         # register, login, verify, reset-password-by-identity
│   │       ├── calendar.py
│   │       ├── clothing.py     # wardrobe CRUD / upload
│   │       ├── model_photos.py
│   │       ├── system.py       # health / misc
│   │       ├── users.py        # profile / me
│   │       ├── virtual_tryon.py
│   │       └── weather.py
│   ├── core/                   # config, database engine/session, security (JWT), exceptions
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic request/response models
│   ├── crud/                   # database access per entity
│   ├── services/               # business logic (messages, clothing, try-on, weather, analysis, ComfyUI client, …)
│   ├── utils/                  # cross-cutting helpers (e.g. envelopes, language policy)
│   └── resources/              # static workflow JSON (ComfyUI templates)
│
├── AIwardrobe/                 # LLM agent, RAG, prompts (see AIwardrobe/README.md)
│   ├── agent/                  # ReAct agent, tools/, classification helpers
│   ├── rag/                    # vector store + RAG service
│   ├── model/                  # LLM / embedding factory
│   ├── prompts/                # system & task prompt text files
│   ├── config/                 # YAML + optional .env for AI stack
│   ├── utils/                  # retriever, weather JSON, logging, paths
│   ├── services/               # e.g. weather cache
│   ├── data/                   # knowledge / weather fixtures (runtime-dependent)
│   └── logs/                   # local agent logs
│
├── tests/
│   ├── conftest.py
│   ├── unit_test/
│   └── integration_test/       # includes minimal_apps.py for FastAPI TestClient
│
├── requirements.txt
├── env_example.txt             
└── .env                        # create locally (secrets; not committed)
```

### Documentation (`docs/`)

```
docs/
├── api/                        # per-module *_api.md + README index
└── test/                       # QA summary, questionnaire, etc.
```

At the **`src/`** root (next to `frontend/`, `backend/`, `docs/`): **`README.md`** (this file).

The architecture separates frontend, backend, and AI modules, which improves maintainability and allows independent development and testing.

## Requirements

- Node.js ≥ 18  
- Python ≥ 3.9  
- PostgreSQL (for persistent storage)  
- ComfyUI for virtual try-on  
- API keys for LLM and weather services  

## How to run

**Backend**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
npm run dev:h5
```

Make sure the frontend `API_BASE_URL` (in `frontend/utils/request.js`) matches the backend address.

## Environment variables

Create `backend/.env`:

```env
SECRET_KEY=your-secret
DATABASE_URL=postgresql://user:password@localhost:5432/db

DASHSCOPE_API_KEY=your-key
COMFYUI_SERVER=http://127.0.0.1:8118
```

Optional weather-related keys (when using live weather) are described in `backend/AIwardrobe/README.md` and `backend/app/core/config.py`.

## Features

- Clothing upload and management (search, filter, tagging)  
- AI-based outfit recommendation (multi-turn conversation)  
- Structured recommendation results (card-based UI rendering)  
- Virtual try-on (image generation pipeline)  
- Calendar outfit tracking  
- Wardrobe analytics dashboard  
- User authentication (JWT-based)  

## API overview

Detailed documentation is available in `docs/api/` (see [`docs/api/README.md`](./docs/api/README.md)).

Examples:

- `POST /api/auth/login`  
- `GET /api/clothing`  
- `POST /api/ai/chat/stream`  
- `POST /api/virtual-try-on/generate`  

## Design notes

**Structured AI output**  
Instead of plain text, the LLM produces structured responses (e.g. JSON-like format), which allows the frontend to render recommendation cards, plans, and explanations instead of a plain text “chat wall”.

**End-to-end workflow integration**  
The system connects frontend interaction, backend processing, and AI generation into a unified pipeline, ensuring consistency from input to output.

**Cross-platform frontend**  
UniApp enables a single codebase to support web and mini-program platforms, reducing development cost.

**Modular backend design**  
FastAPI is organized into clear layers (API → service → database), improving readability and scalability.


