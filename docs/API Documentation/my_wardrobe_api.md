# Clothing & model photos — module API & integration reference

**Document scope:** **Current implementation reference** for wardrobe clothing and model-photo APIs: **HTTP behavior**, **field / enum reference**, and **frontend integration**. Not an OpenAPI export.

**Base URL:** `http://localhost:8000` (`frontend/utils/request.js`).

**Auth:** Query **`token`** (JWT) unless noted (e.g. form `token` on multipart).

---

## 1. Upload clothing

- **Method:** `POST`
- **Path:** `/api/clothing/upload`
- **Auth:** Query `token` (required)
- **Content-Type:** `multipart/form-data`

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | Query |
| `file` | file | Yes | Image |
| `name` | string | No | |
| `category`, `subcategory` | string | No | |
| `style`, `color`, `season` | string | No | `season` parsed server-side |
| `color_code` | string | No | e.g. `#RRGGBB` |
| `pattern`, `occasion` | string | No | |
| `brand`, `tags` | string | No | `tags` comma-separated → tag rows |
| `description`, `price`, `purchase_date` | mixed | No | `purchase_date`: `YYYY-MM-DD` |
| `auto_label` | boolean | No | Default **true** |

#### Success response

`HTTP 200`

```json
{
  "success": true,
  "data": {
    "id": 12,
    "user_id": 1,
    "name": "Oxford Shirt",
    "description": null,
    "image_url": "/Personal-AI-Wardrobe-Assistant/uploads/1/shirt_abc.jpg",
    "thumbnail_url": "/Personal-AI-Wardrobe-Assistant/uploads/1/thumb_shirt_abc.jpg",
    "category": "top",
    "subcategory": "Shirt",
    "style": "casual",
    "color": "white",
    "color_code": "#FFFFFF",
    "season": ["spring", "summer"],
    "pattern": "solid",
    "occasion": "work",
    "brand": "Example Co",
    "tags": ["formal", "cotton"],
    "price": 299.0,
    "purchase_date": "2024-06-01",
    "wear_count": 0,
    "last_worn_date": null,
    "is_favorite": 0,
    "condition": "good",
    "fit_type": "regular",
    "created_at": "2024-06-01T08:00:00",
    "updated_at": "2024-06-01T08:00:00"
  }
}
```

`data` is the created clothing object (ORM-serialized; extra/nullable fields may appear).

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 | Invalid token |
| 422 / 400 / 500 | Validation, business rules, server error |

#### Notes

**PUT** (§3) does **not** accept `style`, `color_code`, `pattern`, `occasion`, `auto_label`; only upload does.

---

## 2. List clothing

- **Method:** `GET`
- **Path:** `/api/clothing`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | Query |
| `page` | integer | No | Default `1` |
| `page_size` | integer | No | Default `20`, max `100` |
| `category`, `season`, `color`, `brand` | string | No | Filters |
| `is_favorite` | string | No | Comma-separated levels `0`–`3` |
| `min_price`, `max_price` | number | No | |
| `search` | string | No | Fuzzy name / description |
| `order_by` | string | No | Default `created_at`; must be a valid `ClothingItem` column or falls back |
| `order_desc` | boolean | No | Default `true` |

#### Success response

`HTTP 200`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 12,
        "name": "Oxford Shirt",
        "image_url": "/Personal-AI-Wardrobe-Assistant/uploads/1/shirt_abc.jpg",
        "thumbnail_url": "/Personal-AI-Wardrobe-Assistant/uploads/1/thumb_shirt_abc.jpg",
        "category": "top",
        "subcategory": "Shirt",
        "color": "white",
        "color_code": "#FFFFFF",
        "season": ["spring", "summer"],
        "brand": "Example Co",
        "price": 299.0,
        "wear_count": 3,
        "last_worn_date": "2025-01-20",
        "is_favorite": 0,
        "condition": "good",
        "tags": ["formal"]
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 1,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

Typical item fields: `id`, `name`, `image_url`, `thumbnail_url`, `category`, `subcategory`, `color`, `color_code`, `season`, `brand`, `price`, `wear_count`, `last_worn_date`, `is_favorite`, `condition`, `tags`, … See **Appendix A** for enums.

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 | Invalid token |
| 500 | Server error |

#### Notes

Use `resolveWardrobeImageUrl` (`wardrobeMedia.js`) for display URLs.

---

## 3. Update clothing

