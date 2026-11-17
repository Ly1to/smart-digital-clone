# 个人日程系统

支持多账号、需要登录的个人日程系统。每个账号拥有独立的日程和暂存区，可完成工作、外出、私人时间三类日程的手动创建、查看、编辑、删除、搜索和筛选，并支持 GitHub 自动来源暂存区。

当前进度：**后端、数据库、登录、前端和 Docker/Nginx 部署已完成**，待一周试用反馈。

## 目录

```text
digital-clone/
  Makefile            # 常用开发、测试、构建、部署命令
  docker-compose.yml  # 生产/试用环境的 Compose 编排
  .env.example        # Docker Compose 环境变量示例
  scripts/
    backup-db.sh      # SQLite 在线备份脚本
  backend/
    Dockerfile
    docker-entrypoint.sh
    app/
      api/routes/     # health、schedules 路由
      core/           # 配置与时间工具
      db/             # SQLAlchemy 引擎和会话
      models/         # schedules ORM 模型与枚举
      schemas/        # Pydantic 请求/响应模型
      services/       # 业务规则与查询
    alembic/          # 数据库迁移
    tests/            # pytest API 测试
  frontend/
    Dockerfile
    nginx.conf        # 静态文件与 /api 反向代理
    src/
      api/            # Axios 封装与日程接口
      components/     # 日历、筛选、日程表单与详情
      constants/      # 分类/状态标签与颜色
      stores/         # Pinia 日程与筛选状态
      styles/         # Tailwind 入口、设计 Token 与第三方组件覆盖
      types/          # TypeScript 类型
      utils/          # 日期与表单转换
      views/          # 日历主页
    tests/            # Vitest 单元与组件测试
    e2e/              # Playwright 主流程测试
  data/               # SQLite 数据文件（本地生成）
  docs/               # 产品范围、技术栈、开发手册
```

## 功能

- 首次部署创建管理员账号，之后可在注册页创建更多账号；每个账号的数据相互隔离
- JWT 登录状态保存于浏览器，所有日程、暂存区和自动来源接口均需登录
- 桌面端默认周视图，支持日、周、月三种日历视图和前后切换
- 点击空白日期或「新建日程」手动创建日程，自动带入对应日期和时间
- 点击日程查看详情，支持编辑、删除确认和未保存修改提醒
- 工作、外出、私人时间三类固定分类，颜色、中文文字和一字符标记共同区分
- 三套低饱和主题色：赭石（默认，陶土红）、青墨、苔绿，可切换并在本地记忆
- 全天事件开关与独立日期选择，跨天和全天日程按首尾日期展示
- 顶部搜索浮层支持 300ms 防抖、按日期分组结果，点击结果跳转并打开详情
- 左侧小月历、分类计数、状态和日期范围组合筛选，支持一键清除
- 自动来源暂存区：GitHub / Gitee 最近 14 天仓库更新先生成待确认日程
- 暂存日程可调整、逐条插入、全部插入或丢弃，确认后才写入日历
- 自动插入时按今天 09:00–22:00 的空闲时段依次分配
- 加载骨架、局部加载、空数据、筛选无结果和错误重试状态
- 桌面三栏布局、平板收起侧栏、移动端今日议程与底部抽屉
- 键盘支持 `N` 新建、`T` 回到今天、`/` 搜索、`Esc` 关闭

## 界面方向

视觉基线见 [前端界面与样式设计要求](./docs/03-frontend-design-requirements.md)：暖米色背景、近黑墨色、陶土红强调色和衬线标题，整体参考 claude.com 的克制暖色风格，日历是页面主角。

- 主题色：赭石（默认）、青墨、苔绿，只改变界面强调色，不改变三类日程的固定分类色
- 主题选择保存在浏览器本地，刷新后继续生效
- 样式使用 Tailwind CSS 工具类，设计 Token 集中在 `frontend/src/styles/main.css`

- 桌面端（≥1280px）：小月历与筛选、中央日历、右侧今日议程/详情/表单
- 平板端（768–1279px）：收起侧栏，筛选使用抽屉，详情使用覆盖式面板
- 移动端（<768px）：默认今日议程，底部抽屉创建和编辑，悬浮新建按钮

## 快速开始

需要 Python 3.14、uv、Node.js 26、npm 12 和 make。

```bash
make setup    # 安装后端与前端依赖
make migrate  # 初始化数据库
```

然后分别启动两个终端：

```bash
# 终端一：后端
cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 终端二：前端
cd frontend && npm run dev
```

打开 <http://127.0.0.1:5173>。首次打开会进入「创建管理员账号」页面，设置用户名和密码后即可进入日历。Vite 会把 `/api` 代理到 `http://127.0.0.1:8000`，因此不需要额外配置 CORS。

- Swagger 文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/health>

默认数据库文件为仓库根目录下的 `data/schedules.db`。可通过环境变量 `DATABASE_URL` 覆盖，示例见 `backend/.env.example`。

## Docker 部署

需要 Docker Engine 和 Docker Compose 插件，适用于生产或完整试用环境。

