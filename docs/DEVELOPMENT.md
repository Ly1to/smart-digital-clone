# 个人日程系统开发手册

> 技术方向：Vue 3 前端 + Python（FastAPI）后端  
> 文档状态：核心功能已实现，进入试用与 P1 补全阶段  
> 更新日期：2026-11-20

## 1. 项目目标

开发一个面向个人使用的多账号日程管理系统。当前已完成日程管理、日历展示、登录注册、自动来源暂存区和 Docker 部署；提醒、重复日程、标签与第三方日历同步仍待实现。

推荐采用 **Vue 3 + FastAPI**，先实现可用的 MVP，再根据实际使用反馈持续迭代。

## 2. 第一版范围

详细需求、业务规则与验收标准见 [步骤一：明确第一版范围](./01-product-scope.md)（基线已被实现超出，见文首现状表）。

| 能力 | 状态 |
| --- | --- |
| 创建、编辑、删除日程（标题、描述、开始/结束时间、全天、地点、状态） | 已实现 |
| 日、周、月三种视图 | 已实现 |
| 按关键词、日期、分类、状态筛选 | 已实现 |
| 多账号登录、注册与数据隔离 | 已实现 |
| GitHub / Gitee 自动来源与暂存区 | 已实现 |
| 对话助手（DeepSeek，只读查询日程） | Phase 1 已实现 |
| QQ 机器人接入与账号绑定 | Phase 2 待实现 |
| 三套主题色与响应式布局 | 已实现 |
| 开始前提醒 | 未实现（P1） |
| 每天、每周、每月重复日程 | 未实现（P1） |
| 标签 | 未实现（P1） |
| ICS 导入导出 | 未实现（P1） |
| 第三方日历双向同步、AI 自动排期 | 未实现（P2） |

自动来源、暂存区和时区窗口的实现细节见 [自动日程来源与暂存区](./04-auto-schedule-sources.md)，认证细节见 [登录与认证](./05-authentication.md)。

## 3. 界面与交互原型

第一版前端界面、视觉样式与交互规范见 [前端界面与样式设计要求](./03-frontend-design-requirements.md)。

使用 Figma、Excalidraw 或纸笔画出主要页面：

- 登录/注册页
- 日历主页面
- 日程创建/编辑面板（移动端为底部抽屉）
- 日程详情侧边栏
- 设置区域：主题、账号与退出（时区选择、默认提醒尚未实现）
- 搜索和筛选区域

同时确定关键交互：

- 点击日期空白处创建日程
- 点击已有日程查看详情
- 拖动日程修改时间
- 调整日程后自动保存或点击保存
- 到期提醒如何展示

## 4. 技术栈

第一版已确认的具体技术选型和版本策略见 [步骤二：确认技术栈](./02-tech-stack.md)。

| 模块 | 当前使用 |
| --- | --- |
| 前端框架 | Vue 3、Vite、TypeScript |
| 路由与状态 | Vue Router、Pinia |
| UI 组件 | Element Plus |
| 样式系统 | Tailwind CSS 4 |
| 日历组件 | FullCalendar |
| 后端框架 | FastAPI |
| ORM | SQLAlchemy |
| 数据迁移 | Alembic |
| 数据库 | SQLite（单机部署，后续可迁 PostgreSQL） |
| 登录认证 | JWT + scrypt 密码哈希 |
| 定时任务 | 自动来源同步使用 asyncio 循环；提醒未实现 |
| 接口文档 | FastAPI Swagger |
| 测试 | pytest、Vitest、Playwright |
| 部署 | Docker Compose + Nginx（HTTPS 由前置代理终止） |

## 5. 数据库设计

