# AI 虚拟衣橱助手 - 前端项目

这是一个基于 Vue 3 + UniApp 开发的虚拟试衣网页应用，采用 Apple 设计风格。

## 📋 项目简介

本项目实现了虚拟衣橱助手的登录、注册、首页与衣橱管理等功能，具有优雅的用户界面和流畅的交互体验。项目采用 UniApp 框架开发，支持多端部署（H5、小程序、App）。**登录 / 注册已与后端联调完成**；首页包含推荐 AI、虚拟试穿、我的衣橱、我的日历、衣橱分析等模块。

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
│           ├── RecommendationAI/       # 推荐 AI（多会话 + 侧栏对话列表）
│           │   ├── RecommendationAI.vue   # 主聊天组件（问候、输入、消息、推荐卡片）
│           │   ├── ConversationSidebar.vue # 侧栏「新建会话」+ 对话列表 + Rename/Delete 弹窗
│           │   ├── RecommendationCard.vue # 单条推荐卡片展示
│           │   ├── RenameModal.vue        # 会话重命名弹窗
│           │   └── DeleteModal.vue        # 会话删除确认弹窗
│           ├── VirtualTryOn.vue       # 虚拟试穿
│           ├── MyWardrobe/            # 我的衣橱
│           │   ├── WardrobeView.vue   # 衣橱列表与筛选
│           │   ├── DetailModal.vue    # 衣服详情弹窗
│           │   └── ModelDetailModal.vue # 模特详情弹窗
│           ├── MyCalendar/            # 我的日历
│           │   ├── MyCalendar.vue     # 日历主组件
│           │   └── AddOutfitPanel.vue # 添加穿搭面板
│           └── WardrobeAnalysis/      # 衣橱分析
│               ├── WardrobeAnalysis.vue # 分析主组件
│               ├── ActivityReport.vue   # 活动报告视图
│               ├── IdleItemsView.vue    # 闲置物品视图
│               └── ViewByFilter.vue    # 筛选视图组件
├── utils/
│   ├── request.js          # 请求封装
│   └── wardrobeEnums.js    # 衣橱枚举（type/color/season code↔label）
├── static/                 # 静态资源（图标、背景、示例图等）
├── App.vue
├── main.js
├── pages.json
├── manifest.json
└── uni.scss
```

## 🚀 功能特性

### 登录与注册（已与后端联调）

- **登录** (`/pages/login/login.vue`)：用户名、密码、记住我、表单验证；**已对接后端登录接口**，详见 `LOGIN_REGISTER.md`。
- **注册** (`/pages/register/register.vue`)：邮箱、用户名、密码、表单验证；**已对接后端注册接口**，注册成功后可跳转登录。

### 首页与导航

- 侧栏导航：推荐 AI、虚拟试穿、我的衣橱、我的日历、衣橱分析等，可折叠。
- 选中「推荐 AI」且侧栏未折叠时，侧栏会显示「新建会话」与对话列表（`ConversationSidebar`），可新建/切换/重命名/删除会话。
- 主内容区根据菜单切换对应组件，支持过渡动画。

### 我的衣橱 (`My Wardrobe`)

- **衣服视图**：网格展示衣服，支持关键词搜索、按类型/颜色/季节/收藏/日期筛选与排序、分页；支持多选类型/颜色/季节（code 存储，逗号分隔无空格，与 API 约定一致）。
- **模特视图**：网格展示模特图，支持搜索、筛选、设为默认模特（用于虚拟试穿）。
- **详情与编辑**：点击单条可打开详情弹窗，编辑名称、类型、颜色、季节、收藏等级；可删除或发起虚拟试穿。
- **上传**：支持选择文件或拖拽添加新衣服/新模特图（当前为本地预览；联调时需先调用上传接口获取 fileId，再以 imageFileId 调用创建接口）。
- **枚举与 API**：type/color/season 使用 `utils/wardrobeEnums.js` 的 code（如 `t_shirt`、`burnt_orange`），请求与筛选传 code，展示用 label。完整接口约定见 **`MY_WARDROBE.md`**。

### 我的日历 (`My Calendar`)

- **日历视图**：展示月历视图，支持月份切换，显示每日穿搭记录。
- **统计信息**：显示本月记录天数、独特单品数量、连续记录天数（streak）。
- **穿搭记录**：点击日期可查看或添加当日穿搭，支持从衣橱选择多件衣服组合成穿搭。
- **穿搭详情**：查看历史穿搭记录，包括日期、选择的衣服列表等信息。

### 衣橱分析 (`Wardrobe Analysis`)

- **Bento Grid 布局**：采用卡片式网格布局展示各项分析数据。
- **衣橱活动度**：显示本周相比上周的活动度变化（增加/减少百分比），可查看详细活动报告。
- **闲置率**：统计未穿过的物品数量及占比，可查看所有闲置物品列表。
- **总物品数**：展示衣橱总物品数的历史趋势图表，支持按类型/颜色/季节筛选查看。
- **最常穿物品**：列出最常穿着的物品及其穿着次数，支持按类型/颜色/季节筛选。
- **热门统计**：显示最常用颜色和最常用风格及其占比。
- **建议添加**：基于衣橱数据提供建议添加的物品类型，支持展开查看详情。

### 推荐 AI (`Recommendation AI`)

- **主聊天区**（`RecommendationAI.vue`）：初始问候、多行输入、图片上传；用户/AI 消息展示；推荐结果以多套推荐卡片 + 左右滑动展示。
- **多会话**：由父级 `index.vue` 同步 `conversationState`；支持 `currentConversationId` / `currentConversation` 与 `create-conversation` / `update-conversation` 事件。
- **侧栏对话列表**（`ConversationSidebar.vue`）：选中推荐 AI 且侧栏未折叠时显示「新建会话」按钮与「你的对话」列表；支持切换会话、重命名（RenameModal）、删除（DeleteModal）；状态与逻辑集中在 ConversationSidebar，通过 `update:conversationState` 回传 index 再传给主聊天组件。
- **API 联调**：默认使用 Mock 数据；将 `RecommendationAI/mockData.js` 中 `USE_RECOMMENDATION_MOCK = false` 可请求后端 `POST /api/ai/chat/stream`。详见 `pages/index/components/RecommendationAI/RECOMMENDATION_AI.md`。

### 虚拟试穿 (`Virtual Try-On`)

- **入口**：首页侧栏「Virtual Try-On」；也可从「我的衣橱」衣服详情中一键跳转并带入当前衣服图与默认模特图（`initialClothingImage` / `initialPersonImage`）。
- **上传区**（`VirtualTryOn.vue`）：
  - **Person Model**：上传人物/模特图，支持点击或拖拽，建议竖版 JPG/PNG；可预览、移除。
  - **Try-On Clothing**：上传待试穿服装图，支持点击或拖拽，建议平铺 JPG/PNG；可预览、移除。
- **生成**：两个图都上传后「Generate」按钮可用，点击后进入加载态（Shimmer 动画），生成结果展示在「Generation Result」区域。
- **结果区**：展示试穿结果图；无结果时显示占位。接口与上传约定见 `VIRTUAL_TRYON.md`。

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
| 推荐 AI | `pages/index/components/RecommendationAI/RECOMMENDATION_AI.md` | 已联调；`POST /api/ai/chat/stream`，Mock 开关、SSE 流式约定 |
| 我的衣橱 | `MY_WARDROBE.md` | 衣橱列表、筛选、增删改、默认模特、枚举 code、imageFileId 约定等 |
| 虚拟试穿 | `VIRTUAL_TRYON.md` | 虚拟试穿相关接口与上传约定 |

后端实现时请以上述文档为准；请求基址等可在 `utils/request.js`、`api/recommendationApi.js` 或环境变量中配置。

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
