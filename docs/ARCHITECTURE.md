# 系统架构

> 适用版本：当前 `main` 分支  
> 更新日期：2026-11-20

## 1. 总览

```text
浏览器（Vue 3 + Element Plus + FullCalendar）
  │  /api 同源请求（开发环境由 Vite 代理）
  ▼
Nginx（frontend 容器）
  │-- /       → Vue 静态文件
  │-- /api/   → FastAPI
  ▼
FastAPI（backend 容器，uvicorn 单进程）
  │-- /api/auth       登录、注册、JWT
  │-- /api/schedules  日程 CRUD
  │-- /api/staging    自动来源暂存区
  │-- /api/auto-sources GitHub / Gitee 同步
  │-- /api/bot        对话助手与 QQ 绑定
  │-- /api/health     健康检查
  ▼
SQLite（/app/data/schedules.db，Docker 命名卷）
```

后台任务：

- GitHub / Gitee 自动同步（asyncio 循环，可配置间隔）
- QQ OneBot WebSocket 客户端（`QQ_BOT_ENABLED=true` 时启动）

## 2. 代码地图

```text
backend/app/
  main.py             应用装配、lifespan 后台任务、异常处理
  api/
    deps.py           Bearer Token → 当前用户
    routes/           health、auth、schedules、staging、auto_sources、bot
  core/
    config.py         Settings（环境变量）
    time.py           UTC/时区工具
  db/
    base.py           声明式 Base
    session.py        SQLite 引擎、会话、外键 pragma
  models/             users、schedules、staged_schedules、qq_bindings
  schemas/            Pydantic 请求/响应
  services/
    auth_service.py   密码哈希、JWT、用户
    schedule_service.py
    staging_service.py + scheduling.py
    github_service.py / gitee_service.py
    sync_lock.py
  bot/
    llm.py            Provider 协议 + DeepSeek
    tools.py          只读日程工具
    pipeline.py       对话与工具调用循环
    prompt.py         系统提示词
    context.py        进程内会话历史
    binding.py        绑定码 + qq_bindings
    qq.py             OneBot 事件解析与消息路由
    onebot.py         WebSocket 客户端、重连、收发
frontend/src/
  api/                Axios 封装
  stores/             Pinia：auth、schedule
  views/              LoginView、RegisterView、CalendarView
  components/         calendar、agenda、filters、schedule、staging、settings、common
  styles/             Tailwind @theme 设计令牌 + FullCalendar/Element Plus 覆盖
  utils/              日期、表单、事件渲染
```

## 3. 请求流程

### 3.1 浏览器请求

1. Axios 从 `localStorage` 读取 JWT，附加 `Authorization: Bearer <token>`。
2. FastAPI 的 `get_current_user` 解析 JWT，加载 `User`，未通过返回 401。
3. 路由层做参数校验，调用 service；service 的每条查询都带 `user_id`。
4. 响应统一使用 Pydantic 模型，时间序列化为 UTC `Z` 字符串。
5. 前端按浏览器本地时区展示；全天事件按 UTC 日期分量展示。

### 3.2 账号隔离

- `schedules.user_id`、`staged_schedules.user_id`、`qq_bindings.user_id` 均指向 `users.id`。
- 所有读取/更新/删除都同时匹配资源 ID 和当前 `user_id`，不匹配时返回 404，避免泄露资源是否存在。
- 删除账号由 SQLite 外键 `ON DELETE CASCADE` 级联删除日程、暂存和 QQ 绑定。

### 3.3 自动来源

```text
GitHub / Gitee API
  → 抓取最近 N 天仓库事件
  → 按仓库聚合成待确认条目（staged_schedules，pending）
  → 分配“今天 09:00–22:00”内的空闲时段
  → 用户确认后写入 schedules
```

- 同步使用 `sync_lock` 防止同一进程内并发同步。
- 后台任务归属第一个创建的管理员账号；其他账号手动同步写入自己的暂存区。
- 时间窗口和占位日期由 `APP_TIMEZONE` 决定。

