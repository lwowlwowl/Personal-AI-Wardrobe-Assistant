# API 文档 - 虚拟试穿模块（Vue3 + UniApp）

## 概述

本文档描述了前端虚拟试穿页面（`pages/index/components/VirtualTryOn.vue`）所需的 API 接口规范。

**基础 URL**: `https://your-api-domain.com/api`（请根据实际环境修改）

**请求格式**: 
- 文件上传：`multipart/form-data`
- 生成接口：`application/json`

**响应格式**: `application/json`

---

## 通用约定（建议）

### Headers（如需登录）

若你的系统对上传/生成接口有鉴权需求，建议统一使用：

```
Authorization: Bearer <token>
```

> 若目前未接入登录鉴权，可忽略该 Header。

---

## 接口流程说明

**重要**：由于 `uni.uploadFile` 一次只能上传一个文件，无法在同一个请求中同时上传两张图片，因此采用**两步上传方案**：

1. **Step 1**：用户选择图片后，前端立即上传到服务器，获取文件 ID（`fileId`）
2. **Step 2**：用户点击 Generate 按钮时，前端将两张图片的 `fileId` 发送给后端进行生成

这样的设计既符合用户操作流程（先上传图片，再生成），又避免了 uni-app 的技术限制。

---

## 1. 文件上传接口

### 接口信息

- **接口路径**: `/files/upload`
- **请求方法**: `POST`
- **接口描述**: 上传图片文件到服务器，返回文件 ID（`fileId`）（可选返回 `fileUrl` 供前端预览）

### 请求参数

#### Headers

```
Content-Type: multipart/form-data
```

**注意**：`uni.uploadFile` 会自动设置正确的 Content-Type。

#### Form Data 参数

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| file | File | 是 | 图片文件 | 图片文件对象 |

**图片格式要求**：
- 支持格式：JPG、PNG
- 文件大小：建议不超过 10MB
- 人物模型图片：建议使用竖版（portrait）图片，包含完整人物
- 试穿衣服图片：建议使用平铺图（flat lay），清晰展示服装细节

### 响应参数

#### 成功响应 (HTTP 200)

| 参数名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| code | number | 状态码，200 表示成功 | 200 |
| message | string | 响应消息 | "上传成功" |
| data | object | 文件数据 | - |
| data.fileId | string | 文件 ID（用于后续生成接口，建议必返） | "file_123456789" |
| data.fileUrl | string | 文件访问 URL（可选，仅用于前端预览/展示） | "https://example.com/files/xxx.jpg" |

#### 成功响应示例

```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "fileId": "file_123456789",
    "fileUrl": "https://example.com/files/person_123456789.jpg"
  }
}
```

**说明**：
- 建议后端**至少返回 `fileId`**，这样生成接口只需传 ID，语义统一且实现最简单。
- `fileUrl` 若返回，仅用于前端预览/展示（本方案下生成接口不接受 URL 输入）。
- ⚠️ `fileUrl` **仅用于前端展示**，后端业务逻辑、生成接口、模型调用 **不依赖 URL**。

#### 错误响应

| HTTP 状态码 | code | message | 说明 |
|------------|------|---------|------|
| 400 | 400 | "文件不能为空" | file 参数缺失 |
| 400 | 400 | "图片格式不支持，仅支持 JPG、PNG" | 图片格式验证失败 |
| 400 | 400 | "图片文件过大，最大支持 10MB" | 文件大小超限 |
| 400 | 400 | "图片解析失败" | 图片文件损坏或格式错误 |
| 500 | 500 | "文件上传失败" | 服务器存储异常 |
| 500 | 500 | "服务器内部错误" | 服务器异常 |

#### 错误响应示例

```json
{
  "code": 400,
  "message": "图片格式不支持，仅支持 JPG、PNG",
  "data": null
}
```

---

## 2. 虚拟试穿生成接口

### 接口信息

- **接口路径**: `/virtual-tryon/generate`
- **请求方法**: `POST`
- **接口描述**: 根据已上传的人物图片和衣服图片的文件 ID（`fileId`），调用 qwen-image-edit 模型生成虚拟试穿结果图片

### 请求参数

#### Headers

```
Content-Type: application/json
```

#### Body 参数

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| personFileId | string | 是 | 人物图片文件 ID | "file_123456789" |
| clothingFileId | string | 是 | 衣服图片文件 ID | "file_987654321" |

