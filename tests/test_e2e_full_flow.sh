#!/bin/bash

# E2E 快速测试脚本

set -e

echo "=========================================="
echo "hereOffer 快速 E2E 测试"
echo "=========================================="
echo ""

API_BASE="http://localhost:8000"

# 测试颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_count=0
pass_count=0

# 测试函数
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    test_count=$((test_count + 1))
    echo -e "${YELLOW}[测试 $test_count]${NC} $name"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s "$API_BASE$endpoint")
    else
        response=$(curl -s -X "$method" "$API_BASE$endpoint" \
            -H 'Content-Type: application/json' \
            -d "$data")
    fi
    
    if echo "$response" | grep -q '"code":0'; then
        echo -e "${GREEN}✓ 通过${NC}"
        pass_count=$((pass_count + 1))
        echo "  响应: $(echo $response | jq -c .)"
    else
        echo -e "${RED}✗ 失败${NC}"
        echo "  响应: $response"
    fi
    echo ""
}

# 1. 健康检查
test_endpoint "健康检查" "GET" "/healthz" ""

# 2. 注册候选人
test_endpoint "注册候选人" "POST" "/auth/register" \
    '{"email":"test_candidate@example.com","password":"password123","user_type":"candidate"}'

# 3. 注册管理员
test_endpoint "注册管理员" "POST" "/auth/register" \
    '{"email":"test_admin@example.com","password":"password123","user_type":"admin"}'

# 4. 候选人登录
login_response=$(curl -s -X POST "$API_BASE/auth/login" \
    -H 'Content-Type: application/json' \
    -d '{"email":"test_candidate@example.com","password":"password123"}')

if echo "$login_response" | grep -q '"code":0'; then
    echo -e "${YELLOW}[测试 4]${NC} 候选人登录"
    echo -e "${GREEN}✓ 通过${NC}"
    pass_count=$((pass_count + 1))
    TOKEN=$(echo "$login_response" | jq -r '.data.access_token')
    echo "  Token: ${TOKEN:0:20}..."
    echo ""
    test_count=$((test_count + 1))
else
    echo -e "${YELLOW}[测试 4]${NC} 候选人登录"
    echo -e "${RED}✗ 失败${NC}"
    echo "  响应: $login_response"
    echo ""
    test_count=$((test_count + 1))
fi

# 统计
echo "=========================================="
echo "测试结果: $pass_count/$test_count 通过"
echo "=========================================="

if [ $pass_count -eq $test_count ]; then
    echo -e "${GREEN}✓ 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}✗ 部分测试失败${NC}"
    exit 1
fi
