# API 文档 - 登录与注册模块（Vue3 + UniApp）

## 概述

本文档介绍个人AI衣柜助手系统中的用户认证相关API，包括用户注册、登录和Token验证等功能。所有API均基于RESTful架构设计，使用JSON格式进行数据交换。

## 基础信息

- **基础URL**: http://localhost:8000
- **API前缀**: /api/auth
- **认证方式**: JWT Token (Bearer Token)
- **响应格式**: JSON

---

### **API列表**



## 1. 用户登录接口

### 接口信息

- **接口路径**: `/api/auth/login`
- **请求方法**: `POST`
- **接口描述**: 用户登录并获取JWT访问令牌

### 请求参数

#### Headers

```
Content-Type: application/json
```

#### Body 参数

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| username | string | 是 | 用户名或邮箱 | "john_doe" |
| password | string | 是 | 密码 | "password123" |
| remember | boolean | 否 | 记住我选项，默认false | true |

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
| success | boolean | 请求是否成功 | true |
| message | string | 响应消息 | "登录成功" |
| access_token | string | JWT访问令牌 | "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."- |
| token_type | string | Token类型 | "bearer" |
| user_id | number | 用户ID | 12345 |
| username | string | 用户名 | "john_doe" |
| email | string | 邮箱地址 | "john@example.com" |
| expiresIn | number | Token有效期（秒） | 3600 |
| remember | boolean | 是否记住登录状态 | true |
| status_code | number | HTTP状态码 | 200 |

#### 成功响应示例

```json
{
  "success": true,
  "message": "登录成功",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 12345,
  "username": "john_doe",
  "email": "john@example.com",
  "expires_in": 604800,
  "remember": true,
  "status_code": 200
}
```

#### 错误响应

| HTTP 状态码 | success | message | 说明 |
|------------|------|---------|------|
| 400 | false | "请求参数错误" | 请求参数格式错误 |
| 401 | false   | "用户名或密码错误" | 认证失败 |
| 401 | false | "无效的token" | Token验证失败 |
| 403 | false | "账号已被禁用，请联系管理员" | 账户状态异常 |
| 500 | false | "服务器内部错误" | 服务器异常 |

#### 错误响应示例

```json
{
  "success": false,
  "message": "用户名或密码错误",
  "status_code": 401
}
```

### 前端处理逻辑

1. **前端验证**
   - 检查用户名是否为空
   - 检查密码是否为空
   - 验证失败：前端提示，不发送请求

2. **请求发送**
   
   - 使用 `uni.request` 发送 POST 请求到`/api/auth/login`
   - 可选择性传 `remember` 参数（用于后端决定 token 过期策略）
   
3. **成功处理**
   - 存储 token 到本地：`uni.setStorageSync('token', access_token)`
   
     存储用户信息：`uni.setStorageSync('userInfo', { user_id, username, email })`

     跳转主页面：`uni.redirectTo({ url: '/pages/index/index' })`
   
4. **错误处理**
   - 显示后端返回的错误消息（`uni.showToast`）
   - 不跳转页面

---



## 2. 用户注册接口

### 接口信息

- **接口路径**: `/api/auth/register`
- **请求方法**: `POST`
- **接口描述**: 新用户注册账号

### 请求参数

#### Headers

```
Content-Type: application/json
```

#### Body 参数

| 参数名 | 类型 | 必填 | 说明 | 验证规则 | 示例值 |
|--------|------|------|------|----------|--------|
| email | string | 是 | 邮箱地址 | 符合邮箱格式 | "john@example.com" |
| username | string | 是 | 用户名 | 非空 | "john_doe" |
| password | string | 是 | 密码 | 至少 6 位字符（或后端规则） | "password123" |
| confirm_password | string | 是 | 确认密码 | 必须与password一致 | "password123" |

**说明（重要）**：后端会接收并验证 `confirm_password`，确保与 `password` 一致

#### 请求示例

```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "password123",
  "confirm_password": "password123"
}
```

### 响应参数

#### 成功响应 (HTTP 200)

| 参数名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| success | boolean | 请求是否成功 | true |
| message | string | 响应消息 | "注册成功" |
| data | object | 用户数据 | - |
| data.id | number | 用户ID | 12345 |
| data.username | string | 用户名 | "john_doe" |
| data.email | string | 邮箱地址 | "john@example.com" |
| data.is_active | boolean | 是否激活 | true |
| data.created_at | string | 创建时间 | "2024-01-15T10:30:00" |
| status_code | number | HTTP状态码 | 200 |

#### 成功响应示例

```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "id": 12345,
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00"
  },
  "status_code": 200
}
```

#### 错误响应