**说明**：
- 推荐使用 `fileId`，因为更简洁且便于后端管理
- 如果提供 `fileId`，后端需要通过文件服务根据 ID 获取实际文件

#### 请求示例

```json
{
  "personFileId": "file_123456789",
  "clothingFileId": "file_987654321"
}
```

### 响应参数

#### 成功响应 (HTTP 200)

| 参数名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| code | number | 状态码，200 表示成功 | 200 |
| message | string | 响应消息 | "生成成功" |
| data | object | 生成结果数据 | - |
| data.resultImageUrl | string | 生成的虚拟试穿结果图片 URL | "https://example.com/results/virtual-tryon-123456789.jpg" |
| data.resultImageBase64 | string | 生成的虚拟试穿结果图片 Base64 编码（可选） | "data:image/jpeg;base64,/9j/4AAQ..." |
| data.taskId | string | 任务 ID（可选，用于查询任务状态） | "task_123456789" |
| data.generationTime | number | 生成耗时（秒，可选） | 15.3 |

#### 成功响应示例

```json
{
  "code": 200,
  "message": "生成成功",
  "data": {
    "resultImageUrl": "https://example.com/results/virtual-tryon-123456789.jpg",
    "resultImageBase64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
    "taskId": "task_123456789",
    "generationTime": 15.3
  }
}
```

**说明**：
- `resultImageUrl` 和 `resultImageBase64` 至少返回其中一个
- 如果返回 URL，前端可以直接使用 `<image :src="resultImageUrl">` 显示
- 如果返回 Base64，前端可以使用 `data:image/jpeg;base64,${resultImageBase64}` 格式显示
- 建议优先使用 URL，Base64 作为备选方案

#### 错误响应

| HTTP 状态码 | code | message | 说明 |
|------------|------|---------|------|
| 400 | 400 | "人物图片文件 ID 不能为空" | personFileId 参数缺失 |
| 400 | 400 | "衣服图片文件 ID 不能为空" | clothingFileId 参数缺失 |
| 404 | 404 | "人物图片文件不存在" | personFileId 对应的文件未找到 |
| 404 | 404 | "衣服图片文件不存在" | clothingFileId 对应的文件未找到 |
| 500 | 500 | "模型调用失败，请稍后重试" | qwen-image-edit 模型调用异常 |
| 500 | 500 | "图片生成失败" | 生图过程出错 |
| 500 | 500 | "服务器内部错误" | 服务器异常 |
| 503 | 503 | "服务暂时不可用，请稍后重试" | 服务过载或维护中 |

#### 错误响应示例

```json
{
  "code": 404,
  "message": "人物图片文件不存在",
  "data": null
}
```

```json
{
  "code": 500,
  "message": "模型调用失败，请稍后重试",
  "data": null
}
```

### 后端处理流程

1. **接收请求**
   - 验证请求参数（personFileId、clothingFileId）
   - 根据 `fileId` 从文件服务/存储中获取两张原图

2. **调用 qwen-image-edit 模型**
   - 将两张图片输入到 qwen-image-edit 模型
   - 调用生图接口生成虚拟试穿结果
   - 等待模型返回生成结果

3. **处理生成结果**
   - 保存生成的图片到服务器或云存储
   - 生成图片访问 URL
   - 或转换为 Base64 编码

4. **返回响应**
   - 返回图片 URL 或 Base64
   - 返回任务相关信息（可选）

---

## 3. 任务状态查询接口（可选）

如果生成过程较长，后端可以实现异步任务机制，前端可以通过此接口查询任务状态。

### 接口信息

- **接口路径**: `/virtual-tryon/status/{taskId}`
- **请求方法**: `GET`
- **接口描述**: 查询虚拟试穿生成任务的状态

### 请求参数

#### URL 参数

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| taskId | string | 是 | 任务 ID（从生成接口返回） | "task_123456789" |

#### 请求示例

```
GET /api/virtual-tryon/status/task_123456789
```

### 响应参数

#### 成功响应 (HTTP 200)

