"""
T21: Admin 投递管理功能测试
测试 Admin 查询、筛选、详情、统计功能
"""
import sys
import requests
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*80)
    print(f"{title}")
    print("="*80)

def print_success(msg):
    print(f"✓ {msg}")

def print_error(msg):
    print(f"✗ {msg}")
    sys.exit(1)

def register_and_login(email, password, user_type):
    """注册并登录"""
    # 注册
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "user_type": user_type
    })
    
    # 登录
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    
    if resp.status_code != 200:
        print_error(f"登录失败: {resp.status_code} - {resp.text}")
    
    data = resp.json()
    return data["data"]["access_token"]

def create_job(token, job_data):
    """创建岗位"""
    resp = requests.post(
        f"{BASE_URL}/admin/jobs",
        json=job_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if resp.status_code != 200:
        print_error(f"创建岗位失败: {resp.status_code} - {resp.text}")
    
    return resp.json()["data"]

def submit_application(token, job_id, resume_file_path):
    """提交投递"""
    with open(resume_file_path, "rb") as f:
        files = {"file": (resume_file_path.name, f, "text/plain")}
        data = {"job_id": job_id}
        
        resp = requests.post(
            f"{BASE_URL}/applications",
            data=data,
            files=files,
            headers={"Authorization": f"Bearer {token}"}
        )
    
    if resp.status_code != 200:
        print_error(f"投递失败: {resp.status_code} - {resp.text}")
    
    return resp.json()["data"]

def wait_for_status(token, app_id, target_statuses, timeout=60):
    """等待投递状态变化"""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(
            f"{BASE_URL}/applications/{app_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if resp.status_code == 200:
            status = resp.json()["data"]["status"]
            if status in target_statuses:
                return status
        
        time.sleep(2)
    
    return None

def main():
    print_section("T21: Admin 投递管理功能测试")
    
    # 准备测试数据
    admin_email = f"admin_t21_{int(time.time())}@test.com"
    candidate1_email = f"candidate1_t21_{int(time.time())}@test.com"
    candidate2_email = f"candidate2_t21_{int(time.time())}@test.com"
    password = "test123456"
    
    resume_file = Path("sample_resume.txt")
    if not resume_file.exists():
        print_error(f"简历文件不存在: {resume_file}")
    
    # === 1. 注册用户 ===
    print_section("1. 准备测试用户")
    admin_token = register_and_login(admin_email, password, "admin")
    print_success(f"管理员注册并登录: {admin_email}")
    
    candidate1_token = register_and_login(candidate1_email, password, "candidate")
    print_success(f"候选人1注册并登录: {candidate1_email}")
    
    candidate2_token = register_and_login(candidate2_email, password, "candidate")
    print_success(f"候选人2注册并登录: {candidate2_email}")
    
    # === 2. 创建岗位 ===
    print_section("2. 创建测试岗位")
    
    job1 = create_job(admin_token, {
        "title": "Python 后端工程师",
        "description": "负责后端开发...",
        "requirements": "3年以上Python经验",
        "responsibilities": "开发和维护后端服务",
        "department": "技术部",
        "location": "北京",
        "salary_range": "20k-35k",
        "threshold_score": 70,
        "is_active": True
    })
    job1_id = job1["id"]
    print_success(f"岗位1创建成功: ID={job1_id}, Title={job1['title']}")
    
    job2 = create_job(admin_token, {
        "title": "前端工程师",
        "description": "负责前端开发...",
        "requirements": "熟悉React/Vue",
        "responsibilities": "开发和维护前端应用",
        "department": "技术部",
        "location": "上海",
        "salary_range": "18k-30k",
        "threshold_score": 60,
        "is_active": True
    })
    job2_id = job2["id"]
    print_success(f"岗位2创建成功: ID={job2_id}, Title={job2['title']}")
    
    # === 3. 提交多个投递 ===
    print_section("3. 提交测试投递")
    
    app1 = submit_application(candidate1_token, job1_id, resume_file)
    app1_id = app1["id"]
    print_success(f"候选人1投递岗位1: application_id={app1_id}")
    
    app2 = submit_application(candidate2_token, job1_id, resume_file)
    app2_id = app2["id"]
    print_success(f"候选人2投递岗位1: application_id={app2_id}")
    
    app3 = submit_application(candidate1_token, job2_id, resume_file)
    app3_id = app3["id"]
    print_success(f"候选人1投递岗位2: application_id={app3_id}")
    
    print("\n⏱️  等待异步任务处理（最多60秒）...")
    
    # 等待第一个投递完成
    final_status = wait_for_status(
        candidate1_token, 
        app1_id, 
        ["QUESTIONS_READY", "HUMAN_REVIEW", "REJECTED"],
        timeout=60
    )
    
    if final_status:
        print_success(f"投递1处理完成，状态: {final_status}")
    else:
        print("⚠️  投递1未在60秒内完成，继续测试...")
    
    # === 4. 测试 Admin 查询列表（无筛选） ===
    print_section("4. Admin 查询所有投递")
    
    resp = requests.get(
        f"{BASE_URL}/admin/applications",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print_error(f"查询失败: {resp.text}")
    
    data = resp.json()["data"]
    print_success(f"查询成功，总投递数: {data['total']}")
    print(f"  当前页: {data['page']}, 每页: {data['page_size']}")
    print(f"  返回数量: {len(data['applications'])}")
    
    for app in data["applications"][:3]:  # 显示前3个
        print(f"    - [ID={app['id']}] {app['job_title']} | {app['status']} | 候选人: {app.get('candidate_email', 'N/A')}")
    
    # === 5. 测试 Admin 按岗位筛选 ===
    print_section("5. Admin 按岗位筛选投递")
    
    resp = requests.get(
        f"{BASE_URL}/admin/applications?job_id={job1_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print_error(f"查询失败: {resp.text}")
    
    data = resp.json()["data"]
    print_success(f"岗位1的投递数: {data['total']}")
    
    for app in data["applications"]:
        print(f"    - [ID={app['id']}] {app['job_title']} | {app['status']}")
    
    # === 6. 测试 Admin 按状态筛选 ===
    print_section("6. Admin 按状态筛选投递")
    
    resp = requests.get(
        f"{BASE_URL}/admin/applications?status=PARSING",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print_error(f"查询失败: {resp.text}")
    
    data = resp.json()["data"]
    print_success(f"PARSING 状态的投递数: {data['total']}")
    
    # === 7. 测试 Admin 查询详情 ===
    print_section("7. Admin 查询投递详情")
    
    resp = requests.get(
        f"{BASE_URL}/admin/applications/{app1_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print_error(f"查询详情失败: {resp.text}")
    
    detail = resp.json()["data"]
    print_success(f"获取详情成功")
    print(f"  投递ID: {detail['id']}")
    print(f"  岗位: {detail['job_title']}")
    print(f"  状态: {detail['status']}")
    print(f"  候选人: {detail.get('candidate_email', 'N/A')}")
    print(f"  简历文本: {'有' if detail.get('resume_text') else '无'}")
    print(f"  简历JSON: {'有' if detail.get('resume_json') else '无'}")
    print(f"  评分JSON: {'有' if detail.get('score_json') else '无'}")
    print(f"  题目JSON: {'有' if detail.get('questions_json') else '无'}")
    
    if detail.get('job_info'):
        print(f"  岗位信息: ID={detail['job_info']['id']}, 阈值={detail['job_info']['threshold_score']}")
    
    # === 8. 测试 Admin 更新状态 ===
    print_section("8. Admin 手动更新状态")
    
    resp = requests.post(
        f"{BASE_URL}/admin/applications/{app1_id}/status",
        json={
            "new_status": "HUMAN_REVIEW",
            "note": "需要人工审核"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print_error(f"更新状态失败: {resp.text}")
    
    data = resp.json()["data"]
    print_success(f"状态更新成功")
    print(f"  投递ID: {data['application_id']}")
    print(f"  旧状态: {data['old_status']}")
    print(f"  新状态: {data['new_status']}")
    
    # 验证状态
    resp = requests.get(
        f"{BASE_URL}/admin/applications/{app1_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    current_status = resp.json()["data"]["status"]
    
    if current_status == "HUMAN_REVIEW":
        print_success(f"验证成功: 当前状态为 {current_status}")
    else:
        print_error(f"验证失败: 期望 HUMAN_REVIEW, 实际 {current_status}")
    
    # === 9. 测试 Admin 统计信息 ===
    print_section("9. Admin 查询统计信息")
    
    resp = requests.get(
        f"{BASE_URL}/admin/applications/stats/summary",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print_error(f"查询统计失败: {resp.text}")
    
    stats = resp.json()["data"]
    print_success(f"统计查询成功")
    print(f"  总投递数: {stats['total']}")
    print(f"  已评分数: {stats['scored_count']}")
    print(f"  平均分: {stats.get('avg_score', 'N/A')}")
    print(f"  达标数: {stats.get('pass_count', 0)}")
    print(f"  达标率: {stats.get('pass_rate', 'N/A')}%")
    
    print("\n  各状态统计:")
    for status, count in stats["status_stats"].items():
        if count > 0:
            print(f"    - {status}: {count}")
    
    # === 10. 测试按岗位统计 ===
    print_section("10. Admin 按岗位查询统计")
    
    resp = requests.get(
        f"{BASE_URL}/admin/applications/stats/summary?job_id={job1_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print_error(f"查询统计失败: {resp.text}")
    
    stats = resp.json()["data"]
    print_success(f"岗位1统计")
    print(f"  投递数: {stats['total']}")
    print(f"  已评分: {stats['scored_count']}")
    
    # === 11. 测试分页 ===
    print_section("11. 测试分页功能")
    
    resp = requests.get(
        f"{BASE_URL}/admin/applications?page=1&page_size=2",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print_error(f"查询失败: {resp.text}")
    
    data = resp.json()["data"]
    print_success(f"分页查询成功")
    print(f"  页码: {data['page']}, 每页: {data['page_size']}")
    print(f"  返回数量: {len(data['applications'])}")
    print(f"  总数: {data['total']}")
    
    # === 最终总结 ===
    print_section("✅ T21 Admin 投递管理功能测试通过！")
    
    print("\n功能验证：")
    print("  ✓ Admin 查询所有投递")
    print("  ✓ Admin 按岗位筛选")
    print("  ✓ Admin 按状态筛选")
    print("  ✓ Admin 查询投递详情")
    print("  ✓ Admin 手动更新状态")
    print("  ✓ Admin 查询统计信息")
    print("  ✓ Admin 按岗位统计")
    print("  ✓ 分页功能")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
