#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建 Admin 账号和测试数据
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json

BASE_URL = "http://localhost:8000"

def create_admin_user():
    """创建管理员账号"""
    print("=" * 60)
    print("1. 创建 Admin 账号")
    print("=" * 60)
    
    url = f"{BASE_URL}/auth/register"
    data = {
        "username": "admin",
        "email": "admin@hereoffer.com",
        "password": "admin123456",
        "user_type": "admin"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("✓ Admin 账号创建成功")
            print(f"  用户名: admin")
            print(f"  邮箱: admin@hereoffer.com")
            print(f"  密码: admin123456")
            return True
        else:
            print("✗ Admin 账号创建失败")
            return False
    except Exception as e:
        print(f"✗ 请求错误: {e}")
        return False

def login_admin():
    """登录获取 token"""
    print("\n" + "=" * 60)
    print("2. 登录 Admin 账号")
    print("=" * 60)
    
    url = f"{BASE_URL}/auth/login"
    data = {
        "email": "admin@hereoffer.com",
        "password": "admin123456"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("data", {}).get("access_token")
            print("✓ 登录成功")
            print(f"  Token: {token[:50]}...")
            return token
        else:
            print(f"✗ 登录失败: {response.json()}")
            return None
    except Exception as e:
        print(f"✗ 请求错误: {e}")
        return None

def create_test_jobs(token):
    """创建测试职位"""
    print("\n" + "=" * 60)
    print("3. 创建测试职位")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/admin/jobs"
    
    jobs_data = [
        {
            "title": "Python 后端工程师",
            "description": "职位描述：负责后端系统开发和维护。\n要求：熟悉 Python、FastAPI、MySQL，有 3 年以上工作经验。",
            "threshold_score": 70,
            "is_active": True
        },
        {
            "title": "前端工程师",
            "description": "职位描述：负责前端界面开发。\n要求：熟悉 React、TypeScript、Ant Design，有 2 年以上工作经验。",
            "threshold_score": 65,
            "is_active": True
        },
        {
            "title": "全栈工程师",
            "description": "职位描述：负责全栈开发。\n要求：熟悉前后端技术栈，有独立开发能力。",
            "threshold_score": 75,
            "is_active": True
        }
    ]
    
    created_jobs = []
    for i, job in enumerate(jobs_data, 1):
        try:
            response = requests.post(url, json=job, headers=headers)
            print(f"\n职位 {i}: {job['title']}")
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get("data", {}).get("id")
                print(f"  ✓ 创建成功, ID: {job_id}")
                created_jobs.append(job_id)
            else:
                print(f"  ✗ 创建失败: {response.json()}")
        except Exception as e:
            print(f"  ✗ 请求错误: {e}")
    
    return created_jobs

def verify_jobs(token):
    """验证职位列表"""
    print("\n" + "=" * 60)
    print("4. 验证职位列表")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/admin/jobs?is_active=true"
    
    try:
        response = requests.get(url, headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            # 后端返回的数据结构是 { "jobs": [...], "total": N }
            jobs = result.get("data", {}).get("jobs", [])
            print(f"✓ 找到 {len(jobs)} 个活跃职位")
            
            for job in jobs:
                print(f"\n  - ID: {job.get('id')}")
                print(f"    标题: {job.get('title')}")
                print(f"    状态: {'✓ 激活' if job.get('is_active') else '✗ 未激活'}")
            
            return jobs
        else:
            print(f"✗ 获取失败: {response.json()}")
            return []
    except Exception as e:
        print(f"✗ 请求错误: {e}")
        return []

def main():
    print("\n" + "=" * 60)
    print("hereOffer - 创建 Admin 账号和测试数据")
    print("=" * 60 + "\n")
    
    # 1. 创建 admin 用户
    if not create_admin_user():
        print("\n注意: 如果账号已存在，请忽略此错误")
    
    # 2. 登录
    token = login_admin()
    if not token:
        print("\n✗ 无法继续，登录失败")
        return
    
    # 3. 创建测试职位
    jobs = create_test_jobs(token)
    
    # 4. 验证
    verify_jobs(token)
    
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
    print("\n您现在可以使用以下账号登录:")
    print("  管理员账号:")
    print("    邮箱: admin@hereoffer.com")
    print("    密码: admin123456")
    print("\n  访问前端: http://localhost:3000")
    print("  访问后端: http://localhost:8000")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
