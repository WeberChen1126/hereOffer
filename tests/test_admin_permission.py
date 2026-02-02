#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Admin 权限
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json

BASE_URL = "http://localhost:8000"

def test_admin_login_and_create_job():
    """测试 Admin 登录并创建职位"""
    print("=" * 60)
    print("测试 Admin 权限")
    print("=" * 60)
    
    # 1. 登录 Admin
    print("\n1. 登录 Admin 账号...")
    login_url = f"{BASE_URL}/auth/login"
    login_data = {
        "email": "admin@hereoffer.com",
        "password": "admin123456"
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ✗ 登录失败: {response.text}")
            return
        
        result = response.json()
        token = result.get("data", {}).get("access_token")
        user_type = result.get("data", {}).get("user_type")
        user_id = result.get("data", {}).get("user_id")
        
        print(f"   ✓ 登录成功")
        print(f"   Token: {token[:50]}...")
        print(f"   User ID: {user_id}")
        print(f"   User Type: {user_type}")
        
        # 验证 token 中的信息
        import jwt
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            print(f"\n   Token 内容:")
            print(f"   - user_id: {decoded.get('user_id')}")
            print(f"   - user_type: {decoded.get('user_type')}")
            print(f"   - exp: {decoded.get('exp')}")
        except Exception as e:
            print(f"   ✗ 解析 token 失败: {e}")
        
    except Exception as e:
        print(f"   ✗ 请求错误: {e}")
        return
    
    # 2. 创建职位
    print("\n2. 创建测试职位...")
    create_url = f"{BASE_URL}/admin/jobs"
    headers = {"Authorization": f"Bearer {token}"}
    job_data = {
        "title": "权限测试职位",
        "description": "这是一个用于测试 Admin 权限的职位",
        "threshold_score": 70,
        "is_active": True
    }
    
    try:
        response = requests.post(create_url, json=job_data, headers=headers)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print(f"   ✓ 创建成功")
        elif response.status_code == 403:
            print(f"   ✗ 权限被拒绝")
            print(f"\n   问题分析:")
            print(f"   - Token 中 user_type: {decoded.get('user_type')}")
            print(f"   - 后端期望: admin")
            print(f"   - 可能原因: 后端验证逻辑有问题或 token 未正确传递")
        else:
            print(f"   ✗ 创建失败")
    except Exception as e:
        print(f"   ✗ 请求错误: {e}")
    
    # 3. 测试获取职位列表
    print("\n3. 测试获取职位列表...")
    list_url = f"{BASE_URL}/admin/jobs"
    
    try:
        response = requests.get(list_url, headers=headers)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            jobs = result.get("data", {}).get("jobs", [])
            print(f"   ✓ 获取成功，共 {len(jobs)} 个职位")
        else:
            print(f"   ✗ 获取失败: {response.text}")
    except Exception as e:
        print(f"   ✗ 请求错误: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_admin_login_and_create_job()
