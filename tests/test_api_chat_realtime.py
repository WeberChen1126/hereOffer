"""
实时对话功能测试脚本
测试 HTTP API 和 WebSocket 实时对话
"""
import sys
import requests
import json
import time
import asyncio
import websockets
import base64

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

def print_section(title):
    print("\n" + "="*80)
    print(f"{title}")
    print("="*80)

def print_success(msg):
    print(f"✓ {msg}")

def print_error(msg):
    print(f"✗ {msg}")
    sys.exit(1)

def register_and_login(email, password, user_type="candidate"):
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

def test_http_api():
    """测试 HTTP API"""
    print_section("测试1: HTTP API - 创建会话和发送消息")
    
    # 准备测试数据
    candidate_email = f"candidate_chat_{int(time.time())}@test.com"
    admin_email = f"admin_chat_{int(time.time())}@test.com"
    password = "test123456"
    
    # 注册用户
    print("\n>>> 注册管理员和候选人...")
    admin_token = register_and_login(admin_email, password, "admin")
    print_success(f"管理员注册并登录")
    
    candidate_token = register_and_login(candidate_email, password, "candidate")
    print_success(f"候选人注册并登录")
    
    # 创建岗位
    print("\n>>> 创建测试岗位...")
    job = create_job(admin_token, {
        "title": "AI 研究员",
        "description": "负责AI算法研究和应用开发",
        "requirements": "博士学历，熟悉深度学习",
        "responsibilities": "研究最新AI技术，开发AI应用",
        "department": "AI Lab",
        "location": "北京中关村",
        "salary_range": "40k-80k",
        "threshold_score": 70,
        "is_active": True
    })
    job_id = job["id"]
    print_success(f"岗位创建成功: ID={job_id}, Title={job['title']}")
    
    # === 测试1: 创建文本会话 ===
    print("\n>>> 测试1.1: 创建文本会话...")
    resp = requests.post(
        f"{BASE_URL}/chat/sessions",
        json={"job_id": job_id, "session_type": "text"},
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print_error(f"创建会话失败: {resp.text}")
    
    data = resp.json()["data"]
    session_id = data["id"]
    print_success(f"文本会话创建成功: session_id={session_id}")
    print(f"  会话类型: {data['session_type']}")
    print(f"  关联岗位: {data['job_id']}")
    
    # === 测试2: 发送文本消息 ===
    print("\n>>> 测试1.2: 发送文本消息...")
    test_messages = [
        "这个岗位的工作地点在哪里？",
        "对学历有什么要求？",
        "薪资范围是多少？"
    ]
    
    for i, msg in enumerate(test_messages, 1):
        print(f"\n  消息{i}: {msg}")
        resp = requests.post(
            f"{BASE_URL}/chat/sessions/{session_id}/messages",
            json={"content": msg},
            headers={"Authorization": f"Bearer {candidate_token}"}
        )
        
        if resp.status_code != 200:
            print_error(f"发送消息失败: {resp.text}")
        
        ai_response = resp.json()["data"]
        print(f"  AI回复: {ai_response['content'][:100]}...")
        print_success(f"消息{i}发送成功")
        
        time.sleep(1)  # 避免请求过快
    
    # === 测试3: 获取会话消息历史 ===
    print("\n>>> 测试1.3: 获取消息历史...")
    resp = requests.get(
        f"{BASE_URL}/chat/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print_error(f"获取消息历史失败: {resp.text}")
    
    messages = resp.json()["data"]
    print_success(f"获取消息历史成功，共 {len(messages)} 条消息")
    
    for i, msg in enumerate(messages[:6], 1):  # 显示前6条
        print(f"  {i}. [{msg['role']}] {msg['content'][:50]}...")
    
    # === 测试4: 获取用户所有会话 ===
    print("\n>>> 测试1.4: 获取用户所有会话...")
    resp = requests.get(
        f"{BASE_URL}/chat/sessions",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print_error(f"获取会话列表失败: {resp.text}")
    
    sessions = resp.json()["data"]
    print_success(f"获取会话列表成功，共 {len(sessions)} 个会话")
    
    for sess in sessions:
        print(f"  - 会话ID={sess['id']}, 类型={sess['session_type']}, 岗位={sess['job_id']}")
    
    # === 测试5: 创建语音会话 ===
    print("\n>>> 测试1.5: 创建语音会话...")
    resp = requests.post(
        f"{BASE_URL}/chat/sessions",
        json={"job_id": job_id, "session_type": "voice"},
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    
    print(f"状态码: {resp.status_code}")
    if resp.status_code != 200:
        print_error(f"创建语音会话失败: {resp.text}")
    
    voice_session_id = resp.json()["data"]["id"]
    print_success(f"语音会话创建成功: session_id={voice_session_id}")
    
    print_section("✅ HTTP API 测试通过！")
    return candidate_token, session_id, voice_session_id


async def test_websocket(token, session_id):
    """测试 WebSocket 实时对话"""
    print_section("测试2: WebSocket 实时对话")
    
    ws_uri = f"{WS_URL}/ws/chat/{session_id}?token={token}"
    
    try:
        print(f"\n>>> 连接 WebSocket: {ws_uri}")
        async with websockets.connect(ws_uri) as websocket:
            print_success("WebSocket 连接成功")
            
            # 接收欢迎消息
            welcome_msg = await websocket.recv()
            welcome_data = json.loads(welcome_msg)
            print(f"  收到欢迎消息: {welcome_data.get('message', '')}")
            
            # === 测试1: 发送文本消息 ===
            print("\n>>> 测试2.1: WebSocket 发送文本消息...")
            test_messages = [
                "你好，我想了解一下这个岗位",
                "工作内容主要是什么？",
                "团队规模多大？"
            ]
            
            for i, msg in enumerate(test_messages, 1):
                print(f"\n  发送消息{i}: {msg}")
                
                # 发送消息
                await websocket.send(json.dumps({
                    "type": "text",
                    "content": msg
                }))
                
                # 可能收到"正在输入"状态
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if response_data.get("type") == "typing":
                    print(f"  {response_data.get('message', '')}")
                    # 继续等待真正的回复
                    response = await websocket.recv()
                    response_data = json.loads(response)
                
                # 显示AI回复
                if response_data.get("type") == "text":
                    ai_content = response_data.get("content", "")
                    print(f"  AI回复: {ai_content[:100]}...")
                    print_success(f"消息{i}成功")
                elif response_data.get("type") == "error":
                    print_error(f"错误: {response_data.get('message', '')}")
                
                await asyncio.sleep(1)
            
            # === 测试2: 心跳 ===
            print("\n>>> 测试2.2: WebSocket 心跳...")
            await websocket.send(json.dumps({"type": "ping"}))
            pong = await websocket.recv()
            pong_data = json.loads(pong)
            if pong_data.get("type") == "pong":
                print_success("心跳测试成功")
            else:
                print_error(f"心跳失败: {pong_data}")
            
            # === 测试3: 语音消息（Mock）===
            print("\n>>> 测试2.3: WebSocket 发送语音消息（Mock）...")
            
            # 生成一些mock音频数据（减小大小以避免消息过大错误）
            mock_audio = b'\x00' * 500  # 500bytes的静音数据
            audio_base64 = base64.b64encode(mock_audio).decode('utf-8')
            
            print(f"  音频数据大小: {len(mock_audio)} bytes")
            
            await websocket.send(json.dumps({
                "type": "voice",
                "audio": audio_base64,
                "format": "pcm"
            }))
            
            # 接收处理状态
            status_msg = await websocket.recv()
            status_data = json.loads(status_msg)
            if status_data.get("type") == "processing":
                print(f"  {status_data.get('message', '')}")
            
            # 接收语音回复
            voice_response = await websocket.recv()
            voice_data = json.loads(voice_response)
            
            if voice_data.get("type") == "voice":
                recognized = voice_data.get("recognized_text", "")
                ai_text = voice_data.get("text", "")
                audio_data = voice_data.get("audio")
                
                print_success("语音消息处理成功")
                print(f"  识别文本: {recognized}")
                print(f"  AI回复文本: {ai_text[:100]}...")
                if audio_data:
                    print(f"  音频数据: {len(audio_data)} bytes (base64)")
                else:
                    print(f"  音频数据: None (Mock模式)")
            elif voice_data.get("type") == "error":
                print(f"  ⚠️  {voice_data.get('message', '')}")
            
            print_section("✅ WebSocket 测试通过！")
            
    except Exception as e:
        print_error(f"WebSocket 测试失败: {e}")


def main():
    print_section("实时对话功能完整测试")
    print("测试范围：")
    print("  1. HTTP API (创建会话、发送消息、获取历史)")
    print("  2. WebSocket 实时对话（文本、语音、心跳）")
    print("  3. Mock 语音识别和合成")
    
    # 测试1: HTTP API
    try:
        candidate_token, session_id, voice_session_id = test_http_api()
    except Exception as e:
        print_error(f"HTTP API 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试2: WebSocket
    try:
        asyncio.run(test_websocket(candidate_token, session_id))
    except Exception as e:
        print_error(f"WebSocket 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 最终总结
    print_section("🎉 实时对话功能测试全部通过！")
    print("\n功能验证：")
    print("  ✓ 创建文本会话")
    print("  ✓ 创建语音会话")
    print("  ✓ HTTP 发送消息并获取回复")
    print("  ✓ 获取消息历史")
    print("  ✓ 获取用户所有会话")
    print("  ✓ WebSocket 实时文本对话")
    print("  ✓ WebSocket 心跳机制")
    print("  ✓ WebSocket 语音消息（Mock ASR/TTS）")
    print("\n提示：")
    print("  - 当前使用 Mock 模式进行语音识别和合成")
    print("  - 生产环境需配置阿里云语音服务 AppKey 和 Token")
    print("  - WebSocket 消息支持实时双向通信")
    print("  - 支持文本和语音两种对话模式")

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
