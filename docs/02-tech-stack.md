# 步骤二：确认技术栈

> 所属项目：个人日程系统  
> 上位文档：[开发手册](./DEVELOPMENT.md)  
> 范围依据：[步骤一：明确第一版范围](./01-product-scope.md)  
> 文档状态：第一版技术栈已确认  
> 更新日期：2026-11-04

## 1. 决策原则

第一版技术栈以 `01-product-scope.md` 已确认的范围为准。开发手册提供总体技术方向，但当两份文档存在差异时，第一版执行以下已收敛决策：

- 单用户、免登录
- 只支持手动创建、编辑和删除日程
- 日程固定分为工作、外出、私人时间三类
- 不接入第三方应用、消息或外部数据源
- 提醒、重复日程和标签不阻塞 MVP

技术选择遵循以下原则：

- 使用成熟且常见的 Vue 和 Python 生态
- 优先减少基础组件数量，避免为尚未实现的 P1 能力提前引入基础设施
- 保持前后端职责清晰，日程校验不能只依赖前端
- 数据库和接口设计保留未来迁移空间，但不为多用户提前增加复杂度
- 所有依赖通过锁文件固定版本，保证开发、测试和部署环境一致

## 2. 最终技术栈

| 层级 | 已确认技术 | 第一版用途 |
| --- | --- | --- |
| 运行环境 | Python 3.14.x | FastAPI 后端运行环境 |
| Python 包管理 | uv | 创建虚拟环境、安装依赖并锁定版本 |
| 前端运行环境 | Node.js 26.x、npm 12.x | Vue 构建、测试和依赖管理 |
| 前端框架 | Vue 3 + TypeScript | 单页应用和类型安全开发 |
| 构建工具 | Vite | 本地开发服务器和生产构建 |
| 路由 | Vue Router 4 | 管理应用页面路由 |
| 状态管理 | Pinia | 日程列表、筛选条件等共享状态 |
| UI 组件 | Element Plus | 表单、按钮、弹窗、日期选择和消息提示 |
| 日历组件 | FullCalendar Vue 3 | 日、周、月视图及日程展示 |
| 日期处理 | Day.js | 本地时间、UTC 转换和日期格式化 |
| HTTP 客户端 | Axios | 前端调用 FastAPI 接口 |
| 后端框架 | FastAPI | REST API、参数校验和 OpenAPI 文档 |
| 数据校验 | Pydantic 2 | 请求、响应和配置模型 |
| ORM | SQLAlchemy 2 | 日程持久化和查询 |
| 数据迁移 | Alembic | 数据库表结构版本管理 |
| 数据库 | SQLite | 单用户 MVP 的本地持久化 |
| ASGI 服务 | Uvicorn | 本地开发和单实例服务运行 |
| 后端测试 | pytest + pytest-asyncio + HTTPX | API、业务规则和异步请求测试 |
| 前端测试 | Vitest + Vue Test Utils | 组件、表单和状态测试 |
| 端到端测试 | Playwright | 浏览器中的创建、编辑和筛选流程 |
| Python 质量工具 | Ruff | 代码检查、导入排序和格式化 |
| 前端质量工具 | ESLint + Prettier | 代码检查与格式统一 |
| 部署 | Docker Compose + Nginx | 静态前端、API 代理和数据持久化 |

版本说明：运行时使用当前开发环境已安装的 Python 3.14 和 Node.js 26。具体依赖版本在项目初始化时由 `uv.lock` 和 `package-lock.json` 固定，不在文档中手工维护补丁版本号。

## 3. 前端技术决策

### 3.1 Vue 3 + TypeScript

前端使用 Vue 3 Composition API 和单文件组件，并启用 TypeScript 严格模式。TypeScript 用于日程实体、分类枚举、筛选条件和 API 响应类型，避免标题、时间或分类字段在组件之间出现拼写错误。

建议启用：

- `<script setup lang="ts">`
- `strict: true`
- 日期字符串和日期对象使用明确类型
- 分类使用联合类型，例如 `"work" | "outing" | "private"`

### 3.2 Vite

Vite 同时负责：

- 本地前端开发服务器
- Vue 单文件组件编译
- 生产静态资源构建
- 开发环境 `/api` 代理到 FastAPI

开发环境中，Vite 将 `/api` 请求代理到后端的 `http://127.0.0.1:8000`。生产环境中，Nginx 使用同源方式将 `/api` 转发给 FastAPI，因此不需要长期开放宽松的 CORS 配置。

