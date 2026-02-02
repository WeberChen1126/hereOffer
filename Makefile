.PHONY: help install build up down logs test clean migrate

help:
	@echo "hereOffer 项目管理命令"
	@echo ""
	@echo "快速开始："
	@echo "  make install    - 安装依赖"
	@echo "  make build      - 构建 Docker 镜像"
	@echo "  make up         - 启动所有服务"
	@echo "  make down       - 关闭所有服务"
	@echo "  make logs       - 查看日志"
	@echo ""
	@echo "数据库："
	@echo "  make migrate    - 执行迁移"
	@echo ""
	@echo "测试："
	@echo "  make test       - 运行单元测试"
	@echo "  make e2e        - 运行端到端测试（待实现）"
	@echo ""
	@echo "开发："
	@echo "  make clean      - 清理临时文件"

install:
	pip install -r requirements.txt

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "服务启动中..."
	@sleep 5
	@echo "检查健康状态..."
	curl http://localhost:8000/healthz

down:
	docker-compose down

logs:
	docker-compose logs -f api

logs-worker:
	docker-compose logs -f worker

test:
	pytest tests/ -v

migrate:
	docker-compose exec api alembic upgrade head

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf dist build *.egg-info

shell:
	docker-compose exec api python

db-shell:
	docker-compose exec mysql mysql -urecruit_user -precruit_password recruit_flow
