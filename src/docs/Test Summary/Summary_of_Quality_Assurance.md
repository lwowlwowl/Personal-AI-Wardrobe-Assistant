# Summary of Quality Assurance

This document aligns with the formal report **Testing** chapter and **Appendices D.1–D.3**, so that cross-references to **Table 6.1 / Table 6.2** and appendix case IDs in the main text stay consistent. By default, **Actual Result** records the outcome when pytest or system tests run successfully; **Status** is **Pass**.

**Related artefact:** the user study instrument (exact Likert items, instructions, and layout) is in **[Questionnaire.pdf](./Questionnaire.pdf)** in this folder; §6.2.1 summarises outcomes that were collected using that questionnaire.

---

## Testing Philosophy: Verification and Validation

Quality is addressed from two complementary angles:

| Perspective | Focus | How it appears in this project |
|-------------|-------|--------------------------------|
| **Verification** | Whether the system was **built correctly** against specification: functional requirements (FR), non-functional requirements (NFR), API contracts, data consistency, key-path performance | Unit tests, integration tests, system-level functional cases; API correctness, schema validation, different types of responses |
| **Validation** | Whether the system **meets real user needs** in realistic use | Experience-focused system tests; UAT via **[Questionnaire.pdf](./Questionnaire.pdf)**; iterations after stakeholder feedback |

---

## 6.1 Verification

### 6.1.1 Unit Testing

**Goal:** Exercise core backend logic under controlled inputs. Since the system depends on external services and complex components, some dependencies are simplified or isolated during unit testing to ensure stable and reproducible results. A **fixed test configuration** is used (e.g. `conftest.py` pins `SECRET_KEY`) so token behaviour is deterministic where needed.

**Table 6.1: Summary of Unit Testing Coverage with Requirement Mapping**

IDs follow **Table 3.1 (FR)** and **Table 3.2 (NFR)** in the requirements specification.

| Module | Test Focus | Related FR/NFR |
|--------|------------|----------------|
| **User authentication and token validation** | Password hashing; token creation/validation; expired/invalid tokens; login checks with mocked DB session | **FR-01** (register/login/logout/session); **FR-04** (profile-related identity only at token/user boundary) |
| **Wardrobe data management** | User input processing (categories, attributes); error handling on failed saves; full DB CRUD at integration level | **FR-02** (structured clothing metadata); **FR-03** (partial—forms/parsing; auto-tag pipeline not fully unit-tested); **FR-13** (search/filter/maintenance logic) |
| **Recommendation preprocessing** | User context construction; summary statistics; validation of required inputs (e.g. user id)—feeds **constraint-aware** dialogue | **FR-05** (outfit **constraints** / context for recommendations); **FR-06** (weather context rules mirrored in agent helpers) |
| **Chat input preprocessing** | Input language detection (Chinese/English); short replies inheriting prior context | **NFR-07** (CN/EN behaviour for assistant replies) |
| **LLM output parsing** | Structured output parsing/normalization; missing fields; invalid formats; defaults—supports multi-card recommendations and explanations | **FR-07** (generate multiple outfit recommendations); **FR-08** (structured explanations / adjustable presentation) |
| **Weather data processing** | Time-based freshness for weather data; fixed timestamps for determinism | **FR-06** (timely weather use); **NFR-01** (latency-related freshness rules, not full 95%/3s load test) |
| **Request validation** | Input validation schemas: login/register, location, AI chat request | **FR-01**; **FR-05** / **FR-06** where chat/weather params apply |
| **Virtual try-on workflow** | Mapping user-selected images into ComfyUI workflow configuration | **FR-10**, **FR-11** |

Each case supplies concrete inputs and asserts observable outputs or validation errors. **Representative cases are listed in Appendix D.1** (mapped to tests under `src/backend/tests/unit_test/`).

---

### 6.1.2 Integration Testing

Integration testing focuses on verifying the interaction between major system components, including backend APIs, database operations, and external services. It ensures that data flows correctly across modules such as authentication, wardrobe management, recommendation services, and virtual try-on.

Representative API-level behaviours, including standard request-response handling and streaming-based interactions (e.g., chat responses), are covered in Appendix D.2.

**Table 6.2: Summary of Integration Testing Coverage with Requirement Mapping**

