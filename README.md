# 个人日程系统

单用户、免登录的个人日程 MVP。第一版完成工作、外出、私人时间三类日程的手动创建、查看、编辑、删除、搜索和筛选。

当前进度：**后端、数据库与前端已完成**，待做部署与试用反馈。

## 目录

```text
digital-clone/
  Makefile            # 常用开发、测试、构建命令
  backend/
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
    src/
      api/            # Axios 封装与日程接口
      components/     # 日历、筛选、日程表单与详情
      constants/      # 分类/状态标签与颜色
      stores/         # Pinia 日程与筛选状态
      types/          # TypeScript 类型
      utils/          # 日期与表单转换
      views/          # 日历主页
    tests/            # Vitest 单元与组件测试
    e2e/              # Playwright 主流程测试
  data/               # SQLite 数据文件（本地生成）
  docs/               # 产品范围、技术栈、开发手册
```

## 功能

- 桌面端默认周视图，支持日、周、月三种日历视图和前后切换
- 点击空白日期或「新建日程」手动创建日程，自动带入对应日期和时间
- 点击日程查看详情，支持编辑、删除确认和未保存修改提醒
- 工作、外出、私人时间三类固定分类，颜色、中文文字和一字符标记共同区分
- 全天事件开关与独立日期选择，跨天和全天日程按首尾日期展示
- 顶部搜索浮层支持 300ms 防抖、按日期分组结果，点击结果跳转并打开详情
- 左侧小月历、分类计数、状态和日期范围组合筛选，支持一键清除
- 加载骨架、局部加载、空数据、筛选无结果和错误重试状态
- 桌面三栏布局、平板收起侧栏、移动端今日议程与底部抽屉
- 键盘支持 `N` 新建、`T` 回到今天、`/` 搜索、`Esc` 关闭

## 界面方向

视觉基线见 [前端界面与样式设计要求](./docs/03-frontend-design-requirements.md)：暖纸背景、墨色文字、低饱和三分类色，日历是页面主角。

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

打开 <http://127.0.0.1:5173>。Vite 会把 `/api` 代理到 `http://127.0.0.1:8000`，因此不需要额外配置 CORS。

- Swagger 文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/health>

默认数据库文件为仓库根目录下的 `data/schedules.db`。可通过环境变量 `DATABASE_URL` 覆盖，示例见 `backend/.env.example`。

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查（含数据库连通性） |
| GET | `/api/schedules` | 列表查询，支持时间和条件筛选 |
| GET | `/api/schedules/{id}` | 日程详情 |
| POST | `/api/schedules` | 手动创建日程 |
| PATCH | `/api/schedules/{id}` | 局部更新日程 |
| DELETE | `/api/schedules/{id}` | 删除日程 |

列表查询参数：

- `start`、`end`：ISO 8601 时间区间，半开区间 `[start, end)`
- `categories`：逗号分隔的分类，如 `work,outing`
- `statuses`：逗号分隔的状态，如 `pending,completed`
- `keyword`：同时匹配标题和描述，`%`、`_` 按普通字符处理

请求示例：

```bash
curl -X POST http://127.0.0.1:8000/api/schedules \
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

## 测试与检查

首次使用先运行 `make setup`，之后：

| 命令 | 作用 |
| --- | --- |
| `make test` | 后端 pytest + 前端 Vitest |
| `make check` | Ruff、ESLint、Prettier、TypeScript 全部检查 |
| `make e2e` | Playwright 桌面端、移动端和全天日程流程（自动启动前后端） |
| `make verify` | `check` + `test` + 前端生产构建，提交前执行 |
| `make build` | 只构建前端生产静态文件 |

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

按 `docs/02-tech-stack.md` 的部署方案补充 Docker Compose + Nginx，把静态前端、FastAPI 和 SQLite 持久化卷串起来，并完成一周试用验证。
