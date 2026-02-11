# 衣物及模特照片管理 API 文档

## 概述

本文档详细说明衣物管理（包括上传、查询、更新、删除）和模特照片管理（包括上传、设置、删除）相关的所有API接口。

------

## 1. 衣物管理 API

### 1.1 上传衣物

上传衣物图片并创建衣物记录。

- **URL**: `POST /api/clothing/upload`
- **认证**: 需要Token验证
- **请求类型**: `multipart/form-data`

#### 请求参数

| 参数            | 类型         | 必填 | 说明                                            |
| :-------------- | :----------- | :--- | :---------------------------------------------- |
| `token`         | query string | 是   | 用户认证令牌                                    |
| `file`          | file         | 是   | 衣物图片文件（支持：jpg, jpeg, png, webp, gif） |
| `name`          | form         | 是   | 衣物名称                                        |
| `category`      | form         | 是   | 衣物分类                                        |
| `color`         | form         | 否   | 颜色                                            |
| `season`        | form         | 否   | 适用季节                                        |
| `brand`         | form         | 否   | 品牌                                            |
| `tags`          | form         | 否   | 标签，逗号分隔                                  |
| `description`   | form         | 否   | 描述                                            |
| `price`         | form         | 否   | 价格                                            |
| `purchase_date` | form         | 否   | 购买日期（YYYY-MM-DD格式）                      |

#### 成功响应

```json
{
  "success": true,
  "message": "衣物上传成功",
  "data": {
    "id": 123,
    "name": "夏季T恤",
    "image_url": "/Personal-AI-Wardrobe-Assistant/uploads/1/clothing_abc123.jpg",
    "created_at": "2024-01-01T10:00:00"
  }
}
```



#### 错误响应

- `400`: 文件类型不支持/文件过大/参数错误
- `401`: 未授权/Token无效
- `500`: 服务器内部错误

------

### 1.2 获取衣物列表

获取用户的衣物列表，支持分页、筛选和搜索。

- **URL**: `GET /api/clothing`
- **认证**: 需要Token验证

#### 请求参数

| 参数          | 类型         | 必填 | 说明                             |
| :------------ | :----------- | :--- | :------------------------------- |
| `token`       | query string | 是   | 用户认证令牌                     |
| `page`        | query        | 否   | 页码（默认：1）                  |
| `page_size`   | query        | 否   | 每页数量（默认：20，最大：100）  |
| `category`    | query        | 否   | 分类筛选                         |
| `season`      | query        | 否   | 季节筛选                         |
| `color`       | query        | 否   | 颜色筛选                         |
| `brand`       | query        | 否   | 品牌筛选                         |
| `is_favorite` | query        | 否   | 是否收藏                         |
| `min_price`   | query        | 否   | 最低价格                         |
| `max_price`   | query        | 否   | 最高价格                         |
| `search`      | query        | 否   | 搜索关键词（模糊匹配名称和描述） |
| `order_by`    | query        | 否   | 排序字段（默认：created_at）     |
| `order_desc`  | query        | 否   | 是否降序（默认：true）           |