| 参数名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| code | number | 状态码 | 200 |
| message | string | 响应消息 | "查询成功" |
| data | object | 任务状态数据 | - |
| data.status | string | 任务状态：pending（处理中）、completed（已完成）、failed（失败） | "completed" |
| data.progress | number | 任务进度（0-100，可选） | 85 |
| data.resultImageUrl | string | 生成结果图片 URL（status 为 completed 时返回） | "https://example.com/results/xxx.jpg" |
| data.error | string | 错误信息（status 为 failed 时返回） | "模型调用超时" |

#### 响应示例

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "status": "completed",
    "progress": 100,
    "resultImageUrl": "https://example.com/results/virtual-tryon-123456789.jpg"
  }
}
```

---

## 4. 通用响应格式

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
| 500 | 服务器内部错误 | 500 |
| 503 | 服务暂时不可用 | 503 |

---

## 5. 前端请求示例代码（完整实现）

### 完整流程实现

```javascript
// pages/index/components/VirtualTryOn.vue
import { ref, computed } from 'vue'

const personImg = ref('')
const clothingImg = ref('')
const personFileId = ref('') // 存储人物图片文件 ID
const clothingFileId = ref('') // 存储衣服图片文件 ID
const resultImg = ref('') // 存储生成结果
const showResult = ref(false) // 控制结果区域显示
const isLoading = ref(false)
const isUploading = ref(false) // 上传状态

const canGenerate = computed(() => personImg.value && clothingImg.value)

// 上传单张图片
const uploadImage = async (filePath, type) => {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: 'https://your-api-domain.com/api/files/upload',
      filePath: filePath,
      name: 'file',
      success: (res) => {
        try {
          const data = JSON.parse(res.data)
          if (data.code === 200) {
            // 保存文件 ID
            if (type === 'person') {
              personFileId.value = data.data.fileId
            } else {
              clothingFileId.value = data.data.fileId
            }
            resolve(data.data)
          } else {
            reject(new Error(data.message || '上传失败'))
          }
        } catch (e) {
          reject(new Error('响应解析失败'))
        }
      },
      fail: (err) => {
        reject(err)
      }
    })
  })
}

// 用户选择图片后立即上传
const handleImageSelect = async (type) => {
  uni.chooseImage({
    count: 1,
    sizeType: ['original', 'compressed'],
    sourceType: ['album', 'camera'],
    success: async (res) => {
      const tempFilePath = res.tempFilePaths[0]
      
      // 先显示预览
      if (type === 'person') {
        personImg.value = tempFilePath
      } else {
        clothingImg.value = tempFilePath
      }
      
      // 开始上传
      isUploading.value = true
      try {
        await uploadImage(tempFilePath, type)
        uni.showToast({
          title: '上传成功',
          icon: 'success',
          duration: 1500
        })
      } catch (error) {
        console.error('上传失败:', error)
        uni.showToast({
          title: error.message || '上传失败，请重试',
          icon: 'none',
          duration: 3000
        })
        // 上传失败，清除预览
        if (type === 'person') {
          personImg.value = ''
          personFileId.value = ''
        } else {
          clothingImg.value = ''
          clothingFileId.value = ''
        }
      } finally {
        isUploading.value = false
      }
    }
  })
}

// 生成虚拟试穿结果
const handleGenerate = async () => {
  if (!canGenerate.value) {
    return
  }
  
  // 检查是否已上传文件
  if (!personFileId.value || !clothingFileId.value) {
    uni.showToast({
      title: '请先上传图片',
      icon: 'none',
      duration: 2000
    })
    return
  }
  
  // 展开结果区域
  showResult.value = true
  // 开始加载
  isLoading.value = true
  
  // 显示加载提示
  uni.showToast({
    title: 'Generating...',
    icon: 'loading',
    duration: 2000
  })
  
  try {
    // 发送生成请求
    const res = await uni.request({
      url: 'https://your-api-domain.com/api/virtual-tryon/generate',
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: {
        personFileId: personFileId.value,
        clothingFileId: clothingFileId.value
      },
      timeout: 120000 // 设置超时时间为 120 秒（生图可能需要较长时间）
    })
    
    if (res.statusCode === 200 && res.data.code === 200) {
      // 处理生成结果
      isLoading.value = false
      showResult.value = true
      
      // 获取生成的图片
      if (res.data.data.resultImageUrl) {
        resultImg.value = res.data.data.resultImageUrl
      } else if (res.data.data.resultImageBase64) {
        resultImg.value = res.data.data.resultImageBase64
      }
      
      // 显示成功提示
      uni.showToast({
        title: '生成成功',
        icon: 'success',
        duration: 2000
      })
    } else {
      // 处理错误
      isLoading.value = false
      uni.showToast({
        title: res.data.message || '生成失败',
        icon: 'none',
        duration: 3000
      })
    }
  } catch (error) {
    console.error('生成请求失败:', error)
    isLoading.value = false
    uni.showToast({
      title: '网络错误，请稍后再试',
      icon: 'none',
      duration: 3000
    })
  }
}

