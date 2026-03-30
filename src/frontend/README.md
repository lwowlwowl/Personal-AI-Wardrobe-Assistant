# AI 虚拟衣橱助手 · 前端

基于 **Vue 3 + UniApp（Vite）** 的跨端前端：登录／首页壳层、推荐 AI、虚拟试穿、衣橱、日历、衣橱分析等模块，整体为偏 Apple 风的自定义 UI。

---

## 功能说明

面向使用者与产品说明：**应用里有哪些能力**（与界面文案可能为英文一致）。

### 登录与账号

- **登录**：用户名、密码登录；可配合「记住」等本地状态（以实际页面为准）。
- **注册**：同一登录页内切换 Tab 完成注册（邮箱、用户名、密码等）。
- **忘记密码**：支持忘记密码流程（弹窗，入口以页面为准）。
- **进入主应用**：登录成功后进入 **`index`** 首页（侧栏 + 五大功能模块）。

### 首页（导航与设置）

- **侧栏导航**：在 **推荐 AI**、**虚拟试穿**、**我的衣橱**、**我的日历**、**衣橱分析** 之间切换；侧栏可折叠。
- **推荐 AI 会话列表**：选中「推荐 AI」且侧栏展开时，可 **新建 / 切换 / 重命名 / 删除** 对话会话。
- **用户区**：展示登录状态、头像与昵称；可 **打开设置**、**退出登录**；未登录时可跳转登录。
- **设置**：在设置弹窗中查看或修改个人资料（如头像、用户名、邮箱等，以实际表单项为准）。

### 推荐 AI

- **对话**：多行输入、发送；支持 **附带图片**（相册或拖拽等，以端能力为准）。
- **问候与上下文**：首次进入有问候区；登录后可展示 **当日天气** 等辅助信息。
- **AI 回复**：支持纯文本、以及结构化展示（如 **日程 / 计划卡片**、**穿搭推荐卡片** 等）。
- **与衣橱联动**：可结合用户衣橱数据做推荐；支持从推荐 **跳转到虚拟试穿**（带入衣物 / 模特或成套顺序）。
- **与日历联动**：推荐流程中若涉及日历，可触发 **日历数据刷新**（以实际交互为准）。

### 虚拟试穿

- **上传人像与服装**：分别上传模特图与服装图，支持点击选择与 **拖拽**（H5）；可预览、移除。
- **生成结果**：一键生成试穿效果图，加载中有动效，结果展示在生成区。
- **从其它模块带入**：可从衣橱等入口 **预填当前衣服图、默认模特图**，减少重复上传。
- **成套试穿（多步）**：支持按顺序试穿多件单品：每件依次生成，**上一步结果作为下一步的人像**，界面展示试穿顺序与进度。

### 我的衣橱

- **衣物（Cloth）**：网格浏览衣橱单品；**搜索**；按收藏、类型、颜色、季节等多条件 **筛选**；**分页加载**（以实际交互为准）。
- **上传与编辑衣物**：新增衣服（图片 + 名称、分类、颜色、季节等信息）；查看 **详情** 并 **编辑 / 删除**。
- **模特（Model）**：管理个人模特照片；可 **搜索**；支持 **设为主模特**（虚拟试穿默认人像）、上传与详情编辑、删除等。
- **跳转试穿**：在衣物详情等入口可 **一键前往虚拟试穿**，并带入当前图与默认模特。

### 我的日历

- **月历**：按月查看，切换月份；某日可有穿搭记录标记。
- **本月概览**：展示本月 **有记录的天数**、**不重复单品数**、**连续记录天数** 等统计。
- **单日穿搭**：选择日期后，可 **查看或编辑** 当日穿搭；可从衣橱 **多选单品** 组成一套记录。
- **视觉呈现**：日历页含装饰性视觉（如散点照片、玻璃拟态等），便于演示与使用体验。

### 衣橱分析

- **总览看板（Bento）**：以多块卡片展示衣橱洞察，例如：
  - **活动度**：本周与上周对比，可 **展开查看活动报告**；
  - **闲置率**：未穿着占比与件数，可 **展开闲置清单**；
  - **总件数与趋势**：历史总件数变化趋势，支持按维度筛选查看；
  - **最常穿**：穿着次数排行，支持筛选；
  - **热门颜色 / 风格**：占比展示；
  - **建议补充**：基于数据的添置建议，可刷新；
  - **分类分布**：各类别占比，可切换统计维度。
- **筛选**：部分卡片支持 **类型 / 颜色 / 季节** 等筛选（与后端分析接口一致）。

---

## 架构概览

前端采用 **分层** 组织，避免在 `.vue` 内散落 `uni.request`／URL：

| 层级 | 路径 | 职责 |
|------|------|------|
| **HTTP 基底** | `utils/request.js` | 统一 `API_BASE_URL` 与 `request()`（`uni.request` 封装），为唯一底层。 |
| **领域 API** | `api/*.js` | 按业务拆分：衣橱／模特、用户、日历、分析、推荐 AI、虚拟试穿等，内部从 `@/utils/request.js`（或同层 re-export）取用 `request`／`API_BASE_URL`。 |
| **纯数据／枚举** | `utils/wardrobeEnums.js` | 衣物 type／season／color 等 code ↔ 文案，**不含**网络请求。 |
| **页面与组件** | `pages/` | 路由页与首页内子组件；复杂逻辑可抽到同目录 `utils/*.js`（如推荐 AI）。 |

