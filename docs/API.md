# API 参考

> Base URL：`http://127.0.0.1:8000/api`  
> Swagger：`/docs`，OpenAPI：`/openapi.json`  
> 更新日期：2026-11-20

## 1. 通用约定

- 请求与响应均为 JSON（删除接口返回 204 无正文）。
- 除下列公开接口外，都需要 `Authorization: Bearer <access_token>`：

```text
GET  /api/health
GET  /api/auth/status
POST /api/auth/setup
POST /api/auth/register
POST /api/auth/login
```

- 时间使用 ISO 8601；服务端返回 UTC 并带 `Z`。
- 不带时区的输入按 UTC 处理。
- 全天日程按日期保存：开始日 `00:00:00Z` 到结束日 `23:59:59.999999Z`，首尾日期都包含。
- 错误响应统一为：

```json
{ "detail": "错误说明" }
```

| 状态码 | 含义 |
| --- | --- |
| 400 | 业务参数错误，例如结束时间早于开始时间 |
| 401 | 未登录或 Token 失效 |
| 403 | 功能被配置关闭（如注册） |
| 404 | 资源不存在，或不属于当前账号 |
| 409 | 冲突，例如用户名已存在、暂存已处理 |
| 422 | 请求字段校验失败 |
| 502 | 上游服务异常（GitHub/Gitee/对话模型） |
| 503 | 功能未配置（例如缺少 DeepSeek Key） |

## 2. 接口总览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/auth/status` | 初始化与注册开关状态 |
| POST | `/api/auth/setup` | 首次创建管理员 |
| POST | `/api/auth/register` | 注册新账号 |
| POST | `/api/auth/login` | 登录 |
| GET | `/api/auth/me` | 当前用户 |
| POST | `/api/auth/logout` | 退出登录 |
| GET | `/api/schedules` | 日程列表与筛选 |
| GET | `/api/schedules/{id}` | 日程详情 |
| POST | `/api/schedules` | 创建日程 |
| PATCH | `/api/schedules/{id}` | 局部更新日程 |
| DELETE | `/api/schedules/{id}` | 删除日程 |
| GET | `/api/staging` | 暂存列表 |
| PATCH | `/api/staging/{id}` | 调整暂存日程 |
| POST | `/api/staging/{id}/approve` | 插入单条暂存 |
| POST | `/api/staging/{id}/reject` | 丢弃单条暂存 |
| POST | `/api/staging/approve-all` | 全部插入今天空闲时段 |
| GET | `/api/auto-sources/github/status` | GitHub 配置状态 |
| POST | `/api/auto-sources/github/sync` | 同步 GitHub |
| GET | `/api/auto-sources/gitee/status` | Gitee 配置状态 |
| POST | `/api/auto-sources/gitee/sync` | 同步 Gitee |
| GET | `/api/bot/status` | 对话助手状态 |
| POST | `/api/bot/chat` | HTTP 对话入口 |
| POST | `/api/bot/bind-code` | 生成 QQ 绑定码 |
| GET | `/api/bot/bindings` | QQ 绑定列表 |
| DELETE | `/api/bot/bindings/{id}` | 解绑 QQ |

## 3. 健康检查

```http
GET /api/health
```

```json
{
  "status": "ok",
  "database": "ok",
  "timezone": "Asia/Shanghai"
}
```

`timezone` 是当前生效的 `APP_TIMEZONE`，可用于部署后核对配置。

## 4. 认证

### 4.1 状态

```http
GET /api/auth/status
```

```json
{ "initialized": true, "registration_enabled": true }
```

### 4.2 首次创建管理员

```http
POST /api/auth/setup
Content-Type: application/json

{ "username": "admin", "password": "至少8位密码" }
```

- 仅当 `users` 表为空时可用，否则 409。
- 返回 201：

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "username": "admin", "created_at": "2026-11-20T01:00:00Z" }
}
```

### 4.3 注册

```http
POST /api/auth/register

{ "username": "alice", "password": "至少8位密码" }
```

- `ALLOW_REGISTRATION=false` 时返回 403。
- 用户名重复返回 409。
- 成功返回 201，结构同 setup。

### 4.4 登录

```http
POST /api/auth/login

{ "username": "admin", "password": "..." }
```

成功返回 200 与 TokenResponse；密码错误返回 401。

### 4.5 当前用户与退出

```http
GET  /api/auth/me        → { "id": 1, "username": "admin", "created_at": "..." }
POST /api/auth/logout    → 204
```

JWT 没有服务端会话，退出由客户端删除 Token。

### 4.6 获取 Token 示例

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"your-password"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
```

## 5. 日程

### 5.1 列表与筛选

```http
GET /api/schedules
```

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `start` | ISO 8601 | 区间开始（含） |
| `end` | ISO 8601 | 区间结束（不含），必须晚于 `start` |
| `categories` | string | 逗号分隔：`work,outing,private` |
| `statuses` | string | 逗号分隔：`pending,completed,cancelled` |
| `keyword` | string | 同时匹配标题和描述，`%`/`_` 按普通字符处理 |

省略时间参数时返回当前账号的全部日程。

### 5.2 单条与写入

```http
GET    /api/schedules/{id}
POST   /api/schedules
PATCH  /api/schedules/{id}
DELETE /api/schedules/{id}
```

创建请求：

```json
{
  "title": "项目周会",
  "category": "work",
  "description": "讨论本周进度",
  "start_at": "2026-11-21T14:00:00+08:00",
  "end_at": "2026-11-21T15:00:00+08:00",
  "all_day": false,
  "location": "线上",
  "status": "pending"
}
```