// 删除图片时清除文件 ID
const removeImage = (type) => {
  if (type === 'person') {
    personImg.value = ''
    personFileId.value = ''
  } else {
    clothingImg.value = ''
    clothingFileId.value = ''
  }
  // 如果两个图片都被删除，隐藏结果区域并重置加载状态
  if (!personImg.value && !clothingImg.value) {
    showResult.value = false
    isLoading.value = false
    resultImg.value = ''
  }
}
```

### 更新模板以支持上传和显示

```vue
<template>
  <view class="virtual-tryon-container">
    <view class="upload-section">
      <view class="upload-item">
        <text class="upload-title">Person Model</text>
        
        <div 
          class="upload-zone" 
          :class="{ 'dragging': draggingTarget === 'person' }"
          v-if="!personImg" 
          @click="handleImageSelect('person')"
          @drop.prevent="handleDrop($event, 'person')"
          @dragover.prevent="handleDragOver($event, 'person')"
          @dragleave.prevent="handleDragLeave($event, 'person')"
          @dragenter.prevent
        >
          <view class="upload-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
          </view>
          <view class="upload-text">
            <text class="upload-link">Click to upload</text>
            <text class="upload-hint">or drag and drop</text>
          </view>
          <text class="upload-format">JPG, PNG vertical preferred</text>
        </div>
        
        <view class="preview-box" v-else>
          <image :src="personImg" mode="aspectFill" class="blur-bg"></image>
          <view class="overlay-dim"></view>
          <image :src="personImg" mode="aspectFit" class="main-img"></image>
          <view class="remove-btn" @click.stop="removeImage('person')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </view>
          <!-- 上传状态指示 -->
          <view v-if="isUploading && personImg" class="upload-status">
            <text>上传中...</text>
          </view>
        </view>
      </view>
      
      <view class="upload-item">
        <text class="upload-title">Try-On Clothing</text>
        
        <div 
          class="upload-zone" 
          :class="{ 'dragging': draggingTarget === 'clothing' }"
          v-if="!clothingImg" 
          @click="handleImageSelect('clothing')"
          @drop.prevent="handleDrop($event, 'clothing')"
          @dragover.prevent="handleDragOver($event, 'clothing')"
          @dragleave.prevent="handleDragLeave($event, 'clothing')"
          @dragenter.prevent
        >
          <view class="upload-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
          </view>
          <view class="upload-text">
            <text class="upload-link">Click to upload</text>
            <text class="upload-hint">or drag and drop</text>
          </view>
          <text class="upload-format">JPG, PNG flat lay preferred</text>
        </div>
        
        <view class="preview-box" v-else>
          <image :src="clothingImg" mode="aspectFill" class="blur-bg"></image>
          <view class="overlay-dim"></view>
          <image :src="clothingImg" mode="aspectFit" class="main-img"></image>
          <view class="remove-btn" @click.stop="removeImage('clothing')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </view>
          <!-- 上传状态指示 -->
          <view v-if="isUploading && clothingImg" class="upload-status">
            <text>上传中...</text>
          </view>
        </view>
      </view>
    </view>
    
    <view class="action-section">
      <button 
        class="generate-btn" 
        :disabled="!canGenerate || isUploading" 
        :class="{'active': canGenerate && !isUploading}"
        @click="handleGenerate"
      >
        <span class="sparkle-icon" v-if="canGenerate && !isUploading">✨</span>
        {{ isUploading ? '上传中...' : 'Generate' }}
      </button>
    </view>
    
    <view class="preview-section" :class="{ 'expanded': showResult }">
      <view class="section-header">
        <text class="preview-title">Generation Result</text>
      </view>
      
      <view class="preview-zone result-zone" :class="{ 'loading': isLoading }">
        <!-- 加载中 -->
        <view v-if="isLoading" class="loading-content">
          <view class="shimmer-overlay">
            <view class="shimmer"></view>
          </view>
          <view class="preview-icon">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
          </view>
        </view>
        
        <!-- 生成结果 -->
        <view v-else-if="resultImg" class="result-content">
          <image :src="resultImg" mode="aspectFit" class="result-image"></image>
        </view>
        
        <!-- 占位符（无结果时） -->
        <view v-else class="preview-icon">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
          </svg>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