```bash
cp .env.example .env
# 编辑 .env，至少填写 JWT_SECRET：
# openssl rand -base64 48
make docker-up
```

打开 <http://127.0.0.1:8080>（端口由 `.env` 中的 `APP_PORT` 控制）。首次访问仍会进入「创建管理员账号」页面，也可以在 `.env` 中配置 `AUTH_BOOTSTRAP_USERNAME` / `AUTH_BOOTSTRAP_PASSWORD` 自动创建。

部署结构：

```text
浏览器 :8080
  |
  v
web (Nginx)
  |-- /      -> Vue 静态文件 /usr/share/nginx/html
  |-- /api/  -> backend:8000
                  |
                  v
              SQLite /app/data/schedules.db
                  |
                  v
              Docker 卷 digital-clone_schedules-data
```

相关文件：

- `backend/Dockerfile`：uv 多阶段构建，启动时自动执行 `alembic upgrade head`，以非 root 用户运行
- `frontend/Dockerfile`：Node 构建静态文件，Nginx 提供服务
- `frontend/nginx.conf`：SPA 路由回退、静态资源缓存、`/api` 反向代理和基础安全响应头
- `docker-compose.yml`：编排、健康检查、日志轮转和 SQLite 持久化卷
- `scripts/backup-db.sh`：使用 SQLite 在线备份 API 生成一致性备份

常用命令：

| 命令 | 作用 |
| --- | --- |
| `make docker-up` | 构建并后台启动全部服务 |
| `make docker-down` | 停止并移除容器（保留数据库卷） |
| `make docker-logs` | 持续查看容器日志 |
| `make docker-ps` | 查看容器与健康状态 |
| `make backup` | 备份数据库到 `backups/schedules-<时间>.db` |

环境变量：

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `JWT_SECRET` | 是 | JWT 签名密钥，至少 32 字节；未设置时 Compose 会拒绝启动 |
| `APP_PORT` | 否 | 宿主机端口，默认 `8080` |
| `APP_TIMEZONE` | 否 | 应用时区，默认 `Asia/Shanghai`，影响自动日程时间窗口 |
| `AUTH_BOOTSTRAP_USERNAME` / `AUTH_BOOTSTRAP_PASSWORD` | 否 | 首次启动自动创建管理员 |
| `ALLOW_REGISTRATION` | 否 | 是否开放注册，默认 `true` |
| `GITHUB_*` / `GITEE_*` | 否 | 自动来源同步配置，含义与 `backend/.env.example` 一致 |

注意：

- `docker compose down` 不会删除数据库；`docker compose down -v` 会连同数据卷一起删除
- 后端容器启动时会自动迁移数据库，不需要手动执行 `make migrate`
- Nginx 默认只提供 HTTP，公网部署建议在宿主机、云负载均衡或前置代理上终止 HTTPS，再转发到 `APP_PORT`
- 恢复备份时先 `make docker-down`，再执行：

```bash
docker compose run --rm -v "$PWD/backups:/backup:ro" --entrypoint sh backend -c \
  'cp /backup/schedules-YYYYMMDD-HHMMSS.db /app/data/schedules.db'
make docker-up
```

## 登录与账号

- 首次部署在登录页创建管理员账号，之后可在登录页进入注册页创建更多账号
- 每个账号只能访问自己的日程和暂存区
- 密码使用 scrypt 加盐哈希保存，登录后签发 JWT
- 除 `/api/health` 和 `/api/auth/*` 外，所有 API 都要求 `Authorization: Bearer <token>`
- 退出登录只清理浏览器 Token；JWT 有效期默认 7 天
- 本地开发建议在 `backend/.env` 中固定 `JWT_SECRET`；Docker 部署必须在根目录 `.env` 中固定，否则进程重启后需要重新登录
- 也可以通过 `AUTH_BOOTSTRAP_USERNAME` / `AUTH_BOOTSTRAP_PASSWORD` 在首次启动时自动创建管理员账号
- 通过 `ALLOW_REGISTRATION=false` 可以关闭注册入口；关闭后注册接口返回 403

更完整的说明见 [登录与认证](./docs/05-authentication.md)。

## 自动来源与暂存区

自动来源采用“先暂存、再确认”的流程：

```text
GitHub / Gitee 最近 14 天仓库动态
  -> 按仓库汇总为待确认日程
  -> 分配今天 09:00–22:00 内的空闲时段
  -> 在暂存区调整 / 插入 / 全部插入 / 丢弃
  -> 确认后才写入 schedules
```

启用 GitHub / Gitee 同步：

```bash
cd backend
cp .env.example .env
# GitHub：填写 GITHUB_USERNAME；私有仓库再填写 GITHUB_TOKEN
# Gitee：填写 GITEE_USERNAME；私有仓库再填写 GITEE_ACCESS_TOKEN
uv run uvicorn app.main:app --reload --port 8000
```

配置后在前端侧栏或移动端今日议程打开「暂存区」，选择对应来源点击「同步」即可；两个来源默认每 6 小时也会各自自动同步一次，设为 `0` 可关闭自动同步。Token 需要具备读取仓库的权限。当天没有足够空闲时间时，暂存条目会保留，稍后可再次插入。

