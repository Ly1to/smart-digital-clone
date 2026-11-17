# 对话机器人与 QQ 接入

> 所属项目：个人日程系统  
> 参考项目：AstrBot 的平台适配器、LLM Provider 和工具调用分层  
> 状态：Phase 1 已实现；Phase 2–4 待实现  
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
  onebot.py     平台适配器：收发消息、重连、echo 关联      Phase 2
  pipeline.py   对话管道：消息 → LLM → 工具 → 回复        Phase 1
  llm.py        Provider 协议 + DeepSeek 实现             Phase 1
  tools.py      日程工具：查询 / 搜索 / 详情              Phase 1
  context.py    进程内短期对话历史                        Phase 1
  binding.py    QQ ↔ 账号绑定                            Phase 2
  ▼
schedule_service（严格按 user_id 过滤）
```

机器人作为 FastAPI 进程内的 asyncio 后台任务启动，由 `QQ_BOT_ENABLED` 控制，默认关闭。当前是单进程 + SQLite 部署，模块保持独立，后续可以拆成单独的 bot worker。

## 3. Phase 1：对话内核（已实现）

### 3.1 接口

```text
GET  /api/bot/status    # 是否配置 LLM、模型名、QQ 是否启用
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
- 只依赖已有的 `httpx`，不新增 SDK
- 通过 `DEEPSEEK_BASE_URL` / `DEEPSEEK_MODEL` 可以接入其他兼容服务

### 3.4 对话与上下文

- 系统提示词包含当前时间、应用时区和“只回答日程问题、必须调用工具”等规则
- 每个会话保留最近 `BOT_HISTORY_TURNS` 轮（默认 6），保存在进程内
- 历史按 `user:<id>:<conversation_id>` 隔离；重启后清空，Phase 3 再评估是否需要持久化

### 3.5 配置

```env
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
BOT_HISTORY_TURNS=6
BOT_MAX_TOOL_ROUNDS=4
BOT_LLM_TIMEOUT_SECONDS=30
QQ_BOT_ENABLED=false
```

## 4. Phase 2：QQ 接入与账号绑定（待实现）

### 4.1 OneBot v11

- 后端启动一个 WebSocket 客户端，连接 NapCat 的 OneBot v11 服务
- 配置：`ONEBOT_WS_URL`、`ONEBOT_ACCESS_TOKEN`
- 处理 `message` 事件，调用 `send_msg`，用 `echo` 关联请求与响应
- 断线指数退避重连；连接状态通过 `/api/bot/status` 暴露

消息策略：

- 私聊：直接响应
- 群聊：只有 @机器人 或以 `/日程` 开头时响应
- 支持 `QQ_BOT_ALLOWED_USERS` / `QQ_BOT_ALLOWED_GROUPS` 白名单
- 未绑定账号：回复绑定指引，不执行任何日程工具

### 4.2 账号绑定

新增迁移 `0005_qq_bindings`：

```text
qq_bindings
- id
- user_id（外键，级联删除）
- platform（onebot）
- external_id（QQ 号）
- created_at
- unique(platform, external_id)
```

流程：

1. 用户在网页设置中请求绑定码：`POST /api/bot/bind-code`
2. 后端生成 6 位一次性验证码，10 分钟有效
3. 用户在 QQ 私聊发送“绑定 123456”
4. 机器人校验后写入 `qq_bindings`，回复绑定成功
5. 网页端提供解绑入口

### 4.3 测试

- 本地起假的 OneBot WebSocket 服务，验证事件解析、消息发送和重连
- 绑定码过期、重复绑定、未绑定访问、跨账号查询
- 不需要真实 QQ 号即可覆盖大部分逻辑

## 5. Phase 3：写操作与确认（待实现）

- 新增 `create_schedule`、`update_schedule_status`、`delete_schedule`
- 写操作采用“模型提议 → 用户回复确认 → 执行”的两步流程
- 删除仍要求二次确认，所有写操作记录操作日志
- 每个 QQ 增加频率限制，避免刷接口和 Token 消耗

## 6. Phase 4：部署与运维（待实现）

- Docker Compose 增加可选的 `napcat` 服务（profile，默认不启动）
- NapCat 与后端通过内部网络连接，QQ 号只配置在 NapCat 侧
- 文档补充 QQ 风控说明、Token 成本、密钥管理和备份
- 手工验收清单：私聊查询、群内 @、未绑定提示、解绑、断线重连

## 7. 安全边界

- QQ 只能访问绑定账号的数据，工具层强制 `user_id` 过滤
- 绑定码一次性、短有效期，避免被猜中
- 群聊默认需要 @ 或前缀，避免刷屏
- 写操作必须二次确认
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

Phase 2（待实现）：

- [ ] NapCat WebSocket 连接与重连
- [ ] 私聊 / 群内 @ 路由
- [ ] 绑定码生成、绑定、解绑
- [ ] 未绑定提示与白名单
