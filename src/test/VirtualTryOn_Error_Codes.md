# 虚拟试衣（Virtual Try-On）错误码对照表

> 用途：对照「程序抛错位置」与「用户可读说明」。  
> 前缀：**VTO-FE** = 前端 `virtualTryOnApi.js` / `VirtualTryOn.vue`；**VTO-BE** = 后端 `virtual_tryon_service.py` 等。

---

## 一、前端 API（`frontend/api/virtualTryOnApi.js`）

### 1. 上传响应解析 `parseVirtualTryUploadResponse`

| 错误码 | 触发条件（简述） | 用户可读说明 |
|--------|------------------|----------------|
| **VTO-FE-U01** | HTTP 502/503，且响应非合法 JSON | ComfyUI 或后端暂不可用；请确认 ComfyUI 已启动且 `COMFYUI_SERVER` 正确 |
| **VTO-FE-U02** | 上传响应无法解析为 JSON（其他状态码） | 后端返回格式异常；请检查 API 地址是否为本项目后端、网络是否正常 |
| **VTO-FE-U03** | HTTP 2xx 且 `success` 为真，但缺少 `filename` | 上传名义成功但未取得文件名；多为后端与 ComfyUI 衔接异常 |
| **VTO-FE-U04** | 后端 JSON 含 `message` 或 `detail`（验证错等） | 以后端原文为准（常见：权限、参数、服务未就绪） |
| **VTO-FE-U05** | 其余非成功上传 | 上传失败；请看 HTTP 状态码与后端消息 |

### 2. `upload-from-storage` 请求失败（`uni.request` 的 `fail`）

| 错误码 | 触发条件 | 用户可读说明 |
|--------|----------|----------------|
| **VTO-FE-U06** | 网络层失败（无法连线、超时等） | 无法连上后端；请检查 `API_BASE_URL`、设备网络、后端是否启动 |

### 3. 下载远端图到暂存 `downloadToTempFile`

| 错误码 | 触发条件 | 用户可读说明 |
|--------|----------|----------------|
| **VTO-FE-D01** | 正规化后不是 `http(s)://` | 图片网址无效，无法下载；请改用有效链接或本机选图 |
| **VTO-FE-D02** | HTTP 非 200，但响应为 JSON 且含错误消息 | 以服务器返回消息为准（例如后端代理错误） |
| **VTO-FE-D03** | HTTP 502/503/504 | 后端或上游（含 ComfyUI）暂时不可用 |
| **VTO-FE-D04** | 其他 HTTP 错误码 | 图片网址无法取得；检查网址、跨域、或服务是否启动 |
| **VTO-FE-D05** | `uni.downloadFile` 的 `fail` | 下载失败（网络、域名白名单、HTTPS 证书等）；若为本机静态图，建议改走「后端读档」流程 |

### 4. `data:` / `blob:` 转暂存

| 错误码 | 触发条件 | 用户可读说明 |
|--------|----------|----------------|
| **VTO-FE-D06** | `data:` 格式不符合 base64 预期 | 图片数据损坏或格式不正确，请重新选图 |
| **VTO-FE-D07** | 写入暂存文件失败（小程序文件系统） | 设备存储空间或权限问题，请重试或换环境 |
| **VTO-FE-D08** | Blob 读取失败 | 浏览器/运行环境无法读取该 blob，请重新产生或选图 |

### 5. `resolveLocalFilePathForUpload`（上传前统一处理来源）

| 错误码 | 触发条件 | 用户可读说明 |
|--------|----------|----------------|
| **VTO-FE-D09** | 来源为空或非字符串 | 未选择有效图片 |
| **VTO-FE-D10** | 检测为占位图（placehold 等） | 请使用真实照片，并在衣柜设置有效默认模特 |

### 6. `uploadVirtualTryOnImage`（multipart 上传）

| 错误码 | 触发条件 | 用户可读说明 |
|--------|----------|----------------|
| **VTO-FE-D11** | 无 token | 请先登录 |
| **VTO-FE-D12** | `uni.uploadFile` 的 `fail` | 上传请求失败；若 ComfyUI 未启动也会影响后端转发，请先启动 ComfyUI 再试 |

> 注：若走 **服务器已存储路径**（`upload-from-storage`），错误会落在 **VTO-FE-U01～U06** 与后端 **VTO-BE-S\***。

### 7. `generateVirtualTryOn`（POST `/api/virtual-try-on/generate`）

| 错误码 | 触发条件 | 用户可读说明 |
|--------|----------|----------------|
| **VTO-FE-G01** | 响应非 JSON | API 地址可能指到错误服务（例如静态页或代理 HTML） |
| **VTO-FE-G02** | HTTP 非 200，或 `success` 为假，或无 `result_image` | 生成失败；消息以后端 `message/detail` 为准，否则显示 HTTP 状态 |
| **VTO-FE-G03** | `uni.request` 的 `fail` | 无法连上后端；检查网络与 `API_BASE_URL` |