后台自动同步归属于第一个创建的管理员账号；其他账号手动点击同步时，暂存条目会写入自己的暂存区，不会看到彼此的日程。

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查（含数据库连通性与当前应用时区） |
| GET | `/api/auth/status` | 是否已创建管理员账号 |
| POST | `/api/auth/setup` | 首次创建管理员账号 |
| POST | `/api/auth/register` | 注册新账号（可通过环境变量关闭） |
| POST | `/api/auth/login` | 登录并获取 JWT |
| GET | `/api/auth/me` | 当前登录用户 |
| POST | `/api/auth/logout` | 退出登录（客户端清除 Token） |
| GET | `/api/schedules` | 列表查询，支持时间和条件筛选 |
| GET | `/api/schedules/{id}` | 日程详情 |
| POST | `/api/schedules` | 手动创建日程 |
| PATCH | `/api/schedules/{id}` | 局部更新日程 |
| DELETE | `/api/schedules/{id}` | 删除日程 |
| GET | `/api/staging` | 待确认暂存日程 |
| PATCH | `/api/staging/{id}` | 调整暂存日程 |
| POST | `/api/staging/{id}/approve` | 插入单条暂存日程 |
| POST | `/api/staging/{id}/reject` | 丢弃暂存日程 |
| POST | `/api/staging/approve-all` | 全部插入今天空闲时间 |
| GET | `/api/auto-sources/github/status` | GitHub 同步配置状态 |
| POST | `/api/auto-sources/github/sync` | 同步最近 14 天 GitHub 仓库更新 |
| GET | `/api/auto-sources/gitee/status` | Gitee 同步配置状态 |
| POST | `/api/auto-sources/gitee/sync` | 同步最近 14 天 Gitee 仓库更新 |

列表查询参数：

- `start`、`end`：ISO 8601 时间区间，半开区间 `[start, end)`
- `categories`：逗号分隔的分类，如 `work,outing`
- `statuses`：逗号分隔的状态，如 `pending,completed`
- `keyword`：同时匹配标题和描述，`%`、`_` 按普通字符处理

请求示例（先登录获取 Token）：

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"your-password"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

curl -X POST http://127.0.0.1:8000/api/schedules \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "项目周会",
    "category": "work",
    "description": "讨论本周进度",
    "start_at": "2026-11-05T14:00:00+08:00",
    "end_at": "2026-11-05T15:00:00+08:00",
    "all_day": false,
    "location": "线上"
  }'
```

## 数据与时间约定

- 分类固定为 `work`（工作）、`outing`（外出）、`private`（私人时间）
- 状态固定为 `pending`（待进行）、`completed`（已完成）、`cancelled`（已取消）
- 数据库保存 UTC 时间，接口返回带 `Z` 的 ISO 8601 UTC 字符串；未带时区的输入按 UTC 处理
- 普通日程要求 `end_at > start_at`
- 全天事件按日期保存：开始日 `00:00:00 UTC` 到结束日 `23:59:59.999999 UTC`，首尾日期都包含
- 删除前二次确认、错误提示和空状态由前端负责；后端统一返回 `{"detail": "..."}`

## 时区设置

- `APP_TIMEZONE` 决定后端自动来源排程的“今天 09:00–22:00”窗口，默认 `Asia/Shanghai`；本地开发写入 `backend/.env`，Docker 部署写入根目录 `.env`
- 启动时会校验时区名称，非法值（如 `Asia/Shanghia`）会直接导致进程启动失败；`/api/health` 返回当前生效的 `timezone`
- 界面时间仍按浏览器本地时区展示。建议让 `APP_TIMEZONE` 与日常使用的浏览器时区保持一致，避免自动插入的时段看起来偏移
- Compose 会把同一个值同时传给容器的 `APP_TIMEZONE` 和 `TZ`，容器日志时间与服务时区保持一致

## 测试与检查

首次使用先运行 `make setup`，之后：

| 命令 | 作用 |
| --- | --- |
| `make test` | 后端 pytest + 前端 Vitest |
| `make check` | Ruff、ESLint、Prettier、TypeScript 全部检查 |
| `make e2e` | Playwright 登录、桌面、移动端、暂存区和全天日程流程（自动启动前后端） |
| `make verify` | `check` + `test` + 前端生产构建，提交前执行 |
| `make build` | 只构建前端生产静态文件 |
| `make docker-up` | 构建并启动 Docker Compose 服务 |
| `make backup` | 在线备份 Docker 中的 SQLite 数据库 |

`make e2e` 首次运行会自动安装 Chromium。运行 `make help` 可查看全部命令。

数据库迁移：

```bash
make migrate
```

需要验证迁移可重复执行时：

```bash
cd backend
uv run alembic downgrade base
uv run alembic upgrade head
uv run alembic check
```

## 下一步

完成一周实际试用并收集反馈。公网部署时再按实际入口补充 HTTPS、访问保护和定期备份任务。
