# Virtual try-on — module API & integration reference

**Document scope:** **Current implementation reference** for ComfyUI-backed try-on: **HTTP behavior** (including **binary PNG** and **JSON error** paths) and **client integration**. This module is **not** a plain JSON REST CRUD API end-to-end. Not an OpenAPI export.

**Base URL:** `http://localhost:8000` (`frontend/utils/request.js`).

**Dependencies:** ComfyUI (`app/services/comfyui_client.py`, `COMFYUI_SERVER`, …). If disabled: **503** or JSON `{ "success": false, "message" }`.

---

## 1. Upload image (multipart)

- **Method:** `POST`
- **Path:** `/api/virtual-try-on/upload-image`
- **Auth:** Form field `token` (required)
- **Content-Type:** `multipart/form-data`

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `file` | file | Yes | |
| `token` | string | Yes | Form (not header) |
| `image_type` | string | No | e.g. `person` / `clothing` (logging) |

#### Success response

`HTTP 200` — `application/json`

```json
{
  "success": true,
  "filename": "<comfyui-name>",
  "data": { "filename": "<same>" }
}
```

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 | Invalid token |
| 503 | ComfyUI unavailable / misconfigured |
| 500 | Upload failure |

---

## 2. Upload from server storage

- **Method:** `POST`
- **Path:** `/api/virtual-try-on/upload-from-storage`
- **Auth:** Body `token` required for successful auth
- **Content-Type:** `application/json`

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `image_ref` | string | Yes | Path under `UPLOAD_URL_PREFIX` (default `/Personal-AI-Wardrobe-Assistant/uploads/...`); full URL allowed |
| `token` | string | Yes | Invalid/missing → **401** |
| `image_type` | string | No | `person` / `clothing` |

#### Success response

`HTTP 200` — same JSON shape as §1.

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 | Auth |
| 403 | File not under current user’s upload segment |
| 400 | Invalid path |
| 503 / 500 | ComfyUI / server |

---

## 3. Generate try-on result

- **Method:** `POST`
- **Path:** `/api/virtual-try-on/generate`
- **Auth:** Body `token` optional (missing/invalid often → **HTTP 200** + JSON `success: false`)
- **Content-Type:** `application/json` (request); response may be **image** or **JSON**

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `person_image` | string | Yes | ComfyUI filename from §1/§2 |
| `clothing_image` | string | Yes | |
| `token` | string | No | |
| `model_type` | string | No | Default `"2509"` |
| `prompt` | string | No | Empty → workflow default; **client** `generateVirtualTryOn` may omit (server default `""`) |

#### Success response

**A)** `HTTP 200`, `Content-Type: image/png`, body = **raw bytes**. Headers may include `X-Result-Image-Bytes`, `Content-Length`.

**B)** Rare JSON success with `data.result_image` (base64) — client handles both.

#### Error response

Often **`HTTP 200`** with JSON:

```json
{ "success": false, "message": "<reason>" }
```

Also **503** if module disabled.

| HTTP | Meaning |
|------|---------|
| 200 + JSON | Queue failure, auth message, empty image, etc. |
| 503 | Disabled |

#### Notes

Client uses `arraybuffer`, checks PNG magic, then parses JSON if not PNG.

---

## Client flow (summary)

1. `uploadVirtualTryOnImage` → §1 or §2.  
2. `generateVirtualTryOn` → §3.  
3. Multi-step outfits: repeat §1–§3 in the UI.  
4. `getCleanAuthToken()` reads `auth_token`, `token`, `user_info.token`, etc.

---

## Known inconsistencies / implementation notes

| Topic | Detail |
|-------|--------|
| Mixed bodies | Success may be **binary PNG** or **JSON**; errors often **200 + JSON**. |
| Token | Query on some modules; here **form** (upload) or **JSON body** (generate/storage). |
| ComfyUI | Required for real runs; otherwise 503 / disabled messages. |

---

## Code map

| Layer | Path |
|-------|------|
| Routes | `backend/app/api/v1/virtual_tryon.py` |
| Service | `backend/app/services/virtual_tryon_service.py` |
| Schemas | `backend/app/schemas/virtual_tryon.py` |
| Frontend | `frontend/api/virtualTryOnApi.js`, `VirtualTryOn.vue` |

---

## Frontend integration

| UI | `virtualTryOnApi.js` |
|----|------------------------|
| `VirtualTryOn.vue` | `uploadVirtualTryOnImage`, `generateVirtualTryOn`, `getCleanAuthToken` |

Parent `index.vue` passes wardrobe/recommendation props into the same component.

---

**Document version:** 2.1  
**Last updated:** 2026-03-28
