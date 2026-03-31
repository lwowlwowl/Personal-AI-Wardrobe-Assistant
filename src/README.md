# Personal AI Wardrobe Assistant 

This project builds a personal AI wardrobe assistant focused on practical daily outfit support. It helps users manage wardrobe items, get context-aware outfit suggestions, try outfits virtually, and keep track of outfit history.

The goal is to combine wardrobe management, recommendation, virtual try-on and analysis into one user-friendly workflow, so users can decide what to wear more efficiently and understand their clothing usage patterns over time.

## Quick Start (if the database is already configured)

Assume `src/backend/.env` exists with a valid `DATABASE_URL` and other required keys (see `src/backend/env_example.txt`). Commands below use paths from the **repository root** (the folder that contains `src/`).

### Backend

```bash
cd src/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd src/frontend
npm install
npm run dev:h5
```

**Access**

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend: [http://localhost:8000/docs](http://localhost:8000/docs)

The system integrates a Vue 3 + UniApp frontend, a FastAPI backend, and an LLM-driven recommendation module (AIwardrobe). Through this architecture, the system forms a complete workflow from user input -> AI processing -> structured output -> visual rendering.

## Project structure

Paths are relative to **`src/`**.

### Frontend (`frontend/`)

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
│   ├── userApi.js              # login/register/profile/password (auth & user, not wardrobe CRUD)
│   ├── wardrobe.js             # clothing & model-photo HTTP API + shared `request` / `API_BASE_URL`
│   ├── wardrobeMedia.js        # wardrobe image URL helpers, placeholders, H5 image probe
│   ├── calendarApi.js          # calendar outfit records (/api/calendar/outfits)
│   ├── analysisApi.js          # wardrobe analytics (/api/analysis/*)
│   ├── recommendationApi.js    # Recommendation AI: streaming chat, conversations
│   └── virtualTryOnApi.js      # virtual try-on upload & ComfyUI generation
│
├── utils/
│   ├── request.js              # API_BASE_URL + uni.request wrapper
│   ├── wardrobeEnums.js        # category/color/style labels ↔ backend codes for forms & filters
│   └── apiErrors.js            # format FastAPI/Pydantic error JSON into user-visible strings
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
│           ├── VirtualTryOn.vue            # virtual try-on screen (manual / pipeline entry)
│           ├── MyWardrobe/                 # wardrobe grid, filters, cloth & model flows
│           │   ├── WardrobeView.vue        # main list + filter + favorites
│           │   ├── DeleteConfirmModal.vue
│           │   ├── cloth-modal/              # upload & detail for clothing items
│           │   │   ├── ClothUploadModal.vue
│           │   │   └── ClothDetailModal.vue
│           │   └── model-modal/            # upload & detail for model photos
│           │       ├── ModelUploadModal.vue
│           │       └── ModelDetailModal.vue
│           ├── MyCalendar/                 # monthly calendar + outfit slots
│           │   ├── MyCalendar.vue
│           │   ├── MyCalendar.scss
│           │   └── AddOutfitPanel.vue      # add outfit to a date
│           ├── WardrobeAnalysis/           # analytics dashboard + drill-down views
│           │   ├── WardrobeAnalysis.vue
│           │   ├── ViewByFilter.vue
│           │   ├── bento-widgets/          # summary cards (stats, charts, suggestions)
│           │   │   ├── CategoryBreakdown.vue
│           │   │   ├── IdleRate.vue
│           │   │   ├── MostWorn.vue
│           │   │   ├── SuggestedAdditions.vue
│           │   │   ├── TopStats.vue
│           │   │   ├── TotalItems.vue
│           │   │   └── WardrobeActivity.vue
│           │   └── expanded-pages/         # full-page reports (activity, idle items)
│           │       ├── ActivityReport.vue
│           │       └── IdleItemsView.vue
│           └── RecommendationAI/           # AI chat UI + recommendation cards
│               ├── RecommendationAI.vue    # conversation shell
│               ├── InputBar.vue
│               ├── sidebar/                # conversation list, rename/delete
│               │   ├── ConversationSidebar.vue
│               │   ├── DeleteModal.vue
│               │   └── RenameModal.vue
│               ├── chat-content/           # bubbles, loading, plan card, outfit cards
│               │   ├── ChatMessageBubble.vue
│               │   ├── LoadingPanel.vue
│               │   ├── PlanScheduleCard.vue
│               │   └── RecommendationCard.vue
│               └── utils/                  # RecommendationAI-only helpers (not global utils/)
│                   ├── chat/               # parse AI JSON, render messages, history, images
│                   │   ├── aiJson.js
│                   │   ├── chatContentAdapter.js
│                   │   ├── historyMsg.js
│                   │   ├── msgRender.js
│                   │   └── wardrobeImages.js
│                   ├── rec/                # outfit ordering, item display, labels
│                   │   ├── outfitOrder.js
│                   │   ├── recItem.js
│                   │   └── textDisplay.js
│                   └── common/             # dates, regenerate look
│                       ├── dates.js
│                       └── regenerate.js
```

### Backend (`backend/`)

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
├── User Guide/
│   ├── installation_instruction.md   # install & run guide
│   └── user_manual.md                # user manual
├── API Documentation/
└── Test Summary/
```

At the **`src/`** root (next to `frontend/`, `backend/`, `docs/`): **`README.md`** (this file).

The architecture separates frontend, backend, and AI modules, which improves maintainability and allows independent development and testing.

## Environment Requirements

### 1. Hardware Requirements

#### Minimum Requirements

- CPU: Modern multi-core processor (e.g., Intel i5 / AMD Ryzen 5 or above)
- Memory: 12 GB RAM or above
- GPU: Not required (except for virtual try-on)
- Network: Stable internet connection (required for API calls)

> Under minimum requirements, most core features can run, but the full feature set may not be available.
> Virtual try-on depends on local ComfyUI deployment and is more likely to be limited or unavailable on lower-end setups; use the recommended requirements for a complete experience.

#### Recommended Requirements

- CPU: Intel i7 / AMD Ryzen 7 or above
- **GPU:** NVIDIA GeForce RTX 4090 or better (recommended for virtual try-on).
- **Memory:** 32 GB RAM or more.
- Network: High-speed stable internet connection

> **Note:** If suitable hardware is not available, you may skip installing ComfyUI. This may disable the Virtual Try-on feature, but other core features (wardrobe, recommendation, and calendar) can still run.

### 2. Software Requirements

- **Operating system:** Windows, macOS, or Linux (local development).
- **Runtime:** Node.js ≥ 18; Python ≥ 3.9.
- **Database:** PostgreSQL — create an empty database; put connection info in `backend/.env`. Tables are created automatically on first successful backend start.
- **ComfyUI:** virtual try-on pipeline; workflow files under `backend/app/resources/`.
- **Environment variables:** backend requires `backend/.env`; for setup options (normal template vs teaching/demo quick setup), see the **Installation instruction** section below.

## Installation instruction

Installation instruction: [Click to installation instruction](./docs/User%20Guide/installation_instruction.md).

Environment template: `src/backend/env_example.txt`.
Environment setup (same as installation guide):
- Normal setup: create `src/backend/.env`, copy from `env_example.txt`, then fill in your own API keys.
- Teaching/demo quick setup: create `src/backend/.env`, copy all content from `env.txt` (pre-filled), and only replace `DATABASE_URL` with your own PostgreSQL connection string.

## User manual

User manual: [Click to user manual](./docs/User%20Guide/user_manual.md).

## Test

Test summary: [Click to test summary](./docs/Test%20Summary/Summary_of_Quality_Assurance.md).

## Features

- Clothing upload and management (search, filter, tagging)  
- AI-based outfit recommendation (multi-turn conversation)  
- Structured recommendation results (card-based UI rendering)  
- Virtual try-on (image generation pipeline)  
- Calendar outfit tracking  
- Wardrobe analytics dashboard  
- User authentication (JWT-based)  

## API overview

Detailed documentation is available in [`docs/API Documentation/README.md`](./docs/API%20Documentation/README.md).

## Design notes

**Structured AI output**  
Instead of plain text, the LLM produces structured responses (e.g. JSON-like format), which allows the frontend to render recommendation cards, plans, and explanations instead of a plain text “chat wall”.

**End-to-end workflow integration**  
The system connects frontend interaction, backend processing, and AI generation into a unified pipeline, ensuring consistency from input to output.

**Modular backend design**  
FastAPI is organized into clear layers (API → service → database), improving readability and scalability.


