# API 文档 - 登录与注册模块（Vue3 + UniApp）

## 概述

本文档描述了前端登录页面（`pages/login/login.vue`）和注册页面（`pages/register/register.vue`）所需的 API 接口规范。

**基础 URL**: `https://your-api-domain.com/api`（请根据实际环境修改）

**请求格式**: `application/json`

**响应格式**: `application/json`

---

## 1. 用户登录接口

### 接口信息

- **接口路径**: `/auth/login`
- **请求方法**: `POST`
- **接口描述**: 用户通过用户名和密码登录系统

### 请求参数

#### Headers

```
Content-Type: application/json
```

#### Body 参数

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| username | string | 是 | 用户名 | "john_doe" |
| password | string | 是 | 密码（明文，后端需加密验证） | "password123" |
| remember | boolean | 否 | 是否记住登录状态（可用于后端设置更长 token 过期时间） | true |

#### 请求示例

```json
{
  "username": "john_doe",
  "password": "password123",
  "remember": true
}
```

### 响应参数

#### 成功响应 (HTTP 200)

| 参数名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| code | number | 状态码，200 表示成功 | 200 |
| message | string | 响应消息 | "登录成功" |
| data | object | 用户数据 | - |
| data.token | string | 访问令牌（JWT） | "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." |
| data.refreshToken | string | 刷新令牌（可选） | "refresh_token_string" |
| data.user | object | 用户信息 | - |
| data.user.id | number | 用户ID | 12345 |
| data.user.username | string | 用户名 | "john_doe" |
| data.user.email | string | 邮箱地址 | "john@example.com" |
| data.user.avatar | string | 头像URL（可选） | "https://example.com/avatar.jpg" |
| data.expiresIn | number | token 过期时间（秒） | 3600 |

#### 成功响应示例

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx",
    "refreshToken": "refresh_token_string",
    "user": {
      "id": 12345,
      "username": "john_doe",
      "email": "john@example.com",
      "avatar": "https://example.com/avatar.jpg"
    },
    "expiresIn": 3600
  }
}
```

#### 错误响应

| HTTP 状态码 | code | message | 说明 |
|------------|------|---------|------|
| 400 | 400 | "用户名不能为空" | 用户名参数缺失 |
| 400 | 400 | "密码不能为空" | 密码参数缺失 |
| 401 | 401 | "用户名或密码错误" | 认证失败 |
| 401 | 401 | "账户已被禁用" | 账户状态异常 |
| 500 | 500 | "服务器内部错误" | 服务器异常 |

#### 错误响应示例

```json
{
  "code": 401,
  "message": "用户名或密码错误",
  "data": null
}
```

### 前端处理逻辑

1. **前端验证**
   - 检查用户名是否为空
   - 检查密码是否为空
   - 验证失败：前端提示，不发送请求

2. **请求发送**
   - 使用 `uni.request` 发送 POST 请求
   - 可选择性传 `remember` 参数（用于后端决定 token 过期策略）

3. **成功处理**
   - 存储 token、refreshToken（如果后端返回）到本地：`uni.setStorageSync`
   - 存储 userInfo
   - 跳转主页面：`/pages/index/index`

4. **错误处理**
   - 显示后端返回的错误消息（`uni.showToast`）
   - 不跳转页面

---

## 2. 用户注册接口

### 接口信息

- **接口路径**: `/auth/register`
- **请求方法**: `POST`
- **接口描述**: 新用户注册账号

### 请求参数

#### Headers

```
Content-Type: application/json
```

#### Body 参数（✅ confirmPassword 不传后端）

| 参数名 | 类型 | 必填 | 说明 | 验证规则 | 示例值 |
|--------|------|------|------|----------|--------|
| email | string | 是 | 邮箱地址 | 符合邮箱格式 | "john@example.com" |
| username | string | 是 | 用户名 | 非空 | "john_doe" |
| password | string | 是 | 密码 | 至少 6 位字符（或后端规则） | "password123" |

**说明（重要）**：`confirmPassword` 仅用于前端校验（与 `password` 是否一致），不会发送给后端。

#### 请求示例（✅ 不包含 confirmPassword）

```json
{
  "email": "john@example.com",
  "username": "john_doe",
  "password": "password123"
}
```

### 响应参数

#### 成功响应 (HTTP 200)

| 参数名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| code | number | 状态码，200 表示成功 | 200 |
| message | string | 响应消息 | "注册成功" |
| data | object | 用户数据 | - |
| data.user | object | 用户信息 | - |
| data.user.id | number | 用户ID | 12345 |
| data.user.username | string | 用户名 | "john_doe" |
| data.user.email | string | 邮箱地址 | "john@example.com" |

#### 成功响应示例

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "user": {
      "id": 12345,
      "username": "john_doe",
      "email": "john@example.com"
    }
  }
}
```

#### 错误响应

