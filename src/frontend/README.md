# AI虚拟衣橱助手 - 前端（Vue3 + UniApp）

这是一个基于 Vue 3 + UniApp 开发的虚拟衣橱助手前端项目，整体 UI 走 Apple 风格，支持多端构建（H5/小程序/App）。

## 📋 项目简介

本项目包含登录/注册与首页应用框架，并提供两个核心功能页：

- Recommendation AI：聊天式穿搭/检索交互界面（当前以前端展示为主）
- Virtual Try-On：双图上传 + 生成结果展示（当前生成流程为前端模拟，接口规范已提供给后端）

## ✨ 功能概览

### 1) 登录页（`pages/login/login.vue`）

- 表单校验（用户名/密码）
- 记住我选项（UI）
- 登录成功后跳转首页（逻辑以对接后端为准）

### 2) 注册页（`pages/register/register.vue`）

- 表单校验（邮箱格式/用户名/密码）
- 注册成功后跳转登录页（逻辑以对接后端为准）

### 3) 首页（`pages/index/index.vue`）

- 侧边栏布局与菜单切换
- 已接入组件：
  - `pages/index/components/RecommendationAI.vue`
  - `pages/index/components/VirtualTryOn.vue`
- 侧边栏中的 `My Wardrobe / Wardrobe Analysis` 为预留菜单项（当前未实现对应页面）

### 4) Virtual Try-On（`pages/index/components/VirtualTryOn.vue`）

- 人物图 + 服装图双图上传（H5 支持拖拽上传）
- 图片预览与删除
- 点击 Generate：
  - 展开结果区域
  - 进入加载态（当前为模拟加载）
  - 自动滚动到结果区域，便于查看生成结果

## 🧰 技术栈

- 框架：Vue 3（Composition API）
- 跨端：UniApp
- 构建：Vite（`@dcloudio/vite-plugin-uni`）
- 样式：SCSS

## 📁 目录结构（核心）

```
.
├── pages/
│   ├── login/                 # 登录页
│   ├── register/              # 注册页
│   └── index/                 # 首页（侧边栏 + 功能切换）
│       ├── index.vue
│       └── components/
│           ├── RecommendationAI.vue
│           └── VirtualTryOn.vue
├── static/                    # 静态资源
├── App.vue
├── main.js
├── pages.json
├── manifest.json
├── uni.scss
├── API_DOCUMENTATION.md
└── API_DOCUMENTATION_VIRTUAL_TRYON.md
```

## 📦 安装与运行

### 环境要求

- Node.js >= 14
- HBuilderX（推荐）

### 安装依赖

```bash
npm install
```

### 开发运行

```bash
# H5
npm run dev:h5

# 微信小程序
npm run dev:mp-weixin

# 支付宝小程序
npm run dev:mp-alipay
```

### 构建发布

```bash
# H5
npm run build:h5

# 微信小程序
npm run build:mp-weixin
```

## 🧩 待办（建议）

- 对接真实登录/注册接口（参考 `API_DOCUMENTATION.md`）
- 对接虚拟试穿上传 + 生成接口（参考 `API_DOCUMENTATION_VIRTUAL_TRYON.md`）
- Recommendation AI 对接后端/大模型服务（当前偏展示）
- 补齐 `My Wardrobe / Wardrobe Analysis` 对应页面与数据流

## 🤝 团队

teammmm13

---

备注：当前仓库以前端展示为主，后端接口需另行实现/对接。