| Module | Test Focus | Related FR/NFR |
|--------|------------|----------------|
| **Authentication API** | Registration, login, token lifecycle via HTTP; success and failure; **verify** rejects invalid token when `verify_access_token` returns `None` (**expired** semantics are covered in unit tests JWT-04, not as a separate integration case) | **FR-01** |
| **User profile management** | `GET/PATCH` profile with authenticated requests | **FR-04** (user preference / profile) |
| **Recommendation AI — conversations** | Create, list, delete chat sessions; consistency with storage—supports multi-turn **constraint** gathering | **FR-05** |
| **Recommendation AI — chat stream** | Representative streaming-style chat (e.g., response chunks and completion); empty-query handling | **FR-05**, **FR-07**, **FR-08** |
| **Wardrobe / clothing API** | List with filters, search, pagination; parameters passed to data layer | **FR-02**, **FR-13** |
| **Calendar and analysis** | **Calendar:** monthly outfit records (HTTP contract; integration: empty month). **Analysis:** wardrobe statistics summary (e.g. `total-items/summary`). Aligns with **wardrobe maintenance / insight** (**FR-13**). **Not** **FR-09**: preference learning from like/dislike is **not** covered by these pytest modules (see spec Table 3.1). | **FR-13** |
| **Model photo upload** | Upload handling, persistence, response shape for full-body / model images used in try-on | **FR-10**; **NFR-08** (user-uploaded images scoped to try-on / service use—policy-level; tests assert API contract only) |
| **Weather service** | Delegation to service layer; response shape | **FR-06**; **NFR-01** (same caveat as stream—not full performance suite) |
| **Virtual try-on API** | Generate pipeline: PNG vs JSON error envelope; upload envelope | **FR-10**, **FR-11** |
| **Password reset by identity** | Identity-matched reset flow | **FR-01** |

Integration tests run in a **controlled test environment**. **Representative cases are listed in Appendix D.2** (mapped to `src/backend/tests/integration_test/`).

---

### 6.1.3 System Testing

**Goal:** Before user sign-off, validate **end-to-end workflows** across frontend, backend, AI modules, and external services under conditions close to real use.

**Functional coverage (examples):** login; wardrobe management; recommendation generation; virtual try-on; weather display; chat interaction.

**Non-functional / experience:** whether AI replies and recommendations are reasonable; virtual try-on **response time**; **visual quality** of try-on output.

**Errors and boundaries:** stability and user-visible feedback under invalid input and external service failures.

**Detailed steps and priorities are in Appendix D.3 (System Test Cases).**

---

## 6.2 Validation

### 6.2.1 User Acceptance Testing (UAT)

**Method:** Structured questionnaire. **Participants:** 23 (mostly undergraduates). **Scale:** 5-point Likert (Strongly Disagree → Strongly Agree).

**Instrument:** All items, scales, and participant instructions are defined in **[Questionnaire.pdf](./Questionnaire.pdf)**. Readers should use that PDF as the authoritative reference for *what was asked*; this section only reports *aggregate outcomes* and themes.

**Dimensions (aligned with the questionnaire):** (1) usability and interface clarity; (2) system responsiveness and interaction; (3) recommendation quality and virtual try-on; (4) visual design and overall experience.

**Results summary:** **21** of 23 participants gave positive feedback (Agree or Strongly Agree); mean score **9.82 / 10**. Users found the flow clear and intuitive; recommendations and virtual try-on were seen as useful and engaging. **Example improvement ideas:** voice interaction, real-time camera outfit analysis, e-commerce integration. Conclusion: the system meets baseline needs; recommendation AI and virtual try-on remain areas for further refinement.

---

### 6.2.2 Stakeholder Feedback

**Supervisor suggestion (example):** generate multiple outfit options — **not implemented** in the current version due to time constraints.

**Implemented iterations:**  
- **Workflow integration:** **“Virtual Try-On” / “Full Outfit Try-On”** entry points on recommendation cards to shorten paths into try-on.  
- **Response readability:** **Restructured AI responses** for clearer, more scannable recommendations.

This feedback loop supports design evolution and overall usability.

---

## Appendix D.1 Unit Test Cases

The following tables summarise **representative unit tests** by module. **Actual Result** and **Status** reflect the default record when the suite **runs successfully**.

