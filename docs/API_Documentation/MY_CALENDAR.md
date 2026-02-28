# API 文档 - 日历穿搭记录模块（Vue3 + UniApp）

## 概述

本文档描述前端 **My Calendar** 功能（`pages/index/components/MyCalendar/MyCalendar.vue`）所需的 API 约定：**每日穿搭记录** 的查询、新增、修改、删除，以及**月度统计**和**连续记录天数（Streak）**的计算。

**文档结构**：
- **Section 1-5**：API 接口（核心接口 + 可选接口）
- **Section 6**：通用响应格式与状态码
- **Section 7**：接口实现优先级
- **Section 8**：数据关联说明
- **Section 9**：安全与校验建议
- **Section 10**：联系方式
- **附录**：补充内容（统计字段计算口径、前端调用对照表、前端处理逻辑说明、测试用例、接口复用说明）

**文档参考**：
- 本文档参考并复用了 `LOGIN_REGISTER.md` 和 `MY_WARDROBE.md` 的接口设计规范
- **响应格式**：与 `LOGIN_REGISTER.md`、`MY_WARDROBE.md` 保持一致（`{ success, message, data, status_code }`）
- **认证方式**：与已实现模块一致，通过 query 参数 `token` 传递 JWT Token
- **基础 URL**：与已实现模块一致，使用 `http://localhost:8000`
- **接口复用**：日历模块复用衣橱模块的 `GET /api/clothing` 接口获取衣物列表（详见 Section 8 和附录）

**基础 URL**：`http://localhost:8000`

**接口路径说明**：本文档中所有接口均写为完整路径（例如 `GET /api/calendar/outfits`），无需再拼接额外前缀。

**认证方式**：JWT Token（通过 query 参数 `token` 传递）

**请求格式**：`application/json`

**响应格式**：`application/json`

---

## 功能概要（供后端理解）

| 模块 | 说明 |
|------|------|
| **日历视图** | 以日历形式展示每日穿搭记录。用户可切换月份查看历史记录，点击日期查看或编辑当天的穿搭。日历上会标记有记录的日期（显示圆点），hover 时显示预览。 |
| **每日穿搭记录** | 每个日期可记录多个单品（outfit items），每个单品包含：id、name、image、accentColor（可选）。用户可添加、删除单个单品，或清除当天所有记录。 |
| **月度统计** | 显示当前查看月份的数据：`daysRecorded`（有记录的天数）、`uniqueItems`（不重复单品数，同一件衣服在不同日期只算1次）。 |
| **连续记录天数（Streak）** | 计算从今天（或查看月份的最后一天）往前连续有记录的天数，用于激励用户持续记录。**重要**：`currentStreak` 的计算范围仅限当前请求的月份（year+month）内。跨月不连续，月初前一天不计入。 |

**数据结构约定**：
- 日期格式：`YYYY-MM-DD`（如 `"2025-02-09"`）
- 每个日期对应一个数组，包含该天的所有穿搭单品
- 每个单品对象包含：`id`（必填）、`name`（可选，后端可补齐）、`image`（可选，后端可补齐）、`accentColor`（可选，用于 UI 展示）
- 响应时保证返回完整字段（id、name、image、accentColor），无论存储方式如何

---

## 与后端交互概览（自然语言）

**日历数据获取**
- **进入日历页面、切换月份**：前端会向你要「当前用户指定月份的穿搭记录」，返回 `data.outfits`，其结构为 `{ "YYYY-MM-DD": items[] }` 的映射（仅包含有记录的日期）。你需要按月份范围查询并返回该月所有有记录的日期及其单品列表。
- **月度统计**：前端会根据返回的数据计算 `daysRecorded` 和 `uniqueItems`，但后端也可在响应中直接提供这些统计数据（可选，前端可自行计算）。

**每日穿搭操作**
- **用户添加/修改某天的穿搭**：前端会把选中的单品列表（来自衣橱）发给你，你保存该日期与这些单品的关联关系。如果该日期已有记录，则**全量覆盖**（替换）原有记录。这是**核心接口**，所有写操作都通过此接口完成。
- **用户删除某天的某个单品**：前端可以通过两种方式实现：
  1. **推荐方式**：前端从当前 items 中 filter 掉要删除的 item，然后调用 POST 接口全量覆盖（保持接口一致性）。
  2. **可选便捷接口**：后端可提供 `DELETE /api/calendar/outfits/{date}/items/{itemId}` 接口作为便捷方式，但非必需。
