"""T10 投递管理 API 测试"""
import requests
import json
import sys
import io

# 设置输出编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VyX3R5cGUiOiJjYW5kaWRhdGUiLCJleHAiOjE3Njk5NjA3NDh9.E0YLxXPVAaZNvOrd101kRtP_7vhLl69Y_yrcrKScUqI"

headers = {"Authorization": f"Bearer {TOKEN}"}


def test_create_application():
    """测试创建投递"""
    print("\n=== 1. 测试创建投递 ===")
    
    with open("test_resume_zh.txt", "rb") as f:
        files = {"file": ("test_resume_zh.txt", f, "text/plain")}
        data = {
            "job_title": "高级后端工程师",
            "job_description": """
职位要求：
1. 本科及以上学历，计算机相关专业
2. 3年以上后端开发经验
3. 熟练掌握 Python 或 Java
4. 熟悉 FastAPI、Spring Boot
5. 熟悉 MySQL、Redis
            """
        }
        
        print("正在创建投递并上传简历...")
        response = requests.post(
            f"{BASE_URL}/applications",
            headers=headers,
            files=files,
            data=data,
            timeout=60,
        )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        app_data = result["data"]
        
        print(f"✓ 创建投递成功")
        print(f"\n投递ID: {app_data['id']}")
        print(f"职位: {app_data['job_title']}")
        print(f"状态: {app_data['status']}")
        print(f"创建时间: {app_data['created_at']}")
        
        return app_data['id']
    else:
        print(f"✗ 创建投递失败")
        print(f"错误信息: {response.text}")
        return None


def test_get_application(application_id):
    """测试获取投递详情"""
    print(f"\n=== 2. 测试获取投递详情 (ID: {application_id}) ===")
    
    response = requests.get(
        f"{BASE_URL}/applications/{application_id}",
        headers=headers,
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        app_data = result["data"]
        
        print(f"✓ 获取投递详情成功")
        print(f"\n投递ID: {app_data['id']}")
        print(f"职位: {app_data['job_title']}")
        print(f"状态: {app_data['status']}")
        print(f"简历文本（前200字）: {app_data['resume_text'][:200] if app_data['resume_text'] else 'N/A'}...")
        
        return True
    else:
        print(f"✗ 获取投递详情失败")
        print(f"错误信息: {response.text}")
        return False


def test_list_applications():
    """测试获取投递列表"""
    print(f"\n=== 3. 测试获取投递列表 ===")
    
    response = requests.get(
        f"{BASE_URL}/applications",
        headers=headers,
        params={"skip": 0, "limit": 10},
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        apps = result["data"]["applications"]
        total = result["data"]["total"]
        
        print(f"✓ 获取投递列表成功")
        print(f"\n总数: {total} 条")
        print(f"返回: {len(apps)} 条")
        
        for app in apps[:3]:  # 只显示前3条
            print(f"  - ID: {app['id']}, 职位: {app['job_title']}, 状态: {app['status']}")
        
        return True
    else:
        print(f"✗ 获取投递列表失败")
        print(f"错误信息: {response.text}")
        return False


def test_update_status(application_id):
    """测试更新投递状态"""
    print(f"\n=== 4. 测试更新投递状态 (ID: {application_id}) ===")
    
    # 尝试转移到 SCORING
    payload = {"new_status": "SCORING"}
    
    response = requests.post(
        f"{BASE_URL}/applications/{application_id}/status",
        headers=headers,
        json=payload,
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        app_data = result["data"]
        
        print(f"✓ 状态更新成功")
        print(f"新状态: {app_data['status']}")
        
        return True
    else:
        print(f"✗ 状态更新失败")
        print(f"错误信息: {response.text}")
        return False


def main():
    """主测试流程"""
    print("=" * 80)
    print("T10: 投递管理 API 自动化测试")
    print("=" * 80)
    
    # 1. 创建投递
    application_id = test_create_application()
    if not application_id:
        print("\n❌ 测试失败：创建投递失败")
        return
    
    # 2. 获取投递详情
    success = test_get_application(application_id)
    if not success:
        print("\n⚠️ 警告：获取投递详情失败")
    
    # 3. 获取投递列表
    success = test_list_applications()
    if not success:
        print("\n⚠️ 警告：获取投递列表失败")
    
    # 4. 更新状态
    success = test_update_status(application_id)
    if not success:
        print("\n⚠️ 警告：更新状态失败")
    
    print("\n" + "=" * 80)
    print("✅ T10 测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