### D.1.1 Authentication Tests

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| JWT-01 | JWT creation and successful verification | pytest env; `conftest.py` fixed `SECRET_KEY` | Decoded payload contains correct `sub`, user id, and `exp` | As expected | Pass |
| JWT-02 | Reject malformed JWT | Same as JWT-01 | `verify_access_token` returns `None` | As expected | Pass |
| JWT-03 | Reject tampered signature | Valid token then alter last segment | Verification returns `None` | As expected | Pass |
| JWT-04 | Reject expired JWT | Token with past `exp` | `verify_access_token` returns `None` | As expected | Pass |
| JWT-05 | Password-reset token create/verify | Fixed `SECRET_KEY` via conftest | `verify_password_reset_token` returns original email | As expected | Pass |
| JWT-06 | Reject access token as reset token | Valid access token from `create_access_token` | `verify_password_reset_token` returns `None` (wrong type) | As expected | Pass |
| JWT-07 | Reject expired password-reset token | JWT with past `exp` and type reset | `verify_password_reset_token` returns `None` | As expected | Pass |
| PWD-01 | Password hashing and verification | None | Correct password verifies; incorrect rejected | As expected | Pass |
| DB-01 | `authenticate_user` success | Mock DB returns user; hash matches | Returns user and no error string | As expected | Pass |
| DB-02 | `authenticate_user` wrong password | Mock user with known hash | Returns `None` and incorrect-credentials message | As expected | Pass |
| DB-03 | `authenticate_user` unknown user | Mock returns no row | Returns `None` and error message | As expected | Pass |
| DEP-01 | `get_current_user` returns active user | `verify_access` + `get_user_by_id` patched | Same user object as mocked row | As expected | Pass |
| DEP-02 | `get_current_user` rejects invalid token | `verify_access_token` returns `None` | `HTTPException` 401 | As expected | Pass |
| DEP-03 | `get_current_user` rejects payload without user id | Payload missing `user_id` | `HTTPException` 401 | As expected | Pass |
| DEP-04 | `get_current_user` user row missing | `get_user_by_id` returns `None` | `HTTPException` 404 | As expected | Pass |
| DEP-05 | `get_current_user` inactive account | `User.is_active` is False | `HTTPException` 403 | As expected | Pass |

### D.1.2 Schema Validation Tests

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| REG-01 | `UserCreate` rejects mismatched passwords | Input validation models available | `ValidationError` | As expected | Pass |
| REG-02 | `UserCreate` rejects invalid username chars | None | `ValidationError` | As expected | Pass |
| LOGIN-01 | `UserLogin` rejects empty username | None | `ValidationError` | As expected | Pass |
| RST-01 | Password reset rejects non-matching confirm | None | `ValidationError` | As expected | Pass |
| RST-02 | Password reset trims username | None | Username stripped to non-empty token | As expected | Pass |
| WX-01 | Weather lat/lon coerces string coordinates | None | `lat`/`lon` parsed as floats | As expected | Pass |
| CHAT-01 | `ChatReq` default and non-empty history | None | Default empty history; optional history accepted | As expected | Pass |

### D.1.3 API Response and Error Types

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| API-01 | Success body minimal shape | None | `success` true; message ok; status code 200; `data` only if set | As expected | Pass |
| API-02 | Success body with `data` and extra fields | None | `data` and extra keys merged | As expected | Pass |
| API-03 | Error body shape | None | `success` false; message and status code set | As expected | Pass |
| ERR-01 | `AppError` carries message and HTTP status | None | `exception.message` and `exception.status_code` match constructor | As expected | Pass |

### D.1.4 Wardrobe Module Tests

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| NORM-01 | Normalize clothing category from form | conftest stubs heavy AI imports | Invalid/blank → `other`; valid unchanged | As expected | Pass |
| SEAS-01 | Parse/validate season JSON from forms | None | Array parsed; empty → `None`; invalid JSON raises | As expected | Pass |
| CRUD-01 | Clothing create rolls back on commit failure | Mock DB; commit raises | No item returned, error string, rollback invoked | As expected | Pass |
| GET-01 | `get_clothing_item` returns row | Mock query returns one item | Same object returned | As expected | Pass |
| GET-02 | `get_clothing_item` returns None when missing | Mock returns `None` | `None` returned | As expected | Pass |
| OUT-01 | `create_outfit` rolls back when clothing not owned | Mock assigns outfit id; clothing query `None` | No outfit, error string, rollback called | As expected | Pass |

