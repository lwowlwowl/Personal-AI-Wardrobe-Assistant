# API 文档 - 衣橱分析模块（Vue3 + UniApp）

## 概述

本文档描述前端 **Wardrobe Analysis** 功能（`pages/index/components/WardrobeAnalysis/`）所需的 API 约定：**衣橱活动度统计**、**闲置率分析**、**最常穿物品**、**分类统计**、**活动报告**、**闲置物品列表**、**推荐添加**等数据分析功能。

**文档结构**：
- **Section 1-8**：API 接口（核心接口 + 可选接口）
- **Section 9**：通用响应格式与状态码
- **Section 10**：接口实现优先级
- **Section 11**：数据关联说明
- **Section 12**：安全与校验建议
- **Section 13**：联系方式
- **附录**：补充内容（统计字段计算口径、前端调用对照表、测试用例、接口复用说明）

**文档参考**：本文档参考 `LOGIN_REGISTER.md`、`MY_WARDROBE.md`，响应格式（`{ success, message, data, status_code }`）及认证、基础 URL 与彼等一致。接口复用见 Section 11 与附录 D。

**⚠️ 接口路径**：衣橱复用路径为 `GET /api/clothing`（与 MY_WARDROBE 一致）；若后端实为其他路径，请全局替换。衣橱返回 `image_url`/`category`，分析模块统一使用 `image`/`category`（可后端或前端映射）。

**基础 URL**：`http://localhost:8000` · **认证**：query 参数 `token`（JWT） · **请求/响应**：`application/json`。接口均写为完整路径（如 `GET /api/analysis/activity`），无需再拼接前缀。

---

## MVP 快速对接（1页）

### 必须实现的接口列表

| 接口 | 路径 | 说明 |
|------|------|------|
| 活动度统计 | `GET /api/analysis/activity?token=xxx` | 返回本周与上周对比 |
| 闲置率统计 | `GET /api/analysis/idle-rate?token=xxx` | 返回未穿过物品数量 |
| 总物品数统计 | `GET /api/analysis/total-items?token=xxx&viewBy=yearly` | 返回历年物品数（需 `created_at` 字段） |
| 最常穿物品 | `GET /api/analysis/most-worn?token=xxx&viewBy=yearly` | 返回穿着次数最多的物品（使用 `wear_count`） |
| 最常用颜色/风格 | `GET /api/analysis/top-stats?token=xxx` | 返回最常用颜色和风格（`topStyle` 可为 `null`） |
| 分类统计 | `GET /api/analysis/category-breakdown?token=xxx` | 返回分类分布（不返回 `color`，前端映射） |
| 闲置物品列表 | `GET /api/analysis/idle-items?token=xxx` | 返回闲置物品（使用 `last_worn_date`） |
| 推荐添加 | `GET /api/analysis/suggested-additions?token=xxx` | 返回推荐物品（MVP阶段可用简单规则） |

### 关键口径

1. **数据源统一口径**：
   - **物品统计**（闲置率、最常穿、闲置列表）：优先使用衣橱表的 `wear_count`、`last_worn_date`、`created_at` 字段
   - **活动度统计**（活动度、活动报告）：基于日历记录（`/api/calendar/outfits`）或 wear 事件表统计本周/上周的记录数
   - **前提条件**：后端在写入日历穿搭时，需同步更新衣橱表的 `wear_count` 和 `last_worn_date`（或通过 `POST /api/clothing/{id}/record-wear` 更新），确保数据一致性
2. **字段映射**：衣橱返回 `image_url`，分析模块统一返回 `image`；统一使用 `category` 字段
3. **活动度百分比**：返回 `deltaPercent`（可正可负），处理除零：上周为0时，本周>0返回100，否则返回0
4. **分类颜色**：后端只返回 `code`，颜色由前端映射
5. **风格数据**：来自 `tags`（`string[]`），如果无数据 `topStyle` 返回 `null`

### 响应示例

**活动度统计**：
```json
{
  "success": true,
  "data": {
    "deltaPercent": 15,
    "trend": "increase",
    "currentWeekCount": 23,
    "lastWeekCount": 20
  }
}
```

**最常穿物品**：
```json
{
  "success": true,
  "data": {
    "items": [
      { "id": 1, "name": "White Cotton T-shirt", "wears": 35, "color": "white", "image": "..." }
    ]
  }
}
```

**分类统计**：
```json
{
  "success": true,
  "data": {
    "categories": [
      { "label": "Top", "value": 35, "code": "top" }
    ]
  }
}
```

**详细接口说明见下方 Section 1-9**

---

## 功能概要（供后端理解）

| 模块 | 说明 |
|------|------|
| **衣橱活动度（Wardrobe Activity）** | 显示本周与上周的穿搭活动对比，以百分比形式展示（如 +15% 或 -8%），并标识趋势（increase/decrease）。点击可展开查看详细的活动报告。 |
| **闲置率（Idle Rate）** | 显示未穿过的物品数量及占比。点击可展开查看所有闲置物品列表，支持按时间（All/Never worn/Over a year）和季节筛选。 |
| **总物品数统计（Total Items）** | 以折线图形式展示历年物品总数变化趋势，支持按年/月/日维度查看。 |
| **最常穿物品（Most Worn Items）** | 列出穿着次数最多的物品，支持按年/月/日维度筛选。每个物品显示名称、穿着次数、颜色标识。 |
| **最常用颜色/风格（Top Color/Style）** | 显示最常用的颜色和风格及其占比。 |
| **分类统计（Category Breakdown）** | 以圆环图形式展示各分类（Top/Bottom/Footwear/Outerwear/Accessories）的物品数量分布。 |
| **活动报告（Activity Report）** | 展开视图，显示每周趋势、每日穿着次数柱状图、各分类活动度等详细信息。 |
| **闲置物品列表（Idle Items）** | 展开视图，列出所有未穿过的物品，支持筛选和排序。 |
| **推荐添加（Suggested Additions）** | 基于用户现有衣橱，推荐可添加的物品，包含名称、图片、标签、描述等信息。 |

