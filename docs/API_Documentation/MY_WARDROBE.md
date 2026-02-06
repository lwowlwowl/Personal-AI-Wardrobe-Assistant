# API 文档 - 我的衣橱模块（Vue3 + UniApp）

## 概述

本文档描述前端 **我的衣橱** 功能（`pages/index/components/MyWardrobe/`）所需的 API 约定：**衣服** 与 **模特图** 的列表、筛选、搜索、新增、修改、删除，以及设置 **默认模特**（用于虚拟试穿）。

**基础 URL**：`https://your-api-domain.com/api`（请按实际环境修改）

**请求格式**：
- JSON：`application/json`
- 文件上传：`multipart/form-data`

**响应格式**：`application/json`

### 图片字段命名约定（强烈推荐）

| 场景 | 字段名 | 说明 |
|------|--------|------|
| **Response（读）** | `image` | 所有返回单条/列表的接口，图片 URL 统一用字段 `image`。前端直接用 `item.image` 展示，无需做字段映射。 |
| **Request（写）** | `imageFileId` | 创建衣服/模特时**只接收** `imageFileId`（必填）。前端先调用 `/files/upload` 获取 fileId，再传入创建接口。后端根据 imageFileId 查文件并生成最终 image URL。**不直接接收 imageUrl**，以保证资源权限与安全管控，并与虚拟试穿模块、小程序上传流程一致。 |

**一句话**：前端展示永远用 `item.image`，后端写入永远只接收 `imageFileId`。

### 关于资源更新（Update）

所有更新接口统一使用 **PATCH** 方法，语义为 **部分更新（Partial Update）**：

- 仅更新 Body 中包含的字段。
- Body 中未包含的字段，后端应保持原值不变（不要置空）。

### 字段枚举值规范（Enum Codes，重要约定）

API 交互（Request / Response）与数据库存储**统一使用 code**，格式要求：

- 小写
- 下划线
- 无空格
- 无特殊符号

**UI 展示文案**由前端维护 `code -> text` 映射（可多语言）；后端只需处理与校验 code。

若后端收到未定义的 code，应返回 **HTTP 400**，并在 `message` 中指明错误字段，例如：`"Invalid type code"`。

**多选**：前端详情中 type、color、season 支持多选，请求与响应、以及**列表筛选 Query** 中均以**逗号分隔的 code** 表示，**不加空格**（如 `white,burnt_orange`），便于 URL 安全、小程序友好。列表筛选时「命中任意一个 code」即展示该条。

---

## 功能概要（供后端理解）

| 模块 | 说明 |
|------|------|
| **衣服视图** | 以网格展示衣服。每项包含：图片、名称、类型、颜色、季节、添加日期、收藏等级（0–3）。用户可按关键词搜索，按收藏/日期/类型/颜色/季节筛选，打开详情弹窗编辑或删除，或点击「虚拟试穿」用该衣服试穿。 |
| **模特视图** | 以网格展示模特（人物）照片。每项：图片、姿势名称、添加日期、收藏等级（0–3）。可指定一个模特为 **默认**（在衣服详情里点「虚拟试穿」时使用）。用户可按姿势搜索、筛选、编辑、删除或设为默认。 |
| **上传** | 用户通过选择文件或拖拽添加新衣服或新模特图。前端先调用通用上传接口 `/files/upload` 获取 fileId，再将该 fileId 作为 `imageFileId` 传入创建接口完成记录创建。 |

所有列表类接口需支持 **分页** 与 **筛选/排序**，以便前端实现当前 UI（如每页 8 条、按日期升序/降序、按收藏/类型/颜色/季节筛选）。

---

## 与后端交互概览（自然语言）

下面用自然语言概括「我的衣橱」里哪些地方要和后端打交道，便于后端同学快速对齐。

**衣服相关**