### D.1.5 Context Builder Tests

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| CTX-01 | `build_agent_context` aggregated structure | DB reader functions patched | Payload includes user, closet, summary, pagination, constraints | As expected | Pass |
| CTX-02 | `build_agent_context` rejects non-positive user id | None | `ValueError` | As expected | Pass |
| CTX-03 | `build_agent_context` user row missing | `fetchall` empty | `ValueError` for missing user | As expected | Pass |
| CTX-04 | Retriever serialization and summary helpers | None | Enum/decimal serialized; counts and recent-wear order correct | As expected | Pass |

### D.1.6 Language Policy Tests

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| LANG-01 | Detect Chinese vs English dominant text | None | `zh` or `en` matches input dominance | As expected | Pass |
| LANG-02 | Short English ack follows Chinese context | History has Chinese user turn | `decide_reply_language` returns `zh` | As expected | Pass |
| LANG-03 | Explicit Chinese query selects `zh` | None | Returns `zh` | As expected | Pass |

### D.1.7 LLM Message Processing Tests

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| LLM-01 | Plain-text assistant message (no JSON) | None | `renderType` is `text` | As expected | Pass |
| LLM-02 | Invalid JSON string fallback | None | `renderType` is `text` | As expected | Pass |
| LLM-03 | Normalize recommendation JSON | Valid JSON with mixed types/empty names | Types normalized; empty names skipped; locale set | As expected | Pass |
| LLM-04 | Plan preferred when both plan and recommendations exist | JSON has `plan.days` and `recommendations` | `renderType` is `plan` | As expected | Pass |
| LLM-05 | Whitespace-only recommendation titles skipped | JSON with blank title | Falls back to text mode | As expected | Pass |
| LLM-06 | Unsupported locale defaults to English | Unknown `locale` in JSON | Output `locale` is `en` | As expected | Pass |

### D.1.8 Weather and Wind Scale Tests

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| WXF-01 | Weather observation freshness within 30 min | Fixed reference time aligned with production rule | Returns True for fresh `obsTime` | As expected | Pass |
| WXF-02 | Stale observation not fresh | Old `obsTime` | Returns False | As expected | Pass |
| WXF-03 | Missing observation time not fresh | Payload without `now.obsTime` | Returns False | As expected | Pass |
| WND-01 | Wind scale mapping (breeze bands) | `weather_service` loaded | Scales 0–2 → Light Breeze; mid → Moderate/Strong Breeze | As expected | Pass |
| WND-02 | Wind scale mapping (gale/storm) | None | High scales → Gale or Storm | As expected | Pass |
| WND-03 | Wind scale invalid input | Non-integer scale string | Returns em dash placeholder | As expected | Pass |

### D.1.9 Virtual Try-on Workflow Tests

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| VTO-01 | Map images into ComfyUI workflow template | Template `qwen_edit_v1.json` under `app/resources` | Person/clothing/accessory filenames mapped to expected nodes | As expected | Pass |
| VTO-02 | `clean_token` strips quotes and whitespace | None | `None` → empty string; wrapped tokens normalized | As expected | Pass |

---

## Appendix D.2 Integration Test Cases

### D.2.1 Authentication API (HTTP)

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| AUT-01 | `POST /api/auth/register` returns user payload | `auth` app; `create_user` patched success | HTTP 200; `success` true; `data` has username and id | As expected | Pass |
| AUT-02 | `POST /api/auth/register` conflict returns 409 | `create_user` returns error (username taken) | HTTP 409; `success` false | As expected | Pass |
| AUT-03 | `POST /api/auth/login` returns access token | `authenticate_user` + `create_access_token` patched | HTTP 200; `success` true; `access_token` and `user_id` | As expected | Pass |
| AUT-04 | `POST /api/auth/login` invalid credentials envelope | `authenticate_user` returns `None` with message | HTTP 200; `success` false; `status_code` 401 in JSON | As expected | Pass |
| AUT-05 | `GET /api/auth/verify` accepts valid token | `verify_access_token` + `get_user_by_id` patched | HTTP 200; `valid` true; username matches mock | As expected | Pass |
| AUT-06 | `GET /api/auth/verify` rejects invalid token | `verify_access_token` returns `None` | HTTP 401 | As expected | Pass |