### 3.3 Vue Router 和 Pinia

MVP 虽然以日历主页为核心，但仍保留 Vue Router 和 Pinia：

- Vue Router 管理日历主页及未来的独立设置页
- Pinia 管理当前日期范围、当前视图、分类筛选和日程数据
- 不创建 `auth` store，因为第一版没有登录状态

日程详情、创建和编辑优先使用弹窗或侧边抽屉，不额外拆成独立路由。这样既保留后续页面扩展能力，也不让简单交互承担多余的路由复杂度。

### 3.4 Element Plus

Element Plus 用于：

- 日程创建和编辑表单
- 日期时间选择
- 分类选择
- 删除确认
- 错误和信息提示
- 加载状态和空状态

分类颜色同时通过日期区块样式和文字标识呈现，不能只依赖颜色区分，以免展示不清晰或无法识别。

### 3.5 FullCalendar

使用 FullCalendar 的开源 Vue 3 组件和以下插件：

- `@fullcalendar/vue3`
- `@fullcalendar/daygrid`
- `@fullcalendar/timegrid`
- `@fullcalendar/interaction`
- 中文语言包

MVP 使用月、周、日视图。拖拽修改时间属于 P1，因此第一版只保留事件点击和日期点击交互。

### 3.6 Day.js 和 Axios

- Day.js 负责前端日期格式化、日期区间计算和本地时区展示
- Axios 负责统一请求地址、超时、错误转换和 API 类型封装
- Pinia 不直接拼接请求，所有网络访问集中在 `src/api/` 目录

## 4. 后端技术决策

### 4.1 FastAPI + Pydantic

FastAPI 提供 REST API 和自动生成的 OpenAPI 文档。Pydantic 模型负责：

- 请求字段类型转换
- 标题和分类必填校验
- 日期时间格式校验
- 响应数据序列化
- 统一错误响应结构

后端必须再次校验结束时间、分类和标题，不能只相信 Element Plus 的表单校验结果。

### 4.2 SQLAlchemy + Alembic

使用 SQLAlchemy 2 的声明式模型管理日程数据，使用 Alembic 管理所有表结构变更。

第一版不需要 `users`、`roles` 或 `schedule_users` 表。日程表至少包含：

```text
schedules
- id
- title
- category
- description
- start_at
- end_at
- all_day
- location
- status
- created_at
- updated_at
```

约束建议：

- `title` 不能为空
- `category` 只允许 `work`、`outing`、`private`
- `end_at` 必须晚于 `start_at`
- `start_at` 和 `category` 建立索引，支持日历区间查询和分类筛选
- 时间字段以 UTC 存储

提醒、重复规则和标签字段不进入 MVP 第一次迁移。后续加入时通过新的 Alembic 迁移完成，避免为未实现功能预留含义不清的列。

### 4.3 SQLite

MVP 是单用户、低并发应用，SQLite 足以支撑日程 CRUD、日期范围查询和分类筛选：

- 数据库文件放在持久化数据目录中
- 所有查询使用 SQLAlchemy，不直接依赖 SQLite 专有接口
- 使用 Alembic 管理结构，便于以后迁移到 PostgreSQL
- 部署时给数据库文件配置持久化卷并定期备份

如果后续出现多实例部署、高频并发写入或跨设备同步需求，再评估迁移 PostgreSQL。

### 4.4 Uvicorn

本地开发通过 Uvicorn 启动 FastAPI。单用户 MVP 使用单进程部署，不引入 Gunicorn 多进程、Celery 或 Redis。

## 5. API 技术约定

第一版接口不包含认证接口，建议使用：

```text
GET    /api/health

GET    /api/schedules?start=...&end=...&categories=work,outing
GET    /api/schedules/{id}
POST   /api/schedules
PATCH  /api/schedules/{id}
DELETE /api/schedules/{id}
```

接口约定：

- 使用 JSON 传输数据
- 时间使用 ISO 8601 UTC 字符串
- 分类使用固定英文值，前端展示中文标签
- 日期范围查询按 `start` 和 `end` 参数过滤
- 标题和描述搜索使用 `keyword` 参数
- 使用统一错误结构，例如 `{"detail": "结束时间必须晚于开始时间"}`
- 不设计 `login`、`register`、`logout`、`refresh_token` 等接口

## 6. 推荐的 Mono-repo 结构

