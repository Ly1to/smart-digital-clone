# 自动日程来源与暂存区

> 所属项目：个人日程系统  
> 范围说明：这是 MVP 之外的增量能力，默认关闭，配置 GitHub 或 Gitee 后启用。  
> 更新日期：2026-11-08

## 1. 设计目标

自动来源不应该直接污染日历。所有外部数据先进入类似 git 暂存区的「待确认日程」，用户确认后才写入正式日程。

```text
外部来源 -> 暂存区（pending） -> 插入日程（approved）
                            \-> 丢弃（rejected）
```

## 2. 数据模型

### staged_schedules

- `source`：来源，当前为 `github` 或 `gitee`
- `source_ref`：来源内唯一标识，用于幂等同步
- `source_url`、`source_meta`：来源链接和原始摘要
- 日程字段：标题、分类、描述、建议开始/结束时间、全天、地点
- `status`：`pending` / `approved` / `rejected`
- `schedule_id`：插入后关联的正式日程
- `approved_at`、`created_at`、`updated_at`

### schedules 新增字段

- `source`：`manual`、`github` 或 `gitee`
- `source_ref`、`source_url`：自动来源追踪信息

## 3. GitHub 与 Gitee 同步

配置：

```env
# GitHub
GITHUB_USERNAME=your-github-name
GITHUB_TOKEN=github_pat_xxx   # 私有仓库才需要
GITHUB_LOOKBACK_DAYS=14
GITHUB_AUTO_SYNC_MINUTES=360  # 0 表示只手动同步

# Gitee
GITEE_USERNAME=your-gitee-name
GITEE_ACCESS_TOKEN=your-token # 私有仓库才需要
GITEE_LOOKBACK_DAYS=14
GITEE_AUTO_SYNC_MINUTES=360
```

配置后后端会分别每 6 小时同步一次，也可以在前端暂存区手动点击对应来源的「同步」。

同步流程：

1. 读取用户最近 14 天的 GitHub / Gitee 事件；配置 Token 后使用认证账号能力。
2. 按仓库聚合 Push、Pull Request、Release、Tag 事件。
3. 每个仓库生成一条工作类暂存日程，描述中包含提交数量、最近提交、PR 和发布。
4. 同一仓库存在待确认条目时更新该条，不重复堆积。
5. 已插入或已丢弃的同一来源版本不会再次生成。

Gitee 使用 v5 OpenAPI：

- 公开动态：`GET /users/{username}/events/public`
- Token 动态：`GET /users/{username}/events?access_token=...`
- 没有动态时 Gitee 可能返回 404，同步会按空结果处理

## 4. 空闲时间分配

- 窗口：今天 09:00–22:00（可配置）
- 默认时长：30 分钟（可配置）
- 忙碌来源：今天的正式日程 + 其他待确认暂存的建议时间
- 算法：按时间排序忙碌区间，寻找第一个可放下时长的空档，5 分钟粒度
- 插入时如果原建议时间已被占用，会重新寻找今天下一个空档
- 没有空档时保留暂存条目，不强行创建冲突日程

配置项：

```env
AUTO_SCHEDULE_DURATION_MINUTES=30
AUTO_SCHEDULE_DAY_START_HOUR=9
AUTO_SCHEDULE_DAY_END_HOUR=22
```

## 5. API

```text
GET    /api/staging
PATCH  /api/staging/{id}
POST   /api/staging/{id}/approve
POST   /api/staging/{id}/reject
POST   /api/staging/approve-all

GET    /api/auto-sources/github/status
POST   /api/auto-sources/github/sync
GET    /api/auto-sources/gitee/status
POST   /api/auto-sources/gitee/sync
```

## 6. 前端入口

- 桌面/平板：顶部「暂存」按钮
- 移动端：今日议程标题旁的「暂存」按钮
- 抽屉中分别显示 GitHub、Gitee 同步状态、建议时间、来源链接和操作按钮
- 插入成功后刷新当前日历和今日议程

## 7. 当前限制

- 一次 GitHub 同步按仓库汇总，不按单次 commit 建日程
- 不支持双向回写 GitHub
- 自动同步依赖后端进程持续运行；进程停止期间不会轮询
- 时间窗口按后端本地时区计算，部署时建议设置正确的 `TZ`


## 多账号行为

后台自动同步任务归属于第一个创建的管理员账号。其他账号登录后手动点击同步时，会使用相同的全局来源配置，但暂存条目和生成的日程只属于当前账号。
