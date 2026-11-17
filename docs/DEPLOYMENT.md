# 部署与运维

> 适用版本：当前 `main` 分支  
> 更新日期：2026-11-20

## 1. 环境要求

| 场景 | 要求 |
| --- | --- |
| 本地开发 | Python 3.14、[uv](https://docs.astral.sh/uv/)、Node.js 26、npm 12 |
| Docker 部署 | Docker Engine、Docker Compose v2 |
| QQ 机器人 | NapCat 或 Lagrange（OneBot v11），可选 |

## 2. 本地开发

```bash
make setup     # 安装后端/前端依赖
make migrate   # 初始化数据库
```

两个终端分别启动：

```bash
# 后端
cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 前端
cd frontend && npm run dev
```

- 前端：<http://127.0.0.1:5173>
- Swagger：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/health>
- 默认数据库：`data/schedules.db`，可用 `DATABASE_URL` 覆盖
- 本地后端配置写在 `backend/.env`（参考 `backend/.env.example`）

## 3. Docker 部署

### 3.1 首次启动

```bash
cp .env.example .env
# 必填 JWT_SECRET
openssl rand -base64 48
make docker-up
```

访问 `http://<host>:${APP_PORT:-8080}`。

### 3.2 编排结构

```text
浏览器 :8080
  │
  ▼
web（Nginx）
  │-- /       → /usr/share/nginx/html（Vue 静态文件）
  │-- /api/   → backend:8000
  ▼
backend（uvicorn 单进程）
  │
  ▼
SQLite /app/data/schedules.db
  │
  ▼
Docker 命名卷 digital-clone_schedules-data
```

相关文件：

- `backend/Dockerfile`：uv 多阶段构建，启动时执行 `alembic upgrade head`
- `frontend/Dockerfile`：Node 构建 + Nginx 运行
- `frontend/nginx.conf`：SPA 回退、静态缓存、`/api` 反代、基础安全头
- `docker-compose.yml`：健康检查、日志轮转、SQLite 持久化卷
- `scripts/backup-db.sh`：SQLite 在线备份

### 3.3 常用命令

```bash
make docker-up      # 构建并后台启动
make docker-down    # 停止并移除容器（保留数据卷）
make docker-logs    # 查看日志
make docker-ps      # 查看健康状态
make backup         # 备份数据库到 backups/
```

`docker compose down -v` 会删除数据卷，谨慎使用。

## 4. 环境变量矩阵

### 4.1 通用

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `APP_PORT` | `8080` | Compose 暴露到宿主机的端口 |
| `DATABASE_URL` | `sqlite:///…/data/schedules.db` | SQLAlchemy 连接串 |
| `APP_TIMEZONE` | `Asia/Shanghai` | 应用时区，影响自动排程窗口 |
| `CORS_ORIGINS` | 本地 5173 | JSON 数组；生产同源部署通常不需要改 |
| `JWT_SECRET` | 随机生成 | 生产必填，至少 32 字节；否则重启后登录失效 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` | Token 有效期（7 天） |

### 4.2 账号

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `ALLOW_REGISTRATION` | `true` | `false` 时注册接口 403、前端隐藏入口 |
| `AUTH_BOOTSTRAP_USERNAME` | 空 | 首次启动自动创建管理员 |
| `AUTH_BOOTSTRAP_PASSWORD` | 空 | 与用户名成对配置 |

### 4.3 自动来源

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `GITHUB_USERNAME` | 空 | GitHub 用户名 |
| `GITHUB_TOKEN` | 空 | 私有仓库需要 |
| `GITHUB_LOOKBACK_DAYS` | `14` | 回溯天数 |
| `GITHUB_AUTO_SYNC_MINUTES` | `360` | 自动同步间隔，`0` 关闭 |
| `GITEE_USERNAME` | 空 | Gitee 用户名 |
| `GITEE_ACCESS_TOKEN` | 空 | 私有仓库需要 |
| `GITEE_LOOKBACK_DAYS` | `14` | 回溯天数 |
| `GITEE_AUTO_SYNC_MINUTES` | `360` | 自动同步间隔，`0` 关闭 |
| `AUTO_SCHEDULE_DAY_START_HOUR` | `9` | 分配空档的起始小时 |
| `AUTO_SCHEDULE_DAY_END_HOUR` | `22` | 分配空档的结束小时 |
| `AUTO_SCHEDULE_DURATION_MINUTES` | `30` | 每条暂存日程默认时长 |

### 4.4 对话助手

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 空 | 未配置时 `/api/bot/chat` 返回 503 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | OpenAI 兼容接口地址 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 模型名 |
| `BOT_HISTORY_TURNS` | `6` | 每个会话保留轮数，`0` 表示不保留 |
| `BOT_MAX_TOOL_ROUNDS` | `4` | 单轮对话最多工具调用次数 |
| `BOT_LLM_TIMEOUT_SECONDS` | `30` | 模型请求超时 |

### 4.5 QQ 接入

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `QQ_BOT_ENABLED` | `false` | 是否启动 OneBot 客户端 |
| `ONEBOT_WS_URL` | 空 | NapCat 正向 WebSocket，例如 `ws://127.0.0.1:3001` |
| `ONEBOT_ACCESS_TOKEN` | 空 | 与 NapCat 的 access token 一致 |
| `QQ_BOT_ALLOWED_USERS` | 空 | QQ 号白名单，逗号分隔；留空不限制 |
| `QQ_BOT_ALLOWED_GROUPS` | 空 | 群号白名单，逗号分隔；留空不限制 |
| `QQ_BIND_CODE_TTL_SECONDS` | `600` | 绑定码有效期 |
| `QQ_BOT_REPLY_CHUNK_SIZE` | `1200` | 单条 QQ 回复最大长度 |

## 5. 数据库迁移与升级

```bash
make migrate                      # 本地升级到最新
cd backend && uv run alembic check
```

Docker 部署在后端容器启动时自动执行 `alembic upgrade head`，不需要手动迁移。

升级流程：

```bash
git pull
make verify        # 可选但推荐
make docker-up     # 重新构建并重启
make docker-ps     # 确认 health 状态
```

回滚策略：

1. 先停止服务：`make docker-down`
2. 恢复升级前的数据库备份（见下节）
3. 切回旧代码版本并重新启动
4. 如果旧版本不支持新迁移，需要手动 `alembic downgrade <revision>`

## 6. 备份与恢复

### 6.1 在线备份

```bash
make backup
# 输出：backups/schedules-YYYYMMDD-HHMMSS.db
```

脚本使用 SQLite 在线备份 API，一致性优于直接复制数据库文件。

### 6.2 恢复

```bash
make docker-down
docker compose run --rm \
  -v "$PWD/backups:/backup:ro" \
  --entrypoint sh backend \
  -c 'cp /backup/schedules-YYYYMMDD-HHMMSS.db /app/data/schedules.db'
make docker-up
```

恢复前建议先另存当前数据库。

### 6.3 建议

- 每天至少备份一次，备份文件放到不同磁盘或对象存储
- 备份包含密码哈希和 QQ 绑定关系，注意访问权限
- 定期在测试环境验证恢复流程

## 7. HTTPS 与反向代理

Nginx 默认只提供 HTTP。推荐在宿主机或云负载均衡终止 HTTPS，再转发到 `APP_PORT`。

如果要在 Nginx 内终止 HTTPS：

1. 挂载证书到 `web` 容器
2. 在 `frontend/nginx.conf` 增加 443 server 与证书配置
3. Compose 暴露 443 端口
4. 配置 HTTP → HTTPS 跳转

公网部署至少启用：HTTPS、强 `JWT_SECRET`、`ALLOW_REGISTRATION=false`、定期备份。

## 8. QQ 机器人部署

### 8.1 安装 NapCat

参考 [NapCat 文档](https://napcat.napneko.icu/) 启动 QQ 并开启 OneBot v11 正向 WebSocket：

- 监听地址：`0.0.0.0:3001`（按需）
- Access Token：与 `ONEBOT_ACCESS_TOKEN` 一致

### 8.2 与后端的网络关系

| 部署方式 | `ONEBOT_WS_URL` |
| --- | --- |
| 本机直接运行后端 + NapCat | `ws://127.0.0.1:3001` |
| 后端在 Docker，NapCat 在宿主机 | `ws://host.docker.internal:3001`，Linux 需给 backend 增加 `extra_hosts: ["host.docker.internal:host-gateway"]` |
| NapCat 与后端在同一 Compose 网络 | `ws://napcat:3001` |

### 8.3 启用

```env
QQ_BOT_ENABLED=true
ONEBOT_WS_URL=ws://127.0.0.1:3001
ONEBOT_ACCESS_TOKEN=...
DEEPSEEK_API_KEY=sk-...
```

重启后端后：

```bash
curl -s http://127.0.0.1:8000/api/bot/status -H "Authorization: Bearer $TOKEN"
# qq_enabled 与 qq_connected 应为 true
```

生成绑定码并在 QQ 私聊发送 `绑定 <code>`。详见 [对话机器人与 QQ 接入](./06-qq-bot.md)。

### 8.4 注意事项

- NapCat / Lagrange 属于非官方 QQ 协议，存在风控风险
- 机器人必须是单实例；多 worker 会导致重复回复和连接冲突
- 群聊默认需要 @ 或 `/日程` 前缀；建议配置群白名单
- 绑定码只接受私聊，不要在群里发送

## 9. 日志与监控

- 后端日志：`make docker-logs`，Uvicorn 输出到 stdout/stderr
- 容器日志轮转：单文件 10 MB，保留 3 个
- 健康检查：`GET /api/health`（数据库 + 时区）
- Nginx 健康检查：`/healthz`
- 建议在宿主机或云监控中监控：
  - 容器健康状态
  - `/api/health` 5xx
  - 磁盘空间（SQLite、备份目录）
  - QQ 连接状态（`/api/bot/status`）

## 10. 安全清单

- [ ] `JWT_SECRET` 已设置为随机值且不外泄
- [ ] 公网部署已启用 HTTPS
- [ ] `ALLOW_REGISTRATION` 按需关闭
- [ ] 数据库与备份文件权限仅服务账号可读
- [ ] `DEEPSEEK_API_KEY`、GitHub/Gitee Token 只放环境变量
- [ ] QQ 白名单已配置（如面向小范围使用）
- [ ] 定期执行并验证备份恢复
- [ ] 升级前跑过 `make verify`

## 11. 常见问题排查

| 现象 | 排查方向 |
| --- | --- |
| 容器健康检查失败 | `make docker-logs` 看迁移或启动错误；确认 `/app/data` 可写 |
| 登录后立即失效 | `JWT_SECRET` 未固定，进程重启后随机密钥变化 |
| 接口 401 | Token 过期或未附加 `Authorization`；重新登录 |
| 注册入口消失/403 | `ALLOW_REGISTRATION=false` |
| 自动来源 400 | 未配置 `GITHUB_USERNAME` / `GITEE_USERNAME` |
| 自动来源 502 | Token 权限不足、API 限流或网络不通 |
| 暂存插入 409 | 今天 09:00–22:00 没有足够空档 |
| 机器人 503 | 未配置 `DEEPSEEK_API_KEY` |
| `qq_connected=false` | 检查 `QQ_BOT_ENABLED`、`ONEBOT_WS_URL`、NapCat 是否监听、Token 是否一致 |
| QQ 不回复群消息 | 未 @机器人，或群号不在白名单 |
| 绑定失败 | 绑定码过期/已被使用；QQ 已绑定其他账号 |
| 时间显示偏移 | 核对 `APP_TIMEZONE` 与浏览器时区；`/api/health` 返回当前值 |
| 备份脚本失败 | 后端容器未运行，或 `docker compose ps` 中服务名不是 `backend` |