- **用户清除某天的所有穿搭**：前端调用 POST 接口，传入 `items: []`（空数组）即可删除该日期的所有记录。

**连续记录天数（Streak）**
- 前端会根据返回的数据自行计算，但后端也可提供该数据（可选）。计算规则：从今天（或查看月份的最后一天）往前倒推，连续有记录的天数。
- **重要口径声明**：`currentStreak` 的计算范围仅限当前请求的月份（year+month）内。跨月不连续，月初前一天不计入。

---

## 1. 获取指定月份的穿搭记录

### 接口信息

- **路径**：`GET /api/calendar/outfits`
- **认证**：需要Token验证
- **说明**：返回当前用户指定月份的每日穿搭记录。返回 `data.outfits`，其结构为 `{ "YYYY-MM-DD": items[] }` 的映射（仅包含有记录的日期）。

### 请求

#### Query 参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|--------|
| token | string | 是 | 用户认证令牌 | `"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."` |
| year | number | 是 | 年份（如 2025） | `2025` |
| month | number | 是 | 月份（1-12，1 表示一月） | `2` |

**注意**：`month` 参数使用 **1-12** 的格式（1=一月，12=十二月），而非 JavaScript 的 0-11 格式。

#### 请求示例

```
GET /api/calendar/outfits?token=xxx&year=2025&month=2
```

### 响应

#### 成功（HTTP 200）

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 提示信息，如 "Success" |
| data | object | - |
| data.outfits | object | 日期到单品数组的映射，key 为 `YYYY-MM-DD`，value 为单品数组 |
| data.monthStats | object | （可选）月度统计数据，若后端不实现，前端可自行计算 |
| data.monthStats.daysRecorded | number | 该月有记录的天数（计算口径见下方） |
| data.monthStats.uniqueItems | number | 该月不重复单品数（计算口径见下方） |
| data.currentStreak | number | （可选）连续记录天数（计算口径见下方） |
| status_code | number | HTTP 状态码（200） |

**统计字段计算口径（重要）**：

即使后端不实现这些字段，前端也会按此口径计算。后端若实现，必须遵循相同口径，确保前后端一致：

- **daysRecorded**：本月 `outfits` 中 `items.length > 0` 的日期数量
- **uniqueItems**：本月内按 `item.id` 去重的数量（**必须用 id 去重，不要用 name 去重，避免冲突**）
- **currentStreak**：从当月今天（或查看月份的最后一天）往前倒推，连续有记录的天数，遇到空日期即断开。**计算范围仅限当前请求的月份（year+month）内，跨月不连续，月初前一天不计入**。

**单品对象结构**

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|--------|
| id | number 或 string | 单品唯一 id（通常来自衣橱中的衣服 id） | `1` |
| name | string | 单品名称 | `"Basic White Tee"` |
| image | string | 图片 URL（绝对或相对） | `"https://..."` 或 `"/files/xxx.jpg"` |
| accentColor | string | （可选）主题色（用于 UI 展示），十六进制颜色值 | `"#8d6e63"` |

#### 响应示例

```json
{
  "success": true,
  "message": "Success",
  "data": {
    "outfits": {
      "2025-02-09": [
        {
          "id": 1,
          "name": "Basic White Tee",
          "image": "http://localhost:8000/uploads/1/clothing_abc123.jpg",
          "accentColor": "#8d6e63"
        },
        {
          "id": 5,
          "name": "Black Jeans",
          "image": "http://localhost:8000/uploads/1/clothing_def456.jpg",
          "accentColor": "#1d1d1f"
        }
      ],
      "2025-02-10": [
        {
          "id": 2,
          "name": "Summer Dress",
          "image": "http://localhost:8000/uploads/1/clothing_ghi789.jpg"
        }
      ]
    },
    "monthStats": {
      "daysRecorded": 2,
      "uniqueItems": 3
    },
    "currentStreak": 5
  },
  "status_code": 200
}
```

**说明**：
- `outfits` 对象只包含**有记录的日期**，没有记录的日期不需要出现在对象中。
- 如果某个月份完全没有记录，返回 `outfits: {}`（空对象）。
- `monthStats` 和 `currentStreak` 为可选字段，前端可自行计算，但后端提供可减少前端计算负担。

#### 错误响应

| HTTP 状态码 | success | message | 说明 |
|------------|---------|---------|------|
| 400 | false | "请求参数错误" | year 或 month 参数缺失或格式错误 |
| 401 | false | "未授权" | token 无效或缺失 |
| 500 | false | "服务器内部错误" | 服务器异常 |

