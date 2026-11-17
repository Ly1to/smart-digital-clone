# 文档导航

> 项目：个人日程系统  
> 更新日期：2026-11-20

本目录分为三类文档：

1. **设计基线**：`01`–`03`，记录最初的产品范围、技术选型和视觉规范，保留历史决策。
2. **专题设计**：`04`–`06`，自动来源、认证、对话机器人与 QQ 接入。
3. **使用指南**：`API.md`、`ARCHITECTURE.md`、`DEPLOYMENT.md`、`TESTING.md`、`ROADMAP.md`，描述当前实现与运维方式。

## 推荐阅读顺序

| 目的 | 阅读顺序 |
| --- | --- |
| 第一次了解项目 | [README](../README.md) → [ARCHITECTURE](./ARCHITECTURE.md) → [ROADMAP](./ROADMAP.md) |
| 本地开发 | [README 快速开始](../README.md#快速开始) → [DEVELOPMENT](./DEVELOPMENT.md) → [TESTING](./TESTING.md) |
| 调用接口 | [API](./API.md) → [认证专题](./05-authentication.md) |
| 部署上线 | [DEPLOYMENT](./DEPLOYMENT.md) → [自动来源](./04-auto-schedule-sources.md) → [QQ 接入](./06-qq-bot.md) |
| 排查问题 | [DEPLOYMENT 排查表](./DEPLOYMENT.md#11-常见问题排查) → [TESTING](./TESTING.md) |
| 产品/视觉回顾 | [01 产品范围](./01-product-scope.md) → [03 前端规范](./03-frontend-design-requirements.md) |

## 当前实现状态

| 能力 | 状态 | 说明 |
| --- | --- | --- |
| 日程 CRUD、日/周/月视图、搜索筛选 | 已实现 | 三类固定分类，多账号隔离 |
| 登录、注册、JWT、账号隔离 | 已实现 | 见 [05-authentication](./05-authentication.md) |
| GitHub / Gitee 自动来源与暂存区 | 已实现 | 见 [04-auto-schedule-sources](./04-auto-schedule-sources.md) |
| 三套主题与 Tailwind 视觉体系 | 已实现 | 默认赭石（陶土红） |
| 时区配置 `APP_TIMEZONE` | 已实现 | 影响自动排程窗口 |
| 对话助手 Phase 1（DeepSeek + 只读工具） | 已实现 | 见 [06-qq-bot](./06-qq-bot.md) |
| QQ 接入与账号绑定（Phase 2） | 已实现 | OneBot v11 + NapCat |
| 提醒、重复日程、标签、ICS | 未实现 | P1 |
| QQ 写操作、频率限制、绑定 UI | 未实现 | Phase 3–4 |

## 文档约定

- **基线文档**（01–03）描述最初决策，与当前实现不一致处会在文首标注“实现现状”。
- **环境变量**统一用大写，示例见项目根目录 `.env.example` 与 `backend/.env.example`。
- **时间**统一写 UTC ISO 8601；涉及用户时区时注明 `APP_TIMEZONE` 或“浏览器本地时区”。
- **状态标记**：已实现 / Phase N 已实现 / 待实现 / 暂不规划。
- 新增功能时，至少同步：`README` 功能列表、[API](./API.md)、[ARCHITECTURE](./ARCHITECTURE.md)、[ROADMAP](./ROADMAP.md)，涉及部署的再更新 [DEPLOYMENT](./DEPLOYMENT.md)。
