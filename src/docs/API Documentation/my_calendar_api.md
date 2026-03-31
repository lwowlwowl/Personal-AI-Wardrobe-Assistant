# Calendar outfit records — module API & integration reference

**Document scope:** **Current implementation reference** for calendar outfit APIs: **HTTP behavior** and **frontend–backend integration**. Not an OpenAPI export.

**Base URL:** `http://localhost:8000`

**Auth:** Query **`token`** (JWT) on all routes below.

**Data model:** Responses are built from **`WearHistory`** joined with **`ClothingItem`**. **POST** fully replaces one day’s clothing-linked rows and recomputes wear stats. Item **`image`** mirrors wardrobe **`image_url`**; **`accentColor`** is always **`null`** on the server.

---

## 1. Get outfits for a month

- **Method:** `GET`
- **Path:** `/api/calendar/outfits`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | Query |
| `year` | integer | Yes | Query, e.g. `2025` |
| `month` | integer | Yes | Query, **1–12** |

#### Success response

`HTTP 200`

```json
{
  "success": true,
  "message": "Success",
  "data": {
    "outfits": {
      "2025-02-09": [
        {
          "id": 1,
          "name": "White Tee",
          "image": "/Personal-AI-Wardrobe-Assistant/uploads/1/xxx.jpg",
          "accentColor": null
        }
      ]
    },
    "monthStats": {
      "daysRecorded": 1,
      "uniqueItems": 1
    }
  },
  "status_code": 200
}
```

`outfits` keys are **`YYYY-MM-DD`**. `monthStats.uniqueItems` counts distinct `clothing_id` in the month.

#### Error response

| HTTP | Meaning |
|------|---------|
| 400 | Invalid `year` / `month` |
| 401 | Invalid or missing token |
| 500 | Server error |

---

## 2. Save or clear one day (full replace)

- **Method:** `POST`
- **Path:** `/api/calendar/outfits`
- **Auth:** Query `token` (required)
- **Content-Type:** `application/json`

#### Request

**Query**

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |

**Body** (`CalendarOutfitSave`)

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `date` | string | Yes | `YYYY-MM-DD`; future date rejected when persisting (**400**) |
| `items` | array | Yes | Empty array **clears** the day |

**Each element of `items`** (`CalendarOutfitItem`)

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `id` | integer | Yes | Wardrobe `clothing_id` |
| `name` | string | No | Ignored for persistence |
| `image` | string | No | Ignored for persistence |
| `accentColor` | string | No | UI only |

All `id` values must belong to the current user or **404**.

#### Success response

`HTTP 200`

```json
{
  "success": true,
  "message": "Saved",
  "data": {
    "date": "2025-02-09",
    "items": [
      { "id": 1, "name": "White Tee", "image": "/.../x.jpg", "accentColor": null }
    ]
  },
  "status_code": 200
}
```

When cleared: `"message": "Deleted"`, `"items": []`.

#### Error response

| HTTP | Meaning |
|------|---------|
| 400 | Bad date, `items` not an array, missing `id`, validation |
| 401 | Unauthorized |
| 404 | Clothing id not in user’s wardrobe |

#### Notes

`GET /api/clothing` returns **`image_url`**; this API returns **`image`** for the same path role.

---

## 3. Client helpers

```text
getCalendarOutfits({ token, year, month })
saveCalendarOutfits({ token, date, items })
```

`calendarApi.js` imports `request` / `API_BASE_URL` from `./wardrobe.js`.

---

## Known inconsistencies / implementation notes

| Topic | Detail |
|-------|--------|
| Response envelope | Calendar list/save include `message` and `status_code` alongside `success` / `data`. |
| Token | Same JWT as other modules (e.g. `auth_token`). |

---

## Code map

| Layer | Path |
|-------|------|
| Backend | `backend/app/api/v1/calendar.py` |
| Schemas | `backend/app/schemas/wear_history.py` |
| Frontend API | `frontend/api/calendarApi.js` |

---

## Frontend integration

| UI | `calendarApi.js` |
|----|------------------|
| `MyCalendar.vue` | `getCalendarOutfits`, `saveCalendarOutfits` |
| `AddOutfitPanel.vue` | `getCalendarOutfits` (+ `getClothingList` from `wardrobe.js`) |
| `RecommendationAI.vue` | `getCalendarOutfits`, `saveCalendarOutfits` |
| `IdleItemsView.vue` | `getCalendarOutfits`, `saveCalendarOutfits` |

---

**Document version:** 2.1  
**Last updated:** 2026-03-28
