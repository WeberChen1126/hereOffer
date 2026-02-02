"""
性能指标测试脚本
测试系统的真实性能指标，用于更新 README.md 中的性能数据

测试指标：
1. 处理能力：
   - 简历解析时间
   - 简历评分时间
   - 题目生成时间
   - 并发处理能力

2. 系统性能：
   - API 响应时间（P95）
   - 数据库查询时间（P95）
   - WebSocket 延迟
   - 文件上传速度
"""

import requests
import time
import statistics
import json
import sys
import io
import asyncio
import websockets
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import os

# 设置输出编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"
# 需要先获取有效的 token，这里使用环境变量或手动设置
TOKEN = os.getenv("TEST_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VyX3R5cGUiOiJhZG1pbiIsImV4cCI6MTc3MDEwMjE4NX0.HsL-Xh40hWJkYAx6xSIc1PnLNsOnG4Tsb5yLLUeIhmU")

if not TOKEN:
    print("警告: 未设置 TEST_TOKEN 环境变量，某些测试可能失败")
    print("请先登录获取 token，然后设置: export TEST_TOKEN=your_token")

headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.results = {}
    
    def record(self, metric_name: str, value: float, unit: str = "ms"):
        """记录指标"""
        if metric_name not in self.results:
            self.results[metric_name] = []
        self.results[metric_name].append({"value": value, "unit": unit})
    
    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """获取统计信息"""
        if metric_name not in self.results or not self.results[metric_name]:
            return {}
        
        values = [r["value"] for r in self.results[metric_name]]
        unit = self.results[metric_name][0]["unit"]
        
        return {
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": statistics.median(values),
            "p95": self._percentile(values, 95),
            "p99": self._percentile(values, 99),
            "unit": unit,
            "count": len(values)
        }
    
    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """计算百分位数"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]
    
    def print_summary(self):
        """打印汇总"""
        print("\n" + "=" * 80)
        print("性能测试结果汇总")
        print("=" * 80)
        
        for metric_name in sorted(self.results.keys()):
            stats = self.get_stats(metric_name)
            if stats:
                print(f"\n{metric_name}:")
                print(f"  测试次数: {stats['count']}")
                print(f"  最小值: {stats['min']:.2f} {stats['unit']}")
                print(f"  最大值: {stats['max']:.2f} {stats['unit']}")
                print(f"  平均值: {stats['avg']:.2f} {stats['unit']}")
                print(f"  中位数: {stats['median']:.2f} {stats['unit']}")
                print(f"  P95: {stats['p95']:.2f} {stats['unit']}")
                print(f"  P99: {stats['p99']:.2f} {stats['unit']}")


metrics = PerformanceMetrics()


def test_resume_parsing_time():
    """测试简历解析时间"""
    print("\n=== 测试简历解析时间 ===")
    
    if not TOKEN:
        print("跳过: 需要 TOKEN")
        return
    
    # 准备测试简历
    resume_text = """姓名：张三
教育背景：
- 2018-2022 清华大学 计算机科学与技术 本科
- 2022-2024 清华大学 计算机科学与技术 硕士

实习经历：
1. 阿里巴巴 - AI 算法 / LLM 应用实习生 (2023.06-2023.12)
   参与大模型应用落地项目，负责 Agent 模块设计与实现

使用 LLM 实现结构化信息抽取与自动问答

编写 Prompt 模板并持续迭代优化

协助搭建模型调用服务与 API 接口

与产品、后端协作推动功能上线

2. 字节跳动 - 算法实习生 (2024.01-2024.06)
   参与推荐系统优化

智能 AI Agent 招聘系统（核心项目）

项目角色：AI Agent 开发负责人
技术栈：Python · FastAPI · LLM · RAG · Multi-Agent

项目简介：
构建一个基于大语言模型的智能招聘系统，通过多 Agent 协作完成简历解析、候选人评估、面试题生成与 AI 问答。

核心工作：

设计 多 Agent 架构，划分为简历解析 Agent、评估 Agent、面试官 Agent

实现 PDF / DOCX / TXT 简历解析，输出结构化 JSON

基于向量数据库构建 RAG 检索系统，提升岗位匹配与问答准确率

使用 Prompt + Schema 约束模型输出，保证结果稳定性

支持企业岗位知识动态接入，Agent 可实时更新上下文

项目成果：

简历解析准确率显著提升

面试题生成更贴合岗位需求

系统支持模块化扩展，便于二次开发
  
技术栈

编程语言：Python（熟练）、JavaScript / TypeScript