| HTTP 状态码 | code | message | 说明 |
|------------|------|---------|------|
| 400 | 400 | "邮箱地址不能为空" | 邮箱参数缺失 |
| 400 | 400 | "邮箱格式不正确" | 邮箱格式验证失败 |
| 400 | 400 | "用户名不能为空" | 用户名参数缺失 |
| 400 | 400 | "密码不能为空" | 密码参数缺失 |
| 400 | 400 | "密码长度至少6位" | 密码长度不足 |
| 409 | 409 | "邮箱已被注册" | 邮箱已存在 |
| 409 | 409 | "用户名已被使用" | 用户名已存在 |
| 500 | 500 | "服务器内部错误" | 服务器异常 |

**注意**："两次密码不一致"属于前端校验范畴（因为后端不会收到 `confirmPassword`）。

#### 错误响应示例

```json
{
  "code": 409,
  "message": "邮箱已被注册",
  "data": null
}
```

### 前端处理逻辑

1. **前端验证**
   - 检查邮箱是否为空
   - 检查邮箱格式（示例正则：`/^[^\s@]+@[^\s@]+\.[^\s@]+$/`）
   - 检查用户名是否为空
   - 检查密码是否为空、长度是否达标
   - 检查 `confirmPassword` 是否为空、是否与 `password` 一致
   - 验证失败：前端提示，不发送请求给后端

2. **请求发送**
   - 仅发送：`email` + `username` + `password`

3. **成功处理**
   - 显示成功提示（`uni.showToast`）
   - 跳转到登录页面（`/pages/login/login`）

4. **错误处理**
   - 展示后端 message（`uni.showToast`）
   - 不跳转页面

---

## 3. 忘记密码接口（预留）

### 接口信息

- **接口路径**: `/auth/forgot-password`
- **请求方法**: `POST`
- **接口描述**: 用户忘记密码时发送重置密码邮件

**状态**: 当前前端仅显示占位提示，接口待实现

### 请求参数

#### Headers

```
Content-Type: application/json
```

#### Body 参数

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| email | string | 是 | 注册时使用的邮箱地址 | "john@example.com" |

#### 请求示例

```json
{
  "email": "john@example.com"
}
```

### 响应参数

#### 成功响应 (HTTP 200)

```json
{
  "code": 200,
  "message": "重置密码邮件已发送，请查收",
  "data": null
}
```

#### 错误响应

| HTTP 状态码 | code | message | 说明 |
|------------|------|---------|------|
| 400 | 400 | "邮箱地址不能为空" | 邮箱参数缺失 |
| 400 | 400 | "邮箱格式不正确" | 邮箱格式验证失败 |
| 404 | 404 | "该邮箱未注册" | 邮箱不存在 |
| 500 | 500 | "服务器内部错误" | 服务器异常 |

---

## 4. Token 刷新接口（可选）

### 接口信息

- **接口路径**: `/auth/refresh-token`
- **请求方法**: `POST`
- **接口描述**: 使用 refreshToken 刷新 accessToken

### 请求参数（✅ refreshToken 仅在 Body 传）

#### Headers

```
Content-Type: application/json
```

#### Body 参数

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| refreshToken | string | 是 | 刷新令牌 | "refresh_token_string" |

#### 请求示例

```json
{
  "refreshToken": "refresh_token_string"
}
```

### 响应参数

#### 成功响应 (HTTP 200)

```json
{
  "code": 200,
  "message": "Token 刷新成功",
  "data": {
    "token": "new_access_token",
    "expiresIn": 3600
  }
}
```

#### 典型错误响应

| HTTP 状态码 | code | message | 说明 |
|------------|------|---------|------|
| 401 | 401 | "refreshToken 无效或已过期" | refreshToken 失效 |
| 500 | 500 | "服务器内部错误" | 服务器异常 |

---

## 5. 通用响应格式

所有接口应遵循统一的响应格式：