---

## 与后端交互概览（自然语言）

**衣橱活动度统计**
- **进入分析页面**：前端会向你要「本周与上周的穿搭活动对比数据」，你需要统计本周（最近7天）和上周（前7-14天）的穿搭记录数量，计算变化百分比和趋势方向（increase/decrease）。
- **数据来源**：基于日历记录（`/api/calendar/outfits`）或 wear 事件表统计记录数，而不是从衣橱表的 `wear_count` 字段统计（因为 `wear_count` 是累计值，无法区分本周/上周）

**闲置率统计**
- **获取闲置物品数量**：前端会向你要「未穿过的物品数量」，你需要使用衣橱表的 `last_worn_date` 和 `wear_count` 字段判断闲置物品（`last_worn_date` 为 `null` 或 `wear_count` 为 0），以及总物品数，计算闲置率。

**总物品数统计**
- **获取历年物品数趋势**：前端会向你要「按年份统计的物品总数」，你需要返回历年（如2016-2023）每年的物品总数，用于绘制折线图。

**最常穿物品**
- **获取最常穿物品列表**：前端会向你要「穿着次数最多的物品列表」，你需要使用衣橱表的 `wear_count` 字段，按 `wear_count` 降序返回，支持按年/月/日维度筛选（基于 `last_worn_date` 字段）。

**最常用颜色/风格**
- **获取最常用颜色和风格**：前端会向你要「最常用的颜色和风格及其占比」，你需要统计所有物品的颜色和风格分布，返回占比最高的颜色和风格。

**分类统计**
- **获取分类分布**：前端会向你要「各分类的物品数量」，你需要按分类（Top/Bottom/Footwear/Outerwear/Accessories）统计物品数量，返回各分类的数量和占比。

**活动报告详情**
- **获取活动报告数据**：前端会向你要「本周每日穿着次数」和「各分类活动度」，你需要返回本周7天的每日穿着次数，以及各分类在本周的穿着次数和占比。
- **数据来源**：基于日历记录（`/api/calendar/outfits`）或 wear 事件表统计，统计本周7天的每日记录数和各分类活动度

**闲置物品列表**
- **获取闲置物品列表**：前端会向你要「所有未穿过的物品列表」，你需要使用衣橱表的 `last_worn_date` 和 `wear_count` 字段判断闲置物品，返回所有闲置物品，支持按时间（All/Never worn/Over a year）和季节筛选。

**推荐添加**
- **获取推荐物品**：前端会向你要「基于现有衣橱的推荐物品列表」，你可以基于用户的衣橱数据，推荐可添加的物品（如互补颜色、缺失风格等），返回推荐物品的名称、图片、标签、描述等信息。

---

## 1. 获取衣橱活动度统计（必须实现）

### 接口信息

- **路径**：`GET /api/analysis/activity`
- **认证**：需要Token验证
- **说明**：返回本周与上周的穿搭活动对比数据，用于显示活动度百分比和趋势方向。

### 请求

#### Query 参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|--------|
| token | string | 是 | 用户认证令牌 | `"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."` |

#### 请求示例

```
GET /api/analysis/activity?token=xxx
```

### 响应

#### 成功（HTTP 200）

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 响应消息 |
| data | object | 活动度数据 |
| data.deltaPercent | number | 变化百分比（可正可负，如 15 表示 +15%，-8 表示 -8%） |
| data.trend | string | 趋势方向：`"increase"` 或 `"decrease"`（可选，前端可根据 deltaPercent 自行判断） |
| data.currentWeekCount | number | 本周穿搭记录数（最近7天） |
| data.lastWeekCount | number | 上周穿搭记录数（前7-14天） |
| status_code | number | HTTP状态码 |

**统计字段计算口径（重要）**：
- **数据来源**：基于日历记录（`/api/calendar/outfits`）或 wear 事件表统计本周和上周的记录数，而不是从衣橱表的 `wear_count` 字段统计（因为 `wear_count` 是累计值，无法区分本周/上周）
- **本周**：从今天往前推7天（包含今天）
- **上周**：从第8天往前推7天（即前7-14天）
- **变化百分比（deltaPercent）**：
  - 如果上周记录数 > 0：`((本周记录数 - 上周记录数) / 上周记录数) * 100`，四舍五入到整数（可正可负）
  - 如果上周记录数为 0：
    - 如果本周记录数 > 0：返回 `100`（表示从0增长到有记录）
    - 如果本周记录数也为 0：返回 `0`
- **趋势方向（trend）**：如果本周记录数 >= 上周记录数，则为 `"increase"`，否则为 `"decrease"`（可选字段，前端可根据 deltaPercent 自行判断）

#### 响应示例

```json
{
  "success": true,
  "message": "Success",
  "data": {
    "deltaPercent": 15,
    "trend": "increase",
    "currentWeekCount": 23,
    "lastWeekCount": 20
  },
  "status_code": 200
}
```

#### 错误（如 401、500）

与其他文档一致：`{ success: false, message: "...", status_code: ... }`

---

## 2. 获取闲置率统计（必须实现）

### 接口信息