### D.2.2 Password Reset by Identity API (HTTP)

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| RST-01 | `POST /api/auth/reset-password-by-identity` success | `get_user_by_username` + `update_user_password` patched; email matches | HTTP 200; `success` true | As expected | Pass |
| RST-02 | Reset email mismatch | User row email differs from body | HTTP 400 | As expected | Pass |

### D.2.3 User Profile API (HTTP)

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| USR-01 | `GET /api/users/me` returns profile | `users` app; token + `get_user_by_id` patched | HTTP 200; username and id match mock | As expected | Pass |
| USR-02 | `PATCH /api/users/me` updates via CRUD | `get_current_user` + `update_user` patched | HTTP 200; body reflects updated fields | As expected | Pass |

### D.2.4 Recommendation AI — Conversations API (HTTP)

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| AIC-01 | `GET /api/ai/conversations` lists | `ai_chat` app; `get_current_user` + `list_by_user` patched | HTTP 200; `success` true; `data` array and `total` consistent | As expected | Pass |
| AIC-02 | `POST /api/ai/conversations` creates | `create` patched returns new row | HTTP 200; `success` true; `data.id` matches mock | As expected | Pass |
| AIC-03 | `DELETE /api/ai/conversations/{id}` succeeds | `delete` patched success | HTTP 200; `success` true | As expected | Pass |

### D.2.5 Recommendation AI — Chat Stream API (HTTP)

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| STR-01 | `POST /api/ai/chat/stream` rejects blank query (SSE) | Whitespace-only `query` | HTTP 200; SSE body contains `error` type and empty-message wording | As expected | Pass |
| STR-02 | `POST /api/ai/chat/stream` yields delta, final, done | `ReactAgent.execute_stream` patched to yield chunk | SSE contains `delta`, `final`, and `done` events | As expected | Pass |

### D.2.6 Clothing List API (HTTP)

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| CLO-01 | `GET /api/clothing` empty list and pagination | Mocks return empty | HTTP 200; `success` true; items empty; total 0 | As expected | Pass |
| CLO-02 | `GET /api/clothing` passes search/filters to CRUD | Request includes `search`, `category`, `season` | `get_clothing_items` called with matching kwargs | As expected | Pass |

### D.2.7 Calendar and Analysis API (HTTP)

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| CAL-01 | `GET /api/calendar/outfits` empty month | `calendar` app; user + DB chain returns no rows | HTTP 200; `success` true; outfits empty; `monthStats` zeros | As expected | Pass |
| ANA-01 | `GET /api/analysis/total-items/summary` | `analysis` app; `get_current_user` + `run_total_items_summary` patched | HTTP 200; JSON equals mocked summary payload | As expected | Pass |

### D.2.8 Model Photos API (HTTP)

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| MOD-01 | `POST /api/model-photos/upload` success | `model_photos` app; `get_current_user`, `save_upload_file`, `create_model_photo` patched | HTTP 200; `success` true; `data.id` present | As expected | Pass |

### D.2.9 Weather API (HTTP)

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| WEA-01 | `GET /api/weather/now` delegates to service | `weather` app; `fetch_weather_now` patched | HTTP 200; JSON contains mocked temp; called once | As expected | Pass |

### D.2.10 Virtual Try-on API (HTTP)

| ID | Description | Pre-condition | Expected Result | Actual Result | Status |
|----|-------------|---------------|-----------------|---------------|--------|
| VTO-01 | `POST /api/virtual-try-on/generate` returns PNG | `virtual_tryon` app; `run_generate` returns `PngBytesResult` | HTTP 200; `Content-Type` image/png | As expected | Pass |
| VTO-02 | `POST /api/virtual-try-on/generate` error envelope | Service returns `JsonEnvelope` with status 400 | HTTP **400**; JSON body `success` false | As expected | Pass |
| VTO-03 | `POST /api/virtual-try-on/upload-image` returns envelope | `run_upload_virtual_tryon_image` patched (async) | HTTP **200**; `success` true in JSON body | As expected | Pass |

---

## Appendix D.3 System Test Cases

Representative **system** cases (manual / end-to-end). **Prio:** P0 critical path; P1 important; P2 secondary. **Type:** Functional / UI / Exception / AI / Performance.

### D.3.1 Authentication