```text
digital-clone/
  backend/
    pyproject.toml
    uv.lock
    alembic.ini
    app/
      main.py
      api/
      core/
      db/
      models/
      schemas/
      services/
    tests/
  frontend/
    package.json
    package-lock.json
    src/
      api/
      components/
      stores/
      types/
      views/
      router/
    tests/
  docs/
  data/
  Dockerfile
  docker-compose.yml
```

目录边界：

- `frontend/src/api/` 只负责 HTTP 请求和类型转换
- `frontend/src/stores/` 负责页面共享状态
- `backend/app/api/` 负责路由
- `backend/app/services/` 负责业务规则
- `backend/app/models/` 和 `backend/app/schemas/` 分别负责持久化模型和接口模型

## 7. 测试与质量策略

### 7.1 后端

使用 pytest 覆盖：

- 创建合法日程
- 标题为空
- 分类缺失或非法
- 结束时间早于开始时间
- 日期范围查询
- 分类组合筛选
- 关键词查询
- 编辑和删除
- 全天、跨天和本地时间边界

### 7.2 前端

使用 Vitest 和 Vue Test Utils 覆盖：

- 创建表单必填校验
- 三种分类选项和颜色标识
- 编辑表单回填
- 分类筛选状态
- API 错误展示

使用 Playwright 覆盖一条完整的主要流程：

```text
打开日历
  -> 手动创建私人时间日程
  -> 在日历中确认出现
  -> 编辑日程
  -> 按分类筛选
  -> 删除日程并确认消失
```

### 7.3 静态检查

- 后端：Ruff check、Ruff format、pytest
- 前端：ESLint、Prettier check、TypeScript type-check、Vitest
- 端到端：Playwright

## 8. 部署技术方案

第一版采用单机部署：

```text
浏览器
  |
Nginx
  |-- /      -> Vue 静态文件
  |-- /api   -> FastAPI
                  |
                SQLite
                  |
              持久化卷
```

部署要求：

- Docker Compose 启动前端静态服务和后端服务
- SQLite 数据目录挂载持久化卷
- Alembic 在容器启动或发布步骤中执行迁移
- `/api/health` 用作健康检查
- 记录应用日志和异常信息
- 定期备份 SQLite 文件
- 如需公网访问，在 Nginx、VPN 或 Tunnel 层增加访问保护

MVP 不需要 HTTPS 证书配置以外的应用认证。公网部署的访问保护由部署层提供，不属于产品功能。

## 9. 第一版明确不引入的技术

以下技术在 MVP 中不安装、不配置，也不提前建立目录或空服务：

| 技术 | 不引入原因 |
| --- | --- |
| JWT、OAuth、密码哈希 | 第一版单用户免登录 |
| Redis | 没有缓存、消息队列或实时协作需求 |
| Celery | MVP 没有提醒和后台任务 |
| APScheduler | 提醒属于 P1 |
| PostgreSQL | SQLite 足以支撑单用户 MVP |
| WebSocket | 没有实时多人协作需求 |
| GitHub API、音乐平台 API | 明确不做第三方数据接入 |
| 第三方消息 SDK | 明确不做消息导入 |
| Pinia auth store | 没有认证状态 |
| FullCalendar Premium | MVP 只需要开源日、周、月视图 |

## 10. 后续能力的技术扩展边界

- 提醒：后续增加提醒表和 APScheduler；如果部署为多个实例，再评估 Redis 和任务队列
- 重复日程：后续使用 RRULE 库或在服务层展开实例，并把重复相关字段通过 Alembic 加入
- PostgreSQL：通过 SQLAlchemy 和 Alembic 迁移，不在业务代码中依赖 SQLite 专有语法
- ICS：后续增加独立的导入导出服务，不在 MVP API 中预留空接口
- 第三方数据接入：必须单独设计授权、同步频率、数据来源和失败重试，不与手动创建接口混在一起
- 多用户：当前不属于规划范围；如未来引入，需要重新设计方案，不在 MVP 中做无效兼容

## 11. 技术栈确认结论

第一版最终采用：

```text
Vue 3 + TypeScript + Vite + Vue Router + Pinia
Element Plus + FullCalendar + Day.js + Axios
Python 3.14 + FastAPI + Pydantic + SQLAlchemy + Alembic
SQLite + Uvicorn
pytest + Vitest + Playwright
uv + npm + Docker Compose + Nginx
```

该方案只覆盖单用户、免登录、三类日程的手动创建、查看、编辑、删除、搜索和筛选，不包含认证、第三方接入、提醒任务、重复日程或多人协作基础设施。