#### 成功响应

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 123,
        "name": "夏季T恤",
        "image_url": "...",
        "category": "top",
        "color": "蓝色",
        "season": "summer",
        "is_favorite": true,
        "created_at": "2024-01-01T10:00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 150,
      "total_pages": 8,
      "has_next": true,
      "has_prev": false
    }
  }
}
```



------

### 1.3 获取衣物详情

获取单件衣物的详细信息。

- **URL**: `GET /api/clothing/{clothing_id}`
- **认证**: 需要Token验证

#### 路径参数

| 参数          | 类型 | 必填 | 说明   |
| :------------ | :--- | :--- | :----- |
| `clothing_id` | path | 是   | 衣物ID |

#### 查询参数

| 参数    | 类型  | 必填 | 说明         |
| :------ | :---- | :--- | :----------- |
| `token` | query | 是   | 用户认证令牌 |

#### 成功响应

```json
{
  "success": true,
  "data": {
    "id": 123,
    "user_id": 1,
    "name": "夏季T恤",
    "description": "纯棉透气T恤",
    "image_url": "...",
    "category": "top",
    "color": "蓝色",
    "season": "summer",
    "brand": "优衣库",
    "price": 99.0,
    "purchase_date": "2024-05-01",
    "is_favorite": true,
    "wear_count": 5,
    "last_worn_date": "2024-06-15",
    "created_at": "2024-01-01T10:00:00",
    "updated_at": "2024-06-15T14:30:00",
    "tags": ["夏季", "休闲", "纯棉"]
  }
}
```



------

### 1.4 更新衣物信息

更新衣物的信息，可更新图片。

- **URL**: `PUT /api/clothing/{clothing_id}`
- **认证**: 需要Token验证
- **请求类型**: `multipart/form-data`

#### 路径参数

| 参数          | 类型 | 必填 | 说明   |
| :------------ | :--- | :--- | :----- |
| `clothing_id` | path | 是   | 衣物ID |

#### 请求参数

| 参数            | 类型  | 必填 | 说明               |
| :-------------- | :---- | :--- | :----------------- |
| `token`         | query | 是   | 用户认证令牌       |
| `file`          | file  | 否   | 新图片文件（可选） |
| `name`          | form  | 否   | 新名称             |
| `category`      | form  | 否   | 新分类             |
| `color`         | form  | 否   | 新颜色             |
| `season`        | form  | 否   | 新季节             |
| `brand`         | form  | 否   | 新品牌             |
| `tags`          | form  | 否   | 新标签（逗号分隔） |
| `description`   | form  | 否   | 新描述             |
| `price`         | form  | 否   | 新价格             |
| `purchase_date` | form  | 否   | 新购买日期         |
| `is_favorite`   | form  | 否   | 收藏状态           |
| `condition`     | form  | 否   | 衣物状况           |

#### 成功响应

```json
{
  "success": true,
  "message": "衣物更新成功",
  "data": {
    "id": 123,
    "name": "更新后的名称",
    "image_url": "新的图片URL",
    "updated_at": "2024-06-16T09:00:00"
  }
}
```



------

### 1.5 删除衣物

删除指定的衣物。

- **URL**: `DELETE /api/clothing/{clothing_id}`
- **认证**: 需要Token验证

#### 路径参数

| 参数          | 类型 | 必填 | 说明   |
| :------------ | :--- | :--- | :----- |
| `clothing_id` | path | 是   | 衣物ID |

#### 查询参数

| 参数    | 类型  | 必填 | 说明         |
| :------ | :---- | :--- | :----------- |
| `token` | query | 是   | 用户认证令牌 |

#### 成功响应

```json
{
  "success": true,
  "message": "衣物删除成功"
}
```



------

### 1.6 切换收藏状态

切换衣物的收藏状态。

- **URL**: `POST /api/clothing/{clothing_id}/toggle-favorite`
- **认证**: 需要Token验证

#### 路径参数

| 参数          | 类型 | 必填 | 说明   |
| :------------ | :--- | :--- | :----- |
| `clothing_id` | path | 是   | 衣物ID |

#### 查询参数

| 参数    | 类型  | 必填 | 说明         |
| :------ | :---- | :--- | :----------- |
| `token` | query | 是   | 用户认证令牌 |

#### 成功响应

```json
{
  "success": true,
  "message": "已添加收藏",
  "data": {
    "is_favorite": true
  }
}
```



------

### 1.7 记录衣物穿着

记录衣物穿着（增加穿着次数并更新最后穿着日期）。

- **URL**: `POST /api/clothing/{clothing_id}/record-wear`
- **认证**: 需要Token验证

#### 路径参数

| 参数          | 类型 | 必填 | 说明   |
| :------------ | :--- | :--- | :----- |
| `clothing_id` | path | 是   | 衣物ID |

#### 查询参数

| 参数    | 类型  | 必填 | 说明         |
| :------ | :---- | :--- | :----------- |
| `token` | query | 是   | 用户认证令牌 |

#### 成功响应

```json
{
  "success": true,
  "message": "穿着记录已更新",
  "data": {
    "wear_count": 6,
    "last_worn_date": "2024-06-16"
  }
}
```



------

## 2. 衣物标签管理 API

### 2.1 按标签搜索衣物

根据标签关键词搜索衣物（模糊匹配）。

- **URL**: `GET /api/clothing/tags/search`
- **认证**: 需要Token验证

#### 查询参数

| 参数        | 类型  | 必填 | 说明                            |
| :---------- | :---- | :--- | :------------------------------ |
| `token`     | query | 是   | 用户认证令牌                    |
| `tag`       | query | 是   | 标签关键词                      |
| `page`      | query | 否   | 页码（默认：1）                 |
| `page_size` | query | 否   | 每页数量（默认：20，最大：100） |

#### 成功响应

```json
{
  "success": true,
  "data": {
    "items": [...],
    "tag": "夏季",
    "total_count": 45,
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 45,
      "total_pages": 3,
      "has_next": true,
      "has_prev": false
    }
  }
}
```



------

### 2.2 获取热门标签

获取用户最常用的标签（按使用次数排序）。

- **URL**: `GET /api/clothing/tags/popular`
- **认证**: 需要Token验证

#### 查询参数

| 参数    | 类型  | 必填 | 说明                           |
| :------ | :---- | :--- | :----------------------------- |
| `token` | query | 是   | 用户认证令牌                   |
| `limit` | query | 否   | 返回数量（默认：20，最大：50） |

#### 成功响应

```json
{
  "success": true,
  "data": [
    {"tag": "夏季", "count": 25},
    {"tag": "休闲", "count": 18},
    {"tag": "正式", "count": 12}
  ]
}
```



------

### 2.3 获取所有标签

获取用户的所有标签（去重）。

- **URL**: `GET /api/clothing/tags/all`
- **认证**: 需要Token验证

#### 查询参数

| 参数    | 类型  | 必填 | 说明         |
| :------ | :---- | :--- | :----------- |
| `token` | query | 是   | 用户认证令牌 |

#### 成功响应

```json
{
  "success": true,
  "data": ["夏季", "冬季", "休闲", "正式", "运动"]
}
```



------

## 3. 衣物批量操作 API

### 3.1 批量删除衣物

批量删除多件衣物。

- **URL**: `POST /api/clothing/batch/delete`
- **认证**: 需要Token验证
- **请求类型**: `application/json`

#### 请求体

```json
{
  "clothing_ids": [1, 2, 3, 4, 5]
}
```



#### 查询参数

| 参数    | 类型  | 必填 | 说明         |
| :------ | :---- | :--- | :----------- |
| `token` | query | 是   | 用户认证令牌 |

#### 成功响应

```json
{
  "success": true,
  "message": "成功删除 5 件衣物"
}
```



------

### 3.2 批量更新衣物

批量更新多件衣物的信息。

- **URL**: `POST /api/clothing/batch/update`
- **认证**: 需要Token验证
- **请求类型**: `application/json`

#### 请求体

```json
{
  "clothing_ids": [1, 2, 3],
  "update_data": {
    "is_favorite": true,
    "season": "summer"
  }
}
```



#### 查询参数

| 参数    | 类型  | 必填 | 说明         |
| :------ | :---- | :--- | :----------- |
| `token` | query | 是   | 用户认证令牌 |

#### 成功响应

```json
{
  "success": true,
  "message": "成功更新 3 件衣物"
}
```



------

## 4. 模特照片管理 API

### 4.1 上传模特照片

上传模特照片（用于虚拟试衣功能）。

- **URL**: `POST /api/model-photos/upload`
- **认证**: 需要Token验证
- **请求类型**: `multipart/form-data`

#### 请求参数

| 参数          | 类型  | 必填 | 说明                            |
| :------------ | :---- | :--- | :------------------------------ |
| `token`       | query | 是   | 用户认证令牌                    |
| `file`        | file  | 是   | 模特照片文件                    |
| `photo_name`  | form  | 是   | 照片名称                        |
| `description` | form  | 否   | 照片描述                        |
| `is_primary`  | form  | 否   | 是否设为主要照片（默认：false） |

#### 成功响应

```json
{
  "success": true,
  "message": "模特照片上传成功",
  "data": {
    "id": 1,
    "user_id": 1,
    "photo_name": "我的全身照",
    "image_url": "...",
    "description": "用于虚拟试衣",
    "is_primary": false,
    "file_size": 2048576,
    "file_format": "jpg",
    "created_at": "2024-06-16T10:00:00"
  }
}
```



------

### 4.2 获取模特照片列表

获取用户的模特照片列表。

- **URL**: `GET /api/model-photos`
- **认证**: 需要Token验证

#### 查询参数

| 参数        | 类型  | 必填 | 说明                               |
| :---------- | :---- | :--- | :--------------------------------- |
| `token`     | query | 是   | 用户认证令牌                       |
| `page`      | query | 否   | 页码（默认：1）                    |
| `page_size` | query | 否   | 每页数量（默认：20，最大：100）    |
| `is_active` | query | 否   | 是否只显示激活的照片（默认：true） |

#### 成功响应

```json
{
  "success": true,
  "data": {
    "photos": [...],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 5,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```



------

### 4.3 获取主要模特照片

获取用户的主要模特照片（用于虚拟试衣）。

- **URL**: `GET /api/model-photos/primary`
- **认证**: 需要Token验证

#### 查询参数

| 参数    | 类型  | 必填 | 说明         |
| :------ | :---- | :--- | :----------- |
| `token` | query | 是   | 用户认证令牌 |

#### 成功响应

```json
{
  "success": true,
  "data": {
    "id": 2,
    "user_id": 1,
    "photo_name": "主要模特照",
    "image_url": "...",
    "is_primary": true,
    "created_at": "2024-06-15T14:30:00"
  }
}
```



------

### 4.4 获取模特照片详情

获取单张模特照片的详细信息。

- **URL**: `GET /api/model-photos/{photo_id}`
- **认证**: 需要Token验证

#### 路径参数

| 参数       | 类型 | 必填 | 说明       |
| :--------- | :--- | :--- | :--------- |
| `photo_id` | path | 是   | 模特照片ID |

#### 查询参数

| 参数    | 类型  | 必填 | 说明         |
| :------ | :---- | :--- | :----------- |
| `token` | query | 是   | 用户认证令牌 |

#### 成功响应

```json
{
  "success": true,
  "data": {
    "id": 1,
    "user_id": 1,
    "photo_name": "我的全身照",
    "image_url": "...",
    "description": "用于虚拟试衣",
    "is_primary": false,
    "file_size": 2048576,
    "file_format": "jpg",
    "is_active": true,
    "created_at": "2024-06-16T10:00:00",
    "updated_at": "2024-06-16T10:00:00"
  }
}
```



------

### 4.5 更新模特照片

更新模特照片信息。

- **URL**: `PUT /api/model-photos/{photo_id}`
- **认证**: 需要Token验证
- **请求类型**: `multipart/form-data`

#### 路径参数

| 参数       | 类型 | 必填 | 说明       |
| :--------- | :--- | :--- | :--------- |
| `photo_id` | path | 是   | 模特照片ID |

#### 请求参数

| 参数          | 类型  | 必填 | 说明               |
| :------------ | :---- | :--- | :----------------- |
| `token`       | query | 是   | 用户认证令牌       |
| `file`        | file  | 否   | 新照片文件（可选） |
| `photo_name`  | form  | 否   | 新照片名称         |
| `description` | form  | 否   | 新描述             |
| `is_primary`  | form  | 否   | 是否设为主要照片   |

#### 成功响应

```json
{
  "success": true,
  "message": "模特照片更新成功",
  "data": {
    "id": 1,
    "photo_name": "更新后的名称",
    "image_url": "新的图片URL",
    "is_primary": true,
    "updated_at": "2024-06-16T11:00:00"
  }
}
```



------

### 4.6 删除模特照片

删除模特照片（支持软删除和硬删除）。

- **URL**: `DELETE /api/model-photos/{photo_id}`
- **认证**: 需要Token验证

#### 路径参数

| 参数       | 类型 | 必填 | 说明       |
| :--------- | :--- | :--- | :--------- |
| `photo_id` | path | 是   | 模特照片ID |

#### 查询参数

| 参数          | 类型  | 必填 | 说明                                |
| :------------ | :---- | :--- | :---------------------------------- |
| `token`       | query | 是   | 用户认证令牌                        |
| `hard_delete` | query | 否   | 是否永久删除（默认：false，软删除） |

#### 成功响应

```json
{
  "success": true,
  "message": "模特照片删除成功"
}
```



------

### 4.7 设置主要模特照片

设置模特照片为主要照片。

- **URL**: `POST /api/model-photos/{photo_id}/set-primary`
- **认证**: 需要Token验证

#### 路径参数

| 参数       | 类型 | 必填 | 说明       |
| :--------- | :--- | :--- | :--------- |
| `photo_id` | path | 是   | 模特照片ID |

#### 查询参数

| 参数    | 类型  | 必填 | 说明         |
| :------ | :---- | :--- | :----------- |
| `token` | query | 是   | 用户认证令牌 |

#### 成功响应

```json
{
  "success": true,
  "message": "已设置为主要模特照片",
  "data": {
    "id": 1,
    "photo_name": "我的全身照",
    "is_primary": true
  }
}
```



------

## 5. 辅助API

### 5.1 获取衣物分类选项

获取所有衣物分类、季节、状况等枚举选项。

- **URL**: `GET /api/clothing/categories`
- **认证**: 不需要Token验证

#### 成功响应

```json
{
  "success": true,
  "data": {
    "categories": [
      {"value": "top", "label": "上衣"},
      {"value": "bottom", "label": "下装"}
    ],
    "subcategories": {
      "top": [
        {"value": "t-shirt", "label": "T恤"},
        {"value": "shirt", "label": "衬衫"}
      ]
    },
    "seasons": [
      {"value": "spring", "label": "春季"},
      {"value": "summer", "label": "夏季"}
    ],
    "conditions": [
      {"value": "new", "label": "全新"},
      {"value": "good", "label": "良好"}
    ]
  }
}
```



------

## 6. 错误响应格式

所有API返回统一的错误响应格式：

```json
{
  "success": false,
  "message": "错误描述",
  "status_code": 400
}
```

常见状态码：

- `200`: 成功
- `400`: 请求参数错误
- `401`: 未授权/Token无效
- `403`: 禁止访问
- `404`: 资源不存在
- `500`: 服务器内部错误

------

## 注意事项

1. 所有需要认证的API必须在请求中携带`token`参数
2. 图片上传支持格式：jpg, jpeg, png, webp, gif
3. 单个文件最大大小：10MB
4. 模特照片支持软删除和硬删除两种模式
5. 批量操作API支持同时处理多个衣物