| ID | Test Focus | Precondition | Test Steps | Expected Result | Prio | Type |
|----|------------|--------------|------------|-----------------|------|------|
| AUTH-ST-01 | Valid login | User registered | Open login; enter credentials; click login | Login success; redirect to home | P0 | Functional |
| AUTH-ST-02 | Wrong password | User registered | Enter wrong password | Error message shown | P1 | Functional |
| AUTH-ST-03 | Empty username | — | Leave username empty; login | Prompt to enter username | P2 | UI |
| AUTH-ST-04 | Empty password | — | Leave password empty; login | Prompt to enter password | P2 | UI |
| AUTH-ST-05 | Password toggle | User registered | Enter password; click eye icon | Password visible | P2 | UI |
| AUTH-ST-06 | Successful registration | Username unused | New user + password; submit | Registration success | P0 | Functional |
| AUTH-ST-07 | Duplicate account | Username exists | Use existing account | Error shown | P1 | Functional |
| AUTH-ST-08 | Password mismatch | — | Different passwords in form | Error shown | P1 | Functional |
| AUTH-ST-09 | Invalid email | — | Invalid email format | Prompt shown | P1 | Functional |
| AUTH-ST-10 | Empty form | — | Submit empty form | Required fields prompted | P2 | UI |

### D.3.2 Wardrobe Management

| ID | Test Focus | Precondition | Test Steps | Expected Result | Prio | Type |
|----|------------|--------------|------------|-----------------|------|------|
| WRD-ST-01 | Upload single image | Logged in | Wardrobe → upload → image + category + description | Image at top of list | P0 | Functional |
| WRD-ST-02 | Upload non-image | Logged in | Select PDF | Error: select image (jpg/png/jpeg) | P2 | Exception |
| WRD-ST-03 | Upload oversized | Logged in | Select file above limit (e.g. 20MB test) | Error: file size limit message | P2 | Performance |
| WRD-ST-04 | Cancel upload | Logged in | Select image then cancel | List unchanged | P2 | Functional |
| WRD-ST-05 | Delete single item | Item exists | Delete → confirm | Item removed; count −1 | P0 | Functional |
| WRD-ST-06 | Cancel delete | Item exists | Delete → cancel in dialog | Item remains | P2 | Functional |
| WRD-ST-07 | Filter by category | Mixed categories | Filter e.g. T-shirt | Only matching items | P1 | Functional |
| WRD-ST-08 | Multi-condition filter | Various items | Category + color + filter | Only matching items | P1 | Functional |
| WRD-ST-09 | Edit item | Item exists | Change category/description | UI shows updated info | P1 | Functional |

### D.3.3 Recommendation System

| ID | Test Focus | Precondition | Test Steps | Expected Result | Prio | Type |
|----|------------|--------------|------------|-----------------|------|------|
| REC-ST-01 | Recommend for new user | No wardrobe data | Request outfit recommendation | Complete recommendation (e.g. online sources) | P1 | Functional |
| REC-ST-02 | Recommend from wardrobe | Wardrobe has items | Request recommendation | Mix of online + wardrobe items | P0 | Functional |
| REC-ST-03 | Business occasion | — | Request business attire | Business-style outfit | P1 | AI |
| REC-ST-04 | Rainy weather | Rainy weather available | Request outfit for rain | Includes umbrella / waterproof | P1 | AI |
| REC-ST-05 | Season (winter) | — | Request winter outfit | Warm items (jacket, sweater, etc.) | P1 | AI |

### D.3.4 Virtual Try-On

| ID | Test Focus | Precondition | Test Steps | Expected Result | Prio | Type |
|----|------------|--------------|------------|-----------------|------|------|
| VTO-ST-01 | Generate try-on | Logged in; wardrobe has clothing | Select model + clothing → generate | Clear try-on image | P0 | AI |
| VTO-ST-02 | No clothing selected | Logged in | Model only → generate | Error: select clothing item | P2 | Functional |
| VTO-ST-03 | Try-on quality | — | Generate; evaluate visually | Natural edges, color blend | P2 | AI |
| VTO-ST-04 | Different body types | — | Different model photos; same clothing | Clothing adapts reasonably | P2 | AI |
| VTO-ST-05 | Generation time | — | Full generate flow | Within acceptable time (e.g. ~10s target, environment-dependent) | P2 | Performance |

### D.3.5 Weather Integration

