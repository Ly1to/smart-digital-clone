# 登录与认证

> 所属项目：个人日程系统  
> 说明：本文档覆盖 `01-product-scope.md` 中“免登录 / 单用户无认证”的早期决定；登录能力为后续增量。  
> 更新日期：2026-11-08

## 1. 目标

系统仍然只服务一个用户，但需要账号密码保护日历、暂存区和自动来源数据。不提供注册、多用户、角色和权限管理。

```text
首次访问 -> 创建唯一管理员账号 -> 获得 JWT
后续访问 -> 登录 -> 浏览器保存 Token -> 访问受保护 API
```

## 2. 账号模型

`users` 表：

- `id`
- `username`（唯一）
- `password_hash`（scrypt + 随机 salt）
- `created_at`
- `updated_at`

`POST /api/auth/setup` 只在 `users` 为空时可用，因此系统最多创建一个管理员账号。

## 3. API

```text
GET  /api/auth/status    # 是否已完成初始化
POST /api/auth/setup     # 首次创建管理员并返回 Token
POST /api/auth/login     # 登录并返回 Token
GET  /api/auth/me        # 当前用户，需要 Token
POST /api/auth/logout    # 客户端退出，需要 Token
```

除健康检查和 `/api/auth/status|setup|login` 外，所有 API 都要求：

```http
Authorization: Bearer <access_token>
```

Token 为 HS256 JWT，默认有效期 7 天。

## 4. 前端行为

- `/login` 为公开路由，`/` 需要登录
- 首次打开且系统未初始化时，登录页切换为“创建管理员账号”
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

# 可选：首次启动自动创建管理员（仅在 users 为空时）
AUTH_BOOTSTRAP_USERNAME=admin
AUTH_BOOTSTRAP_PASSWORD=change-me-123
```

如果不配置 `JWT_SECRET`，后端每次进程启动会生成随机密钥，重启后已有 Token 全部失效，需要重新登录。

## 6. 忘记密码 / 重置

当前没有邮件找回流程。忘记密码时，在服务停止后清空 users 表，再重新打开系统创建账号：

```bash
cd backend
sqlite3 ../data/schedules.db "DELETE FROM users;"
```

重新启动后端和前端，登录页会回到“创建管理员账号”。

## 7. 安全边界

- 登录接口没有限流；公网部署建议在 Nginx 或反向代理层增加 HTTPS 和访问保护
- JWT 无服务端会话表，退出登录是客户端清除 Token
- 单用户系统不在日程表中增加 `user_id`，不实现多用户数据隔离
- 密码不会通过 API 返回，数据库中只保存 scrypt 哈希