- **路径**：`GET /api/analysis/idle-rate`
- **认证**：需要Token验证
- **说明**：返回未穿过的物品数量及总物品数，用于计算闲置率。

### 请求

#### Query 参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|--------|
| token | string | 是 | 用户认证令牌 | `"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."` |

#### 请求示例

```
GET /api/analysis/idle-rate?token=xxx
```

### 响应

#### 成功（HTTP 200）

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 响应消息 |
| data | object | 闲置率数据 |
| data.unwornCount | number | 未穿过的物品数量 |
| data.totalCount | number | 总物品数 |
| data.idleRate | number | 闲置率百分比（0-100，四舍五入到整数） |
| status_code | number | HTTP状态码 |

**统计字段计算口径（重要）**：
- **数据源**：**优先使用衣橱接口的 `last_worn_date` 和 `wear_count` 字段**（来自 `GET /api/clothing`），而不是从日历记录回溯计算
- **未穿过的物品**：`last_worn_date` 为 `null` 或 `wear_count` 为 0 的物品
- **总物品数**：用户衣橱中的所有物品数量（来自 `/api/clothing`）
- **闲置率**：`(unwornCount / totalCount) * 100`，四舍五入到整数

#### 响应示例

```json
{
  "success": true,
  "message": "Success",
  "data": {
    "unwornCount": 3,
    "totalCount": 106,
    "idleRate": 3
  },
  "status_code": 200
}
```

---

## 3. 获取总物品数统计（必须实现）

### 接口信息

- **路径**：`GET /api/analysis/total-items`
- **认证**：需要Token验证
- **说明**：返回历年物品总数统计，用于绘制折线图。支持按年/月/日维度查看。

### 请求

#### Query 参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|--------|
| token | string | 是 | 用户认证令牌 | `"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."` |
| viewBy | string | 否 | 查看维度：`"yearly"`（默认）、`"monthly"`、`"daily"` | `"yearly"` |

#### 请求示例

```
GET /api/analysis/total-items?token=xxx&viewBy=yearly
```

### 响应

#### 成功（HTTP 200）

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 响应消息 |
| data | object | 统计数据 |
| data.items | array | 统计项列表 |
| data.items[].label | string | 时间标签（如年份 "2016"、月份 "2024-01"、日期 "2024-01-15"） |
| data.items[].value | number | 该时间点的物品总数 |
| status_code | number | HTTP状态码 |

**统计字段计算口径（重要）**：
- **yearly**：返回历年（如2016-2023）每年的物品总数，统计该年年底时的物品总数
- **monthly**：返回近12个月每月的物品总数，统计该月月底时的物品总数
- **daily**：返回近30天每天的物品总数，统计该天结束时的物品总数

#### 响应示例

```json
{
  "success": true,
  "message": "Success",
  "data": {
    "items": [
      { "label": "2016", "value": 5 },
      { "label": "2017", "value": 12 },
      { "label": "2018", "value": 20 },
      { "label": "2019", "value": 18 },
      { "label": "2020", "value": 30 },
      { "label": "2021", "value": 60 },
      { "label": "2022", "value": 90 },
      { "label": "2023", "value": 106 }
    ]
  },
  "status_code": 200
}
```

---

## 4. 获取最常穿物品（必须实现）

### 接口信息

- **路径**：`GET /api/analysis/most-worn`
- **认证**：需要Token验证
- **说明**：返回穿着次数最多的物品列表，支持按年/月/日维度筛选。

### 请求

#### Query 参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|--------|
| token | string | 是 | 用户认证令牌 | `"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."` |
| viewBy | string | 否 | 查看维度：`"yearly"`（默认）、`"monthly"`、`"daily"` | `"yearly"` |
| limit | number | 否 | 返回数量（默认：5，最大：20） | `5` |

#### 请求示例

```
GET /api/analysis/most-worn?token=xxx&viewBy=yearly&limit=5
```

### 响应

#### 成功（HTTP 200）

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 响应消息 |
| data | object | 最常穿物品数据 |
| data.items | array | 物品列表（按穿着次数降序） |
| data.items[].id | number | 物品ID |
| data.items[].name | string | 物品名称 |
| data.items[].wears | number | 穿着次数（来自衣橱接口的 `wear_count` 字段） |
| data.items[].color | string | 颜色 code（用于前端显示颜色点，如 "white"、"blue"、"black"） |
| data.items[].image | string | 图片URL（统一使用 `image`，见字段映射说明） |
| status_code | number | HTTP状态码 |

**统计字段计算口径（重要）**：
- **数据源**：**优先使用衣橱接口的 `wear_count` 字段**（来自 `GET /api/clothing`），而不是从日历记录统计
- **yearly**：如果后端需要按年度筛选，可基于 `last_worn_date` 字段筛选本年度（从1月1日至今）的物品，然后按 `wear_count` 排序
- **monthly**：如果后端需要按月筛选，可基于 `last_worn_date` 字段筛选本月（从1日至今）的物品，然后按 `wear_count` 排序
- **daily**：如果后端需要按天筛选，可基于 `last_worn_date` 字段筛选今天（仅当天）的物品，然后按 `wear_count` 排序
- **注意**：如果 `wear_count` 是累计值（不分时间维度），后端可按 `wear_count` 直接排序，前端通过 `viewBy` 参数仅做展示筛选

#### 响应示例

```json
{
  "success": true,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "White Cotton T-shirt",
        "wears": 35,
        "color": "white",
        "image": "https://example.com/cloth_1.jpg"
      },
      {
        "id": 2,
        "name": "Classic Denim Jacket",
        "wears": 28,
        "color": "blue",
        "image": "https://example.com/cloth_2.jpg"
      },
      {
        "id": 3,
        "name": "Black Knit Top",
        "wears": 27,
        "color": "black",
        "image": "https://example.com/cloth_3.jpg"
      }
    ]
  },
  "status_code": 200
}
```

