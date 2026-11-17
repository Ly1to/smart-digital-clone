# 测试与质量

> 更新日期：2026-11-20

## 1. 一键命令

| 命令 | 内容 |
| --- | --- |
| `make test` | 后端 pytest + 前端 Vitest |
| `make test-backend` | 仅后端 pytest |
| `make test-frontend` | 仅前端 Vitest |
| `make check` | Ruff、ESLint、Prettier、TypeScript |
| `make build` | 前端生产构建（含 typecheck） |
| `make e2e` | Playwright 端到端（自动启动前后端） |
| `make verify` | `check` + `test` + `build`，提交前执行 |

## 2. 当前测试规模

| 层 | 数量 | 位置 |
| --- | --- | --- |
| 后端 pytest | 91 | `backend/tests/` |
| 前端 Vitest | 70（9 个文件） | `frontend/tests/` |
| Playwright | 8 通过 / 8 跳过 | `frontend/e2e/` |

Playwright 配置了两个项目：`chromium`（桌面）与 `mobile-chromium`。多数用例通过 `test.skip` 限定只在对应项目中运行，因此每次会有一半被跳过。

## 3. 后端测试

### 3.1 文件地图

| 文件 | 覆盖内容 |
| --- | --- |
| `conftest.py` | 内存 SQLite、`get_db` 覆盖、登录用户、匿名客户端 |
| `test_health.py` | 健康检查、根路由、时区字段 |
| `test_auth.py` | 初始化、注册、登录、数据隔离、关闭注册 |
| `test_schedules.py` | CRUD、筛选、校验、全天/跨天 |
| `test_scheduling.py` | 空闲时段查找算法 |
| `test_staging.py` | 暂存调整、插入、全部插入、丢弃、无空档 |
| `test_github_sync.py` / `test_gitee_sync.py` | 事件聚合、幂等、分配时段 |
| `test_timezone.py` | 时区校验、日边界、全天占位日期 |
| `test_bot_chat.py` | 对话管道、工具调用、历史、未配置、鉴权 |
| `test_qq_bot.py` | 绑定码、绑定、私聊/群聊路由、白名单、分片 |

### 3.2 常用写法

**数据库隔离**：`conftest.py` 为每个测试创建内存 SQLite，并覆盖 `get_db`：

```python
app.dependency_overrides[get_db] = override_get_db
```

**配置隔离**：`client` fixture 会清空 GitHub/Gitee 配置、固定 JWT Secret。需要改其它配置时用 `monkeypatch`：

```python
monkeypatch.setattr(settings, "deepseek_api_key", "")
```

**假 LLM**：实现 `chat(messages, tools)` 的脚本化 Provider，通过依赖覆盖注入：

```python
app.dependency_overrides[get_llm_provider] = lambda: fake_provider
```

**QQ 消息**：直接构造 OneBot 事件并调用 `handle_event`，不启动 WebSocket：

```python
reply = asyncio.run(handle_event(db, event, provider=fake))
```

**WebSocket 发送**：用 `FakeWebSocket` 记录 `send()` 的 payload，验证 action/params/分片。

**时区**：`app_timezone()` 带 `lru_cache`，测试中修改配置后需要 `cache_clear()`。

### 3.3 运行单个测试

```bash
cd backend
uv run pytest tests/test_bot_chat.py -q
uv run pytest tests/test_qq_bot.py::test_bind_code_binds_qq_via_private_message -q
```

## 4. 前端测试

| 文件 | 覆盖内容 |
| --- | --- |
| `tests/unit/store.spec.ts` | Pinia 日程状态、筛选、加载 |
| `tests/unit/scheduleForm.spec.ts` | 表单校验、全天、序列化 |
| `tests/unit/date.spec.ts` | 日期格式、范围、全天日期 |
| `tests/unit/authStore.spec.ts` | 登录/注册/登出/Token |
| `tests/unit/theme.spec.ts` | 主题、持久化、旧版本重置 |
| `tests/components/` | 组件渲染与交互 |

```bash
cd frontend
npm test
npm test -- tests/unit/theme.spec.ts
```

## 5. 端到端测试

`frontend/playwright.config.ts` 会自动启动：

- 后端：临时数据库 `/tmp/digital-clone-e2e.db`，管理员 `e2e-user / e2e-password-123`
- 前端：`http://127.0.0.1:5173`

覆盖流程：登录/退出、注册、日历 CRUD 与筛选、全天日程、移动端议程、暂存区空状态、主题切换。

```bash
make e2e
cd frontend && npx playwright test e2e/theme.spec.ts
```

首次运行会自动安装 Chromium。若本地已有服务占用 8000/5173，Playwright 会复用；复用前确认数据库与账号与测试一致。

## 6. 数据库迁移检查

```bash
cd backend
uv run alembic downgrade base
uv run alembic upgrade head
uv run alembic check
```

提交包含迁移的改动前至少执行一次，确认可重复升级且模型与迁移无差异。

## 7. 建议的 CI

```yaml
name: verify
on: [push, pull_request]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - uses: actions/setup-node@v4
        with:
          node-version: '26'
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: make setup
      - run: make verify
      - run: cd backend && uv run alembic upgrade head && uv run alembic check
```

`make e2e` 可按需单独跑，首次需要下载 Chromium。

## 8. 当前未覆盖

- 真实 DeepSeek 调用：测试全部使用假 Provider，避免外网和费用
- 真实 QQ / NapCat 连接：只验证了事件处理和发送格式，未做端到端联调
- 并发与压力测试：SQLite 单写者，暂未做压测
- 前端视觉回归：没有截图对比基线
- 覆盖率门槛：未接入 coverage 检查

## 9. 新增功能的测试清单

1. 后端：正常路径 + 参数校验 + 权限/账号隔离 + 边界值
2. 涉及外部服务：用假客户端/假 Provider，不依赖网络
3. 涉及时间：显式时区，避免依赖运行机器的本地时区
4. 涉及数据库：用迁移建表，不在测试中 `create_all` 覆盖生产结构（当前仅测试库使用）
5. 前端：store 单测 + 关键组件；交互流程补 e2e
6. 最后执行 `make verify`；涉及迁移再加 `alembic check`
