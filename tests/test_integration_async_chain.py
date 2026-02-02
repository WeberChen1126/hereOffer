"""异步任务链端到端测试"""
import requests
import json
import sys
import io
import time

# 设置输出编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"

def register_and_login():
    """注册并登录"""
    print("\n=== 1. 用户注册和登录 ===")
    
    # 注册
    email = f"test_async_{int(time.time())}@example.com"
    password = "Test123456"
    
    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "user_type": "candidate"
        }
    )
    
    print(f"注册状态: {register_response.status_code}")
    
    # 登录
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": email,
            "password": password
        }
    )
    
    if login_response.status_code == 200:
        token = login_response.json()["data"]["access_token"]
        print(f"✓ 登录成功，Token: {token[:50]}...")
        return token
    else:
        print(f"✗ 登录失败: {login_response.text}")
        return None


def create_application_with_async(token):
    """创建投递（异步处理）"""
    print("\n=== 2. 创建投递并触发异步任务链 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    with open("test_resume_zh.txt", "rb") as f:
        files = {"file": ("test_resume_zh.txt", f, "text/plain")}
        data = {
            "job_title": "Python 后端工程师",
            "job_description": """
职位要求：
1. 计算机相关专业本科及以上学历
2. 3年以上 Python 后端开发经验
3. 熟练掌握 FastAPI、Django 等框架
4. 熟悉 MySQL、Redis、RabbitMQ
5. 有分布式系统、微服务架构经验
6. 有大型互联网公司工作经验优先

工作职责：
- 负责核心业务系统的设计和开发
- 参与系统架构设计和技术选型
- 优化系统性能，保证服务稳定性
- 指导和培养初级工程师
            """
        }
        
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
        app_id = result["data"]["id"]
        status = result["data"]["status"]
        
        print(f"✓ 投递创建成功")
        print(f"投递ID: {app_id}")
        print(f"初始状态: {status}")
        print(f"异步任务已触发，开始轮询...")
        
        return app_id
    else:
        print(f"✗ 创建投递失败: {response.text}")
        return None


def poll_application_status(token, app_id, max_wait=120):
    """轮询投递状态直到完成"""
    print(f"\n=== 3. 轮询投递状态（最多等待 {max_wait}秒） ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait:
        response = requests.get(
            f"{BASE_URL}/applications/{app_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()["data"]
            current_status = data["status"]
            
            if current_status != last_status:
                print(f"[{int(time.time() - start_time)}s] 状态变更: {current_status}")
                last_status = current_status
                
                # 显示详细信息
                if current_status == "PARSED" and data.get("resume_json"):
                    print(f"  ✓ 简历解析完成")
                    resume_json = data["resume_json"]
                    if resume_json.get("name"):
                        print(f"    姓名: {resume_json.get('name')}")
                    if resume_json.get("skills"):
                        print(f"    技能: {', '.join(resume_json.get('skills', [])[:5])}")
                
                elif current_status == "SCORED" and data.get("score_json"):
                    print(f"  ✓ 简历评分完成")
                    score_json = data["score_json"]
                    print(f"    总分: {score_json.get('overall_score')}/100")
                    print(f"    教育: {score_json.get('education_score')}/100")
                    print(f"    经验: {score_json.get('experience_score')}/100")
                    print(f"    技能: {score_json.get('skills_score')}/100")
                
                elif current_status == "QUESTIONS_READY" and data.get("questions_json"):
                    print(f"  ✓ 面试题生成完成")
                    questions = data["questions_json"].get("questions", [])
                    print(f"    题目数量: {len(questions)}")
                    if questions:
                        print(f"    示例题目: {questions[0].get('question')[:50]}...")
                    return data
                
                elif current_status == "HUMAN_REVIEW":
                    print(f"  ⚠️ 进入人工审核状态")
                    if data.get("error_detail"):
                        print(f"    错误: {data['error_detail']}")
                    return data
            
            # 如果已经是终态，退出
            if current_status in ["QUESTIONS_READY", "HUMAN_REVIEW", "REJECTED", "NEXT_ROUND"]:
                return data
        
        time.sleep(3)
    
    print(f"⚠️ 超时：{max_wait}秒内未完成")
    return None


def display_final_result(data):
    """显示最终结果"""
    print("\n=== 4. 最终结果汇总 ===")
    print(f"投递ID: {data['id']}")
    print(f"职位: {data['job_title']}")
    print(f"最终状态: {data['status']}")
    
    if data.get("score_json"):
        score_json = data["score_json"]
        print(f"\n评分:")
        print(f"  总分: {score_json.get('overall_score')}/100")
        print(f"  匹配度分析: {score_json.get('match_analysis', '')[:100]}...")
        print(f"  优势: {', '.join(score_json.get('strengths', []))}")
        print(f"  不足: {', '.join(score_json.get('weaknesses', []))}")
    
    if data.get("questions_json"):
        questions = data["questions_json"].get("questions", [])
        print(f"\n面试题（共{len(questions)}道）:")
        for i, q in enumerate(questions[:3], 1):
            print(f"  {i}. [{q.get('category')}] {q.get('question')[:60]}...")


def main():
    """主测试流程"""
    print("=" * 80)
    print("异步任务链端到端测试")
    print("=" * 80)
    
    # 1. 注册和登录
    token = register_and_login()
    if not token:
        print("\n❌ 测试失败：无法获取 Token")
        return
    
    # 2. 创建投递
    app_id = create_application_with_async(token)
    if not app_id:
        print("\n❌ 测试失败：创建投递失败")
        return
    
    # 3. 轮询状态
    final_data = poll_application_status(token, app_id, max_wait=180)
    
    if not final_data:
        print("\n❌ 测试失败：任务未在规定时间内完成")
        return
    
    # 4. 显示结果
    display_final_result(final_data)
    
    print("\n" + "=" * 80)
    if final_data["status"] == "QUESTIONS_READY":
        print("✅ 异步任务链测试通过！")
        print("完整流程：上传简历 → 解析 → 评分 → 生成题包 ✓")
    elif final_data["status"] == "SCORED":
        print("⚠️ 部分完成：简历已评分，但未达标（不生成题包）")
    else:
        print(f"⚠️ 测试未完全通过，最终状态: {final_data['status']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
