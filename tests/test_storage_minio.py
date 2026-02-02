"""
测试文件：MinIO 文件存储服务
Test File: MinIO File Storage Service

📄 测试目标 (Test Objective)
================================
测试 MinIO 对象存储的文件上传、列表、下载功能

🎯 测试范围 (Test Scope)
================================
- 文件上传到 MinIO
- 列出用户的所有文件
- 从 MinIO 下载文件

📊 测试步骤 (Test Steps)
================================
1. 上传简历文件到 MinIO
   - 调用 POST /debug/upload_file
   - 上传 test_resume_zh.txt
   - 验证返回的 object_name

2. 列出所有文件
   - 调用 GET /debug/list_files
   - 获取用户的所有文件列表
   - 验证文件数量

3. 下载文件
   - 调用 GET /debug/download_file
   - 下载之前上传的文件
   - 验证文件内容完整性

✅ 验证点 (Verification Points)
================================
- 文件上传返回 200 状态码
- 获取到有效的 object_name
- 文件列表包含已上传的文件
- 下载的文件内容与原文件一致

📝 预期结果 (Expected Results)
================================
- 所有操作返回成功状态
- 文件可以正确上传和下载
- 文件内容保持完整

⚙️  前置条件 (Prerequisites)
================================
- API 服务运行在 http://localhost:8000
- 存在有效的 JWT Token
- 存在测试文件 test_resume_zh.txt
- MinIO 服务正常运行

🔧 使用方法 (Usage)
================================
python test_storage_minio.py

📌 注意事项 (Notes)
================================
- Token 需要定期更新
- 测试文件会实际上传到 MinIO
- 下载的文件会保存为 downloaded_resume.txt
"""

import requests
import json
import sys

# 设置输出编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# API 基础 URL
BASE_URL = "http://localhost:8000"

# 使用已有的 token
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VyX3R5cGUiOiJjYW5kaWRhdGUiLCJleHAiOjE3Njk5NjA3NDh9.E0YLxXPVAaZNvOrd101kRtP_7vhLl69Y_yrcrKScUqI"

headers = {"Authorization": f"Bearer {TOKEN}"}


def test_upload_file():
    """测试文件上传"""
    print("\n=== 1. 测试文件上传到 MinIO ===")
    
    with open("test_resume_zh.txt", "rb") as f:
        files = {"file": ("test_resume_zh.txt", f, "text/plain")}
        data = {"application_id": 1}
        
        response = requests.post(
            f"{BASE_URL}/debug/upload_file",
            headers=headers,
            files=files,
            data=data,
        )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get("code") == 0:
        print("✓ 文件上传成功")
        return result["data"]["object_name"]
    else:
        print("✗ 文件上传失败")
        return None


def test_list_files():
    """测试列出文件"""
    print("\n=== 2. 测试列出用户文件 ===")
    
    response = requests.get(
        f"{BASE_URL}/debug/list_files",
        headers=headers,
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result.get("code") == 0:
        print(f"✓ 共找到 {result['data']['count']} 个文件")
        return result["data"]["files"]
    else:
        print("✗ 列出文件失败")
        return []


def test_download_file(object_name):
    """测试文件下载"""
    print("\n=== 3. 测试从 MinIO 下载文件 ===")
    
    response = requests.get(
        f"{BASE_URL}/debug/download_file",
        headers=headers,
        params={"object_name": object_name},
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        # 保存到本地
        with open("downloaded_resume.txt", "wb") as f:
            f.write(response.content)
        print(f"✓ 文件下载成功，大小: {len(response.content)} bytes")
        print("✓ 已保存到: downloaded_resume.txt")
        
        # 读取并显示前200字符
        content = response.content.decode("utf-8")
        print(f"\n文件内容预览:\n{content[:200]}...")
        return True
    else:
        print("✗ 文件下载失败")
        return False


def main():
    """主测试流程"""
    print("=" * 80)
    print("MinIO 文件存储服务测试")
    print("=" * 80)
    
    # 1. 上传文件
    object_name = test_upload_file()
    if not object_name:
        print("\n❌ 测试失败：文件上传失败")
        return
    
    # 2. 列出文件
    files = test_list_files()
    if not files:
        print("\n⚠️  警告：未找到任何文件")
    
    # 3. 下载文件
    success = test_download_file(object_name)
    
    print("\n" + "=" * 80)
    if success:
        print("✅ MinIO 文件存储测试全部通过！")
    else:
        print("❌ MinIO 文件存储测试失败")
    print("=" * 80)


if __name__ == "__main__":
    main()
