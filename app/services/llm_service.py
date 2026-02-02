"""LLM 服务 - 使用阿里云 DashScope API"""
import os
from openai import OpenAI
from typing import Dict, Any, Optional
import json
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

# 初始化 OpenAI 客户端（兼容 DashScope）
client = OpenAI(
    api_key=settings.DASHSCOPE_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 模型配置
MODEL_RESUME_PARSING = "qwen2.5-7b-instruct"  # 简历解析/评分
MODEL_QUESTION_GEN = "qwen2.5-32b-instruct"   # 面试题生成


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def call_llm(
    prompt: str,
    model: str = MODEL_RESUME_PARSING,
    temperature: float = 0.3,
    max_tokens: int = 4000,
    response_format: Optional[dict] = None,
) -> str:
    """
    调用 LLM API
    
    Args:
        prompt: 提示词
        model: 模型名称
        temperature: 温度参数（0-1，越低越确定）
        max_tokens: 最大生成 token 数
        response_format: 响应格式（如 {"type": "json_object"}）
        
    Returns:
        str: LLM 响应内容
        
    Raises:
        Exception: 调用失败时抛出异常
    """
    try:
        logger.info(f"调用 LLM: model={model}, temp={temperature}")
        
        messages = [{"role": "user", "content": prompt}]
        
        # 构建请求参数
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # 如果指定了响应格式（JSON）
        if response_format:
            kwargs["response_format"] = response_format
        
        # 调用 API
        completion = client.chat.completions.create(**kwargs)
        
        response_content = completion.choices[0].message.content
        logger.info(f"LLM 响应成功，长度: {len(response_content)}")
        
        return response_content
        
    except Exception as e:
        logger.error(f"LLM 调用失败: {e}")
        raise Exception(f"LLM 调用失败: {str(e)}")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def call_llm_chat(
    messages: list[dict],
    model: str = "qwen-plus",
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """
    调用 LLM Chat API（支持多轮对话）
    
    Args:
        messages: 对话消息列表，格式如 [{"role": "user", "content": "..."}]
        model: 模型名称
        temperature: 温度参数
        max_tokens: 最大生成 token 数
        
    Returns:
        str: LLM 响应内容
    """
    try:
        logger.info(f"调用 LLM Chat: model={model}, messages={len(messages)}")
        
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        response_content = completion.choices[0].message.content
        logger.info(f"LLM Chat 响应成功，长度: {len(response_content)}")
        
        return response_content
        
    except Exception as e:
        logger.error(f"LLM Chat 调用失败: {e}")
        raise Exception(f"LLM Chat 调用失败: {str(e)}")


def parse_resume(resume_text: str) -> Dict[str, Any]:
    """
    解析简历，提取结构化信息
    
    Args:
        resume_text: 简历文本
        
    Returns:
        dict: 结构化的简历信息
        
    期望返回格式:
    {
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
                "description": "负责电商核心系统开发..."
            }
        ],
        "projects": [
            {
                "name": "分布式任务调度系统",
                "role": "架构设计、核心开发",
                "tech_stack": ["Python", "FastAPI", "Redis", "MySQL"],
                "description": "..."
            }
        ],
        "skills": ["Python", "Java", "Go", "MySQL", "Redis"]
    }
    """
    prompt = f"""你是一个简历解析专家。请仔细阅读以下简历内容，提取并结构化所有关键信息。

简历内容：
{resume_text}

请按照以下 JSON 格式输出结构化的简历信息：

{{
  "name": "候选人姓名",
  "contact": {{
    "email": "邮箱地址",
    "phone": "电话号码"
  }},
  "education": [
    {{
      "school": "学校名称",
      "degree": "学位（本科/硕士/博士）",
      "major": "专业",
      "start_year": 起始年份（数字），
      "end_year": 结束年份（数字），
      "gpa": "GPA（如有）"
    }}
  ],
  "work_experience": [
    {{
      "company": "公司名称",
      "position": "职位",
      "start_date": "开始日期（YYYY-MM格式）",
      "end_date": "结束日期（YYYY-MM或'至今'）",
      "description": "工作内容描述"
    }}
  ],
  "projects": [
    {{
      "name": "项目名称",
      "role": "担任角色",
      "tech_stack": ["技术1", "技术2"],
      "description": "项目描述"
    }}
  ],
  "skills": ["技能1", "技能2", "技能3"]
}}

注意：
1. 只输出 JSON，不要有任何额外的文字
2. 如果某个字段在简历中没有，设为 null 或空数组
3. 确保 JSON 格式正确，可以被解析
4. 尽可能完整地提取所有信息
"""

    try:
        # 调用 LLM
        response = call_llm(
            prompt=prompt,
            model=MODEL_RESUME_PARSING,
            temperature=0.1,  # 低温度保证稳定性
            max_tokens=4000,
        )
        
        # 解析 JSON
        # 尝试提取 JSON（有时 LLM 会在前后加一些说明文字）
        response = response.strip()
        if "```json" in response:
            # 提取 ```json 和 ``` 之间的内容
            start = response.find("```json") + 7
            end = response.rfind("```")
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.rfind("```")
            response = response[start:end].strip()
        
        parsed_data = json.loads(response)
        logger.info("简历解析成功")
        
        return parsed_data
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        logger.error(f"LLM 原始响应: {response}")
        raise Exception(f"简历解析失败：无法解析 LLM 返回的 JSON")
    except Exception as e:
        logger.error(f"简历解析失败: {e}")
        raise


def score_resume(resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    """
    对简历进行评分
    
    Args:
        resume_data: 结构化的简历数据
        job_description: 职位描述（JD）
        
    Returns:
        dict: 评分结果
        
    期望返回格式:
    {
        "overall_score": 85,
        "education_score": 90,
        "experience_score": 80,
        "skills_score": 85,
        "match_analysis": "候选人具备扎实的计算机基础...",
        "strengths": ["教育背景优秀", "技术栈匹配度高"],
        "weaknesses": ["项目经验相对较少"],
        "recommendation": "建议进入面试"
    }
    """
    resume_json = json.dumps(resume_data, ensure_ascii=False, indent=2)
    
    prompt = f"""你是一个专业的招聘评估专家。请根据职位要求，对候选人简历进行全面评分。

职位描述（JD）：
{job_description}

候选人简历（结构化）：
{resume_json}

请按照以下 JSON 格式输出评分结果：

{{
  "overall_score": 总分（0-100），
  "education_score": 教育背景得分（0-100），
  "experience_score": 工作经验得分（0-100），
  "skills_score": 技能匹配度得分（0-100），
  "match_analysis": "简历与职位匹配度的详细分析（200字左右）",
  "strengths": ["优势1", "优势2", "优势3"],
  "weaknesses": ["不足1", "不足2"],
  "recommendation": "推荐建议（是否进入面试、注意事项等）"
}}

评分标准：
- 教育背景：学历、学校、专业的匹配度
- 工作经验：相关工作经验的年限、深度、匹配度
- 技能匹配：技术栈、工具、方法论的匹配情况
- 总分：综合以上因素，考虑候选人的整体竞争力

注意：
1. 只输出 JSON，不要有任何额外的文字
2. 评分要客观公正，有理有据
3. 确保 JSON 格式正确
"""

    try:
        response = call_llm(
            prompt=prompt,
            model=MODEL_RESUME_PARSING,
            temperature=0.2,
            max_tokens=3000,
        )
        
        # 解析 JSON
        response = response.strip()
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.rfind("```")
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.rfind("```")
            response = response[start:end].strip()
        
        score_data = json.loads(response)
        logger.info(f"简历评分成功，总分: {score_data.get('overall_score')}")
        
        return score_data
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        logger.error(f"LLM 原始响应: {response}")
        raise Exception(f"简历评分失败：无法解析 LLM 返回的 JSON")
    except Exception as e:
        logger.error(f"简历评分失败: {e}")
        raise


def generate_interview_questions(
    resume_data: Dict[str, Any],
    job_description: str,
    num_questions: int = 5,
) -> Dict[str, Any]:
    """
    生成面试题目
    
    Args:
        resume_data: 结构化的简历数据
        job_description: 职位描述（JD）
        num_questions: 生成题目数量，默认 5 道
        
    Returns:
        dict: 面试题目列表
        
    期望返回格式:
    {
        "questions": [
            {
                "id": 1,
                "category": "技术基础",
                "question": "请介绍一下 Python 中的装饰器及其应用场景",
                "difficulty": "中等",
                "reference_answer": "装饰器是...",
                "scoring_points": ["理解装饰器原理", "能举例说明应用场景"]
            }
        ]
    }
    """
    resume_json = json.dumps(resume_data, ensure_ascii=False, indent=2)
    
    prompt = f"""你是一个资深的技术面试官。请根据候选人简历和职位要求，设计 {num_questions} 道高质量的面试题目。

职位描述（JD）：
{job_description}

候选人简历（结构化）：
{resume_json}

请按照以下 JSON 格式输出面试题目：

{{
  "questions": [
    {{
      "id": 1,
      "category": "题目类别（技术基础/项目经验/系统设计/算法/场景题等）",
      "question": "具体的题目内容",
      "difficulty": "难度（简单/中等/困难）",
      "reference_answer": "参考答案（150字左右）",
      "scoring_points": ["评分要点1", "评分要点2", "评分要点3"]
    }}
  ]
}}

出题要求：
1. 题目要针对候选人的实际经历，体现在简历中的项目、技能
2. 题目难度要与职位要求匹配，由浅入深
3. 涵盖多个类别：技术基础、项目经验、系统设计、问题解决能力等
4. 题目要有区分度，能够考察候选人的真实水平
5. 参考答案要包含关键点，评分要点要明确
6. 题目要开放性与针对性结合

题目类别分布建议：
- 技术基础：{num_questions // 3} 道
- 项目经验：{num_questions // 3} 道
- 系统设计/场景题：{num_questions - 2 * (num_questions // 3)} 道

注意：
1. 只输出 JSON，不要有任何额外的文字
2. 确保 JSON 格式正确
3. 题目 ID 从 1 开始连续编号
"""

    try:
        response = call_llm(
            prompt=prompt,
            model=MODEL_QUESTION_GEN,  # 使用更强的模型生成题目
            temperature=0.7,  # 适当提高温度增加创造性
            max_tokens=4000,
        )
        
        # 解析 JSON
        response = response.strip()
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.rfind("```")
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.rfind("```")
            response = response[start:end].strip()
        
        questions_data = json.loads(response)
        logger.info(f"面试题生成成功，共 {len(questions_data.get('questions', []))} 道题")
        
        return questions_data
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        logger.error(f"LLM 原始响应: {response}")
        raise Exception(f"面试题生成失败：无法解析 LLM 返回的 JSON")
    except Exception as e:
        logger.error(f"面试题生成失败: {e}")
        raise


class LLMService:
    """LLM服务类（用于对话等场景）"""
    
    async def chat_completion(
        self,
        messages: list[dict],
        model: str = "qwen-plus",
        temperature: float = 0.7
    ) -> str:
        """异步的聊天完成接口"""
        return call_llm_chat(messages, model, temperature)


# 全局实例
llm_service = LLMService()