**错误响应示例**：

```json
{
  "success": false,
  "message": "未授权",
  "status_code": 401
}
```

---

## 2. 保存或更新某天的穿搭记录（必须实现）

### 接口信息

- **路径**：`POST /api/calendar/outfits`
- **认证**：需要Token验证
- **实现优先级**：**必须实现**（MVP 核心接口）
- **说明**：用于保存、更新或删除指定日期的穿搭记录。采用**全量覆盖**模式：
  - 如果该日期已有记录，则**全量覆盖**（替换）原有记录
  - 如果传入空数组 `items: []`，则删除该日期的记录
  - 前端删除单个单品时，应从当前 items 中 filter 掉要删除的 item，然后调用此接口覆盖

**设计说明**：此接口采用全量覆盖模式，确保后端只需维护一套写逻辑，前端状态管理更简单一致。删除操作也通过此接口实现（传入过滤后的 items 或空数组）。后端可以先实现此接口完成 MVP，后续可选实现 DELETE 便捷接口。

**补齐规则（当仅传 id 时）**：
- 若 item 仅包含 `{ id }`，后端需从当前用户的衣橱数据中查找该 `clothing_id` 对应的 `name`、`image_url`（映射为 `image`）等字段，并在响应中补齐返回。
- 若该 id 不存在，或不属于当前用户：建议返回 404（"衣橱中不存在该单品"）或 403（"禁止访问"），二者择一并保持全项目一致。

**并发/覆盖策略（MVP）**：
- 同一用户同一日期的多次提交采用 **Last write wins**（最后一次提交覆盖前一次），不做版本冲突校验。
- 后端无需实现乐观锁或版本号机制，直接覆盖即可。

### 请求

#### Query 参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|--------|
| token | string | 是 | 用户认证令牌 | `"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."` |

#### Body 参数（JSON）

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| date | string | 是 | 日期（`YYYY-MM-DD`） | `"2025-02-09"` |
| items | array | 是 | 单品数组（可为空数组，表示删除该日期记录） | `[{ id, name, image, accentColor? }]` |

**单品对象结构（Body）**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | number 或 string | **是** | 单品 id（clothing_id，来自衣橱中的衣服 id） |
| name | string | **否** | 单品名称（前端愿意传就传；后端可选择存快照或在写时从衣橱表 join 补齐） |
| image | string | **否** | 图片 URL（前端愿意传就传；后端可选择存快照或在写时从衣橱表 join 补齐） |
| accentColor | string | **否** | 主题色（十六进制颜色值，可选） |

**设计说明**：
- **id 必填**：用于关联衣橱中的衣服记录
- **name/image/accentColor 可选**：前端愿意传就传，后端可以选择：
  - **方式1（快照存储）**：存储前端传入的完整信息，保证历史记录独立性
  - **方式2（写时补齐）**：仅存储 id，响应时从衣橱表 join 补齐 name/image 等信息
- **响应保证**：无论后端采用哪种方式，响应时必须返回完整的字段（id、name、image、accentColor），保证前端渲染稳定

#### 请求示例

**添加/更新某天的穿搭**

```json
{
  "date": "2025-02-09",
  "items": [
    {
      "id": 1,
      "name": "Basic White Tee",
      "image": "https://example.com/files/cloth_1.jpg",
      "accentColor": "#8d6e63"
    },
    {
      "id": 5,
      "name": "Black Jeans",
      "image": "https://example.com/files/cloth_5.jpg"
    }
  ]
}
```

**删除某天的记录（传入空数组）**

```json
{
  "date": "2025-02-09",
  "items": []
}
```

**删除单个单品（通过 POST 全量覆盖实现）**

假设当前该日期有 3 个单品 `[item1, item2, item3]`，要删除 `item2`（id=2），前端应：

1. 从当前 items 中 filter 掉要删除的 item：`items.filter(item => item.id !== 2)`
2. 调用 POST 接口覆盖：

```json
{
  "date": "2025-02-09",
  "items": [
    {
      "id": 1,
      "name": "Basic White Tee",
      "image": "http://localhost:8000/uploads/1/clothing_abc123.jpg",
      "accentColor": "#8d6e63"
    },
    {
      "id": 3,
      "name": "Summer Dress",
      "image": "http://localhost:8000/uploads/1/clothing_ghi789.jpg"
    }
  ]
}
```