| HTTP 状态码 | success | message | 说明 |
|------------|------|---------|------|
| 400 | false | "邮箱地址不能为空" | 邮箱参数缺失 |
| 400 | false | "邮箱格式不正确" | 邮箱格式验证失败 |
| 400 | false | "用户名不能为空" | 用户名参数缺失 |
| 400 | false | "密码不能为空" | 密码参数缺失 |
| 400 | false | "密码长度至少6位" | 密码长度不足 |
| 409 | false | "邮箱已被注册" | 邮箱已存在 |
| 409 | false | "用户名已被使用" | 用户名已存在 |
| 500 | false | "服务器内部错误" | 服务器异常 |

**注意**："两次密码不一致"属于前端校验范畴（因为后端不会收到 `confirmPassword`）。

#### 错误响应示例

```json
{
  "success": false,
  "message": "用户名已被注册",
  "status_code": 409
}
```

### 前端处理逻辑

1. **前端验证**
   - 检查邮箱是否为空
   - 检查用户名是否为空
   - 检查密码是否为空、长度是否达标
   - 检查 `confirmPassword` 是否为空、是否与 `password` 一致
   - 验证失败：前端提示，不发送请求给后端
2. **请求发送**
   - 发送完整数据：`username` +` emai`l + `password` + `confirm_password`
3. **成功处理**
   - 显示成功提示（`uni.showToast`）
   - 跳转到登录页面（`/pages/login/login`）
4. **错误处理**
   - 展示后端 message（`uni.showToast`）
   - 不跳转页面

---



## 3.Token 验证接口

#### 接口信息

- **接口路径**: `/api/auth/verify`
- **请求方法**: `GET`
- **接口描述**: 验证JWT Token的有效性并获取用户信息

#### 请求参数

##### Query 参数

| 参数名 | 类型   | 必填 | 说明        | 示例值                                    |
| :----- | :----- | :--- | :---------- | :---------------------------------------- |
| token  | string | 是   | JWT访问令牌 | "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." |

##### 请求示例

```text
GET /api/auth/verify?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 响应参数

##### 成功响应 (HTTP 200)

| 参数名     | 类型    | 说明          | 示例值                |
| :--------- | :------ | :------------ | :-------------------- |
| valid      | boolean | Token是否有效 | true                  |
| user_id    | number  | 用户ID        | 12345                 |
| username   | string  | 用户名        | "john_doe"            |
| email      | string  | 邮箱地址      | "john@example.com"    |
| is_active  | boolean | 是否激活      | true                  |
| created_at | string  | 创建时间      | "2024-01-15T10:30:00" |

##### 成功响应示例

```json
{
  "valid": true,
  "user_id": 12345,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00"
}
```

##### 错误响应

| HTTP 状态码 | 说明              |
| :---------- | :---------------- |
| 401         | 无效或过期的token |
| 403         | 账号已被禁用      |
| 404         | 用户不存在        |

##### 错误响应示例

```json
{
  "success": false,
  "message": "无效或过期的token",
  "status_code": 401
}
```

### 前端处理逻辑

1. **使用场景**

   - 应用启动时检查本地存储的token是否有效
   - 访问需要认证的页面时验证token有效性
   - 定期检查token状态

2. **调用时机**

   ```javascript
   // 应用启动时
   App.vue 或 main.js 中调用
   
   // 访问需要认证的页面时
   onLoad() {
     this.checkTokenValidity()
   }
   ```

   

3. **处理逻辑**

   - 从本地存储获取token：`uni.getStorageSync('token')`
   - 发送验证请求
   - 有效：更新用户信息，允许访问
   - 无效：清除本地token，跳转到登录页



## 4.获取当前用户信息

#### 接口信息

- **接口路径**: `/api/users/me`
- **请求方法**: `GET`
- **接口描述**: 通过Token获取当前登录用户的详细信息
- **认证要求**: 需要有效的JWT Token

#### 请求参数

##### Query 参数

| 参数名 | 类型   | 必填 | 说明        | 示例值                                    |
| :----- | :----- | :--- | :---------- | :---------------------------------------- |
| token  | string | 是   | JWT访问令牌 | "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." |

##### 请求示例

```text
GET /api/users/me?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 响应参数

##### 成功响应 (HTTP 200)

返回完整的用户信息对象，包含以下字段：

| 参数名     | 类型    | 说明         | 示例值                |
| :--------- | :------ | :----------- | :-------------------- |
| id         | number  | 用户ID       | 12345                 |
| username   | string  | 用户名       | "john_doe"            |
| email      | string  | 邮箱地址     | "john@example.com"    |
| is_active  | boolean | 是否激活     | true                  |
| created_at | string  | 创建时间     | "2024-01-15T10:30:00" |
| last_login | string  | 最后登录时间 | "2024-01-16T14:20:00" |