大模型 & Agent：

OpenAI / Qwen / ChatGLM

LangChain、AgentOpera、多 Agent 架构

RAG & 向量检索：

FAISS、Milvus、Chroma

文档切分、Embedding、Rerank

后端 & 工程化：

FastAPI、Docker、Docker Compose

GitHub Actions、Kubernetes（基础）

数据处理：

PDF / Word / TXT 解析

JSON Schema、结构化输出

数据库：MySQL、Redis、向量数据库

其他：Prompt Engineering、LLM 微调（LoRA 基础）r"""
    
    # 测试 3 次取平均值
    times = []
    for i in range(3):
        print(f"  第 {i+1} 次测试...")
        try:
            start_time = time.time()
            # 创建临时文件对象
            from io import BytesIO
            file_obj = BytesIO(resume_text.encode('utf-8'))
            response = requests.post(
                f"{BASE_URL}/debug/parse_resume",
                headers=headers,
                files={"file": ("resume.txt", file_obj, "text/plain")},
                data={"file_type": "txt"},
                timeout=120
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                times.append(elapsed)
                metrics.record("简历解析时间", elapsed * 1000, "ms")
                print(f"  ✓ 成功，耗时: {elapsed:.2f} 秒")
            else:
                print(f"  ✗ 失败: {response.status_code}")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
    
    if times:
        avg_time = statistics.mean(times)
        print(f"\n简历解析平均时间: {avg_time:.2f} 秒 ({avg_time*1000:.0f} ms)")


def test_resume_scoring_time():
    """测试简历评分时间"""
    print("\n=== 测试简历评分时间 ===")
    
    if not TOKEN:
        print("跳过: 需要 TOKEN")
        return
    
    # 准备测试数据
    resume_data = {
        "name": "张三",
        "contact": {"email": "test@example.com", "phone": "138-0000-0000"},
        "education": [{"school": "清华大学", "degree": "硕士", "major": "计算机科学"}],
        "work_experience": [{"company": "阿里巴巴", "position": "后端开发"}],
        "skills": ["Python", "FastAPI", "MySQL"]
    }
    
    job_description = """高级后端工程师
