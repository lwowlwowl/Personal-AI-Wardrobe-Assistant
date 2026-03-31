# Login & registration — module API & integration reference

**Document scope:** This file is the **current implementation reference** for authentication and current-user profile APIs. It documents **HTTP behavior** as implemented in the codebase **and** **frontend–backend integration** (client module and UI entry points). It is not a generated OpenAPI spec.

**Base URL:** `http://localhost:8000` (see `frontend/utils/request.js` → `API_BASE_URL`).

**Auth:** Protected routes use query parameter **`token`** (JWT). The shared `request.js` helper does not send `Authorization: Bearer` by default.

---

## 1. Login

- **Method:** `POST`
- **Path:** `/api/auth/login`
- **Auth:** None
- **Content-Type:** `application/json`

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `username` | string | Yes | Trimmed server-side |
| `password` | string | Yes | |
| `remember` | boolean | No | Default `false`; `true` → longer token lifetime |

#### Success response

`HTTP 200` — body is a **flat** object (not wrapped in `data`):

```json
{
  "success": true,
  "message": "Signed in successfully.",
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user_id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "expires_in": 7200,
  "remember": false
}
```

`expires_in` is **604800** when `remember === true`, else **7200** (may be a float from `timedelta.total_seconds()`).

#### Error response

| HTTP | Meaning |
|------|---------|
| 200 | Body may be `{ "success": false, "message": "...", "status_code": 401 }` for wrong credentials |
| 403 | Disabled account — `{ "detail": "..." }` |
| 500 | Server error — `detail` |

#### Notes

Client stores `auth_token`, `user_info`, then navigates to the main app (`uni.reLaunch` / `navigateTo`).

---

## 2. Register

- **Method:** `POST`
- **Path:** `/api/auth/register`
- **Auth:** None
- **Content-Type:** `application/json`

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `username` | string | Yes | Per `UserCreate` |
| `email` | string | Yes | `EmailStr` |
| `password` | string | Yes | 6–100 characters |
| `confirm_password` | string | Yes | Must match `password` |

UI may use camelCase `confirmPassword`; API field is **`confirm_password`**.

#### Success response

`HTTP 200`

```json
{
  "success": true,
  "message": "Registration successful.",
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00"
  },
  "status_code": 200
}
```

#### Error response

| HTTP | Meaning |
|------|---------|
| 400 / 409 | `{ "success": false, "message": "...", "status_code": ... }` (e.g. duplicate user) |
| 422 | Validation errors |
| 500 | Server error |

#### Notes

On success the UI stays on the page and switches to the Login tab.

---

## 3. Verify token

- **Method:** `GET`
- **Path:** `/api/auth/verify`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A (no body)

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | JWT (sent as query; `userApi.js` passes via request helper) |

#### Success response

`HTTP 200`

```json
{
  "valid": true,
  "user_id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 403 / 404 | `{ "detail": "..." }` |

---

## 4. Get current user profile

- **Method:** `GET`
- **Path:** `/api/users/me`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | JWT |

#### Success response

`HTTP 200` — **`UserResponse`** shape, e.g.:

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "full_name": null,
  "avatar_url": null,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

No `last_login` in the current schema.

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 404 / 500 | `{ "detail": "..." }` |

---

## 5. Update current user profile

- **Method:** `PATCH`
- **Path:** `/api/users/me`
- **Auth:** Query `token` (required)
- **Content-Type:** `application/json`

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | Query |
| (body) | object | — | Optional fields per `UserUpdate`: `username`, `email`, `full_name`, `avatar_url`, … |

#### Success response

`HTTP 200` — updated **`UserResponse`** (same shape as §4).

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 422 / 500 | FastAPI `detail` or validation |

#### Notes

Client: `updateUsersMe` in `userApi.js`.

---

## 6. Change password

- **Method:** `PATCH`
- **Path:** `/api/users/me/password`
- **Auth:** Query `token` (required)
- **Content-Type:** `application/json`

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | Query |
| `current_password` | string | Yes | Body |
| `new_password` | string | Yes | Body |

#### Success response

`HTTP 200` — per route implementation (success payload or message).

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 400 / 422 | Wrong current password, validation, etc. |

#### Notes

Client: `changePassword` in `userApi.js`.

---

## 7. Upload avatar

- **Method:** `POST`
- **Path:** `/api/users/me/avatar`
- **Auth:** Query `token` (required)
- **Content-Type:** `multipart/form-data`

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | Query |
| `file` | file | Yes | Form field name **`file`** |

#### Success response

`HTTP 200` — updated user info (shape aligned with profile response).

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 400 / 422 / 500 | Per route |

#### Notes

Client: `uploadUserAvatar` (`uni.uploadFile`) in `userApi.js`.

---

## 8. Reset password by identity

- **Method:** `POST`
- **Path:** `/api/auth/reset-password-by-identity`
- **Auth:** None
- **Content-Type:** `application/json`

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `email` | string | Yes | Normalised for lookup |
| `username` | string | Yes | Must match same account as `email` |
| `new_password` | string | Yes | Schema rules |
| `confirm_password` | string | Yes | Must match `new_password` |

#### Success response

`HTTP 200`

```json
{
  "success": true,
  "message": "Password has been reset. You can sign in now."
}
```

#### Error response

| HTTP | Meaning |
|------|---------|
| 400 | Email/username mismatch |
| 403 | Disabled account |
| 500 | Update failure |

#### Notes

No email magic-link flow. `ForgotPasswordModal.vue` → `resetPasswordByIdentity`.

---

## Known inconsistencies / implementation notes

| Topic | Detail |
|-------|--------|
| Success body shapes | Login returns a **flat** object; register wraps user in **`data`** plus **`status_code`**. |
| Errors | Mix of **`{ "detail": ... }`** (FastAPI) and **`{ "success": false, "message", "status_code" }`** with HTTP 200 (login failure). |
| Token transport | Query `token` for protected routes; not `Authorization` header in the default client. |
| Security | Use HTTPS in production; do not log tokens. |

---

## Code map

| Layer | Path |
|-------|------|
| Backend | `backend/app/api/v1/auth.py`, `backend/app/api/v1/users.py` |
| Schemas | `backend/app/schemas/auth.py`, `backend/app/schemas/user.py` |
| Frontend API | `frontend/api/userApi.js` |
| HTTP helper | `frontend/utils/request.js` |

---

## Frontend integration

| UI | `userApi.js` |
|----|----------------|
| `login.vue` | `loginAuth`, `registerAuth` |
| `ForgotPasswordModal.vue` | `resetPasswordByIdentity` |
| `index.vue` | `authVerify`, `getUsersMe` |
| `SettingsModal.vue` | `updateUsersMe`, `uploadUserAvatar`, `changePassword` |

---

**Document version:** 2.1  
**Last updated:** 2026-03-28