- **进衣橱、翻页、搜衣服、按类型/颜色/季节/收藏/日期筛选**：前端会向你要「当前用户的衣服列表」，可能带搜索词、筛选条件、排序和分页（第几页、每页几条）。你需要按条件查出数据并返回列表和总条数。
- **点某件衣服看详情**：如果数据已经在本页列表里，前端不再请求；否则会按 id 向你要这一条衣服的详情。
- **用户改衣服的名字、类型、颜色、季节、收藏**：前端会把改动的字段发给你，你更新库里这条记录并返回更新后的整条数据。
- **用户删某件衣服**：前端按 id 请你删除这条记录，你删掉并返回成功即可。
- **用户上传新衣服**：前端会先把图片传给你的上传接口拿到 fileId，再带着 `imageFileId` 和名称/类型/颜色/季节等信息请你「新建一条衣服」。你根据 fileId 解析出图片并落库，返回新建的这条数据（含 `image` URL）。

**模特相关**

- **进模特 Tab、翻页、搜模特、按收藏/日期筛选**：前端会向你要「当前用户的模特图列表」，可能带搜索、筛选、排序和分页。你需要返回列表、总条数，以及 **defaultModelId**（无默认则为 null）；展示顺序由前端决定。
- **点某张模特图看详情**：一般用列表里已有数据；需要时也会按 id 向你要单条模特详情。
- **用户改模特的姿势名、收藏**：前端把改动的字段发给你，你更新该条并返回更新后的数据。
- **用户把某张模特设为默认**：前端会通知你「把某个 modelId 设为默认」，你这边只保留一个默认，设新的就清掉旧的。
- **用户删某张模特图**：前端按 id 请你删除；若删的是默认模特，则将 defaultModelId 置为 null，不返回新默认 id。
- **用户上传新模特图**：和衣服类似，先上传图片拿 fileId，再带着 `imageFileId` 和姿势名等信息请你新建一条模特记录，你根据 fileId 解析并落库，返回新建数据（含 `image` URL）。

**共用**

- **上传图片**：新增衣服或模特时，前端会先调你的文件上传接口（与虚拟试穿共用 `/files/upload`），传图片文件，你返回 fileId，前端再把该 fileId 作为 `imageFileId` 传入创建接口；后端根据 imageFileId 管理资源并生成返回给前端的 `image` URL。
- **鉴权与归属**：以上衣橱、模特相关请求都会带用户身份（如 token），你需校验身份，且只对应当前用户的数据做增删改查。

---

## 1. 获取衣服列表

### 接口信息

- **路径**：`/wardrobe/clothes`
- **方法**：`GET`
- **说明**：返回当前用户的衣服列表，支持可选的关键词搜索、筛选、排序与分页。

### 请求

#### Headers

```
Content-Type: application/json
Authorization: Bearer <token>   // 若接口需要鉴权
```

#### Query 参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|--------|
| search | string | 否 | 按名称、类型、颜色关键词搜索 | `"white tee"` |
| favourite | string | 否 | 收藏等级，逗号分隔（0–3）。业务上为整数；Query 为字符串，后端需解析为 number[] 再参与筛选，勿按字符串比较 | `"0,1,2"` |
| dateOrder | string | 否 | 按日期排序：`asc` 或 `desc` | `"desc"` |
| type | string | 否 | 类型 code，逗号分隔（见下方选项集） | `"t_shirt,blouse"` |
| color | string | 否 | 颜色 code，逗号分隔 | `"white,black"` |
| season | string | 否 | 季节 code，逗号分隔 | `"summer,winter"` |
| page | number | 否 | 页码，从 1 开始 | `1` |
| pageSize | number | 否 | 每页条数（如 8） | `8` |

**筛选参数多选格式（标准）**

- **枚举类参数**（type、color、season）：一律传 **code**（小写、下划线），不传展示文案，避免 URL 中出现空格、斜杠（如 Black/White），便于小程序与 GET 请求。
- **多选**：多个 code 用**英文逗号分隔，中间不加空格**，例如 `type=t_shirt,blouse`、`color=white,burnt_orange`。  
- 仅使用附录中的 code 时，query 无需 URL 编码即可安全传输；若需传其它字符，请做 URL 编码，后端按标准解码。