当前结构由 Alembic 迁移 `0001`–`0004` 维护，完整字段见 [步骤二：确认技术栈](./02-tech-stack.md#42-sqlalchemy--alembic)，概要如下：

```text
users
- id、username（唯一）、password_hash
- created_at、updated_at

schedules
- id、user_id（外键）
- title、category、description
- start_at、end_at、all_day、location、status
- source、source_ref、source_url
- created_at、updated_at

staged_schedules
- id、user_id（外键）
- source、source_ref、source_url、source_meta
- 日程字段与建议时间
- status（pending / approved / rejected）
- schedule_id、approved_at
- created_at、updated_at
```

时间统一以 UTC 保存，前端按浏览器本地时区展示；后端自动排程窗口由 `APP_TIMEZONE` 决定。

tags、schedule_tags、recurrence_rule、remind_minutes 和 users.timezone 均未建立，避免为未实现功能预留含义不清的列；接入时通过新的 Alembic 迁移添加。

## 6. 后端 API

当前路由（完整列表与示例见 [README](../README.md#api)）：

```text
GET    /api/health
GET    /api/bot/status
POST   /api/bot/chat

GET    /api/auth/status
POST   /api/auth/setup
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me
POST   /api/auth/logout

GET    /api/schedules?start=...&end=...&categories=...&statuses=...&keyword=...
GET    /api/schedules/{id}
POST   /api/schedules
PATCH  /api/schedules/{id}
DELETE /api/schedules/{id}

GET    /api/staging
PATCH  /api/staging/{id}
POST   /api/staging/{id}/approve
POST   /api/staging/{id}/reject
POST   /api/staging/approve-all

GET/POST /api/auto-sources/{github,gitee}/{status,sync}
```

后端重点处理：

- 所有查询和写入必须按当前用户过滤，其他账号的 ID 返回 404
- 校验结束时间不能早于开始时间
- 处理全天事件和跨天事件
- 统一错误格式，例如 400、401、404、409
- 为开始时间、结束时间和用户 ID 建立索引
- `/api/health` 额外返回当前生效的 `timezone`，便于部署后核对配置

## 7. Vue 前端

当前目录结构：

```text
src/
  api/            # axios 封装：auth、schedules、staging、auto-sources
  components/
    agenda/ calendar/ common/ filters/ layout/
    schedule/ search/ settings/ staging/
  composables/    # useMediaQuery、useTheme
  constants/      # 分类/状态颜色与工具类
  router/         # /login、/register、/ 三个路由与登录守卫
  stores/         # auth.ts、schedule.ts
  styles/         # Tailwind @theme 设计令牌与第三方组件覆盖
  types/ utils/ views/
  views/
    LoginView.vue
    RegisterView.vue
    CalendarView.vue
```

实现状态：

1. 登录页和路由守卫 —— 已完成
2. 日历月视图 —— 已完成
3. 创建日程表单 —— 已完成
4. 日程详情和编辑 —— 已完成
5. 日/周视图 —— 已完成
6. 搜索与筛选 —— 已完成；标签未实现
7. 加载状态、空状态和错误提示 —— 已完成
8. 移动端适配 —— 已完成

FullCalendar 负责日历展示和日期交互，Pinia 管理登录状态及日程数据，所有数据通过 API 获取。

## 8. 提醒功能（未实现）

提醒属于 P1，当前没有提醒表、后台任务或通知入口。下面是后续设计基线：

先在数据库中保存提醒时间，然后由后端任务定期检查：

```text
reminder_at <= 当前时间
AND status = pending
```

提醒发送成功后更新状态。实现时需要注意：

- 任务不能只存在内存中，服务重启后要能继续执行
- 定时任务需要幂等，避免同一提醒发送多次

第一版可以使用站内提醒或邮件提醒，后续再接 Web Push、微信通知或手机推送。

## 9. 测试

当前已覆盖：

- 注册、登录、未登录访问和重复用户名
- 日程创建、修改、删除
- 创建时间范围非法
- 跨天和全天日程
- 分类、状态、关键词和日期范围筛选
- 用户不能访问其他用户的数据
- `/api/health` 与 `APP_TIMEZONE` 时区校验、自动排程日期边界
- 前端表单、日期工具、主题、状态管理与登录注册流程

待补充（依赖未实现功能）：

- 重复日程展开
- 提醒是否只发送一次
- 拖拽修改日程

后端使用 pytest，前端组件使用 Vitest，完整流程使用 Playwright。`make verify` 依次执行 Ruff、ESLint、Prettier、TypeScript、后端/前端测试和生产构建。

## 10. 部署与运维

当前部署结构：

```text
浏览器
  |
Nginx（frontend 容器）
  |-- /      -> Vue 静态文件
  |-- /api   -> FastAPI（backend 容器）
                  |
                SQLite
                  |
              Docker 命名卷
```

部署已落地：

- Docker Compose 一键启动：`make docker-up`，配置文件为根目录 `docker-compose.yml`
- Alembic 数据库迁移：`backend/docker-entrypoint.sh` 在容器启动时执行 `alembic upgrade head`
- 环境变量管理：复制根目录 `.env.example` 为 `.env`，至少设置 `JWT_SECRET`
- 时区：`APP_TIMEZONE` 控制自动排程窗口，默认 `Asia/Shanghai`；Compose 同时传给容器 `TZ`，`/api/health` 可直接核对
- 健康检查：后端 `/api/health`，Nginx `/healthz`，Compose 已配置 healthcheck
- 日志记录：Uvicorn 输出到容器日志，Compose 限制单文件 10 MB、保留 3 个文件
- 数据库备份：`make backup`，使用 SQLite 在线备份 API 写入 `backups/`
- HTTPS：默认由宿主机、云负载均衡或前置代理终止，再转发到 `APP_PORT`；如需在 Nginx 内终止，可挂载证书后扩展 `frontend/nginx.conf`

完整命令、环境变量和恢复步骤见 [README 的 Docker 部署章节](../README.md#docker-部署)。

## 11. 后续增强功能

MVP 稳定后继续增加：

- ICS 导入导出
- Google/Outlook 日历双向同步
- 重复日程例外处理
- 任务清单和日程整合
- 拖动调整日程
- 日程冲突检测
- 多设备实时同步
- 分享只读日程
- AI 自动安排空余时间
- 桌面端或 PWA 安装
- QQ 机器人写操作与确认流程

## 12. 推荐实施顺序

整体按照以下顺序实施，括号内为当前状态：

1. 确定需求和产品范围（已完成）
2. 完成页面原型（已完成）
3. 设计数据库（已完成，迁移 0001–0004）
4. 实现后端 CRUD（已完成）
5. 实现 Vue 日历界面（已完成）
6. 接入登录认证（已完成）
7. 实现提醒任务（未开始，P1）
8. 补充自动化测试（持续进行）
9. 部署并收集使用反馈（部署已完成，待一周试用）
10. 规划后续增强功能（待办）

一个人开发可用 MVP，通常需要约 2～4 周。加入完整重复规则、日历同步和移动端推送后，开发周期会相应增加。