- **Method:** `PUT`
- **Path:** `/api/clothing/{clothing_id}`
- **Auth:** Query `token` (required)
- **Content-Type:** `multipart/form-data` (new image) **or** `application/x-www-form-urlencoded` (fields only, as in `updateClothing`)

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | Query |
| `clothing_id` | integer | Yes | Path |
| `name`, `description` | string | No | Form |
| `category` | string | No | `normalize_category` |
| `subcategory`, `color`, `brand` | string | No | |
| `season` | string | No | `parse_season_form` |
| `tags` | string | No | Comma-separated |
| `price`, `purchase_date` | mixed | No | Bad date → **400** |
| `is_favorite` | string | No | Parsed to int `0`–`3` |
| `condition` | string | No | Enum |
| `file` | file | No | Replaces image |

#### Success response

`HTTP 200`

```json
{
  "success": true,
  "message": "Item updated.",
  "data": {
    "id": 12,
    "user_id": 1,
    "name": "Oxford Shirt",
    "description": "Updated note",
    "image_url": "/Personal-AI-Wardrobe-Assistant/uploads/1/shirt_abc.jpg",
    "thumbnail_url": "/Personal-AI-Wardrobe-Assistant/uploads/1/thumb_shirt_abc.jpg",
    "category": "top",
    "subcategory": "Shirt",
    "color": "white",
    "season": ["spring", "summer"],
    "brand": "Example Co",
    "tags": ["formal"],
    "price": 279.0,
    "purchase_date": "2024-06-01",
    "wear_count": 3,
    "last_worn_date": "2025-01-20",
    "is_favorite": 1,
    "condition": "good",
    "created_at": "2024-06-01T08:00:00",
    "updated_at": "2025-02-15T14:30:00"
  }
}
```

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 | Invalid token |
| 404 | Not found / not owned |
| 422 | Validation |
| 400 / 500 | Business / server |

---

## 4. Delete clothing

- **Method:** `DELETE`
- **Path:** `/api/clothing/{clothing_id}`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | Query |
| `clothing_id` | integer | Yes | Path |

#### Success response

`HTTP 200`

```json
{
  "success": true,
  "message": "Item deleted."
}
```

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 | Invalid token |
| 404 | Not found / not owned |

#### Notes

Server deletes image files when possible.

---

## 5. Upload model photo

- **Method:** `POST`
- **Path:** `/api/model-photos/upload`
- **Auth:** Query `token` (required)
- **Content-Type:** `multipart/form-data`

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | Query |
| `file` | file | Yes | |
| `photo_name` | string | Yes | |
| `description` | string | No | |
| `is_primary` | string | No | `"true"` / `"false"`; also `1`, `on`, `yes` = true |
| `is_favorite` | integer | No | Favorite level `0`–`3`, default `0` |

#### Success response

`HTTP 200`

```json
{
  "success": true,
  "message": "Model photo uploaded.",
  "data": {
    "id": 3,
    "user_id": 1,
    "photo_name": "Summer full body",
    "description": null,
    "image_url": "/Personal-AI-Wardrobe-Assistant/uploads/1/model_xyz.jpg",
    "thumbnail_url": null,
    "file_size": 245000,
    "file_format": "jpg",
    "is_active": true,
    "is_primary": true,
    "is_favorite": 0,
    "created_at": "2025-02-01T10:00:00",
    "updated_at": "2025-02-01T10:00:00"
  }
}
```

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 400 / 500 | Auth, validation, server |

#### Notes

Do not use Python `bool()` on the raw `is_primary` string.

---

## 6. List model photos

- **Method:** `GET`
- **Path:** `/api/model-photos`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |
| `page` | integer | No | Default `1` |
| `page_size` | integer | No | Default `20`, max `100` |
| `is_active` | boolean | No | Default `true` |

#### Success response

`HTTP 200` — `data.photos`, `data.pagination` (same pattern as clothing list).

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 400 / 500 | |

---

## 7. Get primary model photo

- **Method:** `GET`
- **Path:** `/api/model-photos/primary`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |

#### Success response

`HTTP 200` — either `data: null` with message, or `data: { ...photo }`.

```json
{
  "success": true,
  "message": "No primary model photo is set yet.",
  "data": null
}
```

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 400 / 500 | |

---

## 8. Update model photo

