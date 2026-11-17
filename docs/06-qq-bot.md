# 对话机器人与 QQ 接入

> 所属项目：个人日程系统  
> 参考项目：AstrBot 的平台适配器、LLM Provider 和工具调用分层  
> 状态：Phase 1、Phase 2 已实现；Phase 3–4 待实现  
> 更新日期：2026-11-20

## 1. 目标

通过 QQ 私聊或群内 @ 机器人，用自然语言查询个人日程。机器人只读取当前 QQ 绑定账号的数据，不跨账号访问。

不直接依赖 AstrBot 框架，而是借鉴它的三层结构：

1. **平台适配器**：QQ 通过 OneBot v11（NapCat / Lagrange）接入。
2. **LLM Provider**：统一 OpenAI 兼容接口，默认 DeepSeek，可替换 base URL 和模型。
3. **工具调用管道**：消息 → 绑定账号 → 调用日程工具 → 自然语言回复。

## 2. 架构

```text
QQ 用户
  │  私聊 / 群内 @
  ▼
NapCat（OneBot v11）
  │  WebSocket
  ▼
backend/app/bot/
  onebot.py     平台适配器：收发消息、重连、分片发送        Phase 2
  qq.py         事件解析：私聊/群聊、@、前缀、绑定命令      Phase 2
  binding.py    绑定码与 QQ ↔ 账号关系                      Phase 2
  pipeline.py   对话管道：消息 → LLM → 工具 → 回复          Phase 1
  llm.py        Provider 协议 + DeepSeek 实现               Phase 1
  tools.py      日程工具：查询 / 搜索 / 详情                 Phase 1
  context.py    进程内短期对话历史                          Phase 1
  ▼
schedule_service（严格按 user_id 过滤）
```

机器人作为 FastAPI 进程内的 asyncio 后台任务启动，由 `QQ_BOT_ENABLED` 控制，默认关闭。当前是单进程 + SQLite 部署，模块保持独立，后续可以拆成单独的 bot worker。

## 3. Phase 1：对话内核（已实现）

### 3.1 接口

```text
GET  /api/bot/status    # 是否配置 LLM、模型名、QQ 启用与连接状态
POST /api/bot/chat      # 需要登录；调试用对话入口
```

请求：

```json
{
  "message": "我今天有什么安排？",
  "conversation_id": "可选，同一会话复用"
}
```

响应：

```json
{
  "conversation_id": "6f1c...",
  "reply": "今天有 3 个日程：……",
  "tools_used": ["list_schedules"]
}
```

未配置 `DEEPSEEK_API_KEY` 返回 503；模型服务异常返回 502。

### 3.2 工具

| 工具 | 作用 | 关键参数 |
| --- | --- | --- |
| `list_schedules` | 查询时间区间内的日程，缺省为今天 | `start`、`end`、`categories`、`statuses` |
| `search_schedules` | 按关键词搜索标题和描述 | `keyword` |
| `get_schedule` | 按 ID 查询单条日程 | `schedule_id` |

- 时间使用 ISO 8601；不带时区时按 `APP_TIMEZONE` 解释。
- 全天日程按 UTC 日期分量返回，避免时区换算跨天。
- 工具结果最多返回 50 条，超出时带 `truncated` 标记。
- 工具异常转换为 JSON 错误返回给模型，由模型向用户解释，不打断整轮对话。

### 3.3 Provider

- 默认 DeepSeek：`https://api.deepseek.com` + `deepseek-chat`
- 使用 OpenAI 兼容的 `/chat/completions` 和 function calling
- 只依赖 `httpx`，不新增 SDK
- 通过 `DEEPSEEK_BASE_URL` / `DEEPSEEK_MODEL` 可以接入其他兼容服务

### 3.4 对话与上下文

- 系统提示词包含当前时间、应用时区和“只回答日程问题、必须调用工具”等规则
- 每个会话保留最近 `BOT_HISTORY_TURNS` 轮（默认 6），保存在进程内
- 历史按 `user:<id>:<conversation_id>`（HTTP）或 `qq:<QQ号>`（QQ）隔离
- 重启后清空，Phase 3 再评估是否需要持久化

## 4. Phase 2：QQ 接入与账号绑定（已实现）

### 4.1 OneBot v11 适配器

`onebot.py` 以 WebSocket 客户端连接 NapCat / Lagrange 的正向 WebSocket：

- 配置：`ONEBOT_WS_URL`、`ONEBOT_ACCESS_TOKEN`
- 断线后指数退避重连（5 秒起，最大 60 秒）
- 只处理 `post_type == "message"` 的事件，忽略机器人自己的消息
- 通过 `send_private_msg` / `send_group_msg` 回复，`auto_escape` 避免模型输出被当作 CQ 码
- 长回复按 `QQ_BOT_REPLY_CHUNK_SIZE`（默认 1200 字）分片发送
- 连接状态通过 `/api/bot/status` 的 `qq_connected` 暴露