要求：本科及以上，3年以上经验，熟悉 Python/FastAPI"""
    
    # 测试 3 次取平均值
    times = []
    for i in range(3):
        print(f"  第 {i+1} 次测试...")
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/debug/score_resume",
                headers=headers,
                json={"resume_data": resume_data, "job_description": job_description},
                timeout=120
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                times.append(elapsed)
                metrics.record("简历评分时间", elapsed * 1000, "ms")
                print(f"  ✓ 成功，耗时: {elapsed:.2f} 秒")
            else:
                print(f"  ✗ 失败: {response.status_code}")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
    
    if times:
        avg_time = statistics.mean(times)
        print(f"\n简历评分平均时间: {avg_time:.2f} 秒 ({avg_time*1000:.0f} ms)")


def test_question_generation_time():
    """测试题目生成时间"""
    print("\n=== 测试题目生成时间 ===")
    
    if not TOKEN:
        print("跳过: 需要 TOKEN")
        return
    
    # 准备测试数据
    resume_data = {
        "name": "张三",
        "education": [{"school": "清华大学", "degree": "硕士"}],
        "work_experience": [{"company": "阿里巴巴", "position": "后端开发"}],
        "skills": ["Python", "FastAPI"]
    }
    
    job_description = "高级后端工程师"
    
    # 测试 3 次取平均值
    times = []
    for i in range(3):
        print(f"  第 {i+1} 次测试...")
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/debug/generate_questions",
                headers=headers,
                json={
                    "resume_data": resume_data,
                    "job_description": job_description,
                    "num_questions": 5
                },
                timeout=180
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                times.append(elapsed)
                metrics.record("题目生成时间", elapsed * 1000, "ms")
                print(f"  ✓ 成功，耗时: {elapsed:.2f} 秒")
            else:
                print(f"  ✗ 失败: {response.status_code}")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
    
    if times:
        avg_time = statistics.mean(times)
        print(f"\n题目生成平均时间: {avg_time:.2f} 秒 ({avg_time*1000:.0f} ms)")


def test_api_response_time():
    """测试 API 响应时间（P95）"""
    print("\n=== 测试 API 响应时间 ===")
    
    # 测试不需要认证的端点
    endpoints = [
        ("/healthz", "GET", None),
    ]
    
    # 每个端点测试 20 次
    for endpoint, method, data in endpoints:
        print(f"\n测试端点: {method} {endpoint}")
        times = []
        
        for i in range(20):
            try:
                start_time = time.time()
                if method == "GET":
                    response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
                elapsed = (time.time() - start_time) * 1000  # 转换为毫秒
                
                if response.status_code < 500:  # 忽略服务器错误
                    times.append(elapsed)
                    metrics.record("API响应时间", elapsed, "ms")
                    if i % 5 == 0:
                        print(f"  请求 {i+1}/20: {elapsed:.2f} ms")
            except Exception as e:
                print(f"  请求 {i+1} 失败: {e}")
        
        if times:
            p95 = metrics._percentile(times, 95)
            avg = statistics.mean(times)
            print(f"  平均响应时间: {avg:.2f} ms")
            print(f"  P95 响应时间: {p95:.2f} ms")
    
    # 如果有 TOKEN，测试需要认证的端点
    if TOKEN:
        endpoints_auth = [
            ("/jobs", "GET", None),
        ]
        
        for endpoint, method, data in endpoints_auth:
            print(f"\n测试端点（需认证）: {method} {endpoint}")
            times = []
            
            for i in range(20):
                try:
                    start_time = time.time()
                    if method == "GET":
                        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
                    else:
                        response = requests.post(f"{BASE_URL}{endpoint}", headers=headers, json=data, timeout=10)
                    elapsed = (time.time() - start_time) * 1000
                    
                    if response.status_code < 500:
                        times.append(elapsed)
                        metrics.record("API响应时间", elapsed, "ms")
                except Exception as e:
                    print(f"  请求 {i+1} 失败: {e}")
            
            if times:
                p95 = metrics._percentile(times, 95)
                avg = statistics.mean(times)
                print(f"  平均响应时间: {avg:.2f} ms")
                print(f"  P95 响应时间: {p95:.2f} ms")


def test_database_query_time():
    """测试数据库查询时间（P95）"""
    print("\n=== 测试数据库查询时间 ===")
    
    if not TOKEN:
        print("跳过: 需要 TOKEN（数据库查询需要认证）")
        return
    
    # 测试需要数据库查询的端点
    endpoints = [
        ("/jobs", "GET"),
        ("/applications", "GET"),
    ]
    
    for endpoint, method in endpoints:
        print(f"\n测试端点: {method} {endpoint}")
        times = []
        
        for i in range(20):
            try:
                start_time = time.time()
                if method == "GET":
                    response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
                elapsed = (time.time() - start_time) * 1000  # 转换为毫秒
                
                if response.status_code == 200:
                    times.append(elapsed)
                    metrics.record("数据库查询时间", elapsed, "ms")
                    if i % 5 == 0:
                        print(f"  请求 {i+1}/20: {elapsed:.2f} ms")
            except Exception as e:
                print(f"  请求 {i+1} 失败: {e}")
        
        if times:
            p95 = metrics._percentile(times, 95)
            avg = statistics.mean(times)
            print(f"  平均查询时间: {avg:.2f} ms")
            print(f"  P95 查询时间: {p95:.2f} ms")


def test_file_upload_speed():
    """测试文件上传速度"""
    print("\n=== 测试文件上传速度 ===")
    
    if not TOKEN:
        print("跳过: 需要 TOKEN")
        return
    
    # 创建不同大小的测试文件
    file_sizes = [1024 * 1024, 5 * 1024 * 1024, 10 * 1024 * 1024]  # 1MB, 5MB, 10MB
    
    for size in file_sizes:
        print(f"\n测试文件大小: {size / 1024 / 1024:.1f} MB")
        
        # 创建测试文件内容
        file_content = b"0" * size
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/debug/upload_file",
                headers=headers,
                files={"file": ("test.txt", file_content, "text/plain")},
                data={"application_id": 1},
                timeout=60
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                speed_mbps = (size / 1024 / 1024) / elapsed
                metrics.record("文件上传速度", speed_mbps, "MB/s")
                print(f"  ✓ 上传成功，耗时: {elapsed:.2f} 秒")
                print(f"  上传速度: {speed_mbps:.2f} MB/s")
            else:
                print(f"  ✗ 上传失败: {response.status_code}")
        except Exception as e:
            print(f"  ✗ 错误: {e}")


async def test_websocket_latency():
    """测试 WebSocket 延迟"""
    print("\n=== 测试 WebSocket 延迟 ===")
    
    if not TOKEN:
        print("跳过: 需要 TOKEN")
        return
    
    # 需要先创建会话
    try:
        # 创建会话
        session_response = requests.post(
            f"{BASE_URL}/chat/sessions",
            headers=headers,
            json={"session_type": "text"},
            timeout=10
        )
        
        if session_response.status_code != 200:
            print(f"跳过: 无法创建会话 ({session_response.status_code})")
            return
        
        session_id = session_response.json()["data"]["id"]
        print(f"创建会话成功: session_id={session_id}")
        
        # 连接 WebSocket
        uri = f"ws://localhost:8000/ws/chat/{session_id}?token={TOKEN}"
        
        latencies = []
        for i in range(10):
            try:
                async with websockets.connect(uri) as websocket:
                    # 发送消息
                    send_time = time.time()
                    await websocket.send(json.dumps({
                        "type": "text",
                        "content": "测试消息"
                    }))
                    
                    # 接收响应
                    response = await websocket.recv()
                    receive_time = time.time()
                    
                    latency = (receive_time - send_time) * 1000  # 转换为毫秒
                    latencies.append(latency)
                    metrics.record("WebSocket延迟", latency, "ms")
                    print(f"  第 {i+1} 次: {latency:.2f} ms")
                    
                    # 等待一下再发送下一条
                    await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  第 {i+1} 次失败: {e}")
        
        if latencies:
            avg_latency = statistics.mean(latencies)
            p95_latency = metrics._percentile(latencies, 95)
            print(f"\n平均延迟: {avg_latency:.2f} ms")
            print(f"P95 延迟: {p95_latency:.2f} ms")
    
    except Exception as e:
        print(f"WebSocket 测试失败: {e}")


def main():
    """主测试流程"""
    print("=" * 80)
    print("性能指标测试")
    print("=" * 80)
    print("\n注意: 某些测试需要有效的 TOKEN 和运行中的服务")
    print("请确保:")
    print("1. API 服务运行在 http://localhost:8000")
    print("2. 设置了 TEST_TOKEN 环境变量")
    print("3. Worker 服务正在运行（用于异步任务测试）")
    print("\n开始测试...\n")
    
    # 1. 处理能力测试
    print("\n" + "=" * 80)
    print("处理能力测试")
    print("=" * 80)
    test_resume_parsing_time()
    test_resume_scoring_time()
    test_question_generation_time()
    
    # 2. 系统性能测试
    print("\n" + "=" * 80)
    print("系统性能测试")
    print("=" * 80)
    test_api_response_time()
    test_database_query_time()
    test_file_upload_speed()
    
    # WebSocket 测试（异步）
    try:
        asyncio.run(test_websocket_latency())
    except Exception as e:
        print(f"WebSocket 测试跳过: {e}")
    
    # 打印汇总
    metrics.print_summary()
    
    # 生成 README 更新建议
    print("\n" + "=" * 80)
    print("README.md 更新建议")
    print("=" * 80)
    
    # 简历解析
    parse_stats = metrics.get_stats("简历解析时间")
    if parse_stats:
        avg_sec = parse_stats["avg"] / 1000
        print(f"\n简历解析：{avg_sec:.0f} 秒/份（LLM）")
    
    # 简历评分
    score_stats = metrics.get_stats("简历评分时间")
    if score_stats:
        avg_sec = score_stats["avg"] / 1000
        print(f"简历评分：{avg_sec:.0f} 秒/份（LLM）")
    
    # 题目生成
    question_stats = metrics.get_stats("题目生成时间")
    if question_stats:
        avg_sec = question_stats["avg"] / 1000
        print(f"题目生成：{avg_sec:.0f} 秒/份（LLM）")
    
    # API 响应
    api_stats = metrics.get_stats("API响应时间")
    if api_stats:
        p95_ms = api_stats["p95"]
        print(f"\nAPI 响应：< {p95_ms:.0f}ms（P95）")
    
    # 数据库查询
    db_stats = metrics.get_stats("数据库查询时间")
    if db_stats:
        p95_ms = db_stats["p95"]
        print(f"数据库查询：< {p95_ms:.0f}ms（P95）")
    
    # WebSocket 延迟
    ws_stats = metrics.get_stats("WebSocket延迟")
    if ws_stats:
        p95_ms = ws_stats["p95"]
        print(f"WebSocket 延迟：< {p95_ms:.0f}ms")
    
    # 文件上传
    upload_stats = metrics.get_stats("文件上传速度")
    if upload_stats:
        avg_speed = upload_stats["avg"]
        print(f"文件上传：{avg_speed:.1f}MB/秒+")


if __name__ == "__main__":
    main()
