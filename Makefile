SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help setup migrate test test-backend test-frontend check check-backend \
	check-frontend build e2e verify

help: ## 显示可用命令
	@echo "个人日程系统常用命令："
	@echo "  make setup    首次安装后端/前端依赖"
	@echo "  make migrate  执行数据库迁移"
	@echo "  make test     运行后端 pytest + 前端 Vitest"
	@echo "  make check    运行全部静态检查（Ruff/ESLint/Prettier/TypeScript）"
	@echo "  make e2e      运行 Playwright 端到端测试（自动启动前后端）"
	@echo "  make verify   运行 check + test + 前端生产构建"
	@echo "  make build    构建前端生产静态文件"

setup: ## 安装开发依赖
	cd backend && uv sync --group dev
	cd frontend && npm install

migrate: ## 执行数据库迁移
	cd backend && uv run alembic upgrade head

test: test-backend test-frontend ## 后端 + 前端单元测试

test-backend: ## 后端 pytest
	cd backend && uv run pytest

test-frontend: ## 前端 Vitest
	cd frontend && npm test

check: check-backend check-frontend ## 全部静态检查

check-backend: ## Ruff 检查与格式检查
	cd backend && uv run ruff check .
	cd backend && uv run ruff format --check .

check-frontend: ## ESLint、Prettier、TypeScript
	cd frontend && npm run check

build: ## 构建前端生产静态文件
	cd frontend && npm run build

e2e: ## Playwright 端到端测试（首次运行会安装 Chromium）
	cd frontend && npx playwright install chromium
	cd frontend && npm run test:e2e

verify: check test build ## 发布前完整校验
