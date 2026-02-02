"""T09 面试题目生成测试"""
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


# 使用已有的简历数据（来自 T07 测试）
RESUME_DATA = {
    "name": "张三",
    "contact": {
        "email": "zhangsan@example.com",
        "phone": "138-0000-0000"
    },
    "education": [
        {
            "school": "清华大学",
            "degree": "硕士",
            "major": "计算机科学",
            "start_year": 2022,
            "end_year": 2024,
            "gpa": "3.9/4.0"
        }
    ],
    "work_experience": [
        {
            "company": "阿里巴巴",
            "position": "高级后端工程师",
            "start_date": "2024-06",
            "end_date": "至今",
            "description": "负责电商核心系统开发，优化系统性能"
        }
    ],
    "projects": [
        {
            "name": "分布式任务调度系统",
            "role": "架构设计、核心开发",
            "tech_stack": ["Python", "FastAPI", "Redis", "MySQL"],
            "description": "设计并实现了一个高性能的分布式任务调度系统"
        }
    ],
    "skills": ["Python", "Java", "FastAPI", "MySQL", "Redis", "Docker"]
}

JOB_DESCRIPTION = """
职位：高级后端工程师

职位要求：
1. 本科及以上学历，计算机相关专业
2. 3年以上后端开发经验，熟练掌握 Python 或 Java
3. 熟悉 FastAPI、Spring Boot 等主流框架
4. 熟悉 MySQL、Redis 等数据库和缓存技术
5. 有分布式系统、微服务架构经验优先
6. 有大厂背景优先

工作内容：
- 负责核心业务系统的设计和开发
- 参与系统架构设计和技术选型
- 优化系统性能，保证服务稳定性
"""


def test_generate_questions():
    """测试面试题生成"""
    print("\n=== 测试面试题目生成 ===")
    
    payload = {
        "resume_data": RESUME_DATA,
        "job_description": JOB_DESCRIPTION,
        "num_questions": 5,
    }
    
    print("正在调用 LLM 生成面试题目，请稍候...")
    print(f"生成题目数量: {payload['num_questions']}")
    
    response = requests.post(
        f"{BASE_URL}/debug/generate_questions",
        headers=headers,
        json=payload,
        timeout=120,
    )
    
    print(f"\n状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        questions = result["data"]["questions_data"]["questions"]
        
        print(f"✓ 面试题生成成功，共 {len(questions)} 道题目")
        print("\n" + "=" * 80)
        
        for q in questions:
            print(f"\n【题目 {q['id']}】类别: {q['category']} | 难度: {q['difficulty']}")
            print(f"\n问题: {q['question']}")
            print(f"\n参考答案:\n{q['reference_answer']}")
            print(f"\n评分要点:")
            for point in q['scoring_points']:
                print(f"  - {point}")
            print("\n" + "-" * 80)
        
        return True
    else:
        print(f"✗ 面试题生成失败")
        print(f"错误信息: {response.text}")
        return False


def main():
    """主测试流程"""
    print("=" * 80)
    print("T09: 面试题目生成自动化测试")
    print("=" * 80)
    
    success = test_generate_questions()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ T09 测试通过！")
    else:
        print("❌ T09 测试失败")
    print("=" * 80)


if __name__ == "__main__":
    main()
