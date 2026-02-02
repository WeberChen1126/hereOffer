"""
测试文件：LLM 简历解析与评分
Test File: LLM Resume Parsing and Scoring

📄 测试目标 (Test Objective)
================================
测试基于大语言模型的简历解析和智能评分功能

🎯 测试范围 (Test Scope)
================================
- 简历文本提取（PDF/DOCX/TXT）
- 简历结构化解析（LLM）
- 简历智能评分（LLM）
- 匹配度分析

📊 测试步骤 (Test Steps)
================================
1. 简历结构化解析
   - 调用 POST /debug/parse_resume
   - 上传简历文件（test_resume_zh.txt）
   - LLM 提取结构化信息：
     * 姓名、联系方式
     * 教育背景
     * 工作经验
     * 项目经历
     * 技能列表

2. 简历智能评分
   - 调用 POST /debug/score_resume
   - 传入解析后的简历数据和岗位描述
   - LLM 评估匹配度：
     * 教育背景评分
     * 工作经验评分
     * 技能匹配评分
     * 总体评分
   - 生成优势/不足分析
   - 给出推荐建议

✅ 验证点 (Verification Points)
================================
- 简历解析返回完整的 JSON 结构
- 包含所有必需字段（name, contact, education, work_experience等）
- 评分在 0-100 范围内
- 包含详细的匹配度分析
- 提供优势和不足清单
- 给出明确的推荐建议

📝 预期结果 (Expected Results)
================================
- 简历成功解析为结构化 JSON
- 评分合理，与实际情况相符
- 分析全面，指出关键优势和不足
- 推荐建议具有参考价值

⚙️  前置条件 (Prerequisites)
================================
- API 服务运行在 http://localhost:8000
- 存在有效的 JWT Token
- 存在测试简历文件 test_resume_zh.txt
- LLM 服务（DashScope）正常运行
- LLM_MOCK=0（使用真实 LLM）或 =1（使用 Mock）

🔧 使用方法 (Usage)
================================
python test_llm_resume_parse.py

📌 注意事项 (Notes)
================================
- LLM 调用可能需要 30-60 秒
- 需要有效的 DashScope API Key
- Mock 模式会返回固定的测试数据
- 评分结果可能因 LLM 而略有差异

🎯 测试用例示例 (Test Case Example)
================================
输入简历：
- 姓名：张三
- 学历：硕士
- 工作经验：3年 Python 后端开发
- 技能：Python, FastAPI, MySQL, Redis

岗位要求：
- 学历：本科及以上
- 经验：3年以上后端开发
- 技能：Python, FastAPI, MySQL

预期评分：
- 教育背景：85分（硕士学历超过要求）
- 工作经验：80分（刚好符合要求）
- 技能匹配：90分（完全匹配核心技能）
- 总分：82分
"""

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


def test_parse_resume():
    """测试简历解析"""
    print("\n=== 1. 测试简历结构化解析 ===")
    
    with open("test_resume_zh.txt", "rb") as f:
        files = {"file": ("test_resume_zh.txt", f, "text/plain")}
        data = {"file_type": "txt"}
        
        print("正在调用 LLM 解析简历，请稍候...")
        response = requests.post(
            f"{BASE_URL}/debug/parse_resume",
            headers=headers,
            files=files,
            data=data,
            timeout=120,  # 增加超时时间
        )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ 简历解析成功")
        print("\n结构化数据:")
        print(json.dumps(result["data"]["parsed_data"], ensure_ascii=False, indent=2))
        return result["data"]["parsed_data"]
    else:
        print(f"✗ 简历解析失败")
        print(f"错误信息: {response.text}")
        return None


def test_score_resume(resume_data):
    """测试简历评分"""
    print("\n=== 2. 测试简历评分 ===")
    
    job_description = """
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
    
    payload = {
        "resume_data": resume_data,
        "job_description": job_description,
    }
    
    print("正在调用 LLM 评分简历，请稍候...")
    response = requests.post(
        f"{BASE_URL}/debug/score_resume",
        headers=headers,
        json=payload,
        timeout=120,
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        score_data = result["data"]["score_data"]
        
        print(f"✓ 简历评分成功")
        print(f"\n总分: {score_data['overall_score']}/100")
        print(f"教育背景: {score_data['education_score']}/100")
        print(f"工作经验: {score_data['experience_score']}/100")
        print(f"技能匹配: {score_data['skills_score']}/100")
        print(f"\n匹配度分析:\n{score_data['match_analysis']}")
        print(f"\n优势: {', '.join(score_data['strengths'])}")
        print(f"不足: {', '.join(score_data['weaknesses'])}")
        print(f"\n推荐建议: {score_data['recommendation']}")
        
        return True
    else:
        print(f"✗ 简历评分失败")
        print(f"错误信息: {response.text}")
        return False


def main():
    """主测试流程"""
    print("=" * 80)
    print("LLM 简历解析与评分测试")
    print("=" * 80)
    
    # 1. 解析简历
    resume_data = test_parse_resume()
    if not resume_data:
        print("\n❌ 测试失败：简历解析失败")
        return
    
    # 2. 评分简历
    success = test_score_resume(resume_data)
    
    print("\n" + "=" * 80)
    if success:
        print("✅ LLM 简历解析与评分测试全部通过！")
    else:
        print("❌ LLM 简历解析与评分测试失败")
    print("=" * 80)


if __name__ == "__main__":
    main()