---

## 5. 获取最常用颜色和风格（必须实现）

### 接口信息

- **路径**：`GET /api/analysis/top-stats`
- **认证**：需要Token验证
- **说明**：返回最常用的颜色和风格及其占比。

### 请求

#### Query 参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|--------|
| token | string | 是 | 用户认证令牌 | `"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."` |

#### 请求示例

```
GET /api/analysis/top-stats?token=xxx
```

### 响应

#### 成功（HTTP 200）

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 响应消息 |
| data | object | 统计数据 |
| data.topColor | object | 最常用颜色 |
| data.topColor.name | string | 颜色名称（用于显示，如 "Brown"） |
| data.topColor.code | string | 颜色 code（用于前端映射，如 "brown"） |
| data.topColor.percent | number | 占比百分比（0-100，四舍五入到整数） |
| data.topStyle | object 或 null | 最常用风格（如果后端暂无风格数据，可返回 `null`；为 `null` 时前端显示空态） |
| data.topStyle.name | string | 风格名称（用于显示，如 "Sporty"） |
| data.topStyle.code | string | 风格 code（用于前端映射，如 "sporty"） |
| data.topStyle.percent | number | 占比百分比（0-100，四舍五入到整数） |
| status_code | number | HTTP状态码 |

**统计字段计算口径（重要）**：
- **最常用颜色**：统计所有物品的颜色分布，返回占比最高的颜色。如果物品有多个颜色（逗号分隔），按每个颜色分别计数。
- **最常用风格**：
  - **数据来源**：风格信息来自物品的 `tags` 字段（`tags` 为字符串数组 `string[]`，见 `MY_WARDROBE.md`）
  - 如果后端暂无风格数据或 `tags` 字段为空，`topStyle` 可返回 `null`
  - 统计所有物品的 `tags` 分布，返回占比最高的风格。如果物品有多个 `tags`，按每个 tag 分别计数
- **占比**：`(该颜色/风格的数量 / 总物品数) * 100`，四舍五入到整数

#### 响应示例

```json
{
  "success": true,
  "message": "Success",
  "data": {
    "topColor": {
      "name": "Brown",
      "code": "brown",
      "percent": 38
    },
    "topStyle": {
      "name": "Sporty",
      "code": "sporty",
      "percent": 45
    }
  },
  "status_code": 200
}
```

---

## 6. 获取分类统计（必须实现）

### 接口信息

- **路径**：`GET /api/analysis/category-breakdown`
- **认证**：需要Token验证
- **说明**：返回各分类的物品数量分布，用于绘制圆环图。

### 请求

#### Query 参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|--------|
| token | string | 是 | 用户认证令牌 | `"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."` |

#### 请求示例

```
GET /api/analysis/category-breakdown?token=xxx
```

### 响应

#### 成功（HTTP 200）

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 响应消息 |
| data | object | 分类统计数据 |
| data.categories | array | 分类列表 |
| data.categories[].label | string | 分类名称（用于显示，如 "Top"、"Bottom"） |
| data.categories[].value | number | 该分类的物品数量 |
| data.categories[].code | string | 展示分类 code（必填，统一使用：`"top"`、`"bottom"`、`"footwear"`、`"outerwear"`、`"accessories"`，用于前端映射颜色） |
| status_code | number | HTTP状态码 |

**统计字段计算口径（重要）**：
- **分类枚举来源**：分类枚举值来自 `GET /api/clothing/categories`（衣橱模块接口），不要写死新的枚举体系
- **分类映射规则**：根据物品的 `category` 字段（来自衣橱接口），在后端内部映射到展示分类（Top/Bottom/Footwear/Outerwear/Accessories）：
  - `top` 及其子分类（`t_shirt`、`blouse`、`shirt`、`sweater`、`vest` 等，具体见 `/api/clothing/categories` 的 `subcategories.top`）→ `label: "Top"`, `code: "top"`
  - `bottom` 及其子分类（`pants`、`jeans`、`shorts`、`skirt` 等，具体见 `/api/clothing/categories` 的 `subcategories.bottom`）→ `label: "Bottom"`, `code: "bottom"`
  - `shoes` 及其子分类（`sneakers`、`boots`、`sandals` 等）→ `label: "Footwear"`, `code: "footwear"`
  - `jacket`、`coat`、`outerwear` 等 → `label: "Outerwear"`, `code: "outerwear"`
  - `accessories` 及其子分类（`hat`、`bag`、`watch` 等）→ `label: "Accessories"`, `code: "accessories"`
- **数量统计**：统计每个分类下的物品总数
- **code 字段说明**：`code` 统一使用展示分类 code（`top`、`bottom`、`footwear`、`outerwear`、`accessories`），不要返回衣橱原始 `category` 值，前端根据 `code` 映射颜色
- **注意**：如果后端新增了分类枚举，映射规则需要相应更新

#### 响应示例

```json
{
  "success": true,
  "message": "Success",
  "data": {
    "categories": [
      { "label": "Top", "value": 35, "code": "top" },
      { "label": "Bottom", "value": 25, "code": "bottom" },
      { "label": "Footwear", "value": 10, "code": "footwear" },
      { "label": "Outerwear", "value": 15, "code": "outerwear" },
      { "label": "Accessories", "value": 15, "code": "accessories" }
    ]
  },
  "status_code": 200
}
```