**前端选项集参考**

- **type**：`blouse`、`t_shirt`、`top`、`vest`、`sweater`、`shirt`
- **color**：`white`、`black`、`beige`、`brown`、`navy`、`olive`、`burnt_orange`、`black_white`
- **season**：`spring`、`summer`、`autumn`、`winter`
- **dateOrder**：`asc`（升序）、`desc`（降序），建议默认 `desc`
- **favourite**：收藏等级（评分），业务类型为 **number**（0–3），不是 boolean。Query 中为字符串（如 `"0,1,2"`），后端需 parse 成 number[] 再筛选；Body 中为 number。

#### 示例

```
GET /api/wardrobe/clothes?page=1&pageSize=8&dateOrder=desc
GET /api/wardrobe/clothes?search=tee&favourite=0,1&type=t_shirt
```

### 响应

#### 成功（HTTP 200）

| 字段 | 类型 | 说明 |
|------|------|------|
| code | number | 200 表示成功 |
| message | string | 提示信息，如 "Success" |
| data | object | - |
| data.items | array | 衣服对象列表（结构见下） |
| data.total | number | 总条数（用于分页） |

**单条衣服对象结构**

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|--------|
| id | number 或 string | 唯一 id | `1` |
| name | string | 显示名称 | `"Basic White Tee"` |
| type | string | 类型 code（见枚举附录）。可为单个或逗号分隔多个（如 `"t_shirt,blouse"`） | `"t_shirt"` |
| color | string | 颜色 code。可为单个或逗号分隔多个（如 `"white,burnt_orange"`） | `"white"` |
| season | string | 季节 code。可为单个或逗号分隔多个 | `"summer"` |
| date | string | 添加日期（YYYY-MM-DD） | `"2024-01-10"` |
| favourite | number | 收藏等级（评分），0–3（不是 boolean） | `0` |
| image | string | 图片 URL（绝对或相对），前端直接用于展示 | `"https://..."` 或 `"/files/xxx.jpg"` |