这样即可删除 id=2 的单品，保持接口设计一致性。

### 响应

#### 成功（HTTP 200）

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 提示信息，如 "Saved" 或 "Deleted" |
| data | object | - |
| data.date | string | 日期（`YYYY-MM-DD`） |
| data.items | array | 保存后的单品数组（删除时为空数组） |
| status_code | number | HTTP状态码（200） |

#### 响应示例

**保存成功**

```json
{
  "success": true,
  "message": "Saved",
  "data": {
    "date": "2025-02-09",
    "items": [
      {
        "id": 1,
        "name": "Basic White Tee",
        "image": "http://localhost:8000/uploads/1/clothing_abc123.jpg",
        "accentColor": "#8d6e63"
      },
      {
        "id": 5,
        "name": "Black Jeans",
        "image": "http://localhost:8000/uploads/1/clothing_def456.jpg"
      }
    ]
  },
  "status_code": 200
}
```

**删除成功（传入空数组）**

```json
{
  "success": true,
  "message": "Deleted",
  "data": {
    "date": "2025-02-09",
    "items": []
  },
  "status_code": 200
}
```

#### 错误响应

| HTTP 状态码 | success | message | 说明 |
|------------|---------|---------|------|
| 400 | false | "日期格式不正确" | date 格式错误 |
| 400 | false | "items 必须为数组" | items 类型错误 |
| 400 | false | "单品 id 不能为空" | 某个 item 缺少 id（id 为必填字段） |
| 401 | false | "未授权" | token 无效或缺失 |
| 403 | false | "禁止访问" | item.id 不属于当前用户（推荐校验，与 404 择一使用） |
| 404 | false | "衣橱中不存在该单品" | item.id 不存在或不属于当前用户（推荐校验，与 403 择一使用） |
| 500 | false | "服务器内部错误" | 服务器异常 |

**注意**：
- `name` 和 `image` 为可选字段，前端不传时后端不应报错。后端可以选择存快照（存储前端传入的值）或在响应时从衣橱表 join 补齐。
- **推荐校验**：当 item 仅传 `id` 时，后端应校验该 `id` 是否存在且属于当前用户。若不存在或不属于当前用户，返回 404 或 403（二者择一并保持全项目一致）。

---

## 3. 删除某天的某个单品（可选便捷接口）

- **路径**：`DELETE /api/calendar/outfits/{date}/items/{itemId}`
- **实现优先级**：**可选实现**（便捷接口，非必需）
- **说明**：删除指定日期的指定单品。**推荐后端先实现 POST 接口（Section 2）完成 MVP**，此接口可选实现。
- **请求**：Path 参数 `date`（YYYY-MM-DD）、`itemId`；Query 参数 `token`
- **响应**：`{ success: true, data: { date, items: [] } }`（items 为空数组表示该日期已无记录）
- **错误**：404（日期无记录/单品不存在）、401、500

---

## 4. 清除某天的所有穿搭记录（可选便捷接口）

- **路径**：`DELETE /api/calendar/outfits/{date}`
- **实现优先级**：**可选实现**（便捷接口，非必需）
- **说明**：删除指定日期的所有穿搭记录。**推荐后端先实现 POST 接口（Section 2）完成 MVP**，此接口可选实现。
- **请求**：Path 参数 `date`（YYYY-MM-DD）；Query 参数 `token`
- **响应**：`{ success: true, data: { date, items: [] } }`
- **错误**：404（日期无记录，可选）、401、500

---

## 5. 获取月度统计（可选）

- **路径**：`GET /api/calendar/stats`
- **实现优先级**：**可选实现**（前端可自行计算）
- **说明**：获取指定月份的统计数据。前端可根据 `/api/calendar/outfits` 返回的数据自行计算。**若后端实现此接口，必须遵循附录中的计算口径，确保前后端一致**。
- **请求**：Query 参数 `token`、`year`、`month`（1-12）
- **响应**：`{ success: true, data: { year, month, daysRecorded, uniqueItems, currentStreak } }`
- **计算口径**：详见附录 A.2

---

## 6. 通用响应格式与状态码

与 `LOGIN_REGISTER.md`、`MY_WARDROBE.md` 一致：

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

| status_code | 含义 | HTTP |
|-------------|------|------|
| 200 | 成功 | 200 |
| 400 | 请求错误 | 400 |
| 401 | 未授权 | 401 |
| 403 | 禁止访问 | 403 |
| 404 | 未找到 | 404 |
| 500 | 服务器错误 | 500 |