**注意**：`code` 统一使用展示分类 code（`top`、`bottom`、`footwear`、`outerwear`、`accessories`），勿返回衣橱原始 `category`（如 `t_shirt`、`pants`），前端依 `code` 映射颜色。

---

## 7. 获取活动报告详情（可选）

### 接口信息

- **路径**：`GET /api/analysis/activity-report`
- **认证**：需要Token验证
- **说明**：返回活动报告的详细数据，包括每周趋势、每日穿着次数、各分类活动度等。

### 请求

#### Query 参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|--------|
| token | string | 是 | 用户认证令牌 | `"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."` |

#### 请求示例

```
GET /api/analysis/activity-report?token=xxx
```

### 响应

#### 成功（HTTP 200）

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 响应消息 |
| data | object | 活动报告数据 |
| data.deltaPercent | number | 变化百分比（与 Section 1 一致，可正可负） |
| data.isIncrease | boolean | 是否为增长趋势 |
| data.weekData | array | 本周每日穿着次数（7天） |
| data.weekData[].label | string | 日期标签（如 "Mon"、"Tue"） |
| data.weekData[].wears | number | 该天的穿着次数 |
| data.categoryActivity | array | 各分类活动度 |
| data.categoryActivity[].name | string | 分类名称（如 "Tops"、"Bottoms"） |
| data.categoryActivity[].count | number | 该分类在本周的穿着次数 |
| data.categoryActivity[].icon | string | 分类图标（如 "👕"、"👖"） |
| status_code | number | HTTP状态码 |

**统计字段计算口径（重要）**：
- **数据来源**：基于日历记录（`/api/calendar/outfits`）或 wear 事件表统计本周7天的每日记录数和各分类活动度
- **本周每日穿着次数**：统计本周7天（从今天往前推7天）每天的穿搭记录数
- **各分类活动度**：统计本周各分类的穿着次数，分类映射规则与 Section 6 一致（基于日历记录中的物品分类，映射到展示分类 code）

#### 响应示例

```json
{
  "success": true,
  "message": "Success",
  "data": {
    "deltaPercent": 15,
    "isIncrease": true,
    "weekData": [
      { "label": "Mon", "wears": 10 },
      { "label": "Tue", "wears": 16 },
      { "label": "Wed", "wears": 8 },
      { "label": "Thu", "wears": 18 },
      { "label": "Fri", "wears": 12 },
      { "label": "Sat", "wears": 24 },
      { "label": "Sun", "wears": 18 }
    ],
    "categoryActivity": [
      { "name": "Tops", "count": 42, "icon": "👕" },
      { "name": "Bottoms", "count": 28, "icon": "👖" },
      { "name": "Outerwear", "count": 15, "icon": "🧥" },
      { "name": "Footwear", "count": 12, "icon": "👟" },
      { "name": "Accessories", "count": 9, "icon": "⌚" }
    ]
  },
  "status_code": 200
}
```

---

## 8. 获取闲置物品列表（必须实现）

### 接口信息

- **路径**：`GET /api/analysis/idle-items`
- **认证**：需要Token验证
- **说明**：返回所有未穿过的物品列表，支持按时间和季节筛选。

### 请求

#### Query 参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|--------|
| token | string | 是 | 用户认证令牌 | `"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."` |
| timeFilter | string | 否 | 时间筛选：`"all"`（默认）、`"never"`（从未穿过）、`"over_year"`（超过一年未穿） | `"all"` |
| seasonFilter | string | 否 | 季节筛选：`"all"`（默认）、`"spring"`、`"summer"`、`"autumn"`、`"winter"` | `"all"` |
| page | number | 否 | 页码（默认：1） | `1` |
| pageSize | number | 否 | 每页数量（默认：20，最大：100） | `20` |

#### 请求示例

```
GET /api/analysis/idle-items?token=xxx&timeFilter=never&seasonFilter=summer
```

### 响应

#### 成功（HTTP 200）

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 响应消息 |
| data | object | 闲置物品数据 |
| data.items | array | 物品列表 |
| data.items[].id | number | 物品ID |
| data.items[].name | string | 物品名称 |
| data.items[].image | string | 图片URL（统一使用 `image`，见字段映射说明） |
| data.items[].color | string | 颜色 code |
| data.items[].category | string | 分类 code（与衣橱接口的 `category` 字段一致，如 "top"、"bottom"） |
| data.items[].season | string | 季节 code |
| data.items[].lastWorn | string | 最后穿着日期（YYYY-MM-DD），如果从未穿过则为 `null` |
| data.items[].status | object | 闲置状态 |
| data.items[].status.level | string | 状态级别：`"never"`（从未穿过）、`"over_year"`（超过一年未穿） |
| data.items[].status.label | string | 状态标签（如 "Never worn"、"Over a year ago"） |
| data.pagination | object | 分页信息 |
| data.pagination.page | number | 当前页码 |
| data.pagination.pageSize | number | 每页数量 |
| data.pagination.total | number | 总数量 |
| data.pagination.totalPages | number | 总页数 |
| status_code | number | HTTP状态码 |

**统计字段计算口径（重要）**：
- **从未穿过**：`lastWorn` 为 `null` 的物品
- **超过一年未穿**：`lastWorn` 距离今天超过365天的物品
- **最后穿着日期**：从日历记录中查找该物品最后一次出现的日期

#### 响应示例

