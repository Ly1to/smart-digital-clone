# 登录与认证

> 所属项目：个人日程系统  
> 说明：本文档覆盖 `01-product-scope.md` 中“免登录 / 单用户无认证”的早期决定；当前版本支持多账号登录和数据隔离。
> 更新日期：2026-11-14

## 1. 目标

系统支持多个账号，但每个账号只能访问自己的日历、暂存区和自动来源数据。不提供角色、权限管理和账号切换。

```text
首次部署 -> 创建管理员账号 -> 获得 JWT
后续访问 -> 登录 -> 浏览器保存 Token -> 访问受保护 API
登录页 -> 注册页 -> 创建新账号 -> 获得独立的日程空间
```

## 2. 账号模型

`users` 表：

- `id`
- `username`（唯一）
- `password_hash`（scrypt + 随机 salt）
- `created_at`
- `updated_at`

`POST /api/auth/setup` 只在 `users` 为空时可用，用于创建第一个管理员账号。

`POST /api/auth/register` 用于创建后续账号。注册默认开放，可通过 `ALLOW_REGISTRATION=false` 关闭；关闭后接口返回 403，前端隐藏注册入口。

`schedules` 和 `staged_schedules` 通过 `user_id` 归属到账号，所有查询和写操作都会按当前登录账号过滤。

## 3. API

```text
GET  /api/auth/status    # 是否已完成初始化
POST /api/auth/setup     # 首次创建管理员并返回 Token
POST /api/auth/register  # 注册新账号并返回 Token
POST /api/auth/login     # 登录并返回 Token
GET  /api/auth/me        # 当前用户，需要 Token
POST /api/auth/logout    # 客户端退出，需要 Token
```

除健康检查和 `/api/auth/status|setup|register|login` 外，所有 API 都要求：

```http
Authorization: Bearer <access_token>
```

Token 为 HS256 JWT，默认有效期 7 天。完整的请求与响应示例见 [API 参考](./API.md#4-认证)。

## 4. 前端行为

- `/login`、`/register` 为公开路由，`/` 需要登录
- 首次打开且系统未初始化时，登录页切换为“创建管理员账号”
- 已初始化后，登录页显示“没有账号？创建一个”入口，进入 `/register`
- Token 存储在 `localStorage`，Axios 请求自动附带
- 收到 401 时清除 Token 并跳转登录页
- 侧栏/筛选抽屉提供当前账号和“退出登录”
- 刷新页面后通过 `/auth/me` 恢复登录状态

## 5. 配置

```env
# 生产环境务必固定，长度建议 >= 32 字节
JWT_SECRET=change-me-to-a-long-random-string

# Token 有效期，默认 10080 分钟（7 天）
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# 是否开放注册页，默认 true
ALLOW_REGISTRATION=true

# 可选：首次启动自动创建管理员（仅在 users 为空时）
AUTH_BOOTSTRAP_USERNAME=admin
AUTH_BOOTSTRAP_PASSWORD=change-me-123
```

如果不配置 `JWT_SECRET`，后端每次进程启动会生成随机密钥，重启后已有 Token 全部失效，需要重新登录。

## 6. 忘记密码 / 重置

当前没有邮件找回流程。注意：账号删除会通过外键级联删除该账号的日程和暂存数据，操作前请先执行 `make backup`。

忘记密码时，在服务停止后清空 users 表，再重新打开系统创建账号：

```bash
cd backend
sqlite3 ../data/schedules.db "DELETE FROM users;"
```

Docker 部署可以执行：

```bash
docker compose exec backend python -c "import sqlite3; c = sqlite3.connect('/app/data/schedules.db'); c.execute('DELETE FROM users'); c.commit(); c.close()"
```

重新启动后端和前端，登录页会回到“创建管理员账号”。如果是多账号部署，删除其他账号也会同时删除该账号的数据。

## 7. 安全边界

- 登录接口没有限流；公网部署建议在 Nginx 或反向代理层增加 HTTPS 和访问保护
- JWT 无服务端会话表，退出登录是客户端清除 Token
- 所有日程和暂存查询都按当前账号的 `user_id` 过滤，其他账号的 ID 会返回 404
- 删除账号会级联删除该账号的日程、暂存数据和 QQ 绑定
- 密码不会通过 API 返回，数据库中只保存 scrypt 哈希