---

## 7. 接口实现优先级

### 必须实现的接口（MVP）

| 接口 | 说明 |
|------|------|
| `GET /api/calendar/outfits` | 获取指定月份的穿搭记录（Section 1） |
| `POST /api/calendar/outfits` | 保存/更新/删除某天的穿搭记录（Section 2） |

### 可选实现的接口

| 接口 | 说明 |
|------|------|
| `DELETE /api/calendar/outfits/{date}/items/{itemId}` | 删除某天的某个单品（Section 3） |
| `DELETE /api/calendar/outfits/{date}` | 清除某天的所有记录（Section 4） |
| `GET /api/calendar/stats` | 获取月度统计（Section 5） |

**说明**：后端可以先实现必须接口完成 MVP，后续按需实现可选接口。删除操作可通过 POST 全量覆盖实现（详见 Section 2）。

---

## 8. 数据关联说明

### 与衣橱模块的关系

- **单品来源**：日历中的单品（outfit items）通常来自用户的衣橱（`/api/clothing`）。前端在添加穿搭时，会从衣橱中选择衣服，然后将这些衣服的信息保存到日历记录中。
- **复用接口**：
  - **获取衣橱列表**：前端可使用 `GET /api/clothing?token=xxx&page=1&page_size=100`（详见 `MY_WARDROBE.md`）来获取用户的衣物列表，供用户在添加穿搭时选择。
  - **衣物字段映射（重要）**：
    - **衣橱接口真实返回字段**（`MY_WARDROBE.md` 中的字段）：`image_url`、`id`、`name`、`category`、`color`、`season` 等
    - **日历模块对外字段**：`image`（对应衣橱的 `image_url`）、`id`、`name`、`accentColor`（可选）
    - **字段映射处理**：前端在调用衣橱接口获取数据后，将 `image_url` 映射为 `image`，然后调用日历接口保存；或后端在日历接口返回时统一输出 `image` 字段
    - **重要说明**：衣橱接口字段（`image_url`）保持不变，无需修改。日历模块使用 `image` 字段，由前端映射或后端在日历接口返回时统一转换。
- **数据一致性**：
  - 如果用户删除了衣橱中的某件衣服，日历中引用该衣服的记录**可以保留**（仅保留 id、name、image 的快照），也可以选择级联删除（建议保留，避免用户历史记录丢失）。
  - 如果用户修改了衣橱中衣服的名称或图片，日历中的历史记录**不应自动更新**（保持历史记录的准确性）。

### 数据存储建议

- **日期格式**：统一使用 `YYYY-MM-DD` 字符串格式存储和传输。
- **单品存储方式**：后端可以选择两种方式：
  - **方式1（快照存储）**：存储前端传入的完整信息（id、name、image、accentColor），保证历史记录独立性，即使衣橱中的衣服被删除或修改，历史记录仍完整
  - **方式2（关联存储）**：仅存储 id（clothing_id），响应时从衣橱表 join 补齐 name/image 等信息，节省存储空间，但需确保衣橱数据存在
- **响应保证**：无论采用哪种存储方式，响应时必须返回完整的字段（id、name、image、accentColor），保证前端渲染稳定

---

## 9. 安全与校验建议

1. **鉴权**：所有日历相关接口应校验用户身份（如 JWT），token 通过 query 参数传递，缺失或无效时返回 401。
2. **归属**：所有操作均按当前用户 id 过滤，仅允许操作本人数据。
3. **日期校验**：校验日期格式（`YYYY-MM-DD`），无效格式返回 400。
4. **数据校验**：
   - 单品数组中的每个 item **必须包含 `id`**（clothing_id）。
   - `name`、`image`、`accentColor` 为可选字段，前端不传时后端不应报错。
   - 后端可以选择：存储前端传入的快照（name/image），或在响应时从衣橱表 join 补齐。
   - `accentColor` 应为有效的十六进制颜色值（可选）。
5. **月份参数**：`month` 参数使用 1-12 格式（1=一月），而非 0-11。
6. **与衣橱数据关联**：保存日历记录时，**推荐校验** `item.id` 是否存在于用户的衣橱中。若不存在或不属于当前用户，返回 404（"衣橱中不存在该单品"）或 403（"禁止访问"），二者择一并保持全项目一致。
7. **Streak 计算口径**：`currentStreak` 的计算范围仅限当前请求的月份（year+month）内。跨月不连续，月初前一天不计入。后端在计算 streak 时需严格限制在当前月份范围内，避免跨月计算。
8. **统计字段计算口径**：若后端实现统计字段（monthStats、currentStreak），必须遵循文档中明确的计算口径（见 Section 1、5 和附录 A），确保前后端一致。