```json
{
  "success": true,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": 10,
        "name": "Olive Cargo Pants",
        "image": "https://example.com/cloth_10.jpg",
        "color": "olive",
        "category": "bottom",
        "season": "autumn",
        "lastWorn": null,
        "status": {
          "level": "never",
          "label": "Never worn"
        }
      },
      {
        "id": 11,
        "name": "Navy Blazer",
        "image": "https://example.com/cloth_11.jpg",
        "color": "navy",
        "category": "outerwear",
        "season": "winter",
        "lastWorn": null,
        "status": {
          "level": "never",
          "label": "Never worn"
        }
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 3,
      "totalPages": 1
    }
  },
  "status_code": 200
}
```

---

## 9. 获取推荐添加（必须实现）

### 接口信息

- **路径**：`GET /api/analysis/suggested-additions`
- **认证**：需要Token验证
- **说明**：基于用户现有衣橱，返回推荐可添加的物品列表。**MVP阶段可使用简单推荐规则（如基于颜色互补、风格缺失、季节需求等），无需复杂的AI算法**。

### 请求

#### Query 参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|--------|
| token | string | 是 | 用户认证令牌 | `"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."` |
| limit | number | 否 | 返回数量（默认：3，最大：10） | `3` |

#### 请求示例

```
GET /api/analysis/suggested-additions?token=xxx&limit=3
```

### 响应

#### 成功（HTTP 200）

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 响应消息 |
| data | object | 推荐数据 |
| data.items | array | 推荐物品列表 |
| data.items[].name | string | 物品名称 |
| data.items[].image | string | 图片URL（可选，可以是占位图） |
| data.items[].tags | array | 标签列表（如 ["Warm Layer", "Minimal"]） |
| data.items[].desc | string | 推荐描述 |
| status_code | number | HTTP状态码 |

**设计说明**：
- **MVP阶段**：可使用简单推荐规则（如基于颜色互补、风格缺失、季节需求、分类平衡等），返回3-5条推荐数据即可
- **推荐逻辑示例**：
  - 如果用户缺少某种颜色（如棕色），推荐该颜色的物品
  - 如果用户某个分类物品较少（如 Outerwear），推荐该分类的物品
  - 如果当前季节（如冬季）缺少相应季节的物品，推荐该季节的物品
- **未来扩展**：可逐步引入更复杂的推荐算法（如AI推荐、搭配推荐等）
- **如果暂无推荐逻辑**：可返回空数组 `[]`，前端会显示空状态（不显示推荐卡片）

#### 响应示例

```json
{
  "success": true,
  "message": "Success",
  "data": {
    "items": [
      {
        "name": "Cream Knit Sweater",
        "image": "https://example.com/suggested_1.jpg",
        "tags": ["Warm Layer", "Minimal"],
        "desc": "Complements your white cotton tees; provides a clean seasonal outer layer. Pairs with 3 items in your wardrobe."
      },
      {
        "name": "Dark Denim Overshirt",
        "image": "https://example.com/suggested_2.jpg",
        "tags": ["Layering", "Versatile"],
        "desc": "Pairs well with the classic denim jacket; adds structure and versatility for casual or smart-casual looks."
      }
    ]
  },
  "status_code": 200
}
```

---

## 10. 通用响应格式与状态码

所有接口应遵循统一的响应格式：

**成功响应格式**：

```json
{
  "success": true,
  "message": "Success",
  "data": { ... },
  "status_code": 200
}
```

**错误响应格式**：

```json
{
  "success": false,
  "message": "错误描述",
  "status_code": 400
}
```

### 状态码说明

| code | 说明 | HTTP 状态码 |
|------|------|------------|
| 200 | 成功 | 200 |
| 400 | 请求参数错误 | 400 |
| 401 | 未授权（需要登录/Token 无效） | 401 |
| 403 | 禁止访问 | 403 |
| 404 | 资源不存在 | 404 |
| 500 | 服务器内部错误 | 500 |

---

## 11. 接口实现优先级

### 必须实现（MVP）

以下接口为分析模块的核心功能，必须实现：

1. **Section 1：获取衣橱活动度统计** - 用于显示活动度卡片
2. **Section 2：获取闲置率统计** - 用于显示闲置率卡片
3. **Section 3：获取总物品数统计** - 用于显示折线图
4. **Section 4：获取最常穿物品** - 用于显示最常穿列表
5. **Section 5：获取最常用颜色和风格** - 用于显示 Top Color/Style 卡片
6. **Section 6：获取分类统计** - 用于显示圆环图
7. **Section 8：获取闲置物品列表** - 用于展开视图
8. **Section 9：获取推荐添加** - 用于显示推荐卡片（MVP阶段可使用简单推荐规则，返回空数组也可接受）

### 可选实现

以下接口为增强功能，可选实现：

1. **Section 7：获取活动报告详情** - 如果未实现，前端可使用 Section 1 的数据自行计算

---

## 12. 数据关联说明

### 与已实现模块的接口复用

分析模块需要复用以下已实现的接口：