```json
{
  "code": number,      // 状态码：200 成功，4xx 客户端错误，5xx 服务器错误
  "message": string,    // 响应消息
  "data": any          // 响应数据，成功时返回具体数据，失败时为 null
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
| 409 | 资源冲突（如用户名/邮箱已存在） | 409 |
| 500 | 服务器内部错误 | 500 |

---

## 6. 前端请求示例代码（uni.request）

### 登录请求示例

```javascript
// pages/login/login.vue
const handleLogin = async () => {
  // 前端验证
  if (!formData.value.username) {
    uni.showToast({
      title: '請輸入用戶名',
      icon: 'none'
    })
    return
  }
  if (!formData.value.password) {
    uni.showToast({
      title: '請輸入密碼',
      icon: 'none'
    })
    return
  }
  
  // 发送请求
  try {
    const res = await uni.request({
      url: 'https://your-api-domain.com/api/auth/login',
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: {
        username: formData.value.username,
        password: formData.value.password,
        remember: formData.value.remember
      }
    })

    if (res.statusCode === 200 && res.data.code === 200) {
      // 存储 token
      uni.setStorageSync('token', res.data.data.token)
      if (res.data.data.refreshToken) {
        uni.setStorageSync('refreshToken', res.data.data.refreshToken)
      }
      
      // 存储用户信息
      uni.setStorageSync('userInfo', res.data.data.user)
      
      // 显示成功提示
      uni.showToast({
        title: '登录成功',
        icon: 'success',
        duration: 1500
      })
      
      // 跳转到主页面
      setTimeout(() => {
        uni.redirectTo({
          url: '/pages/index/index'
        })
      }, 1500)
    } else {
      // 显示错误信息
      uni.showToast({
        title: res.data.message || '登录失敗',
        icon: 'none'
      })
    }
  } catch (error) {
    console.error('登录请求失败:', error)
    uni.showToast({
      title: '网络错误，请稍后再试',
      icon: 'none'
    })
  }
}
```

### 注册请求示例（✅ 不发送 confirmPassword）

```javascript
// pages/register/register.vue
const handleRegister = async () => {
  // 注意：confirmPassword 仅用于前端校验，不会发送给后端
  if (!formData.value.email) {
    uni.showToast({ title: '请输入邮箱', icon: 'none' })
    return
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.value.email)) {
    uni.showToast({ title: '邮箱格式不正确', icon: 'none' })
    return
  }
  if (!formData.value.username) {
    uni.showToast({ title: '请输入用户名', icon: 'none' })
    return
  }
  if (!formData.value.password || formData.value.password.length < 6) {
    uni.showToast({ title: '密码至少6位', icon: 'none' })
    return
  }
  if (!formData.value.confirmPassword) {
    uni.showToast({ title: '请再次输入密码', icon: 'none' })
    return
  }
  if (formData.value.password !== formData.value.confirmPassword) {
    uni.showToast({ title: '两次密码不一致', icon: 'none' })
    return
  }

  try {
    const res = await uni.request({
      url: 'https://your-api-domain.com/api/auth/register',
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: {
        email: formData.value.email,
        username: formData.value.username,
        password: formData.value.password
      }
    })

    if (res.statusCode === 200 && res.data.code === 200) {
      // 显示成功提示
      uni.showToast({
        title: '註冊成功',
        icon: 'success',
        duration: 2000
      })
      
      // 跳转到登录页面
      setTimeout(() => {
        uni.redirectTo({ url: '/pages/login/login' })
      }, 1500)
    } else {
      uni.showToast({ title: res.data.message || '注册失败', icon: 'none' })
    }
  } catch (e) {
    console.error(e)
    uni.showToast({ title: '网络错误，请稍后再试', icon: 'none' })
  }
}
```

### refreshToken 刷新示例（✅ 仅 Body 传）

```javascript
const refreshAccessToken = async () => {
  const refreshToken = uni.getStorageSync('refreshToken')
  if (!refreshToken) return null

  const res = await uni.request({
    url: 'https://your-api-domain.com/api/auth/refresh-token',
    method: 'POST',
    header: { 'Content-Type': 'application/json' },
    data: { refreshToken }
  })

  if (res.statusCode === 200 && res.data.code === 200) {
    uni.setStorageSync('token', res.data.data.token)
    return res.data.data.token
  }
  return null
}
```

---

## 7. 安全建议

1. **密码传输**：必须使用 HTTPS
2. **Token 存储**：使用 `uni.setStorageSync`，避免明文持久化到不安全介质
3. **输入验证**：前端做基础校验，后端必须做完整校验
4. **频率限制**：登录/注册建议限流（如每分钟最多 5 次）

---

## 8. 测试用例

### 登录接口测试

| 测试场景 | 请求参数 | 预期结果 |
|---------|---------|---------|
| 正常登录 | 正确用户名+密码 | 返回 200，包含 token 与 user |
| 用户名为空 | username: "" | 返回 400，提示"用户名不能为空" |
| 密码为空 | password: "" | 返回 400，提示"密码不能为空" |
| 用户名不存在 | username: "not_exist" | 返回 401，提示"用户名或密码错误" |
| 密码错误 | 错误密码 | 返回 401，提示"用户名或密码错误" |

### 注册接口测试

| 测试场景 | 请求参数 | 预期结果 |
|---------|---------|---------|
| 正常注册 | 合法邮箱+用户名+密码 | 返回 200，提示"注册成功" |
| 邮箱格式错误 | email: "invalid" | 返回 400，提示"邮箱格式不正确" |
| 邮箱已存在 | 已注册邮箱 | 返回 409，提示"邮箱已被注册" |
| 用户名已存在 | 已使用用户名 | 返回 409，提示"用户名已被使用" |
| 密码长度不足 | password: "12345" | 返回 400，提示"密码长度至少6位" |
| 两次密码不一致（前端） | password != confirmPassword | 前端拦截，不发送请求 |

---

## 9. 联系方式

如有疑问，请联系前端开发团队。

**文档版本**: v1.1  
**最后更新**: 2026-01-23
