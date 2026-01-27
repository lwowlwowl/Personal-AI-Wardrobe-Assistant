# AI 虛擬衣櫥助手 - 前端項目

這是一個基於 Vue 3 + UniApp 開發的虛擬試衣網頁應用，採用 Apple 設計風格。

## 📋 項目簡介

本項目實現了虛擬衣櫥助手的登錄和註冊頁面，具有優雅的用戶界面和流暢的交互體驗。項目採用 UniApp 框架開發，支持多端部署（H5、小程序、App）。

## 🎨 設計特點

- **Apple 風格設計**：簡潔、優雅、注重細節
- **響應式佈局**：適配不同屏幕尺寸
- **柔和配色方案**：使用大地色系（#EBE3D5, #9B8B6F）營造溫馨氛圍
- **圓角設計**：所有交互元素採用大圓角設計
- **流暢動畫**：過渡效果和懸停狀態

## 📁 項目結構

```
frontend/
├── pages/
│   ├── login/           # 登錄頁面
│   │   └── login.vue
│   ├── register/        # 註冊頁面
│   │   └── register.vue
│   └── index/           # 首頁（待開發）
│       └── index.vue
├── static/              # 靜態資源
│   ├── logo.png
│   └── README.md       # 資源說明文件
├── App.vue             # 應用配置
├── main.js             # 入口文件
├── pages.json          # 頁面配置
├── manifest.json       # 應用配置
└── uni.scss            # 全局樣式變量
```

## 🚀 功能特性

### 登錄頁面 (`/pages/login/login.vue`)

- ✅ 用戶名輸入
- ✅ 密碼輸入（支持顯示/隱藏）
- ✅ 記住我選項
- ✅ 忘記密碼功能
- ✅ 表單驗證
- ✅ 跳轉到註冊頁面

### 註冊頁面 (`/pages/register/register.vue`)

- ✅ 郵箱地址輸入
- ✅ 用戶名輸入
- ✅ 密碼輸入（支持顯示/隱藏）
- ✅ 表單驗證（包括郵箱格式驗證）
- ✅ 註冊成功後自動跳轉到登錄頁

## 🛠️ 技術棧

- **框架**：Vue 3 (Composition API)
- **跨平台方案**：UniApp
- **樣式**：SCSS
- **UI 設計**：自定義組件

## 📦 安裝與運行

### 環境要求

- Node.js >= 14
- HBuilderX（推薦）或 Vue CLI

### 安裝依賴

```bash
npm install
```

### 開發運行

#### 使用 HBuilderX
1. 用 HBuilderX 打開項目
2. 點擊「運行」-> 選擇運行平台（瀏覽器/小程序/App）

#### 使用命令行

```bash
# H5 開發
npm run dev:h5

# 微信小程序開發
npm run dev:mp-weixin

# 支付寶小程序開發
npm run dev:mp-alipay
```

### 構建發布

```bash
# H5 構建
npm run build:h5

# 微信小程序構建
npm run build:mp-weixin
```

## 🎯 待完成事項

### 資源文件
需要添加以下圖片到 `static` 文件夾：

1. **wardrobe-bg.jpg** - 衣櫥背景圖
   - 建議尺寸：1920x1080
   - 可從 Unsplash 搜索 "wardrobe" 或 "closet"

2. **eye-open.png** - 顯示密碼圖標（可選）
   - 目前使用 emoji 替代

3. **eye-close.png** - 隱藏密碼圖標（可選）
   - 目前使用 emoji 替代

### 功能開發
- [ ] 實現真實的登錄 API 接口
- [ ] 實現真實的註冊 API 接口
- [ ] 添加忘記密碼頁面
- [ ] 添加用戶協議和隱私政策頁面
- [ ] 實現本地存儲「記住我」功能
- [ ] 添加第三方登錄（微信、Apple ID）

## 🎨 設計規範

### 顏色

- 主色調：`#9B8B6F`（暖棕色）
- 背景色：`#EBE3D5`（米色）
- 文字色：`#333333`（深灰）
- 次要文字：`#666666`（中灰）
- 占位文字：`#CCCCCC`（淺灰）

### 圓角

- 按鈕和輸入框：`45rpx`
- 切換標籤：`40rpx`
- 背景卡片：`30rpx`

### 字體大小

- 標題：`36rpx - 48rpx`
- 正文：`28rpx - 32rpx`
- 輔助文字：`24rpx - 26rpx`

## 📱 多端適配

項目使用 UniApp 開發，天然支持：

- ✅ H5 網頁
- ✅ 微信小程序
- ✅ 支付寶小程序
- ✅ iOS App
- ✅ Android App

## 🤝 團隊

**teammmm13**

## 📄 許可證

待定

---

**備註**：這是一個前端展示項目，後端 API 接口需要另外開發實現。