#### 示例

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "Basic White Tee",
        "type": "t_shirt",
        "color": "white",
        "season": "summer",
        "date": "2024-01-10",
        "favourite": 0,
        "image": "https://example.com/files/cloth_1.jpg"
      }
    ],
    "total": 9
  }
}
```

#### 错误（如 401、500）

与其他文档一致：`code`、`message`、`data: null`。

---

## 2. 获取单件衣服（可选）

若前端需要按 id 拉取详情（如深链），可使用本接口。

- **路径**：`/wardrobe/clothes/:id`
- **方法**：`GET`
- **响应**：单条衣服对象，结构与列表中的元素一致。
- **错误**：未找到或非当前用户数据时返回 404。

---

## 3. 新增衣服

### 接口信息

- **路径**：`POST /wardrobe/clothes`
- **方法**：`POST`
- **说明**：创建衣服记录。
- **前置要求**：需先调用 `/files/upload` 获取 fileId。

### 请求

- **Headers**：`Content-Type: application/json`
- **Body（JSON）**：

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| imageFileId | string | 是 | 上传接口返回的图片文件 ID |
| name | string | 否 | 显示名称（默认 "New Item"） |
| type | string | 否 | 类型 code（默认 `blouse`）。多选时多个 code 用英文逗号分隔、不加空格 |
| color | string | 否 | 颜色 code。多选时同上，逗号分隔、不加空格 |
| season | string | 否 | 季节 code。多选时同上，逗号分隔、不加空格 |

请求示例：

```json
{
  "imageFileId": "f_123456789_cloth",
  "name": "Summer White Tee",
  "type": "t_shirt",
  "color": "white",
  "season": "summer"
}
```

### 响应

- **成功（200）**：`data` 为创建后的衣服对象（含 `image` URL，与列表单条结构一致）。

响应示例：

```json
{
  "code": 200,
  "message": "Created",
  "data": {
    "id": 101,
    "name": "Summer White Tee",
    "type": "t_shirt",
    "color": "white",
    "season": "summer",
    "date": "2024-01-10",
    "favourite": 0,
    "image": "https://example.com/files/cloth_101.jpg"
  }
}
```

- **错误**：400（校验失败，如 imageFileId 无效）、401、500 等。

---

## 4. 更新衣服

在详情弹窗中用户修改名称、类型、颜色、季节或收藏时使用。

- **路径**：`/wardrobe/clothes/:id`
- **方法**：`PATCH`
- **说明**：部分更新。仅传需要修改的字段（如仅修改 favourite），其他字段保持不变。

### 请求体（JSON）

仅传需要变更的字段；未传的字段后端保持原值。

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 显示名称 |
| type | string | 类型 code。多选时逗号分隔、不加空格（与 §1 约定一致） |
| color | string | 颜色 code。多选时逗号分隔、不加空格 |
| season | string | 季节 code。多选时逗号分隔、不加空格 |
| favourite | number | 收藏等级（评分），0–3（不是 boolean） |

示例：

```json
{
  "name": "Basic White Tee",
  "type": "t_shirt",
  "color": "white",
  "season": "summer",
  "favourite": 1
}
```

### 响应

- **成功（200）**：`data` 为更新后的衣服对象。
- **错误**：400（请求体不合法）、404（未找到或非本人）、401、500。

---

## 5. 删除衣服

- **路径**：`/wardrobe/clothes/:id`
- **方法**：`DELETE`
- **响应**：200，`message` 如 "Deleted"，`data` 可为 null。
- **错误**：404、401、500。

---

## 6. 获取模特图列表

- **路径**：`/wardrobe/models`
- **方法**：`GET`
- **说明**：返回当前用户的模特（人物）照片列表。**后端必须返回 defaultModelId**（无默认则为 null），前端据此展示「Default」角标并决定列表展示顺序；后端无需对列表排序。

### Query 参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| search | string | 否 | 按姿势/名称关键词搜索 |
| favourite | string | 否 | 收藏等级，逗号分隔 0–3；后端解析为 number[] 再筛选 |
| dateOrder | string | 否 | `asc` 或 `desc`（建议默认 `desc`） |
| page | number | 否 | 页码，从 1 开始 |
| pageSize | number | 否 | 每页条数，如 8 |

### 响应（200）

| 字段 | 类型 | 说明 |
|------|------|------|
| data.items | array | 模特对象列表（结构见下） |
| data.total | number | 总条数 |
| data.defaultModelId | number 或 string | 默认模特 id，**必须返回**；无默认时为 null |

**单条模特对象结构**

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|--------|
| id | number 或 string | 唯一 id | `101` |
| posture | string | 姿势/名称描述 | `"Arms crossed"` |
| date | string | YYYY-MM-DD | `"2024-10-01"` |
| favourite | number | 收藏等级（评分），0–3（不是 boolean） | `0` |
| image | string | 图片 URL | `"https://..."` |

示例：

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": 103,
        "posture": "Example model",
        "date": "2024-12-01",
        "favourite": 0,
        "image": "https://example.com/files/model_103.jpg"
      }
    ],
    "total": 3,
    "defaultModelId": 103
  }
}
```

---

## 7. 获取单条模特（可选）

- **路径**：`/wardrobe/models/:id`
- **方法**：`GET`
- **响应**：单条模特对象。未找到或非当前用户返回 404。

---

## 8. 新增模特图

### 接口信息

- **路径**：`POST /wardrobe/models`
- **方法**：`POST`
- **说明**：新增模特图。
- **前置要求**：需先调用 `/files/upload` 获取 fileId。

### 请求

- **Headers**：`Content-Type: application/json`
- **Body（JSON）**：

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| imageFileId | string | 是 | 上传接口返回的文件 ID |
| posture | string | 否 | 姿势/名称（默认 "New Model"） |

请求示例：

```json
{
  "imageFileId": "f_987654321_model",
  "posture": "Hands in pockets"
}
```

