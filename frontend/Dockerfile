# syntax=docker/dockerfile:1

# 构建阶段：按锁文件安装依赖并生成生产静态文件
FROM node:26-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# 运行阶段：Nginx 提供静态文件并反向代理 /api
FROM nginx:1.28-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["wget", "-q", "--spider", "http://127.0.0.1/healthz"]
