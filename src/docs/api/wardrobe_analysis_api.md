# Wardrobe analysis — module API & integration reference

**Document scope:** **Current implementation reference** for **`GET /api/analysis/*`** analytics: **HTTP query parameters**, **typical `success` + `data` bodies**, and **frontend integration**. Not an OpenAPI export.

**Base URL:** `http://localhost:8000` (`frontend/utils/request.js`).

**Auth:** Query **`token`** (JWT) on every route. `analysisApi.js` reads `auth_token` and fallback keys.

---

## Endpoint overview

| § | Method | Path | Client helper |
|---|--------|------|-----------------|
| 1 | GET | `/api/analysis/total-items/trend` | `getTrend` |
| 2 | GET | `/api/analysis/total-items/summary` | `getSummary` |
| 3 | GET | `/api/analysis/total-items/category-distribution` | `getCategoryDistribution` |
| 4 | GET | `/api/analysis/idle-rate` | `getIdleRate` |
| 5 | GET | `/api/analysis/idle-items/detail` | `getIdleItemsDetail` |
| 6 | GET | `/api/analysis/top-color` | `getTopColor` |
| 7 | GET | `/api/analysis/top-style` | `getTopStyle` |
| 8 | GET | `/api/analysis/most-worn` | `getMostWorn` |
| 9 | GET | `/api/analysis/weekly-activity` | `getWeeklyActivity` |
| 10 | GET | `/api/analysis/suggested-additions` | `getSuggestedAdditions` |

---

## Representative data examples (illustrative)

Successful responses use `{ "success": true, "data": … }`. Field names and counts match backend services; numbers below are **examples only**.

### Total items trend — `GET /api/analysis/total-items/trend` (§1)

Per `run_total_items_trend`: cumulative `values`, per-period `increments`, `labels`, `view_by`, `total_count`, `statistics` (e.g. `avg_growth`, `max_growth`, optional `projection`), `date_range` with ISO `start` / `end`.

```json
{
  "success": true,
  "data": {
    "labels": ["2023", "2024", "2025"],
    "values": [5, 12, 18],
    "increments": [5, 7, 6],
    "view_by": "yearly",
    "total_count": 18,
    "statistics": {
      "avg_growth": 62.5,
      "max_growth": 7,
      "max_period": "2024",
      "projection": 22,
      "projection_year": 2026
    },
    "date_range": {
      "start": "2023-01-01T00:00:00",
      "end": "2025-12-31T23:59:59.999999"
    }
  }
}
```

### Total items summary — `GET /api/analysis/total-items/summary` (§2)

Per `run_total_items_summary`.

```json
{
  "success": true,
  "data": {
    "total_items": 42,
    "total_value": 12800.5,
    "categories_count": 6,
    "latest_added": [
      {
        "id": 12,
        "name": "Oxford Shirt",
        "image_url": "/Personal-AI-Wardrobe-Assistant/uploads/1/shirt.jpg",
        "created_at": "2025-02-01T10:00:00"
      }
    ],
    "growth_rate": 12.5,
    "stats_by_period": {
      "today": 0,
      "this_week": 1,
      "this_month": 3,
      "this_year": 8
    }
  }
}
```

### Category distribution — `GET /api/analysis/total-items/category-distribution` (§3)

`data` is an **array** of `{ "label", "value", "color" }`.

```json
{
  "success": true,
  "data": [
    { "label": "Tops", "value": 8, "color": "#FCD568" },
    { "label": "Bottoms", "value": 5, "color": "#68C5FA" },
    { "label": "Footwear", "value": 3, "color": "#E57373" }
  ]
}
```

### Idle rate — `GET /api/analysis/idle-rate` (§4)

Per `run_idle_rate` (`days` default 30).

```json
{
  "success": true,
  "data": {
    "total_items": 42,
    "idle_items": 15,
    "idle_rate": 35.7,
    "threshold_days": 30,
    "most_idle_items": [
      {
        "id": 7,
        "name": "Grey Hoodie",
        "image_url": "/Personal-AI-Wardrobe-Assistant/uploads/1/hoodie.jpg",
        "wear_count": 0,
        "last_worn_date": null,
        "days_since_last_worn": 60
      },
      {
        "id": 9,
        "name": "Canvas Sneakers",
        "image_url": "/Personal-AI-Wardrobe-Assistant/uploads/1/sneakers.jpg",
        "wear_count": 2,
        "last_worn_date": "2024-11-01",
        "days_since_last_worn": 120
      }
    ]
  }
}
```

---

## 1. Total items trend

- **Method:** `GET`
- **Path:** `/api/analysis/total-items/trend`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |
| `view_by` | string | No | `yearly` \| `monthly` \| `daily` \| `weekly`; default `yearly` |
| `start_year`, `end_year` | integer | No | **2000–2100** when set |
| `include_projection` | boolean | No | Default `true` |

#### Success response

`HTTP 200` — `{ "success": true, "data": { ... } }` per `run_total_items_trend`. **Illustrative JSON:** *Representative data examples → Total items trend* (above).

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 500 | |

---

## 2. Total items summary

- **Method:** `GET`
- **Path:** `/api/analysis/total-items/summary`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |

#### Success response

