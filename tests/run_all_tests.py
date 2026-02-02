"""
hereOffer 测试套件运行脚本
Test Suite Runner

自动运行所有测试并生成报告
"""

import subprocess
import sys
import time
from datetime import datetime

# 配置输出编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class TestRunner:
    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None
    
    def run_test(self, test_file, test_name, description):
        """运行单个测试"""
        print("\n" + "="*80)
        print(f"🧪 运行测试: {test_name}")
        print(f"📝 描述: {description}")
        print("="*80)
        
        start = time.time()
        try:
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                encoding='utf-8',
                errors='replace'
            )
            duration = time.time() - start
            
            success = result.returncode == 0
            self.results.append({
                'name': test_name,
                'description': description,
                'success': success,
                'duration': duration,
                'output': result.stdout if success else result.stderr
            })
            
            if success:
                print(f"✅ {test_name} 通过 ({duration:.2f}秒)")
            else:
                print(f"❌ {test_name} 失败 ({duration:.2f}秒)")
                print(f"错误信息:\n{result.stderr}")
            
            return success
        
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            print(f"⏱️  {test_name} 超时 ({duration:.2f}秒)")
            self.results.append({
                'name': test_name,
                'description': description,
                'success': False,
                'duration': duration,
                'output': 'Test timeout after 300 seconds'
            })
            return False
        
        except Exception as e:
            duration = time.time() - start
            print(f"💥 {test_name} 异常: {e}")
            self.results.append({
                'name': test_name,
                'description': description,
                'success': False,
                'duration': duration,
                'output': str(e)
            })
            return False
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*80)
        print("📊 测试总结")
        print("="*80)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['success'])
        failed = total - passed
        
        print(f"\n总测试数: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"成功率: {(passed/total*100):.1f}%")
        
        total_time = self.end_time - self.start_time
        print(f"\n总耗时: {total_time:.2f}秒")
        
        print("\n详细结果:")
        for i, result in enumerate(self.results, 1):
            status = "✅" if result['success'] else "❌"
            print(f"{i}. {status} {result['name']} - {result['duration']:.2f}秒")
            print(f"   {result['description']}")
        
        return passed == total


def main():
    """主测试流程"""
    print("="*80)
    print("🚀 hereOffer 自动化测试套件")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    runner = TestRunner()
    runner.start_time = time.time()
    
    # 定义测试列表
    tests = [
        {
            'file': 'test_storage_minio.py',
            'name': 'MinIO 文件存储',
            'description': '测试文件上传、下载、列表功能'
        },
        {
            'file': 'test_llm_resume_parse.py',
            'name': 'LLM 简历解析',
            'description': '测试简历结构化解析和智能评分'
        },
        {
            'file': 'test_llm_questions_gen.py',
            'name': 'LLM 题目生成',
            'description': '测试个性化面试题目生成'
        },
        {
            'file': 'test_api_applications.py',
            'name': '投递管理 API',
            'description': '测试候选人投递创建和管理'
        },
        {
            'file': 'test_api_jobs.py',
            'name': '岗位管理 API',
            'description': '测试岗位 CRUD 和题库管理'
        },
        {
            'file': 'test_api_admin_applications.py',
            'name': 'Admin 投递管理',
            'description': '测试管理员投递查询、筛选、统计'
        },
        {
            'file': 'test_api_chat_realtime.py',
            'name': '实时对话',
            'description': '测试 HTTP/WebSocket 对话和语音交互'
        },
        {
            'file': 'test_integration_async_chain.py',
            'name': '异步任务链',
            'description': '测试简历处理完整流程'
        },
    ]
    
    # 运行所有测试
    for test in tests:
        runner.run_test(test['file'], test['name'], test['description'])
        time.sleep(2)  # 测试间隔
    
    runner.end_time = time.time()
    
    # 打印总结
    all_passed = runner.print_summary()
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败，请检查日志")
    print("="*80)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 返回退出码
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 测试运行器异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