消息策略：

- 私聊：直接响应
- 群聊：必须 @机器人 或使用 `/日程` 前缀；二者可以同时使用
- `QQ_BOT_ALLOWED_USERS` / `QQ_BOT_ALLOWED_GROUPS` 为逗号分隔白名单，留空表示不限制
- 未绑定账号：回复绑定指引，不执行任何日程工具

### 4.2 账号绑定

迁移 `0005_qq_bindings`：

```text
qq_bindings
- id
- user_id（外键，ON DELETE CASCADE）
- platform（onebot）
- external_id（QQ 号）
- created_at
- unique(platform, external_id)
- index(user_id)
```

绑定流程：

1. 登录网页后调用 `POST /api/bot/bind-code` 生成 6 位一次性绑定码，10 分钟有效
2. QQ 私聊机器人发送 `绑定 123456`（也支持 `/bind 123456`）
3. 机器人校验并写入 `qq_bindings`，回复绑定成功
4. 一个 QQ 只能绑定一个账号；已被其他账号占用时拒绝，不会自动转移
5. 绑定码只在私聊接受，避免在群里泄露

绑定管理：

```text
POST   /api/bot/bind-code        # 生成绑定码
GET    /api/bot/bindings         # 当前账号的绑定列表
DELETE /api/bot/bindings/{id}    # 解绑
```

### 4.3 配置

```env
QQ_BOT_ENABLED=true
ONEBOT_WS_URL=ws://127.0.0.1:3001
ONEBOT_ACCESS_TOKEN=
QQ_BOT_ALLOWED_USERS=
QQ_BOT_ALLOWED_GROUPS=
QQ_BIND_CODE_TTL_SECONDS=600
QQ_BOT_REPLY_CHUNK_SIZE=1200
```

### 4.4 测试

- 绑定码生成、一次性消费、过期
- 私聊绑定、重复绑定、QQ 被其他账号占用
- 未绑定提示
- 绑定后对话（使用假 Provider，不访问外网）
- 群聊未 @ 忽略、@ 后回复
- 白名单拦截
- 绑定列表与解绑接口
- 长消息分片

### 4.5 当前限制

- 绑定码保存在进程内，重启后失效；有效期只有 10 分钟，可接受
- 只有单进程时能保证连接唯一；多 worker 部署需要单独的 bot worker
- 前端暂时没有绑定码 UI，需要通过 API 或 Swagger 生成
- NapCat / Lagrange 属于非官方 QQ 协议，存在账号风控风险

## 5. Phase 3：写操作与确认（待实现）

- 新增 `create_schedule`、`update_schedule_status`、`delete_schedule`
- 写操作采用“模型提议 → 用户回复确认 → 执行”的两步流程
- 删除仍要求二次确认，所有写操作记录操作日志
- 每个 QQ 增加频率限制，避免刷接口和 Token 消耗
- 评估把对话历史持久化到数据库

## 6. Phase 4：部署与运维（待实现）

- Docker Compose 增加可选的 `napcat` 服务（profile，默认不启动）
- NapCat 与后端通过内部网络连接，QQ 号只配置在 NapCat 侧
- 文档补充 QQ 风控说明、Token 成本、密钥管理和备份
- 手工验收清单：私聊查询、群内 @、未绑定提示、解绑、断线重连
- 前端补充绑定码生成、绑定列表和解绑入口，并展示机器人连接状态

## 7. 安全边界

- QQ 只能访问绑定账号的数据，工具层强制 `user_id` 过滤
- 绑定码一次性、短有效期，且只接受私聊发送
- 群聊默认需要 @ 或前缀，避免刷屏
- 写操作必须二次确认（Phase 3）
- API Key 只放环境变量，不写日志；错误信息不包含密钥
- NapCat / Lagrange 属于非官方 QQ 协议，存在账号风控风险，需自行评估

## 8. 验收清单

Phase 1（已完成）：

- [x] 配置 DeepSeek Key 后 `/api/bot/chat` 能返回日程查询结果
- [x] 未配置 Key 返回 503，不影响其他接口
- [x] 工具按当前用户过滤
- [x] 模型返回工具调用、工具结果回填、最终回复的完整链路
- [x] 对话历史按会话隔离
- [x] 使用假 Provider 的后端测试，不依赖外网

Phase 2（已完成）：

- [x] OneBot WebSocket 连接、消息收发与断线重连
- [x] 私聊 / 群内 @ / `/日程` 前缀路由
- [x] 绑定码生成、私聊绑定、绑定列表与解绑
- [x] 未绑定提示与 QQ / 群白名单
- [x] 长回复分片与连接状态查询

Phase 3–4（待实现）：

- [ ] 写操作与确认流程
- [ ] 频率限制与操作日志
- [ ] NapCat Compose 编排与前端绑定入口