---

---

## 10. 联系方式

如有疑问，请联系前端开发团队。

**文档版本**：v1.3  
**最后更新**：2026-02-27

---

## 当前实现状态（与本文档对齐）

- **前端**
  - **API 封装**：`@/api/calendarApi.js` 提供 `getCalendarOutfits`、`saveCalendarOutfits`，复用 `@/api/wardrobe.js` 的 `request` 与 `API_BASE_URL`。
  - **MyCalendar.vue**：仅使用 GET 返回的 `data.outfits` 渲染日历；`monthStats`（daysRecorded、uniqueItems）与 `currentStreak` 均在前端按附录 A.2 口径从 `outfits` 计算；进入页面与切换月份时拉取当月数据；添加/删除/清空当日穿搭均通过 POST 全量覆盖；删除为乐观更新后再调用 POST；垃圾桶图标使用 `/static/icons/icon-trash-red.svg`。
  - **AddOutfitPanel.vue**：衣橱列表来自 `getClothingList`（`@/api/wardrobe.js`），token 由 props 或 `uni.getStorageSync('auth_token')` 获取；衣橱项做 `image_url`→`image`、`color`→`accentColor`（十六进制时）映射。
- **后端**
  - 已实现 `GET /api/calendar/outfits`、`POST /api/calendar/outfits`；GET 返回 `data.outfits` 与 `data.monthStats`（daysRecorded、uniqueItems），不返回 `currentStreak`；POST 全量覆盖当日记录，响应 `data.date`、`data.items`（由衣橱表 join 补齐 name、image）。
- **前端响应解析**：`uni.request` 的 `res.data` 即为后端 JSON body；前端以 `res.data.success`、`res.data.data` 判断成功并读取 `res.data.data.outfits` / `res.data.data.items` 等。

---

## 附录：与已实现模块的接口复用说明

### 复用衣橱模块接口

日历模块在添加穿搭时，需要从用户的衣橱中选择衣服。可以直接复用衣橱模块的以下接口：

1. **获取衣物列表**：`GET /api/clothing?token=xxx&page=1&page_size=100`
   - 用于在添加穿搭时展示用户的所有衣物供选择
   - 支持筛选和搜索（详见 `MY_WARDROBE.md`）

2. **字段映射（重要）**：
   - **衣橱接口真实返回字段**（详见 `MY_WARDROBE.md`）：`image_url`、`id`、`name`、`category`、`color`、`season` 等；列表可能位于 `data.data.items` 或 `data.items`，前端已做兼容。
   - **日历模块对外字段**：`image`（对应衣橱的 `image_url`）、`id`、`name`、`accentColor`（可选，`color` 为十六进制时直接用作 accentColor，否则默认色）
   - **当前实现**：AddOutfitPanel 调用衣橱接口后做 `image_url`→`image`、`color`→`accentColor` 映射；日历 GET/POST 由后端从衣橱表 join 返回 `image`、`name` 等。
   - **重要说明**：衣橱接口字段（`image_url`）保持不变，无需修改。日历模块使用 `image` 字段，由前端映射或后端在日历接口返回时统一转换。

### 响应格式统一

所有接口统一使用以下响应格式（与 `LOGIN_REGISTER.md`、`MY_WARDROBE.md` 一致）：

- **成功**：`{ success: true, message: string, data: any, status_code: 200 }`
- **失败**：`{ success: false, message: string, status_code: number }`

### 接口设计一致性原则

**核心设计理念**：采用**全量覆盖模式**，保持接口设计一致性。

- **核心接口**：`POST /api/calendar/outfits`（Section 2）
  - 所有写操作（添加、修改、删除）都通过此接口完成
  - 采用全量覆盖模式：传入完整的 items 数组，后端直接替换
  - 删除操作：前端 filter 掉要删除的 item，然后调用 POST 覆盖；或传入空数组清空当天

- **可选便捷接口**：`DELETE /api/calendar/outfits/{date}/items/{itemId}`（Section 3）、`DELETE /api/calendar/outfits/{date}`（Section 4）
  - 后端可以选择不实现这些接口
  - 若未实现，前端将通过 POST 全量覆盖实现删除操作
  - 推荐后端仅实现 POST 接口，减少维护成本，保持接口设计一致性