### 响应

- **成功（200）**：`data` 为创建后的模特对象（含 `image` URL）。

响应示例：

```json
{
  "code": 200,
  "message": "Created",
  "data": {
    "id": 12,
    "posture": "Hands in pockets",
    "date": "2024-01-10",
    "favourite": 0,
    "image": "https://example.com/files/model_12.jpg"
  }
}
```

---

## 9. 更新模特图

- **路径**：`/wardrobe/models/:id`
- **方法**：`PATCH`
- **说明**：部分更新（如仅修改 posture）。仅传需要变更的字段，未传的字段后端保持原值。

**Body（部分更新）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| posture | string | 姿势/名称 |
| favourite | number | 收藏等级（评分），0–3（不是 boolean） |

示例：

```json
{
  "posture": "Arms crossed",
  "favourite": 1
}
```

---

## 10. 设置默认模特

在模特详情弹窗中用户点击「设为默认」时使用。每个用户仅有一个默认模特；设置新的默认时应清除原默认。

**约定**：以**独立默认接口**为准，前端只对接此方式。

- **路径**：`PUT /wardrobe/models/default`
- **方法**：`PUT`
- **Body（JSON）**：`{ "modelId": 103 }`（要设为默认的模特 id）
- **响应**：200，如 `data: { defaultModelId: 103 }`

---

## 11. 删除模特图

- **路径**：`/wardrobe/models/:id`
- **方法**：`DELETE`
- **响应**：200。若删除的为当前默认模特，后端将 defaultModelId 置为 null，不返回新的默认 id。
- **错误**：404、401、500。

---

## 12. 文件上传（共用）

衣橱与虚拟试穿共用同一上传接口，**统一规则**如下：

- **上传接口** `POST /files/upload`：前端传图片文件，后端返回 `data.fileId`（详见 VIRTUAL_TRYON.md）。若上传接口同时返回 `data.fileUrl`，仅作可选预览用；**创建衣橱/模特仍只认 imageFileId**。
- **创建接口**（`POST /wardrobe/clothes`、`POST /wardrobe/models`）：**仅接收** `imageFileId`，不接收 imageUrl。后端根据 imageFileId 查文件、落库，并在响应中返回可访问的 `image`（URL）。
- **业务响应**：列表/详情的图片字段统一为 `image`（URL），不暴露 fileId/fileUrl 混用。

即：前端拿 fileId → 以 imageFileId 写入创建接口；后端只根据 imageFileId 出图，响应里只给 image(URL)。

---

## 13. 通用响应格式与状态码

与 LOGIN_REGISTER.md、VIRTUAL_TRYON.md 一致：

```json
{
  "code": 200,
  "message": "Success",
  "data": { ... }
}
```

| code | 含义     | HTTP |
|------|----------|------|
| 200  | 成功     | 200  |
| 400  | 请求错误 | 400  |
| 401  | 未授权   | 401  |
| 403  | 禁止访问 | 403  |
| 404  | 未找到   | 404  |
| 500  | 服务器错误 | 500  |

---

## 14. 前端调用对照表

| 前端操作 | 使用的接口 |
|----------|------------|
| 打开衣橱（衣服 Tab） | `GET /wardrobe/clothes?page=1&pageSize=8&dateOrder=desc` |
| 搜索/筛选衣服 | 同上，按需加 `search`、`favourite`、`type`、`color`、`season`、`dateOrder` |
| 打开衣服详情弹窗 | 若数据来自列表可不请求；否则 `GET /wardrobe/clothes/:id` |
| 编辑衣服（名称、类型、颜色、季节、收藏） | `PATCH /wardrobe/clothes/:id` |
| 删除衣服 | `DELETE /wardrobe/clothes/:id` |
| 新增衣服 | 先上传图片获取 fileId → `POST /wardrobe/clothes`，body 仅传 `imageFileId` 及元数据（不传 imageUrl） |
| 打开模特 Tab | `GET /wardrobe/models?page=1&pageSize=8`（若返回 defaultModelId 一并使用） |
| 搜索/筛选模特 | 同上，按需加 `search`、`favourite`、`dateOrder` |
| 打开模特详情 | 可不请求或 `GET /wardrobe/models/:id` |
| 编辑模特（姿势、收藏） | `PATCH /wardrobe/models/:id` |
| 设为默认模特 | `PUT /wardrobe/models/default`，Body：`{ "modelId": <id> }`（见 §10） |
| 删除模特 | `DELETE /wardrobe/models/:id` |
| 新增模特 | 先上传图片获取 fileId → `POST /wardrobe/models`，body 仅传 `imageFileId` 及 posture 等（不传 imageUrl） |

