# 个人日程系统开发手册

> 技术方向：Vue 3 前端 + Python（FastAPI）后端  
> 文档状态：初稿  
> 更新日期：2026-11-04

## 1. 项目目标

开发一个面向个人使用的日程管理系统。第一版优先完成日程管理、日历展示和提醒功能，再逐步增加重复日程、第三方日历同步和智能排期等能力。

推荐采用 **Vue 3 + FastAPI**，先实现可用的 MVP，再根据实际使用反馈持续迭代。

## 2. 第一版范围

开始开发前，先确定系统是个人使用还是多用户使用。这会直接影响登录、权限和数据隔离设计。

详细需求、业务规则与验收标准见 [步骤一：明确第一版范围](./01-product-scope.md)。

第一版建议包含：

- 创建、编辑、删除日程
- 日程字段：标题、描述、开始时间、结束时间、全天事件、地点、状态
- 日、周、月三种视图
- 按关键词、日期、标签筛选
- 开始前提醒，例如提前 10 分钟、1 小时
- 用户登录与数据隔离
- 简单的重复日程：每天、每周、每月
- 时区设置

建议把第三方日历同步、多人共享和 AI 自动排期放到后续版本。

## 3. 界面与交互原型

第一版前端界面、视觉样式与交互规范见 [前端界面与样式设计要求](./03-frontend-design-requirements.md)。

使用 Figma、Excalidraw 或纸笔画出主要页面：

- 登录/注册页
- 日历主页面
- 日程创建/编辑弹窗
- 日程详情侧边栏
- 设置页：时区、默认提醒时间
- 搜索和筛选区域

同时确定关键交互：

- 点击日期空白处创建日程
- 点击已有日程查看详情
- 拖动日程修改时间
- 调整日程后自动保存或点击保存
- 到期提醒如何展示

## 4. 技术栈

第一版已确认的具体技术选型和版本策略见 [步骤二：确认技术栈](./02-tech-stack.md)。

| 模块 | 推荐技术 |
| --- | --- |
| 前端框架 | Vue 3、Vite、TypeScript |
| 路由与状态 | Vue Router、Pinia |
| UI 组件 | Element Plus 或 Naive UI |
| 样式系统 | Tailwind CSS |
| 日历组件 | FullCalendar |
| 后端框架 | FastAPI |
| ORM | SQLAlchemy |
| 数据迁移 | Alembic |
| 数据库 | MVP 可选 SQLite，正式部署建议 PostgreSQL |
| 登录认证 | JWT + 密码哈希 |
| 定时提醒 | 单实例使用 APScheduler；多实例使用 Celery + Redis |
| 接口文档 | FastAPI Swagger |
| 测试 | pytest、Vitest、Playwright |
| 部署 | Docker Compose + Nginx + HTTPS |

## 5. 数据库设计

核心表可以先设计为：

```text
users
- id
- email
- password_hash
- timezone
- created_at

schedules
- id
- user_id
- title
- description
- start_at
- end_at
- all_day
- location
- status
- recurrence_rule
- remind_minutes
- created_at
- updated_at
```

如果希望一个日程关联多个标签，再增加：

```text
tags
schedule_tags
```

时间统一以 UTC 保存，前端根据用户时区展示。重复日程使用 iCalendar 的 RRULE 规则字符串，避免自行设计复杂格式。

## 6. 后端 API

先完成认证和日程 CRUD：

```text
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me

GET    /api/schedules?start=...&end=...
GET    /api/schedules/{id}
POST   /api/schedules
PATCH  /api/schedules/{id}
DELETE /api/schedules/{id}
GET    /api/schedules/search?keyword=...
```

后端重点处理：

- 所有查询必须按当前用户过滤
- 校验结束时间不能早于开始时间
- 处理全天事件和跨天事件
- 处理重复日程的展开
- 统一错误格式，例如 400、401、404、409
- 为开始时间和用户 ID 建立索引

## 7. Vue 前端

建议按页面和模块拆分：

```text
src/
  api/
  components/
    calendar/
    schedule/
  views/
    LoginView.vue
    CalendarView.vue
    SettingsView.vue
  stores/
    auth.ts
    schedule.ts
  router/
```

前端实现顺序：

1. 登录页和路由守卫
2. 日历月视图
3. 创建日程表单
4. 日程详情和编辑
5. 日/周视图
6. 搜索、筛选和标签
7. 加载状态、空状态和错误提示
8. 移动端适配

FullCalendar 负责日历展示和日期交互，Pinia 管理登录状态及日程缓存，所有数据通过 API 获取。

## 8. 提醒功能

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

至少覆盖以下场景：

- 注册、登录和未登录访问
- 日程创建、修改、删除
- 创建时间范围非法
- 跨天和全天日程
- 重复日程展开
- 不同时区展示
- 提醒是否只发送一次
- 用户不能访问其他用户的数据
- 前端创建和拖拽修改日程

后端使用 pytest，前端组件使用 Vitest，完整流程使用 Playwright。

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

## 12. 推荐实施顺序

整体按照以下顺序实施：

1. 确定需求和产品范围
2. 完成页面原型
3. 设计数据库
4. 实现后端 CRUD
5. 实现 Vue 日历界面
6. 接入登录认证
7. 实现提醒任务
8. 补充自动化测试
9. 部署并收集使用反馈
10. 规划后续增强功能

一个人开发可用 MVP，通常需要约 2～4 周。加入完整重复规则、日历同步和移动端推送后，开发周期会相应增加。