**优势**：
- 后端只需维护一套写逻辑（全量覆盖），无需维护"覆盖"和"原子删除"两套逻辑
- 前端状态管理更简单，避免多端/并发编辑时的状态不同步问题
- 接口契约清晰一致，降低理解和维护成本

---

## 附录 A：统计字段计算口径

### A.1 计算口径说明

即使后端不实现统计接口（Section 5），前端也会按此口径计算。后端若实现，必须遵循相同口径，确保前后端一致。

### A.2 字段计算口径

#### daysRecorded（有记录的天数）

- **定义**：本月 `outfits` 中 `items.length > 0` 的日期数量
- **计算方式**：遍历该月所有日期，统计 `outfits[dateKey]?.length > 0` 的日期数

#### uniqueItems（不重复单品数）

- **定义**：本月内按 `item.id` 去重的数量
- **重要**：**必须用 id 去重，不要用 name 去重，避免冲突**
- **计算方式**：收集该月所有 items，按 `item.id` 去重后统计数量

#### currentStreak（连续记录天数）

- **定义**：从当月今天（或查看月份的最后一天）往前倒推，连续有记录的天数，遇到空日期即断开
- **重要口径声明**：计算范围仅限当前请求的月份（year+month）内，跨月不连续，月初前一天不计入
- **计算方式**：
  - **当前月份**：从今天往前倒推，连续有记录的天数
  - **过去月份**：从该月最后一天往前倒推，连续有记录的天数
  - **未来月份**：返回 0

---

## 附录 B：前端调用对照表

| 前端操作 | 使用的接口 | 说明 |
|----------|------------|------|
| 进入日历页面、切换月份 | `GET /api/calendar/outfits?token=xxx&year=2025&month=2` | 核心接口 |
| 添加/更新某天的穿搭 | `POST /api/calendar/outfits?token=xxx`，Body：`{ date, items }` | **核心接口**，全量覆盖模式 |
| 删除某天的某个单品 | **方式1（推荐）**：`POST /api/calendar/outfits?token=xxx`，Body：`{ date, items: filteredItems }`<br>**方式2（可选）**：`DELETE /api/calendar/outfits/{date}/items/{itemId}?token=xxx` | 推荐通过 POST 覆盖实现，保持一致性 |
| 清除某天的所有记录 | **方式1（推荐）**：`POST /api/calendar/outfits?token=xxx`，Body：`{ date, items: [] }`<br>**方式2（可选）**：`DELETE /api/calendar/outfits/{date}?token=xxx` | 推荐通过 POST 空数组实现 |
| 获取月度统计（可选） | `GET /api/calendar/stats?token=xxx&year=2025&month=2` | 可选接口 |
| 获取衣橱列表（用于选择衣服） | `GET /api/clothing?token=xxx&page=1&page_size=100` | 复用衣橱模块接口 |

---

## 附录 C：前端处理逻辑说明（参考）

### C.1 月度统计计算

前端可根据 `/api/calendar/outfits` 返回的数据计算：

```javascript
// daysRecorded：统计该月有记录的日期数量
const prefix = `${year}-${String(month).padStart(2, '0')}-`
let daysRecorded = 0
for (const dateKey in outfits) {
  if (dateKey.startsWith(prefix) && outfits[dateKey]?.length > 0) {
    daysRecorded++
  }
}

// uniqueItems：统计该月不重复单品数（必须用 id 去重，不要用 name 去重）
const uniqueIds = new Set()
for (const dateKey in outfits) {
  if (dateKey.startsWith(prefix)) {
    outfits[dateKey].forEach(item => {
      if (item.id) {
        uniqueIds.add(item.id) // 必须用 id 去重，避免 name 冲突
      }
    })
  }
}
const uniqueItems = uniqueIds.size
```

### C.2 连续记录天数（Streak）计算

**重要口径声明**：`currentStreak` 的计算范围仅限当前请求的月份（year+month）内。跨月不连续，月初前一天不计入。