1. **衣橱模块（MY_WARDROBE.md）**：
   - **接口路径**：`GET /api/clothing`（与 `MY_WARDROBE.md` 一致）
     - ⚠️ **如果后端实际实现的是其他路径**（如 `/api/wardrobe/clothes`），请将所有 `/api/clothing` 替换为实际路径
   - `GET /api/clothing`：获取所有物品列表，用于统计总物品数、分类分布、颜色/风格分布等
   - 物品字段：`id`、`name`、`image_url`、`category`、`color`、`season`、`tags`（字符串数组）、`last_worn_date`、`wear_count`、`created_at` 等
   - `GET /api/clothing/categories`：获取分类枚举选项（`categories`、`subcategories`），用于分类映射规则
   - `POST /api/clothing/{id}/record-wear`：记录衣物穿着，更新 `wear_count` 和 `last_worn_date`（该接口已在 `MY_WARDROBE.md` Section 1.7 中定义）
   - **字段映射**：
     - `image_url` → `image`：分析模块统一返回 `image`，后端可从衣橱的 `image_url` 映射（或前端自行映射）
     - `category` → `category`：**统一使用 `category` 字段**，不要引入新的 `type` 字段
   - **数据源统一口径**：
     - **物品统计**（闲置率、最常穿、闲置列表）：优先使用衣橱表的 `wear_count`、`last_worn_date`、`created_at` 字段
     - **活动度统计**（活动度、活动报告）：基于日历记录（`/api/calendar/outfits`）或 wear 事件表统计本周/上周的记录数（因为需要区分本周/上周，不能使用累计的 `wear_count`）
     - **前提条件**：后端在写入日历穿搭时，需同步更新衣橱表的 `wear_count` 和 `last_worn_date`（或通过 `POST /api/clothing/{id}/record-wear` 更新），确保数据一致性

2. **日历模块（MY_CALENDAR.md）**：
   - `GET /api/calendar/outfits`：获取穿搭记录，**仅用于活动度统计**（统计本周和上周的记录数）
   - 记录字段：`date`、`items[]`（包含 `id`、`name`、`image` 等）
   - **注意**：活动度统计需要区分本周/上周，因此基于日历记录统计；物品的 `wear_count` 和 `last_worn_date` 应在写入日历时同步更新

**数据计算依赖**（与上方「数据源统一口径」一致）：活动度/活动报告用日历或 wear 事件；闲置率、最常穿、闲置列表用衣橱表 `wear_count`/`last_worn_date`/`created_at`；分类统计用衣橱 `category` 并映射到展示 code。

### 字段映射说明

| 衣橱模块字段 | 分析模块字段 | 说明 |
|------------|------------|------|
| `image_url` | `image` | 图片URL字段，**分析模块统一返回 `image`**，后端可从衣橱的 `image_url` 映射（或前端自行映射） |
| `category` | `category` | **统一使用 `category` 字段**，不要引入新的 `type` 字段。枚举值来自 `GET /api/clothing/categories` |
| `wear_count` | `wears` | **优先使用**：分析模块的"最常穿物品"直接使用衣橱的 `wear_count` 字段 |
| `last_worn_date` | `lastWorn` | **优先使用**：分析模块的"闲置物品"直接使用衣橱的 `last_worn_date` 字段 |

（数据源优先级与分类枚举约定见本 Section 上方「与已实现模块的接口复用」。）

---

## 13. 安全与校验建议

1. **鉴权**：所有分析相关接口应校验用户身份（如 JWT），token 缺失或无效时返回 401。
2. **归属**：所有统计数据应仅基于当前用户的数据，不允许访问其他用户的数据。
3. **参数校验**：
   - `viewBy` 参数应严格校验，只允许 `"yearly"`、`"monthly"`、`"daily"` 三个值
   - `timeFilter` 参数应严格校验，只允许 `"all"`、`"never"`、`"over_year"` 三个值
   - `seasonFilter` 参数应严格校验，只允许 `"all"`、`"spring"`、`"summer"`、`"autumn"`、`"winter"` 五个值
   - `limit`、`page`、`pageSize` 参数应校验范围，避免过大值导致性能问题
4. **性能优化**：
   - 统计数据可考虑缓存，避免每次请求都重新计算
   - 对于大数据量的统计（如历年数据），可考虑异步计算或预计算
5. **错误处理**：如果依赖的接口（如 `/api/clothing`、`/api/calendar/outfits`）返回错误，应返回适当的错误信息，而不是直接抛出异常。

---

## 14. 联系方式

如有疑问，请联系前端开发团队。

**文档版本**：v1.0  
**最后更新**：2026-02-12

---

## 附录 A：统计字段计算口径（详细说明）

### A.1 活动度统计（Section 1）

口径详见 **Section 1「统计字段计算口径」**（数据来源、本周/上周定义、deltaPercent 与 trend 计算规则）。

### A.2 闲置率统计（Section 2）

- **数据源**：与 Section 2 一致，优先使用衣橱表的 `last_worn_date` 和 `wear_count`
- **未穿过的物品**：`last_worn_date` 为 `null` 或 `wear_count` 为 0 的物品
- **总物品数**：用户衣橱中的所有物品数量（来自 `/api/clothing`）
- **闲置率**：`(unwornCount / totalCount) * 100`，四舍五入到整数

### A.3 总物品数统计（Section 3）

- 时间维度与统计口径见 **Section 3「统计字段计算口径」**。
- **数据依据**：依赖衣橱表 `created_at`（及 `deleted_at`/`is_deleted` 若支持软删除）。若无历史字段，可返回 `[]` 或仅当前总数，前端降级显示。

### A.4 最常穿物品（Section 4）

数据源与 viewBy 维度口径见 **Section 4「统计字段计算口径」**。

### A.5 最常用颜色和风格（Section 5）

口径见 **Section 5「统计字段计算口径」**。风格来自 `tags`（`string[]`），无数据时 `topStyle` 可返回 `null`。

### A.6 分类统计（Section 6）

分类枚举来源、映射规则及 `code` 约定见 **Section 6「统计字段计算口径」**。后端只返回 `label`/`value`/`code`，颜色由前端依 `code` 映射。

### A.7 闲置物品状态（Section 8）

数据源与 never/over_year 定义见 **Section 8「统计字段计算口径」**。

---

## 附录 B：前端调用对照表

### B.1 首屏必需接口（进入分析页面时并行调用）

以下接口在用户进入分析页面时**必须同时调用**，用于渲染首屏的所有卡片：

