# Module API & integration reference

Canonical **current implementation** docs for HTTP APIs and frontend wiring. Each file states scope (API + integration), uses a uniform per-endpoint template, and ends with **Known inconsistencies**, **Code map**, and **Frontend integration**.

| Document | Module |
|----------|--------|
| [login_register_api.md](./login_register_api.md) | Auth, profile, avatar, password |
| [my_wardrobe_api.md](./my_wardrobe_api.md) | Clothing, model photos |
| [my_calendar_api.md](./my_calendar_api.md) | Calendar outfits |
| [wardrobe_analysis_api.md](./wardrobe_analysis_api.md) | `/api/analysis/*` |
| [virtual_tryon_api.md](./virtual_tryon_api.md) | Virtual try-on + ComfyUI |
| [recommendation_ai_api.md](./recommendation_ai_api.md) | Streaming AI, conversations, weather |

Paths are relative to **`src/docs/API Documentation/`** (i.e. under the repo’s `src` tree).