##### 成功响应示例

```json
{
  "id": 12345,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00",
  "last_login": "2024-01-16T14:20:00"
}
```

##### 错误响应

同Token验证接口的错误响应。

### 前端处理逻辑

1. **使用场景**

   - 个人中心页面显示用户信息
   - 应用启动时获取最新用户信息
   - 用户信息更新后刷新显示

2. **调用方式**

   ```javascript
   // 在需要获取用户信息的地方调用
   const getUserInfo = async () => {
     const token = uni.getStorageSync('token')
     const res = await uni.request({
       url: '/api/users/me',
       method: 'GET',
       data: { token }
     })
     if (res.data && res.data.id) {
       uni.setStorageSync('userInfo', res.data)
       return res.data
     }
     return null
   }
   ```

3. **错误处理**

   - Token无效时自动跳转到登录页
   - 网络错误时显示友好提示



## 5. 忘记密码接口（预留）

#### 接口信息

- **接口路径**: `/api/forgot-password`
- **请求方法**: `POST`
- **接口描述**: 发送密码重置邮件
- **状态**: 接口已定义，邮件发送逻辑待实现

#### 请求参数

##### Query 参数

| 参数名 | 类型   | 必填 | 说明         | 示例值             |
| :----- | :----- | :--- | :----------- | :----------------- |
| email  | string | 是   | 用户注册邮箱 | "john@example.com" |

##### 请求示例

```text
POST /api/forgot-password?email=john@example.com
```

#### 响应参数

##### 成功响应 (HTTP 200)

```json
{
  "message": "重置密码链接已发送到邮箱"
}
```

##### 预留实现

当前返回固定消息，实际功能需要配置邮件服务后实现。

---



## 6. 重置密码接口（预留）

#### 接口信息

- **接口路径**: `/api/reset-password`
- **请求方法**: `POST`
- **接口描述**: 重置用户密码
- **状态**: 接口已定义，具体逻辑待实现

#### 请求参数

##### Query 参数

| 参数名       | 类型   | 必填 | 说明         | 示例值               |
| :----------- | :----- | :--- | :----------- | :------------------- |
| token        | string | 是   | 密码重置令牌 | "reset_token_abc123" |
| new_password | string | 是   | 新密码       | "newpassword123"     |

##### 请求示例

```text
POST /api/reset-password?token=reset_token_abc123&new_password=newpassword123
```

#### 响应参数

##### 成功响应 (HTTP 200)

```json
{
  "message": "密码重置成功"
}
```

##### 预留实现

当前返回固定消息，实际功能需要密码重置流程完整实现。

---



## 7. 通用响应格式

所有接口应遵循统一的响应格式：

**成功响应格式**:

```json
{
  "success": boolean,      // 请求是否成功
  "message": string,       // 响应消息
  "data": any,            // 响应数据（可选）
  "status_code": number   // HTTP状态码
}
```



**错误响应格式**:

```json
{
  "success": false,
  "message": "错误描述",
  "status_code": number
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



## 8. 前端请求示例代码（uni.request）

### 登录请求示例

```javascript
// pages/login/login.vue
const handleLogin = async () => {
  // 前端验证
  if (!formData.value.username) {
    uni.showToast({ title: '请输入用户名', icon: 'none' })
    return
  }
  if (!formData.value.password) {
    uni.showToast({ title: '请输入密码', icon: 'none' })
    return
  }
  
  // 发送请求
  try {
    const res = await uni.request({
      url: 'http://localhost:8000/api/auth/login',
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: {
        username: formData.value.username,
        password: formData.value.password,
        remember: formData.value.remember || false
      }
    })

    if (res.data.success) {
      // 存储 token
      uni.setStorageSync('token', res.data.access_token)
      
      // 存储用户信息
      uni.setStorageSync('userInfo', {
        user_id: res.data.user_id,
        username: res.data.username,
        email: res.data.email
      })
      
      // 显示成功提示
      uni.showToast({
        title: '登录成功',
        icon: 'success',
        duration: 1500
      })
      
      // 跳转到主页面
      setTimeout(() => {
        uni.switchTab({
          url: '/pages/index/index'
        })
      }, 1500)
    } else {
      // 显示错误信息
      uni.showToast({
        title: res.data.message || '登录失败',
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

### 注册请求示例

```javascript
// pages/register/register.vue
const handleRegister = async () => {
  // 前端验证
  if (!formData.value.username || formData.value.username.length < 4) {
    uni.showToast({ title: '用户名至少4个字符', icon: 'none' })
    return
  }
  if (!formData.value.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.value.email)) {
    uni.showToast({ title: '请输入正确的邮箱地址', icon: 'none' })
    return
  }
  if (!formData.value.password || formData.value.password.length < 6) {
    uni.showToast({ title: '密码至少6位', icon: 'none' })
    return
  }
  if (formData.value.password !== formData.value.confirm_password) {
    uni.showToast({ title: '两次密码不一致', icon: 'none' })
    return
  }

  try {
    const res = await uni.request({
      url: 'http://localhost:8000/api/auth/register',
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: {
        username: formData.value.username,
        email: formData.value.email,
        password: formData.value.password,
        confirm_password: formData.value.confirm_password
      }
    })

    if (res.data.success) {
      // 显示成功提示
      uni.showToast({
        title: '注册成功',
        icon: 'success',
        duration: 2000
      })
      
      // 跳转到登录页面
      setTimeout(() => {
        uni.redirectTo({ 
          url: '/pages/login/login?username=' + encodeURIComponent(formData.value.username)
        })
      }, 1500)
    } else {
      uni.showToast({ 
        title: res.data.message || '注册失败', 
        icon: 'none' 
      })
    }
  } catch (e) {
    console.error(e)
    uni.showToast({ 
      title: '网络错误，请稍后再试', 
      icon: 'none' 
    })
  }
}
```

#### Token验证示例

```javascript
// utils/auth.js
const checkTokenValidity = async () => {
  const token = uni.getStorageSync('token')
  if (!token) {
    return false
  }

  try {
    const res = await uni.request({
      url: 'http://localhost:8000/api/auth/verify',
      method: 'GET',
      data: { token }
    })

    // 如果返回了 valid 字段且为 true，说明 token 有效
    if (res.data && res.data.valid) {
      // 更新用户信息
      uni.setStorageSync('userInfo', {
        user_id: res.data.user_id,
        username: res.data.username,
        email: res.data.email
      })
      return true
    }
  } catch (error) {
    console.error('Token验证失败:', error)
  }

  // token 无效或验证失败，清除本地存储
  uni.removeStorageSync('token')
  uni.removeStorageSync('userInfo')
  return false
}

// 在应用启动时或需要验证的地方调用
const initAuth = async () => {
  const isValid = await checkTokenValidity()
  if (!isValid) {
    // token 无效，跳转到登录页
    uni.redirectTo({
      url: '/pages/login/login'
    })
  }
}
```

#### 请求拦截器示例

```javascript
// utils/request.js
const baseURL = 'http://localhost:8000'

const request = (options) => {
  return new Promise((resolve, reject) => {
    // 自动添加 token 到请求
    const token = uni.getStorageSync('token')
    if (token) {
      if (!options.header) options.header = {}
      options.header['Authorization'] = `Bearer ${token}`
    }

    // 添加基础 URL
    if (!options.url.startsWith('http')) {
      options.url = baseURL + options.url
    }

    uni.request({
      ...options,
      success: (res) => {
        if (res.statusCode === 401) {
          // token 过期，跳转到登录页
          uni.removeStorageSync('token')
          uni.removeStorageSync('userInfo')
          uni.showToast({
            title: '登录已过期，请重新登录',
            icon: 'none'
          })
          setTimeout(() => {
            uni.redirectTo({
              url: '/pages/login/login'
            })
          }, 1500)
          reject(new Error('登录已过期'))
          return
        }
        resolve(res)
      },
      fail: (err) => {
        uni.showToast({
          title: '网络错误，请检查网络连接',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

export default request
```

---



## 9. Token使用方式

#### 1. Header携带方式

在后续需要认证的API请求中，将Token放在Authorization Header中：

text

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 2. Query参数方式

部分API也支持通过查询参数传递Token：

text

```
GET /api/clothing?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 3. Token有效期策略

- **记住我模式**：7天有效期（604800秒）
- **非记住我模式**：2小时有效期（7200秒）



## 10. 安全建议

1. **HTTPS**：生产环境必须使用HTTPS协议
2. **Token存储**：使用 `uni.setStorageSync`，避免明文持久化
3. **输入验证**：前端做基础校验，后端必须做完整校验
4. **频率限制**：登录/注册建议限流（如每分钟最多5次）
5. **敏感信息**：密码等敏感信息在前端不应明文显示或存储
6. **Token刷新**：当前版本需要重新登录获取新Token，后续可增加Token刷新机制



## 11. 测试用例

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



### 联系方式

如有疑问，请联系前端开发团队。

**文档版本**: v1.1  
**最后更新**: 2026-01-23