---

## 15. 安全与校验建议

1. **鉴权**：所有衣橱相关接口应校验用户身份（如 JWT），token 缺失或无效时返回 401。
2. **归属**：列表/详情/更新/删除均按当前用户 id 过滤，仅允许操作本人数据。
3. **图片写入**：创建衣服/模特只接收 `imageFileId`，不直接接收 `imageUrl`，避免前端提交任意 URL（恶意外链/脏数据）；后端根据 fileId 解析资源并生成 `image` URL。
4. **上传**：与 VIRTUAL_TRYON 保持一致，限制图片类型与大小（如 JPG/PNG，最大 10MB），并校验文件内容。
5. **枚举**：`type`、`color`、`season`、`dateOrder` 严格按文档附录中的 code 校验；收到未定义 code 返回 400，并在 `message` 中指出字段（如 `"Invalid type code"`）。
6. **favourite**：收藏等级（评分），必须为 0–3 的整数；收到非整数或超出范围返回 400。

---

## 16. 联系方式

如有疑问，请联系前端开发团队。

**文档版本**：v1.0  
**最后更新**：2026-02-04

---

## 附录：字段枚举值规范（Enum Codes）

### 重要约定

- API 交互（Request / Response）与数据库存储统一使用 **code**（小写、下划线、无空格、无特殊符号）。  
- UI 展示文案由前端维护 `code -> text` 映射（可多语言）。  
- 后端收到未定义 code：返回 **HTTP 400**，并在 `message` 指明错误字段，例如：`"Invalid type code"`。  

### 1）衣服类型（type）

| Code（API / DB） | UI Display（参考） |
|------------------|-------------------|
| blouse           | Blouse            |
| t_shirt          | T-Shirt           |
| top              | Top               |
| vest             | Vest              |
| sweater          | Sweater           |
| shirt            | Shirt             |

### 2）颜色（color）

| Code（API / DB） | UI Display（参考） |
|------------------|-------------------|
| white            | White             |
| black            | Black             |
| beige            | Beige             |
| brown            | Brown             |
| navy             | Navy              |
| olive            | Olive             |
| burnt_orange     | Burnt Orange      |
| black_white      | Black/White       |

### 3）季节（season）

| Code（API / DB） | UI Display（参考） |
|------------------|-------------------|
| spring           | Spring            |
| summer           | Summer            |
| autumn           | Autumn            |
| winter           | Winter            |

### 4）排序方式（dateOrder）

| Code（API） | 说明 |
|-------------|------|
| asc         | 升序 |
| desc        | 降序 |

建议默认值：`desc`。

### favourite 字段补充说明

`favourite` 在本项目中表示「**收藏等级 / 评分**」，**业务类型为 number**，取值为整数 `0~3`（对应 UI 中的心数量），**不是** boolean。Request Body 中为 number；Query 中为字符串（如 `"0,1,2"`），后端需解析为 number[] 再参与筛选。

### 前端映射（参考）

列表展示用 `label`，传给后端用 `value`；从后端拿到 code 时，用映射表找到 label 显示：

```js
const TYPE_OPTIONS = [
  { label: 'Blouse', value: 'blouse' },
  { label: 'T-Shirt', value: 't_shirt' },
  { label: 'Top', value: 'top' },
]
```