- **Method:** `PUT`
- **Path:** `/api/model-photos/{photo_id}`
- **Auth:** Query `token` (required)
- **Content-Type:** `multipart/form-data` (with file) or urlencoded fields (`updateModelPhoto` in client)

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | Query |
| `photo_id` | integer | Yes | Path |
| `photo_name`, `description` | string | No | |
| `is_primary` | boolean | No | Form (bool on server) |
| `is_favorite` | integer | No | Favorite level `0`–`3` |
| `file` | file | No | New image |

#### Success response

`HTTP 200`

```json
{
  "success": true,
  "message": "Model photo updated.",
  "data": {
    "id": 3,
    "user_id": 1,
    "photo_name": "Summer full body",
    "description": "Outdoor lighting",
    "image_url": "/Personal-AI-Wardrobe-Assistant/uploads/1/model_xyz.jpg",
    "thumbnail_url": null,
    "file_size": 245000,
    "file_format": "jpg",
    "is_active": true,
    "is_primary": true,
    "is_favorite": 2,
    "created_at": "2025-02-01T10:00:00",
    "updated_at": "2025-02-10T09:15:00"
  }
}
```

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 404 / 400 / 500 | |

---

## 9. Delete model photo

- **Method:** `DELETE`
- **Path:** `/api/model-photos/{photo_id}`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |
| `photo_id` | integer | Yes | Path |
| `hard_delete` | boolean | No | Query; default `false` (soft delete) |

#### Success response

`HTTP 200` — `message` is `"Model photo deleted."` or `"Model photo permanently deleted."`

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 404 / 400 | |

---

## 10. Set primary model photo

- **Method:** `POST`
- **Path:** `/api/model-photos/{photo_id}/set-primary`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |
| `photo_id` | integer | Yes | Path |

#### Success response

`HTTP 200`

```json
{
  "success": true,
  "message": "Set as primary model photo.",
  "data": {
    "id": 3,
    "user_id": 1,
    "photo_name": "Summer full body",
    "description": null,
    "image_url": "/Personal-AI-Wardrobe-Assistant/uploads/1/model_xyz.jpg",
    "thumbnail_url": null,
    "file_size": 245000,
    "file_format": "jpg",
    "is_active": true,
    "is_primary": true,
    "is_favorite": 2,
    "created_at": "2025-02-01T10:00:00",
    "updated_at": "2025-02-10T16:00:00"
  }
}
```

`data` is the updated photo record.

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 404 / 400 / 500 | |

#### Notes

Clears `is_primary` on the user’s other photos.

---

## Appendix A — Enums (`ClothingItem`)

| Field | Values |
|-------|--------|
| **category** | `top`, `bottom`, `dress`, `outerwear`, `footwear`, `accessory`, `bag`, `underwear`, `other` |
| **season** (array) | `spring`, `summer`, `autumn`, `winter`, `all_season` |
| **condition** | `new`, `good`, `fair`, `poor` |
| **pattern** | `solid`, `striped`, `checked`, `printed`, `plaid`, `dotted`, `other` |
| **fit_type** | `slim`, `regular`, `loose`, `oversized` |

---

## Appendix B — `order_by`

Must be a real **`ClothingItem`** column name; unknown values fall back to **`created_at`**.

---

## Known inconsistencies / implementation notes

| Topic | Detail |
|-------|--------|
| Upload vs update | Extra taxonomy fields only on **upload** (§1). |
| Token | Query on most routes; multipart upload also uses query `token`. |
| Client upload payload | `uploadClothing` may send a subset of form fields; server accepts the full set in §1. |

---

## Code map

| Layer | Path |
|-------|------|
| Clothing | `backend/app/api/v1/clothing.py`, `backend/app/services/clothing_service.py` |
| Model photos | `backend/app/api/v1/model_photos.py` |
| Model | `backend/app/models/clothing.py` |
| Frontend | `frontend/api/wardrobe.js`, `frontend/api/wardrobeMedia.js` |

---

## Frontend integration

| UI | Module |
|----|--------|
| `MyWardrobe/WardrobeView.vue` | `getClothingList`, `uploadClothing`, `updateClothing`, `deleteClothing`, `getModelPhotos`, `uploadModelPhoto`, `deleteModelPhoto`, `setModelPhotoPrimary`, `updateModelPhoto`, wardrobe media helpers |
| `RecommendationAI/RecommendationAI.vue` | `getClothingList`, `getPrimaryModelPhoto`, `resolveWardrobeImageUrl`, … |
| Session | `WardrobeView.vue` → `authVerify` (`userApi.js`, login reference doc) |

---

**Document version:** 2.1  
**Last updated:** 2026-03-28