---

## 二、前端页面（`VirtualTryOn.vue`）

| 错误码 | 触发条件 | 用户可读说明 |
|--------|----------|----------------|
| **VTO-FE-V01** | 未登录即操作需登录流程 | 请先登录 |
| **VTO-FE-V02** | Full Outfit 流程无人物图 | 请在「我的衣柜」设置默认模特，或上传人物照片 |
| **VTO-FE-V03** | `applyResultImageWithDomFlush` 中 `dataUrlToBlobUrl` 失败 | 结果图数据 URL 无效（极少见）；可重试生成 |
| **VTO-FE-V04** | 单次 Generate 的 `catch`，且错误无法抽出消息 | **兜底**：请看控制台日志；常见仍为上传/生成/网络问题 |
| **VTO-FE-V05** | Full Outfit 的 `catch`，且错误无法抽出消息 | **兜底**：同上，但发生在连续多步穿搭流程 |

---

## 三、后端（`app/services/virtual_tryon_service.py`）

### `POST /api/virtual-try-on/upload-image` 与 `upload-from-storage`

| 错误码 | HTTP / 结构 | 触发条件 | 用户可读说明 |
|--------|-------------|----------|----------------|
| **VTO-BE-S01** | 503 + `success: false` | ComfyUI 客户端不可用或资源缺失 | 虚拟试衣未启用；请检查 `comfyui_client`、工作流 JSON |
| **VTO-BE-A01** | 401 | Token 无效或过期 | 请重新登录 |
| **VTO-BE-A02** | 403 | 用户不存在或未启用 | 账号状态异常，请联系管理或重登 |
| **VTO-BE-S02** | 400 | `image_ref` 无法解析为安全 uploads 路径 | 请使用衣柜/模特有效地址（`.../uploads/...`） |
| **VTO-BE-S03** | 403 | 文件不在当前用户目录下 | 无权读取该图片 |
| **VTO-BE-S04** | 400 | 本机读档 `OSError` | 文件已删除或无法读取 |
| **VTO-BE-S05** | 503 | ComfyUI `upload_image` 无返回 | ComfyUI 未响应；请确认已启动且 `COMFYUI_SERVER` 正确 |
| **VTO-BE-S06** | 500 | 其他例外 | 上传过程例外；消息内含 `str(e)`，可对照后端日志 |

### `POST /api/virtual-try-on/generate`

> 编号 **GM** = Generate（后端业务层），避免与前端 **VTO-FE-G\*** 混淆。

| 错误码 | HTTP / 结构 | 触发条件 | 用户可读说明 |
|--------|-------------|----------|----------------|
| **VTO-BE-GM01** | 503 + body | 与 S01 相同：功能未启用 | 同上 |
| **VTO-BE-GM02** | 200 + `success: false` | 无 token | 请先登录 |
| **VTO-BE-GM03** | 200 + `success: false` | Token 验证失败 | 请重新登录 |
| **VTO-BE-GM04** | 200 + `success: false` | 账号异常 | 账号状态异常 |
| **VTO-BE-GM05** | 200 + `success: false` | `queue_prompt` 无 `prompt_id` | ComfyUI 队列满或连接失败 |
| **VTO-BE-GM06** | 200 + `success: false` | 输出无节点 `60` | 工作流与后端预期不一致（节点 ID 变更） |
| **VTO-BE-GM07** | 200 + `success: false` | 节点 `60` 无图片数组或为空 | 生成未产出有效图（模型/输入/工作流问题） |
| **VTO-BE-GM08** | 200 + `success: false` | `get_image` 回空 | 无法读取 ComfyUI 输出文件（时序或路径问题） |
| **VTO-BE-GM09** | 200 + `success: false` | `generate` 内其他例外 | 生成失败；消息含例外字符串，需对照后端 traceback |

---

## 四、如何从界面反推错误码

1. **Toast 已是具体中文/英文句子** → 对照 **VTO-FE-U\***、**VTO-FE-D\***、**VTO-FE-G\*** 或 **VTO-BE-\*** 中「与消息相似」列。  
2. **只显示 `Render failed`** → **VTO-FE-V04**（请打开控制台 `[VirtualTryOn] handleGenerate failed`）。  
3. **只显示 `Outfit try-on failed`** → **VTO-FE-V05**（Full Outfit 兜底）。  
4. **HTTP 401/403/503** → 优先 **VTO-BE-A\***、**VTO-BE-S01/S05**。  

---

## 五、维护说明

- 若在 `virtualTryOnApi.js` 新增 `throw new Error(...)`，请同步本表新增一行并分配新 **VTO-FE-** 码。  
- 若在 `virtual_tryon_service.py` 新增 `HTTPException` / `JsonEnvelope`，请同步 **VTO-BE-** 码。  

（文件路径：`src/test/VirtualTryOn_Error_Codes.md`）