`HTTP 200` — `{ "success": true, "data": { ... } }`. **Illustrative JSON:** *Representative data examples → Total items summary* (above).

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 500 | |

---

## 3. Category distribution

- **Method:** `GET`
- **Path:** `/api/analysis/total-items/category-distribution`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |

#### Success response

`HTTP 200` — `{ "success": true, "data": … }` where `data` is an **array** of `{ "label", "value", "color" }`. **Illustrative JSON:** *Representative data examples → Category distribution* (above).

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 500 | |

---

## 4. Idle rate

- **Method:** `GET`
- **Path:** `/api/analysis/idle-rate`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |
| `days` | integer | No | Default **30**, range **1–365** |

#### Success response

`HTTP 200` — `data` includes `total_items`, `idle_items`, `idle_rate`, `threshold_days`, `most_idle_items` (each item: `id`, `name`, `image_url`, `wear_count`, `last_worn_date`, `days_since_last_worn`). **Illustrative JSON:** *Representative data examples → Idle rate* (above).

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 500 | |

---

## 5. Idle items detail

- **Method:** `GET`
- **Path:** `/api/analysis/idle-items/detail`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |
| `page` | integer | No | ≥1, default `1` |
| `page_size` | integer | No | 1–100, default `20` |
| `time_filter` | string | No | `never`, `over_season`, `over_year`, `over_six_months`, `over_three_months`; omitted → ~30-day / never-worn default |
| `season_filter` | string | No | |

#### Success response

`HTTP 200` — `data.items`, `data.pagination`.

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 500 | |

#### Notes

Client maps `timeFilter` / `seasonFilter`; omits when `all`.

---

## 6. Top color

- **Method:** `GET`
- **Path:** `/api/analysis/top-color`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |

#### Success response

`HTTP 200` — `data.top_color`, `color_distribution`, `total_items_with_color`.

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 500 | |

---

## 7. Top style

- **Method:** `GET`
- **Path:** `/api/analysis/top-style`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |

#### Success response

`HTTP 200` — `data.top_style`, `style_distribution` (from `ClothingTag` + fixed tag set).

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 500 | |

---

## 8. Most-worn items

- **Method:** `GET`
- **Path:** `/api/analysis/most-worn`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |
| `time_range` | string | No | `yearly` \| `monthly` \| `daily` \| `weekly`; default `yearly` |
| `limit` | integer | No | 1–20, default `5` |

#### Success response

`HTTP 200` — list items typically **`name`**, **`wears`**, **`color`** only (no `id` / `image` in list). Join with `GET /api/clothing` if needed.

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 | |

#### Notes

Backend may return placeholder items on internal errors (defensive path).

---

## 9. Weekly activity

- **Method:** `GET`
- **Path:** `/api/analysis/weekly-activity`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |

#### Success response

`HTTP 200` — `data.total_wears_this_week`, `total_wears_last_week`, `trend_percent`, `week_data` (`label`, `wears`), `category_activity` (`name`, `icon`, `count`). Based on **`WearHistory`** this vs last calendar week (Mon–Sun), `clothing_id` set.

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 500 | |

---

## 10. Suggested additions

- **Method:** `GET`
- **Path:** `/api/analysis/suggested-additions`
- **Auth:** Query `token` (required)
- **Content-Type:** N/A

#### Request

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `token` | string | Yes | |
| `limit` | integer | No | **1–3**, default `3` |

#### Success response

`HTTP 200` — per `run_suggested_additions`.

#### Error response

| HTTP | Meaning |
|------|---------|
| 401 / 500 | |

---

## Data sources (analytics)

| Insight | Primary source |
|---------|----------------|
| Trends / category | `ClothingItem` |
| Weekly activity | `WearHistory` |
| Idle / most-worn | `wear_count`, `last_worn_date`, wear logic |

Calendar writes also update `WearHistory`.

---

## Typical first load (client)

Parallel: §1–§4, §6–§10; open idle detail → §5.

---

## Known inconsistencies / implementation notes

| Topic | Detail |
|-------|--------|
| Token | Always query `token`; same pattern as wardrobe modules. |
| Client | On 401, `analysisApi.js` may toast and return `null`. |
| Export | `GET /api/analysis/total-items/export` exists in backend but **not** wrapped in `analysisApi.js` (not part of current UI doc set). |

---

## Code map

| Layer | Path |
|-------|------|
| Routes | `backend/app/api/v1/analysis.py` |
| Services | `analysis_trend_service.py`, `analysis_wardrobe_insights_service.py`, `analysis_suggestions_service.py` |
| Frontend | `frontend/api/analysisApi.js` |

---

## Frontend integration

| Component | Usage |
|-----------|--------|
| `WardrobeAnalysis.vue` | `isLoggedIn`, `getTrend`, `getSummary`, `getCategoryDistribution`, `getIdleRate`, `getTopColor`, `getTopStyle`, `getMostWorn`, `getWeeklyActivity`, `getSuggestedAdditions` |
| `IdleItemsView.vue` | `getIdleRate`, `getIdleItemsDetail`, `getToken`; plus `calendarApi.js` for outfit save |

`isLoggedIn`, `getToken`, `apiRequest` are helpers, not separate HTTP endpoints.

---

**Document version:** 2.1  
**Last updated:** 2026-03-28