### 3.4 对话助手

```text
HTTP /api/bot/chat 或 QQ 消息
  → 解析当前账号（HTTP 取 JWT；QQ 查 qq_bindings）
  → 组装系统提示词 + 最近历史 + 用户消息
  → DeepSeek Chat Completions（tools 定义）
  → 模型返回 tool_calls
  → 后端执行只读日程工具（强制 user_id）
  → 工具结果回传模型
  → 最终自然语言回复
```

- Provider 通过 `DEEPSEEK_BASE_URL` / `DEEPSEEK_MODEL` 可替换为其他 OpenAI 兼容服务。
- 工具异常转换为 JSON 错误交给模型解释，不会中断整轮对话。
- 对话历史在进程内按会话键保存，重启清空。
- QQ 绑定码保存在进程内，10 分钟有效、一次性，仅私聊接受。

## 4. 数据模型

```text
users
  id, username(unique), password_hash, created_at, updated_at
    │
    ├──< schedules
    │     id, user_id, title, category, description,
    │     start_at, end_at, all_day, location, status,
    │     source, source_ref, source_url, created_at, updated_at
    │
    ├──< staged_schedules
    │     id, user_id, source, source_ref, source_url, source_meta,
    │     title, category, description, start_at, end_at, all_day, location,
    │     status(pending/approved/rejected), schedule_id, approved_at,
    │     created_at, updated_at
    │
    └──< qq_bindings
          id, user_id, platform(onebot), external_id(QQ号), created_at
          unique(platform, external_id)
```

迁移链：`0001` 日程 → `0002` 自动来源 → `0003` 用户 → `0004` 用户归属 → `0005` QQ 绑定。

## 5. 时区与时间

- 数据库统一保存 UTC。
- API 返回带 `Z` 的 ISO 8601 字符串；不带时区的输入按 UTC 处理。
- 全天事件保存为 UTC 日期锚点：开始日 `00:00` 到结束日 `23:59:59.999999`，首尾都包含。
- 后端自动排程的日期边界按 `APP_TIMEZONE` 计算，不依赖宿主机 `TZ`。
- 前端展示按浏览器本地时区；主题与语言不改变时间含义。

## 6. 配置分层

| 文件 | 用途 |
| --- | --- |
| `backend/.env` | 本地直接运行后端 |
| 根目录 `.env` | Docker Compose 部署 |
| 环境变量 | 覆盖默认值；字段见 `backend/app/core/config.py` |
| 前端 | 仅 `VITE_*` 变量；当前没有必须配置项 |

完整变量矩阵见 [DEPLOYMENT](./DEPLOYMENT.md#4-环境变量矩阵)。

## 7. 关键设计决策

| 决策 | 原因 |
| --- | --- |
| FastAPI 单体 + SQLite | 个人/小团队规模，部署简单，迁移路径清晰 |
| JWT 无服务端会话 | 单实例、无状态；退出由客户端清 Token |
| 自动来源“先暂存再确认” | 避免外部数据直接污染日历 |
| 固定三类分类 | 降低录入成本，分类色与文案双重区分 |
| 对话助手使用 function calling | 数据由后端工具读取，避免模型编造 |
| QQ 使用 OneBot v11 | 个人号接入成本低，AstrBot 生态验证充分 |
| 时间窗口显式 `APP_TIMEZONE` | 避免容器/宿主机时区不一致 |
| 主题偏好带版本号 | 升级默认主题时能一次性重置旧值 |

## 8. 扩展边界

- 拆出 bot worker：`app/bot` 已与 Web 路由解耦，可改为独立进程消费同一数据库。
- 迁移 PostgreSQL：SQLAlchemy + Alembic 已抽象，避免在业务代码写 SQLite 方言。
- 多实例部署：需要将会话历史、绑定码迁移到共享存储，并保证只有一个 bot 实例。
- 新增日程来源：实现 `sync_*` service，复用暂存区与空闲时段分配。