| 字段 | 规则 |
| --- | --- |
| `title` | 必填，去除首尾空格后 1–200 字 |
| `category` | `work` / `outing` / `private` |
| `description` | 可选，最多 5000 字 |
| `start_at` / `end_at` | 必填；普通日程要求 `end_at > start_at` |
| `all_day` | 默认 `false`；`true` 时按日期保存 |
| `location` | 可选，最多 200 字 |
| `status` | 默认 `pending` |

`PATCH` 只更新传入的字段。删除返回 204。

### 5.3 日程对象

```json
{
  "id": 12,
  "title": "项目周会",
  "category": "work",
  "description": "讨论本周进度",
  "start_at": "2026-11-21T06:00:00Z",
  "end_at": "2026-11-21T07:00:00Z",
  "all_day": false,
  "location": "线上",
  "status": "pending",
  "source": "manual",
  "source_ref": null,
  "source_url": null,
  "created_at": "2026-11-20T01:00:00Z",
  "updated_at": "2026-11-20T01:00:00Z"
}
```

`source` 可能是 `manual`、`github`、`gitee`。

## 6. 暂存区

### 6.1 列表

```http
GET /api/staging?status=pending
```

`status`：`pending`（默认）/ `approved` / `rejected`。

### 6.2 调整、插入、丢弃

```http
PATCH /api/staging/{id}
POST  /api/staging/{id}/approve
POST  /api/staging/{id}/reject
POST  /api/staging/approve-all
```

调整请求字段与日程创建一致，但不能修改 `status`、`source`。

- `approve` 返回 `{ "staged": StagedScheduleRead, "schedule": ScheduleRead }`
- `reject` 返回更新后的 `StagedScheduleRead`
- `approve-all` 返回 `{ "approved": [ScheduleRead], "skipped": [StagedScheduleRead] }`
- 今天没有空闲时段时返回 409；`approve-all` 会跳过并放入 `skipped`

### 6.3 暂存对象

```json
{
  "id": 3,
  "source": "github",
  "source_ref": "github:owner/repo:2026-11-20",
  "source_url": "https://github.com/owner/repo",
  "source_meta": { "commits": 4 },
  "title": "owner/repo 有新的更新",
  "category": "work",
  "description": "...",
  "start_at": "2026-11-20T09:00:00Z",
  "end_at": "2026-11-20T09:30:00Z",
  "all_day": false,
  "location": null,
  "status": "pending",
  "schedule_id": null,
  "created_at": "2026-11-20T01:00:00Z",
  "updated_at": "2026-11-20T01:00:00Z",
  "approved_at": null
}
```

## 7. 自动来源

```http
GET  /api/auto-sources/github/status
POST /api/auto-sources/github/sync
GET  /api/auto-sources/gitee/status
POST /api/auto-sources/gitee/sync
```

状态响应：

```json
{
  "configured": true,
  "username": "your-name",
  "lookback_days": 14,
  "token_configured": false
}
```

同步响应：

```json
{
  "configured": true,
  "scanned_events": 42,
  "created": 3,
  "updated": 1,
  "skipped": 0,
  "no_slot": 0,
  "message": "已生成 4 条待确认日程"
}
```

未配置用户名/Token 时返回 400。

## 8. 对话助手与 QQ

### 8.1 状态

```http
GET /api/bot/status
```

```json
{
  "configured": true,
  "provider": "deepseek",
  "model": "deepseek-chat",
  "qq_enabled": true,
  "qq_connected": true
}
```

### 8.2 HTTP 对话

```http
POST /api/bot/chat

{ "message": "我今天有什么安排？", "conversation_id": "可选，字母数字_-" }
```

```json
{
  "conversation_id": "6f1c8a...",
  "reply": "今天有 2 个日程：...",
  "tools_used": ["list_schedules"]
}
```

- 未配置 `DEEPSEEK_API_KEY` 返回 503。
- 模型服务异常返回 502。
- `conversation_id` 用于延续上下文；不传则生成新的。

### 8.3 绑定码

```http
POST /api/bot/bind-code
```

```json
{
  "code": "123456",
  "expires_at": "2026-11-20T01:10:00Z",
  "expires_in_seconds": 600
}
```

### 8.4 绑定列表与解绑

```http
GET    /api/bot/bindings
DELETE /api/bot/bindings/{id}
```

```json
[
  {
    "id": 1,
    "platform": "onebot",
    "external_id": "123456789",
    "created_at": "2026-11-20T01:00:00Z"
  }
]
```

QQ 侧操作：

- 私聊发送 `绑定 123456` 完成绑定
- 群聊需 @机器人 或 `/日程` 前缀
- 未绑定 QQ 会收到绑定指引

## 9. 完整调用示例

```bash
BASE=http://127.0.0.1:8000/api

# 登录
TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"your-password"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

# 创建日程
curl -s -X POST "$BASE/schedules" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "项目周会",
    "category": "work",
    "start_at": "2026-11-21T14:00:00+08:00",
    "end_at": "2026-11-21T15:00:00+08:00"
  }'

# 查询本周
curl -s "$BASE/schedules?start=2026-11-17T00:00:00%2B08:00&end=2026-11-24T00:00:00%2B08:00" \
  -H "Authorization: Bearer $TOKEN"

# 问机器人
curl -s -X POST "$BASE/bot/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"message":"我今天有什么安排？"}'
```