**路径别名**：`@/` 指向本前端项目根目录（与 `vite.config.js`、UniApp 惯例一致）。

---

## 目录结构（精简）

```
frontend/
├── api/                          # 后端联调（按模块拆分）
│   ├── wardrobe.js               # 衣物、模特照片、health；re-export request / API_BASE_URL、wardrobeMedia 工具
│   ├── wardrobeMedia.js          # 图片 URL 规范化、删除响应判断等（供衣橱 UI）
│   ├── userApi.js                # 登录、注册、验证等
│   ├── calendarApi.js            # 日历穿搭读写
│   ├── analysisApi.js            # 衣橱分析 /api/analysis/*
│   ├── recommendationApi.js      # 推荐 AI 相关（含流式等）
│   └── virtualTryOnApi.js        # 虚拟试穿：上传图、generate（VirtualTryOn.vue 使用）
├── pages/
│   ├── login/
│   │   ├── login.vue             # 登录 + 注册（分页切换，同一页）
│   │   └── ForgotPasswordModal.vue
│   └── index/
│       ├── index.vue             # 侧栏 + 主内容区切换各功能模块
│       ├── SettingsModal.vue     # 设置等弹层
│       └── components/
│           ├── RecommendationAI/ # 推荐 AI（聊天、卡片、侧栏会话）
│           │   ├── RecommendationAI.vue
│           │   ├── chat-content/     # 消息气泡、推荐卡片、加载态等
│           │   ├── sidebar/          # 会话列表、重命名／删除弹窗
│           │   └── utils/            # chatContentAdapter、穿搭顺序等
│           ├── VirtualTryOn.vue
│           ├── MyWardrobe/       # cloth-modal、model-modal、删除确认等
│           ├── MyCalendar/
│           └── WardrobeAnalysis/ # bento-widgets、expanded-pages、ViewByFilter
├── utils/
│   ├── request.js
│   └── wardrobeEnums.js
├── static/
├── App.vue
├── main.js
├── pages.json
├── manifest.json
├── uni.scss
├── vite.config.js
└── package.json
```

> **说明**：`pages.json` 目前仅注册 **`pages/login/login`** 与 **`pages/index/index`**；注册流程在 `login.vue` 内以 Tab 完成，**没有**独立的 `pages/register/` 路由。

---

## 开发说明（代码入口）

- **页面路由**：`pages/login/login`（登录/注册）、`pages/index/index`（主应用壳层与五大模块）。
- **界面与业务组件**：见 **`pages/index/`** 下 `index.vue`、`components/` 各子目录；HTTP 封装在 **`utils/request.js`**，按领域拆分 **`api/*.js`**。
- **后端契约与字段**：以仓库 **`docs/API_Documentation/`** 为准，下表「API 与文档索引」可快速对应。

---

## 技术栈与环境

| 项目 | 版本／说明 |
|------|------------|
| 运行环境 | **Node.js ≥ 18**（见 `package.json` `engines`） |
| 框架 | Vue 3（Composition API） |
| 构建 | UniApp + **Vite**（`vite.config.js` 使用 `@dcloudio/vite-plugin-uni`） |
| 样式 | SCSS、`uni.scss` 全局变量 |

### 常用命令

```bash
npm install

# H5 开发
npm run dev:h5

# H5 正式构建
npm run build:h5
```

其它平台（微信／支付宝／字节小程序）脚本见 `package.json`；部分在 Windows 下需自行调整 `UNI_INPUT_DIR` 等环境变量（与 Unix 示例不同）。

---

## API 与文档索引

后端契约与联调说明以 **`src/docs/api/`** 下的 **`*_api.md`** 为准（相对仓库根目录；从本目录为 `../docs/api/`）：

| 模块 | 前端封装 | 说明文档 |
|------|----------|----------|
| 登录／注册 | `api/userApi.js` | `../docs/api/login_register_api.md` |
| 衣橱／模特 | `api/wardrobe.js`、`wardrobeMedia.js` | `../docs/api/my_wardrobe_api.md` |
| 日历 | `api/calendarApi.js` | `../docs/api/my_calendar_api.md` |
| 衣橱分析 | `api/analysisApi.js` | `../docs/api/wardrobe_analysis_api.md` |
| 虚拟试穿 | `api/virtualTryOnApi.js` | `../docs/api/virtual_tryon_api.md` |
| 推荐 AI | `api/recommendationApi.js` | `../docs/api/recommendation_ai_api.md`；Agent 另见 `../backend/AIwardrobe/README.md` |

**基底 URL**：默认在 **`utils/request.js`** 的 `API_BASE_URL`；部署时请改为实际后端地址或改为读取构建环境变量（若项目后续加上）。

---

## 设计规范（摘要）

- **色值**：主色 `#9B8B6F`、背景 `#EBE3D5`、主文字 `#333333` 等（与现有 `uni.scss`／各页一致者为准）。
- **圆角／字号**：按组件既有 `rpx` 为准；全局微调见 `uni.scss`。

---

## 多端支持

UniApp 目标包含 H5、各小程序与 App；本仓库日常开发以 **H5**（`dev:h5`／`build:h5`）为主。

---

## 团队与授权

**teammmm13** · 授权待定

---

**备注**：若功能或目录有变更，请同步更新「功能说明」「目录结构」与「API 与文档索引」，以保持与实际产品、代码一致。