// ... 上面的 JavaScript 代码 ...
</script>

<style scoped>
/* ... 原有样式 ... */

.result-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.upload-status {
  position: absolute;
  bottom: 16rpx;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(0, 0, 0, 0.6);
  color: #FFF;
  padding: 8rpx 16rpx;
  border-radius: 20rpx;
  font-size: 24rpx;
  z-index: 10;
}
</style>
```

---

## 6. 安全建议

1. **图片大小限制**：后端应限制上传图片的大小（建议最大 10MB），防止恶意上传大文件
2. **图片格式验证**：后端必须验证图片格式，仅接受 JPG、PNG 等安全格式
3. **文件内容验证**：后端应验证文件内容是否为有效图片，防止文件伪装攻击
4. **频率限制**：建议对上传和生成接口进行限流（如每个用户每分钟最多 10 次上传、5 次生成），防止滥用
5. **HTTPS 传输**：必须使用 HTTPS 传输图片数据，保护用户隐私
6. **文件 ID 验证**：后端应验证 fileId 的有效性和所有权，防止用户使用他人的文件 ID
7. **超时设置**：前端应设置合理的请求超时时间（上传：30 秒，生成：120 秒）
8. **错误处理**：后端应妥善处理模型调用失败的情况，返回明确的错误信息
9. **文件清理**：后端应定期清理未使用的临时文件，避免存储空间浪费

---

## 7. 测试用例

### 文件上传接口测试

| 测试场景 | 请求参数 | 预期结果 |
|---------|---------|---------|
| 正常上传 | 有效的图片文件 | 返回 200，至少包含 fileId（fileUrl 可选） |
| 文件为空 | file: null | 返回 400，提示"文件不能为空" |
| 图片格式错误 | 上传非图片文件（如 .txt） | 返回 400，提示"图片格式不支持" |
| 图片文件过大 | 上传超过 10MB 的图片 | 返回 400，提示"图片文件过大" |
| 图片文件损坏 | 上传损坏的图片文件 | 返回 400，提示"图片解析失败" |

### 虚拟试穿生成接口测试

| 测试场景 | 请求参数 | 预期结果 |
|---------|---------|---------|
| 正常生成 | 有效的 personFileId + clothingFileId | 返回 200，包含生成的图片 URL 或 Base64 |
| 人物文件 ID 为空 | personFileId: null | 返回 400，提示"人物图片文件 ID 不能为空" |
| 衣服文件 ID 为空 | clothingFileId: null | 返回 400，提示"衣服图片文件 ID 不能为空" |
| 人物文件不存在 | 无效的 personFileId | 返回 404，提示"人物图片文件不存在" |
| 衣服文件不存在 | 无效的 clothingFileId | 返回 404，提示"衣服图片文件不存在" |
| 模型调用失败 | 正常文件 ID 但模型服务异常 | 返回 500，提示"模型调用失败" |
| 网络超时 | 请求超时 | 前端捕获超时错误，提示用户重试 |

---

## 8. 性能优化建议

1. **图片压缩**：前端上传前可以对图片进行适当压缩，减少传输时间和存储空间
2. **异步处理**：如果生图时间较长（>30秒），建议后端实现异步任务机制，前端轮询查询结果
3. **缓存机制**：对于相同的输入图片（通过 fileId 或图片 hash），后端可以缓存生成结果，避免重复计算
4. **CDN 加速**：上传和生成的图片 URL 建议使用 CDN，加快前端加载速度
5. **进度反馈**：如果支持，后端可以返回生成进度，前端显示进度条提升用户体验
6. **文件预上传**：用户选择图片后立即上传，而不是等到点击 Generate 才上传，提升用户体验

---

## 9. 联系方式

如有疑问，请联系前端开发团队。

**文档版本**: v2.0  
**最后更新**: 2026-01-27