| 接口 | 用途 | 优先级 |
|------|------|--------|
| `GET /api/analysis/activity` | 活动度卡片（左上） | **必须** |
| `GET /api/analysis/idle-rate` | 闲置率卡片（中上） | **必须** |
| `GET /api/analysis/total-items?viewBy=yearly` | 总物品数折线图（右上） | **必须** |
| `GET /api/analysis/most-worn?viewBy=yearly` | 最常穿物品列表（左中） | **必须** |
| `GET /api/analysis/top-stats` | Top Color/Style 卡片（中中） | **必须** |
| `GET /api/analysis/category-breakdown` | 分类统计圆环图（右下） | **必须** |
| `GET /api/analysis/suggested-additions` | 推荐添加卡片（左下） | **必须**（MVP阶段可使用简单规则） |

### B.2 交互触发接口（用户操作时调用）

| 前端操作 | 使用的接口 | 触发时机 |
|----------|------------|----------|
| 切换总物品数维度（Yearly/Monthly/Daily） | `GET /api/analysis/total-items?viewBy={viewBy}` | 点击 Total Items 卡片的筛选下拉 |
| 切换最常穿物品维度（Yearly/Monthly/Daily） | `GET /api/analysis/most-worn?viewBy={viewBy}` | 点击 Most Worn Items 卡片的筛选下拉 |
| 点击活动度卡片展开报告 | `GET /api/analysis/activity-report` | 点击 "Activity report →" 链接 |
| 点击闲置率卡片展开列表 | `GET /api/analysis/idle-items?timeFilter=all&seasonFilter=all` | 点击 "See all idle items →" 链接 |
| 筛选闲置物品（时间/季节） | `GET /api/analysis/idle-items?timeFilter={timeFilter}&seasonFilter={seasonFilter}` | 在 Idle Items 展开视图中切换筛选条件 |

### B.3 参数说明

- **`viewBy`**：`"yearly"`（默认）、`"monthly"`、`"daily"`，用于切换时间维度
- **`timeFilter`**：`"all"`（默认）、`"never"`（从未穿过）、`"over_year"`（超过一年未穿）
- **`seasonFilter`**：`"all"`（默认）、`"spring"`、`"summer"`、`"autumn"`、`"winter"`

---

## 附录 C：测试用例

### C.1 活动度统计接口测试

| 测试场景 | 请求参数 | 预期结果 |
|---------|---------|---------|
| 正常请求 | token: 有效token | 返回 200，包含 deltaPercent、trend、currentWeekCount、lastWeekCount |
| Token无效 | token: 无效token | 返回 401 |
| Token缺失 | 无token参数 | 返回 401 |

### C.2 闲置率统计接口测试

| 测试场景 | 请求参数 | 预期结果 |
|---------|---------|---------|
| 正常请求 | token: 有效token | 返回 200，包含 unwornCount、totalCount、idleRate |
| 无闲置物品 | token: 有效token（所有物品都穿过） | 返回 unwornCount: 0，idleRate: 0 |
| 全部闲置 | token: 有效token（所有物品都未穿过） | 返回 unwornCount: totalCount，idleRate: 100 |

### C.3 最常穿物品接口测试

| 测试场景 | 请求参数 | 预期结果 |
|---------|---------|---------|
| 正常请求（yearly） | token: 有效token, viewBy: "yearly" | 返回 200，items 按 wears 降序排列 |
| 切换维度（monthly） | token: 有效token, viewBy: "monthly" | 返回 200，统计本月数据 |
| 无效维度 | token: 有效token, viewBy: "invalid" | 返回 400，提示参数错误 |
| 限制数量 | token: 有效token, limit: 10 | 返回最多10条数据 |

### C.4 闲置物品列表接口测试

| 测试场景 | 请求参数 | 预期结果 |
|---------|---------|---------|
| 正常请求 | token: 有效token | 返回 200，包含 items 列表和 pagination |
| 筛选从未穿过 | token: 有效token, timeFilter: "never" | 返回 status.level 为 "never" 的物品 |
| 筛选超过一年 | token: 有效token, timeFilter: "over_year" | 返回 status.level 为 "over_year" 的物品 |
| 筛选季节 | token: 有效token, seasonFilter: "summer" | 返回 season 为 "summer" 的物品 |
| 分页 | token: 有效token, page: 2, pageSize: 10 | 返回第2页数据 |

---

## 附录 D：与已实现模块的接口复用说明

**数据源口径、字段映射及前提条件**均见 **Section 12「数据关联说明」**，此处仅列调用用途。

### D.1 复用衣橱模块接口

- **`GET /api/clothing`**：总物品数、分类/颜色/风格分布、闲置判断（`last_worn_date`/`wear_count`）、最常穿排序（`wear_count`）。
- **`GET /api/clothing/categories`**：分类枚举与映射规则。
- **`POST /api/clothing/{id}/record-wear`**：记录穿着并更新 `wear_count`、`last_worn_date`。

### D.2 复用日历模块接口

- **`GET /api/calendar/outfits`**：仅用于**活动度统计**（本周/上周记录数）及**活动报告**（每日次数、各分类活动度）。最常穿与闲置判断以衣橱表为准，见 Section 12。

### D.3 接口调用顺序建议

1. **进入分析页面时**：可并行调用所有统计接口（Section 1-6、8、9）
2. **展开活动报告时**：调用 Section 7（如果实现）或使用 Section 1 数据自行计算
3. **展开闲置物品列表时**：调用 Section 8
4. **获取推荐添加时**：调用 Section 9（必须实现，MVP阶段可使用简单规则，返回空数组也可接受）
