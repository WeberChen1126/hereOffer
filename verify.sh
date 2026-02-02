#!/bin/bash

# 快速验证脚本 - 检查基础功能

set -e

echo "=========================================="
echo "hereOffer 快速验证脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 检查 Docker 是否运行
echo -e "${YELLOW}[1/5]${NC} 检查 Docker 服务..."
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker 未运行${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker 运行中${NC}"
echo ""

# 2. 启动服务
echo -e "${YELLOW}[2/5]${NC} 启动服务（docker-compose up -d）..."
docker-compose up -d
echo -e "${GREEN}✓ 服务启动${NC}"
echo ""

# 3. 等待服务就绪
echo -e "${YELLOW}[3/5]${NC} 等待服务就绪（30秒）..."
sleep 30
echo -e "${GREEN}✓ 等待完成${NC}"
echo ""

# 4. 执行数据库迁移
echo -e "${YELLOW}[4/5]${NC} 执行数据库迁移..."
docker-compose exec -T api alembic upgrade head
echo -e "${GREEN}✓ 迁移完成${NC}"
echo ""

# 5. 验证健康检查
echo -e "${YELLOW}[5/5]${NC} 验证健康检查接口..."
RESPONSE=$(curl -s http://localhost:8000/healthz)
if echo "$RESPONSE" | grep -q '"code":0'; then
    echo -e "${GREEN}✓ 健康检查通过${NC}"
    echo "响应: $RESPONSE"
else
    echo -e "${RED}✗ 健康检查失败${NC}"
    echo "响应: $RESPONSE"
    exit 1
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✓ 所有验证通过！${NC}"
echo "=========================================="
echo ""
echo "API 地址: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "常用命令:"
echo "  查看日志:        docker-compose logs -f api"
echo "  查看 worker 日志: docker-compose logs -f worker"
echo "  运行测试:        pytest tests/"
echo "  关闭服务:        docker-compose down"
