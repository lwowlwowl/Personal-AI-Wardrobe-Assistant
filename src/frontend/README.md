# AI 虚拟衣橱助手 - 前端项目

这是一个基于 Vue 3 + UniApp 开发的虚拟试衣网页应用，采用 Apple 设计风格。

## 📋 项目简介

本项目实现了虚拟衣橱助手的登录、注册、首页与衣橱管理等功能，具有优雅的用户界面和流畅的交互体验。项目采用 UniApp 框架开发，支持多端部署（H5、小程序、App）。**登录 / 注册已与后端联调完成**；首页包含推荐 AI、虚拟试穿、我的衣橱等模块。

## 🎨 设计特点

- **Apple 风格设计**：简洁、优雅、注重细节
- **响应式布局**：适配不同屏幕尺寸
- **柔和配色方案**：使用大地色系（#EBE3D5, #9B8B6F）营造温馨氛围
- **圆角设计**：所有交互元素采用大圆角设计
- **流畅动画**：过渡效果和悬停状态

## 📁 项目结构

```
frontend/
├── pages/
│   ├── login/              # 登录页面
│   │   └── login.vue
│   ├── register/           # 注册页面
│   │   └── register.vue
│   └── index/              # 首页（主应用）
│       ├── index.vue       # 侧栏 + 主内容切换
│       └── components/
│           ├── RecommendationAI.vue   # 推荐 AI
│           ├── VirtualTryOn.vue       # 虚拟试穿
│           └── MyWardrobe/            # 我的衣橱
│               ├── WardrobeView.vue   # 衣橱列表与筛选
│               ├── DetailModal.vue    # 衣服详情弹窗
│               └── ModelDetailModal.vue # 模特详情弹窗
├── utils/
│   ├── request.js          # 请求封装
│   └── wardrobeEnums.js    # 衣橱枚举（type/color/season code↔label）
├── static/                 # 静态资源（图标、背景、示例图等）
├── App.vue
├── main.js
├── pages.json
├── manifest.json
├── uni.scss
├── LOGIN_REGISTER.md       # 登录/注册 API 文档
├── MY_WARDROBE.md          # 我的衣橱 API 文档
└── VIRTUAL_TRYON.md        # 虚拟试穿 API 文档
```

## 🚀 功能特性

### 登录与注册（已与后端联调）

- **登录** (`/pages/login/login.vue`)：用户名、密码、记住我、表单验证；**已对接后端登录接口**，详见 `LOGIN_REGISTER.md`。
- **注册** (`/pages/register/register.vue`)：邮箱、用户名、密码、表单验证；**已对接后端注册接口**，注册成功后可跳转登录。

### 首页与导航

- 侧栏导航：推荐 AI、虚拟试穿、我的衣橱、衣橱分析等，可折叠。
- 主内容区根据菜单切换对应组件。

### 我的衣橱 (`My Wardrobe`)

- **衣服视图**：网格展示衣服，支持关键词搜索、按类型/颜色/季节/收藏/日期筛选与排序、分页；支持多选类型/颜色/季节（code 存储，逗号分隔无空格，与 API 约定一致）。
- **模特视图**：网格展示模特图，支持搜索、筛选、设为默认模特（用于虚拟试穿）。
- **详情与编辑**：点击单条可打开详情弹窗，编辑名称、类型、颜色、季节、收藏等级；可删除或发起虚拟试穿。
- **上传**：支持选择文件或拖拽添加新衣服/新模特图（当前为本地预览；联调时需先调用上传接口获取 fileId，再以 imageFileId 调用创建接口）。
- **枚举与 API**：type/color/season 使用 `utils/wardrobeEnums.js` 的 code（如 `t_shirt`、`burnt_orange`），请求与筛选传 code，展示用 label。完整接口约定见 **`MY_WARDROBE.md`**。

### 推荐 AI / 虚拟试穿

- 推荐 AI、虚拟试穿组件位于首页；虚拟试穿可从衣橱详情一键带入衣服图与默认模特图。接口约定见 `VIRTUAL_TRYON.md`。

## 🛠️ 技术栈

- **框架**：Vue 3 (Composition API)
- **跨平台方案**：UniApp
- **样式**：SCSS
- **UI 设计**：自定义组件 + 部分 SVG 图标

## 📦 安装与运行

### 环境要求

- Node.js >= 14
- HBuilderX（推荐）或 Vue CLI

### 安装依赖

```bash
npm install
```

### 开发运行

#### 使用 HBuilderX
1. 用 HBuilderX 打开项目
2. 点击「运行」-> 选择运行平台（浏览器/小程序/App）

#### 使用命令行

```bash
# H5 开发
npm run dev:h5

# 微信小程序开发
npm run dev:mp-weixin

# 支付宝小程序开发
npm run dev:mp-alipay
```

### 构建发布

```bash
# H5 构建
npm run build:h5

# 微信小程序构建
npm run build:mp-weixin
```

## 📡 API 文档与联调

| 模块 | 文档 | 说明 |
|------|------|------|
| 登录 / 注册 | `LOGIN_REGISTER.md` | 已联调；登录、注册接口与请求/响应格式 |
| 我的衣橱 | `MY_WARDROBE.md` | 衣橱列表、筛选、增删改、默认模特、枚举 code、imageFileId 约定等 |
| 虚拟试穿 | `VIRTUAL_TRYON.md` | 虚拟试穿相关接口与上传约定 |

后端实现时请以上述文档为准；请求基址等可在 `utils/request.js` 或环境变量中配置。

## 🎯 待完成 / 可选事项

- [ ] 我的衣橱与后端衣橱 API 联调（列表、筛选、创建、更新、删除、默认模特）
- [ ] 虚拟试穿与后端试穿/上传接口联调
- [ ] 添加忘记密码页面
- [ ] 用户协议和隐私政策页面
- [ ] 实现本地存储「记住我」功能
- [ ] 第三方登录（微信、Apple ID）

## 🎨 设计规范

### 颜色

- 主色调：`#9B8B6F`（暖棕色）
- 背景色：`#EBE3D5`（米色）
- 文字色：`#333333`（深灰）
- 次要文字：`#666666`（中灰）
- 占位文字：`#CCCCCC`（浅灰）

### 圆角

- 按钮和输入框：`45rpx`
- 切换标签：`40rpx`
- 背景卡片：`30rpx`

### 字体大小

- 标题：`36rpx - 48rpx`
- 正文：`28rpx - 32rpx`
- 辅助文字：`24rpx - 26rpx`

## 📱 多端适配

项目使用 UniApp 开发，天然支持：

- ✅ H5 网页
- ✅ 微信小程序
- ✅ 支付宝小程序
- ✅ iOS App
- ✅ Android App

## 🤝 团队

**teammmm13**

## 📄 许可证

待定

---

**备注**：登录/注册已与后端联调；我的衣橱、虚拟试穿等模块的接口约定见对应 MD 文档，后端可按文档实现并与前端联调。