```javascript
// 从今天（或查看月份的最后一天）往前倒推，连续有记录的天数
// 注意：计算范围仅限当前请求的月份内，跨月不连续，月初前一天不计入
function calculateStreak(outfits, viewYear, viewMonth) {
  const today = new Date()
  const todayYear = today.getFullYear()
  const todayMonth = today.getMonth() + 1 // 转换为 1-12
  
  let startDate = new Date()
  
  // 根据查看的月份决定起始日期
  if (viewYear === todayYear && viewMonth === todayMonth) {
    // 当前月份：从今天开始
    const todayKey = `${todayYear}-${String(todayMonth).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
    if (!outfits[todayKey]?.length) {
      return 0 // 今天没记录，不显示 streak
    }
  } else if (viewYear < todayYear || (viewYear === todayYear && viewMonth < todayMonth)) {
    // 过去月份：从该月最后一天往前找最后一个有记录的天
    const lastDay = new Date(viewYear, viewMonth, 0).getDate()
    let foundStart = false
    for (let d = lastDay; d >= 1; d--) {
      const dateKey = `${viewYear}-${String(viewMonth).padStart(2, '0')}-${String(d).padStart(2, '0')}`
      if (outfits[dateKey]?.length > 0) {
        startDate = new Date(viewYear, viewMonth - 1, d)
        foundStart = true
        break
      }
    }
    if (!foundStart) return 0
  } else {
    // 未来月份：streak 为 0
    return 0
  }
  
  // 从起始日期往前倒推，计算连续有记录的天数
  // 重要：计算范围仅限当前请求的月份内，跨月不连续，月初前一天不计入
  let streak = 0
  let checkDate = new Date(startDate)
  const firstDayOfMonth = new Date(viewYear, viewMonth - 1, 1) // 该月第一天
  
  while (true) {
    // 边界检查：如果日期已经超出当前月份范围，停止计算
    if (checkDate < firstDayOfMonth) {
      break
    }
    
    const y = checkDate.getFullYear()
    const m = checkDate.getMonth() + 1
    const d = checkDate.getDate()
    
    // 确保只计算当前月份内的日期
    if (y !== viewYear || m !== viewMonth) {
      break
    }
    
    const dateKey = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    
    if (outfits[dateKey]?.length > 0) {
      streak++
      checkDate.setDate(checkDate.getDate() - 1)
    } else {
      break
    }
  }
  
  return streak
}
```

---

## 附录 D：测试用例

### D.1 获取月份记录接口测试

| 测试场景 | 请求参数 | 预期结果 |
|---------|---------|---------|
| 正常获取 | `year=2025&month=2` | 返回 200，包含该月所有有记录的日期及单品 |
| 月份无记录 | `year=2025&month=1` | 返回 200，`outfits: {}` |
| 参数缺失 | 缺少 `year` 或 `month` | 返回 400 |
| 月份格式错误 | `month=13` | 返回 400 |

### D.2 保存穿搭记录接口测试

| 测试场景 | 请求参数 | 预期结果 |
|---------|---------|---------|
| 正常保存 | `{ date: "2025-02-09", items: [{ id: 1, name: "...", image: "..." }] }` | 返回 200，保存成功 |
| 仅传 id（后端补齐） | `{ date: "2025-02-09", items: [{ id: 1 }] }` | 返回 200，后端从衣橱表 join 补齐 name/image |
| 覆盖已有记录 | 同一日期再次保存 | 返回 200，覆盖原有记录 |
| 删除记录（空数组） | `{ date: "2025-02-09", items: [] }` | 返回 200，删除该日期记录 |
| 日期格式错误 | `date: "2025-2-9"` | 返回 400 |
| 缺少必填字段 | item 缺少 `id` | 返回 400 |
| name/image 可选 | `{ date: "2025-02-09", items: [{ id: 1 }] }` | 返回 200，name/image 为可选字段，不传不报错 |

### D.3 删除单品接口测试（可选接口）

**注意**：以下测试场景仅适用于后端实现了 DELETE 便捷接口的情况。若未实现，前端将通过 POST 全量覆盖实现删除。

| 测试场景 | 请求参数 | 预期结果 |
|---------|---------|---------|
| 正常删除（DELETE） | `DELETE /api/calendar/outfits/2025-02-09/items/1?token=xxx` | 返回 200，删除成功 |
| 通过 POST 覆盖删除（推荐） | `POST /api/calendar/outfits?token=xxx`，Body：`{ date: "2025-02-09", items: [filteredItems] }` | 返回 200，覆盖成功 |
| 删除后日期无记录 | 删除最后一个单品 | 返回 200，`items: []` |
| 日期不存在 | `date` 不存在记录 | 返回 404（DELETE）或 200（POST 覆盖） |
| 单品不存在 | `itemId` 不存在 | 返回 404（DELETE）或正常覆盖（POST） |