| ID | Test Focus | Precondition | Test Steps | Expected Result | Prio | Type |
|----|------------|--------------|------------|-----------------|------|------|
| WTH-ST-01 | Display current weather | Location granted | Chat page; check weather bar | City, temperature, status, humidity | P1 | Functional |
| WTH-ST-02 | Invalid / missing location | Permission denied or bad city | Check weather display | User-visible error (e.g. city not found) | P2 | Exception |
| WTH-ST-03 | Auto-refresh | Weather fetched | Stay ~30 min | Weather info updates | P2 | Functional |
| WTH-ST-04 | Chat + weather context | Rainy data | Ask “What should I wear today?” | Reply references rain / umbrella | P1 | AI |

### D.3.6 Wardrobe Analysis

| ID | Test Focus | Precondition | Test Steps | Expected Result | Prio | Type |
|----|------------|--------------|------------|-----------------|------|------|
| ANA-ST-01 | Category statistics | e.g. 10 items | Analysis page; category stats | Counts/percentages (chart) | P1 | Functional |
| ANA-ST-02 | Update after upload | Empty wardrobe | Upload item → analysis refresh | Counts increase correctly | P0 | Functional |
| ANA-ST-03 | Update after delete | 3 items | Delete one → refresh | Counts decrease | P1 | Functional |
| ANA-ST-04 | Color distribution | Known color mix | View color stats | Correct per-color counts | P1 | Functional |
| ANA-ST-05 | Color after new upload | — | Upload red coat → color stats | Red count increases | P2 | AI |

---

## Traceability to the Repository

| Appendix / section | Typical code or artefact location |
|----------------------|-----------------------------------|
| D.1 | `src/backend/tests/unit_test/*.py`, `conftest.py` |
| D.2 | `src/backend/tests/integration_test/*.py`, `minimal_apps.py` |
| D.3 | **Not pytest:** manual / E2E scenario descriptions; **no one-to-one automated mapping** in `backend/tests` (archive with execution logs or screenshots) |
| §6.2.1 UAT | **Not pytest:** raw responses may be stored separately; the **survey instrument** is **[Questionnaire.pdf](./Questionnaire.pdf)** (same folder as this file) |
| §6.2.2 Stakeholder feedback | **Not in the codebase:** narrative conclusions from supervision; cannot be re-run as unit tests |

**ID mapping:** Appendix **D.1 / D.2** IDs such as **JWT-01**, **AUT-01** are **report traceability IDs**. Each table row maps to **one or more `def test_*` functions**, not necessarily one file per ID. For example, **LANG-01** aggregates assertions from both `test_detect_chinese_dominant` and `test_detect_english_dominant`.

**Command (D.1 + D.2 only):** from `src/backend`, run `python -m pytest tests -q`.

---

## Conclusion: Evidence, Requirements Traceability, and Assessment

### Evidence of correct behaviour

We ran different kinds of tests (unit, integration, system, and a user survey). The results show the system usually does what we expect for normal use, and it also handles bad inputs and error cases in a sensible way. **UAT numbers and themes above come from the study run with [Questionnaire.pdf](./Questionnaire.pdf)**—so usability validation is traceable to a fixed instrument, not ad-hoc notes. Together with automated tests, this backs up our FR and NFR.

### Explicit binding to FR and NFR

We did not only test “the app” in general. We linked tests to requirements. Per **Table 3.1**, **FR-05** is **outfit constraints** (occasion, comfort, colour, etc.—mostly via chat/context), **FR-07** is **generating** recommendations (stream + message shape), and **FR-08** is **explanations / structured cards**—those were exercised in scenario-style and integration tests; **FR-10** / **FR-11** (virtual try-on) were checked the same way. **NF-05** (Table 3.2: core flows within **≤3 steps**) was partly reflected in UAT via **[Questionnaire.pdf](./Questionnaire.pdf)** (clarity, flow, try-on, design). **FR-09** (feedback → preference learning) and **FR-12** (share/export links) are **not** claimed as pytest-covered here. The full mapping is in **Tables 6.1 and 6.2** and appendices **D.1–D.3**; **FR-01**, **FR-04**, **FR-06**, **FR-13**, **NFR-07** appear there as well.

### System-level summary

After testing and a few rounds of fixes, the app feels **reliable** enough for demo and daily use, **robust** when something goes wrong (wrong token, empty chat, try-on errors, etc.), and **usable** according to our testers. This matches what we aimed for in the project brief.

---

**Document version:** 3.1
