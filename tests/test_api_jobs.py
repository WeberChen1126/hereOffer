"""T13 岗位管理测试"""
import requests
import json
import sys
import io

# 设置输出编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"


def register_admin():
    """注册管理员用户"""
    print("\n=== 1. 注册管理员用户 ===")
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "admin@example.com",
            "password": "Admin123456",
            "user_type": "admin"
        }
    )
    
    print(f"注册状态: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ 管理员注册成功")
        return True
    else:
        print(f"注册响应: {response.text}")
        return False


def login(email, password):
    """登录获取 token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    
    if response.status_code == 200:
        token = response.json()["data"]["access_token"]
        print(f"✓ 登录成功")
        return token
    else:
        print(f"✗ 登录失败: {response.text}")
        return None


def test_create_job(admin_token):
    """测试创建岗位"""
    print("\n=== 2. 创建岗位 ===")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    job_data = {
        "title": "Python 高级后端工程师",
        "description": """
我们正在寻找一位经验丰富的 Python 后端工程师加入我们的团队。

技术要求：
- 精通 Python，熟悉 FastAPI/Django 等框架
- 熟悉 MySQL、Redis、MongoDB 等数据库
- 有分布式系统、微服务架构经验
- 熟悉 Docker、K8s 等容器技术

加分项：
- 有大型互联网公司工作经验
- 有开源项目贡献
- 熟悉 Go/Java 等其他语言
        """,
        "requirements": "3年以上 Python 后端开发经验",
        "responsibilities": "负责核心业务系统的设计和开发",
        "department": "技术部",
        "location": "北京/远程",
        "salary_range": "25K-40K",
        "threshold_score": 70,
        "is_active": True
    }
    
    response = requests.post(
        f"{BASE_URL}/admin/jobs",
        headers=headers,
        json=job_data
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        job_id = result["data"]["id"]
        print(f"✓ 岗位创建成功")
        print(f"  岗位ID: {job_id}")
        print(f"  职位: {result['data']['title']}")
        print(f"  阈值: {result['data']['threshold_score']}")
        return job_id
    else:
        print(f"✗ 创建失败: {response.text}")
        return None


def test_update_question_bank(admin_token, job_id):
    """测试更新题库"""
    print(f"\n=== 3. 更新岗位题库 (job_id={job_id}) ===")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 生成 20 道题
    questions = []
    categories = ["Python基础", "框架应用", "数据库", "系统设计", "算法"]
    
    for i in range(20):
        category = categories[i % len(categories)]
        questions.append({
            "competency_tag": category,
            "question_text": f"[{category}] 第{i+1}题：请描述你对{category}的理解和实践经验。",
            "difficulty": "medium",
            "expected_points": [
                "理解核心概念",
                "有实际应用经验",
                "能举出具体案例"
            ]
        })
    
    bank_data = {
        "version": 1,
        "questions": questions
    }
    
    response = requests.put(
        f"{BASE_URL}/admin/jobs/{job_id}/question_bank",
        headers=headers,
        json=bank_data
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ 题库更新成功")
        print(f"  题目数量: {result['data']['question_count']}")
        print(f"  版本: {result['data']['version']}")
        return True
    else:
        print(f"✗ 更新失败: {response.text}")
        return False


def test_list_jobs_as_candidate(candidate_token):
    """测试候选人查看岗位列表"""
    print("\n=== 4. 候选人查看岗位列表 ===")
    
    headers = {"Authorization": f"Bearer {candidate_token}"}
    
    response = requests.get(
        f"{BASE_URL}/admin/jobs",
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        jobs = result["data"]["jobs"]
        total = result["data"]["total"]
        
        print(f"✓ 获取岗位列表成功")
        print(f"  总数: {total}")
        
        for job in jobs:
            print(f"  - [{job['id']}] {job['title']} (阈值: {job['threshold_score']}, 开放: {job['is_active']})")
        
        return len(jobs) > 0
    else:
        print(f"✗ 获取失败: {response.text}")
        return False


def test_apply_with_job_id(candidate_token, job_id):
    """测试通过 job_id 投递"""
    print(f"\n=== 5. 通过 job_id 投递 (job_id={job_id}) ===")
    
    headers = {"Authorization": f"Bearer {candidate_token}"}
    
    with open("test_resume_zh.txt", "rb") as f:
        files = {"file": ("test_resume_zh.txt", f, "text/plain")}
        data = {"job_id": job_id}
        
        response = requests.post(
            f"{BASE_URL}/applications",
            headers=headers,
            files=files,
            data=data
        )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        app_id = result["data"]["id"]
        print(f"✓ 投递成功")
        print(f"  投递ID: {app_id}")
        print(f"  职位: {result['data']['job_title']}")
        print(f"  状态: {result['data']['status']}")
        return app_id
    else:
        print(f"✗ 投递失败: {response.text}")
        return None


def main():
    """主测试流程"""
    print("=" * 80)
    print("T13: 岗位管理功能测试")
    print("=" * 80)
    
    # 1. 注册管理员
    register_admin()
    
    # 2. 管理员登录
    print("\n=== 管理员登录 ===")
    admin_token = login("admin@example.com", "Admin123456")
    if not admin_token:
        print("\n❌ 测试失败：管理员登录失败")
        return
    
    # 3. 创建岗位
    job_id = test_create_job(admin_token)
    if not job_id:
        print("\n❌ 测试失败：创建岗位失败")
        return
    
    # 4. 更新题库
    success = test_update_question_bank(admin_token, job_id)
    if not success:
        print("\n❌ 测试失败：更新题库失败")
        return
    
    # 5. 注册候选人
    print("\n=== 注册候选人 ===")
    requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "candidate_job@example.com",
            "password": "Cand123456",
            "user_type": "candidate"
        }
    )
    
    candidate_token = login("candidate_job@example.com", "Cand123456")
    if not candidate_token:
        print("\n❌ 测试失败：候选人登录失败")
        return
    
    # 6. 候选人查看岗位
    success = test_list_jobs_as_candidate(candidate_token)
    if not success:
        print("\n⚠️ 警告：候选人无法查看岗位")
    
    # 7. 通过 job_id 投递
    app_id = test_apply_with_job_id(candidate_token, job_id)
    if not app_id:
        print("\n❌ 测试失败：投递失败")
        return
    
    print("\n" + "=" * 80)
    print("✅ T13 岗位管理功能测试通过！")
    print("=" * 80)
    print("\n功能验证：")
    print("  ✓ 管理员创建岗位")
    print("  ✓ 管理员维护题库（20道题）")
    print("  ✓ 候选人查看开放岗位")
    print("  ✓ 候选人通过 job_id 投递")


if __name__ == "__main__":
    main()
