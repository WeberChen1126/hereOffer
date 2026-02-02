# WebSocket 使用指南

本文档详细介绍如何使用 hereOffer 的 WebSocket 实时对话功能，包括连接建立、消息格式、错误处理和完整的代码示例。

## 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [连接建立](#连接建立)
- [消息格式](#消息格式)
- [心跳机制](#心跳机制)
- [错误处理](#错误处理)
- [完整示例](#完整示例)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 概述

### 功能特性

hereOffer 的 WebSocket 服务提供以下功能：

- ✅ **实时双向通信** - 服务器和客户端可实时收发消息
- ✅ **文本对话** - 支持文本消息的发送和接收
- ✅ **语音对话** - 支持语音输入和语音输出（ASR + TTS）
- ✅ **智能回复** - 基于 LLM 的智能对话
- ✅ **会话管理** - 支持多个对话会话
- ✅ **自动重连** - 连接断开时自动重连
- ✅ **心跳保活** - 定期心跳防止连接超时

### 适用场景

- 面试对话（实时问答）
- 岗位咨询（职位信息查询）
- 简历反馈（AI 评价和建议）
- 语音面试（语音输入输出）

---

## 快速开始

### 前置条件

1. **创建对话会话**：
   ```javascript
   // 调用 HTTP API 创建会话
   const response = await fetch('http://localhost:8000/chat/sessions', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
       'Authorization': `Bearer ${token}`
     },
     body: JSON.stringify({
       job_id: 1,
       session_type: 'interview'
     })
   });
   const { data } = await response.json();
   const sessionId = data.session_id;  // 保存会话 ID
   ```

2. **获取 JWT Token**：
   ```javascript
   // 登录获取 token
   const loginResponse = await fetch('http://localhost:8000/auth/login', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       email: 'user@example.com',
       password: 'password123'
     })
   });
   const { data } = await loginResponse.json();
   const token = data.access_token;  // 保存 token
   ```

### 最简示例

```javascript
// 1. 建立 WebSocket 连接
const ws = new WebSocket(
  `ws://localhost:8000/ws/chat/${sessionId}?token=${token}`
);

// 2. 监听连接打开
ws.onopen = () => {
  console.log('连接已建立');
  
  // 3. 发送文本消息
  ws.send(JSON.stringify({
    type: 'text',
    content: '你好，我想了解这个岗位'
  }));
};

// 4. 监听服务器消息
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('收到消息:', message);
  
  if (message.type === 'text') {
    console.log('AI 回复:', message.content);
  }
};

// 5. 监听错误
ws.onerror = (error) => {
  console.error('WebSocket 错误:', error);
};

// 6. 监听连接关闭
ws.onclose = () => {
  console.log('连接已关闭');
};
```

---

## 连接建立

### WebSocket URL

**格式**:
```
ws://<host>/ws/chat/<session_id>?token=<jwt_token>
```

**参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | integer | 是 | 对话会话 ID |
| token | string | 是 | JWT 认证 token |

**示例**:
```javascript
// 开发环境
const wsUrl = `ws://localhost:8000/ws/chat/${sessionId}?token=${token}`;

// 生产环境（使用 wss）
const wsUrl = `wss://api.hereoffer.com/ws/chat/${sessionId}?token=${token}`;

const ws = new WebSocket(wsUrl);
```

### 连接状态

WebSocket 连接有以下状态：

| 状态 | 值 | 说明 |
|------|---|------|
| CONNECTING | 0 | 正在连接 |
| OPEN | 1 | 连接已建立 |
| CLOSING | 2 | 正在关闭 |
| CLOSED | 3 | 连接已关闭 |

**检查连接状态**:
```javascript
console.log('当前状态:', ws.readyState);

// 判断是否已连接
if (ws.readyState === WebSocket.OPEN) {
  ws.send(JSON.stringify({ type: 'text', content: 'Hello' }));
} else {
  console.log('连接未建立');
}
```

### 认证失败

如果 token 无效或会话不存在，连接会被拒绝：

```javascript
ws.onclose = (event) => {
  if (event.code === 1008) {  // 策略违规（认证失败）
    console.error('认证失败，token 无效或会话不存在');
  }
};
```

---

## 消息格式

### 1. 发送文本消息

**客户端 → 服务器**:
```json
{
  "type": "text",
  "content": "请介绍一下这个岗位的要求"
}
```

**服务器 → 客户端**（AI 回复）:
```json
{
  "type": "text",
  "role": "assistant",
  "content": "这个岗位主要要求候选人具备以下技能：\n1. 熟练掌握 Python 和 FastAPI\n2. 有数据库设计经验..."
}
```

**JavaScript 示例**:
```javascript
// 发送文本消息
function sendTextMessage(content) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'text',
      content: content
    }));
  }
}

// 接收文本消息
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'text') {
    displayMessage(message.content, message.role);
  }
};

function displayMessage(content, role) {
  const messageDiv = document.createElement('div');
  messageDiv.className = role === 'user' ? 'user-message' : 'ai-message';
  messageDiv.textContent = content;
  document.getElementById('chat-container').appendChild(messageDiv);
}
```

---

### 2. 发送语音消息

**客户端 → 服务器**:
```json
{
  "type": "audio",
  "audio_data": "base64_encoded_audio_data"
}
```

**服务器 → 客户端**（AI 回复，包含语音）:
```json
{
  "type": "audio",
  "role": "assistant",
  "text": "您好，这个岗位主要负责...",
  "audio_url": "http://localhost:9000/voices/session_123/msg_456.mp3"
}
```

**JavaScript 示例（录音并发送）**:
```javascript
let mediaRecorder;
let audioChunks = [];

// 开始录音
async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
    
    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data);
    };
    
    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      await sendAudioMessage(audioBlob);
    };
    
    mediaRecorder.start();
    console.log('录音开始');
  } catch (error) {
    console.error('无法访问麦克风:', error);
  }
}

// 停止录音
function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
    console.log('录音停止');
  }
}

// 发送语音消息
async function sendAudioMessage(audioBlob) {
  const reader = new FileReader();
  
  reader.onloadend = () => {
    const base64Audio = reader.result.split(',')[1];
    
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'audio',
        audio_data: base64Audio
      }));
    }
  };
  
  reader.readAsDataURL(audioBlob);
}

// 接收并播放语音
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'audio') {
    // 显示文本
    displayMessage(message.text, message.role);
    
    // 播放语音
    if (message.audio_url) {
      playAudio(message.audio_url);
    }
  }
};

function playAudio(audioUrl) {
  const audio = new Audio(audioUrl);
  audio.play().catch(error => {
    console.error('播放音频失败:', error);
  });
}
```

---

### 3. 心跳消息

**客户端 → 服务器**（Ping）:
```json
{
  "type": "ping"
}
```

**服务器 → 客户端**（Pong）:
```json
{
  "type": "pong"
}
```

**JavaScript 示例**:
```javascript
let heartbeatInterval;

// 启动心跳
function startHeartbeat() {
  heartbeatInterval = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }));
      console.log('发送心跳');
    }
  }, 30000);  // 每 30 秒一次
}

// 停止心跳
function stopHeartbeat() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval);
  }
}

// 监听 Pong 响应
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'pong') {
    console.log('收到心跳响应');
  }
};

// 连接建立后启动心跳
ws.onopen = () => {
  console.log('连接已建立');
  startHeartbeat();
};

// 连接关闭后停止心跳
ws.onclose = () => {
  console.log('连接已关闭');
  stopHeartbeat();
};
```

---

### 4. 错误消息

**服务器 → 客户端**:
```json
{
  "type": "error",
  "content": "语音识别失败，请重试"
}
```

**JavaScript 示例**:
```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'error') {
    console.error('服务器错误:', message.content);
    showError(message.content);
  }
};

function showError(errorMessage) {
  const errorDiv = document.createElement('div');
  errorDiv.className = 'error-message';
  errorDiv.textContent = `错误: ${errorMessage}`;
  document.getElementById('chat-container').appendChild(errorDiv);
  
  // 3 秒后自动消失
  setTimeout(() => {
    errorDiv.remove();
  }, 3000);
}
```

---

## 心跳机制

### 为什么需要心跳？

- 防止连接超时（某些代理或负载均衡器会关闭空闲连接）
- 及时检测连接断开
- 保持连接活跃

### 实现方式

**方法 1: 定时 Ping**（推荐）:
```javascript
class WebSocketClient {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.heartbeatInterval = null;
    this.reconnectTimeout = null;
  }
  
  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('连接已建立');
      this.startHeartbeat();
    };
    
    this.ws.onclose = () => {
      console.log('连接已关闭');
      this.stopHeartbeat();
      this.reconnect();
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket 错误:', error);
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };
  }
  
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);  // 每 30 秒
  }
  
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
  
  reconnect() {
    if (this.reconnectTimeout) return;
    
    console.log('5 秒后尝试重连...');
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      this.connect();
    }, 5000);
  }
  
  send(message) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('连接未建立，无法发送消息');
    }
  }
  
  handleMessage(message) {
    switch (message.type) {
      case 'pong':
        console.log('心跳响应');
        break;
      case 'text':
        console.log('文本消息:', message.content);
        break;
      case 'audio':
        console.log('语音消息:', message.text);
        break;
      case 'error':
        console.error('错误:', message.content);
        break;
    }
  }
  
  close() {
    this.stopHeartbeat();
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close();
    }
  }
}

// 使用示例
const client = new WebSocketClient(`ws://localhost:8000/ws/chat/${sessionId}?token=${token}`);
client.connect();

// 发送消息
client.send({ type: 'text', content: 'Hello' });

// 关闭连接
// client.close();
```

---

## 错误处理

### 常见错误代码

| 代码 | 名称 | 说明 | 处理方式 |
|------|------|------|---------|
| 1000 | Normal Closure | 正常关闭 | 无需处理 |
| 1001 | Going Away | 页面卸载 | 无需处理 |
| 1006 | Abnormal Closure | 异常关闭（网络问题） | 自动重连 |
| 1008 | Policy Violation | 策略违规（认证失败） | 重新登录 |
| 1011 | Internal Error | 服务器错误 | 稍后重试 |

### 错误处理示例

```javascript
ws.onclose = (event) => {
  console.log(`连接关闭，代码: ${event.code}, 原因: ${event.reason}`);
  
  switch (event.code) {
    case 1000:
      console.log('正常关闭');
      break;
    case 1006:
      console.log('异常关闭，尝试重连');
      reconnect();
      break;
    case 1008:
      console.error('认证失败，请重新登录');
      redirectToLogin();
      break;
    case 1011:
      console.error('服务器错误，稍后重试');
      setTimeout(reconnect, 10000);
      break;
    default:
      console.log('未知错误，尝试重连');
      reconnect();
  }
};

ws.onerror = (error) => {
  console.error('WebSocket 错误:', error);
  showNotification('连接错误，请检查网络');
};
```

### 自动重连

```javascript
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const reconnectDelay = 3000;  // 3 秒

function reconnect() {
  if (reconnectAttempts >= maxReconnectAttempts) {
    console.error('重连次数过多，停止重连');
    showNotification('无法连接到服务器，请稍后再试');
    return;
  }
  
  reconnectAttempts++;
  console.log(`第 ${reconnectAttempts} 次重连尝试...`);
  
  setTimeout(() => {
    createWebSocket();
  }, reconnectDelay * reconnectAttempts);  // 指数退避
}

function createWebSocket() {
  ws = new WebSocket(`ws://localhost:8000/ws/chat/${sessionId}?token=${token}`);
  
  ws.onopen = () => {
    console.log('连接已建立');
    reconnectAttempts = 0;  // 重置重连次数
    showNotification('连接成功');
  };
  
  ws.onclose = (event) => {
    if (event.code !== 1000) {
      reconnect();
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket 错误:', error);
  };
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleMessage(message);
  };
}
```

---

## 完整示例

### React 聊天组件

```jsx
import React, { useState, useEffect, useRef } from 'react';

function ChatComponent({ sessionId, token }) {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const heartbeatIntervalRef = useRef(null);
  
  // 建立 WebSocket 连接
  useEffect(() => {
    const ws = new WebSocket(
      `ws://localhost:8000/ws/chat/${sessionId}?token=${token}`
    );
    
    ws.onopen = () => {
      console.log('Connected');
      setIsConnected(true);
      startHeartbeat();
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleMessage(message);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('Disconnected');
      setIsConnected(false);
      stopHeartbeat();
    };
    
    wsRef.current = ws;
    
    return () => {
      stopHeartbeat();
      ws.close();
    };
  }, [sessionId, token]);
  
  // 启动心跳
  const startHeartbeat = () => {
    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  };
  
  // 停止心跳
  const stopHeartbeat = () => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
  };
  
  // 处理收到的消息
  const handleMessage = (message) => {
    switch (message.type) {
      case 'text':
        addMessage(message.content, message.role);
        break;
      case 'audio':
        addMessage(message.text, message.role, message.audio_url);
        if (message.audio_url) {
          playAudio(message.audio_url);
        }
        break;
      case 'error':
        addSystemMessage(`错误: ${message.content}`);
        break;
      case 'pong':
        console.log('Heartbeat received');
        break;
    }
  };
  
  // 添加消息到列表
  const addMessage = (content, role, audioUrl = null) => {
    setMessages(prev => [...prev, {
      content,
      role,
      audioUrl,
      timestamp: new Date()
    }]);
  };
  
  // 添加系统消息
  const addSystemMessage = (content) => {
    setMessages(prev => [...prev, {
      content,
      role: 'system',
      timestamp: new Date()
    }]);
  };
  
  // 发送文本消息
  const sendTextMessage = () => {
    if (!inputText.trim()) return;
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'text',
        content: inputText
      }));
      
      addMessage(inputText, 'user');
      setInputText('');
    } else {
      alert('连接未建立');
    }
  };
  
  // 开始录音
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks = [];
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        await sendAudioMessage(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
    } catch (error) {
      console.error('录音失败:', error);
      alert('无法访问麦克风');
    }
  };
  
  // 停止录音
  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };
  
  // 发送语音消息
  const sendAudioMessage = async (audioBlob) => {
    const reader = new FileReader();
    
    reader.onloadend = () => {
      const base64Audio = reader.result.split(',')[1];
      
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'audio',
          audio_data: base64Audio
        }));
        
        addSystemMessage('语音消息已发送');
      }
    };
    
    reader.readAsDataURL(audioBlob);
  };
  
  // 播放音频
  const playAudio = (audioUrl) => {
    const audio = new Audio(audioUrl);
    audio.play().catch(error => {
      console.error('播放音频失败:', error);
    });
  };
  
  return (
    <div className="chat-container">
      <div className="connection-status">
        {isConnected ? '🟢 已连接' : '🔴 未连接'}
      </div>
      
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="content">{msg.content}</div>
            {msg.audioUrl && (
              <audio controls src={msg.audioUrl} />
            )}
            <div className="timestamp">
              {msg.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
      
      <div className="input-area">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendTextMessage()}
          placeholder="输入消息..."
          disabled={!isConnected}
        />
        <button onClick={sendTextMessage} disabled={!isConnected}>
          发送
        </button>
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={!isConnected}
          className={isRecording ? 'recording' : ''}
        >
          {isRecording ? '⏹ 停止' : '🎤 录音'}
        </button>
      </div>
    </div>
  );
}

export default ChatComponent;
```

### Vue 3 聊天组件

```vue
<template>
  <div class="chat-container">
    <div class="connection-status">
      <span :class="{ connected: isConnected, disconnected: !isConnected }">
        {{ isConnected ? '🟢 已连接' : '🔴 未连接' }}
      </span>
    </div>
    
    <div class="messages" ref="messagesContainer">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message', msg.role]"
      >
        <div class="content">{{ msg.content }}</div>
        <audio v-if="msg.audioUrl" controls :src="msg.audioUrl"></audio>
        <div class="timestamp">{{ formatTime(msg.timestamp) }}</div>
      </div>
    </div>
    
    <div class="input-area">
      <input
        v-model="inputText"
        @keyup.enter="sendTextMessage"
        :disabled="!isConnected"
        placeholder="输入消息..."
      />
      <button @click="sendTextMessage" :disabled="!isConnected">
        发送
      </button>
      <button
        @click="isRecording ? stopRecording() : startRecording()"
        :disabled="!isConnected"
        :class="{ recording: isRecording }"
      >
        {{ isRecording ? '⏹ 停止' : '🎤 录音' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';

const props = defineProps({
  sessionId: Number,
  token: String
});

const messages = ref([]);
const inputText = ref('');
const isConnected = ref(false);
const isRecording = ref(false);
const ws = ref(null);
const mediaRecorder = ref(null);
const heartbeatInterval = ref(null);
const messagesContainer = ref(null);

// 建立连接
onMounted(() => {
  connectWebSocket();
});

// 清理资源
onUnmounted(() => {
  stopHeartbeat();
  if (ws.value) {
    ws.value.close();
  }
});

// 滚动到底部
watch(messages, async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
});

function connectWebSocket() {
  ws.value = new WebSocket(
    `ws://localhost:8000/ws/chat/${props.sessionId}?token=${props.token}`
  );
  
  ws.value.onopen = () => {
    console.log('Connected');
    isConnected.value = true;
    startHeartbeat();
  };
  
  ws.value.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleMessage(message);
  };
  
  ws.value.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  ws.value.onclose = () => {
    console.log('Disconnected');
    isConnected.value = false;
    stopHeartbeat();
  };
}

function startHeartbeat() {
  heartbeatInterval.value = setInterval(() => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({ type: 'ping' }));
    }
  }, 30000);
}

function stopHeartbeat() {
  if (heartbeatInterval.value) {
    clearInterval(heartbeatInterval.value);
  }
}

function handleMessage(message) {
  switch (message.type) {
    case 'text':
      addMessage(message.content, message.role);
      break;
    case 'audio':
      addMessage(message.text, message.role, message.audio_url);
      if (message.audio_url) {
        playAudio(message.audio_url);
      }
      break;
    case 'error':
      addSystemMessage(`错误: ${message.content}`);
      break;
  }
}

function addMessage(content, role, audioUrl = null) {
  messages.value.push({
    content,
    role,
    audioUrl,
    timestamp: new Date()
  });
}

function addSystemMessage(content) {
  messages.value.push({
    content,
    role: 'system',
    timestamp: new Date()
  });
}

function sendTextMessage() {
  if (!inputText.value.trim()) return;
  
  if (ws.value?.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({
      type: 'text',
      content: inputText.value
    }));
    
    addMessage(inputText.value, 'user');
    inputText.value = '';
  }
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    const audioChunks = [];
    
    recorder.ondataavailable = (event) => {
      audioChunks.push(event.data);
    };
    
    recorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      await sendAudioMessage(audioBlob);
      stream.getTracks().forEach(track => track.stop());
    };
    
    recorder.start();
    mediaRecorder.value = recorder;
    isRecording.value = true;
  } catch (error) {
    console.error('录音失败:', error);
    alert('无法访问麦克风');
  }
}

function stopRecording() {
  if (mediaRecorder.value?.state === 'recording') {
    mediaRecorder.value.stop();
    isRecording.value = false;
  }
}

async function sendAudioMessage(audioBlob) {
  const reader = new FileReader();
  
  reader.onloadend = () => {
    const base64Audio = reader.result.split(',')[1];
    
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({
        type: 'audio',
        audio_data: base64Audio
      }));
      
      addSystemMessage('语音消息已发送');
    }
  };
  
  reader.readAsDataURL(audioBlob);
}

function playAudio(audioUrl) {
  const audio = new Audio(audioUrl);
  audio.play().catch(error => {
    console.error('播放音频失败:', error);
  });
}

function formatTime(date) {
  return date.toLocaleTimeString();
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.connection-status {
  padding: 10px;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 8px;
  max-width: 70%;
}

.message.user {
  background: #007bff;
  color: white;
  margin-left: auto;
}

.message.assistant {
  background: #f1f3f5;
}

.message.system {
  background: #fff3cd;
  text-align: center;
  margin: 0 auto;
}

.input-area {
  display: flex;
  padding: 10px;
  border-top: 1px solid #ddd;
  gap: 10px;
}

.input-area input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.input-area button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  background: #007bff;
  color: white;
  cursor: pointer;
}

.input-area button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.input-area button.recording {
  background: #dc3545;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
```

---

## 最佳实践

### 1. 连接管理

```javascript
// ✅ 好的做法
- 使用心跳保持连接
- 实现自动重连机制
- 处理所有连接状态
- 清理资源（组件卸载时关闭连接）

// ❌ 不好的做法
- 忽略连接断开
- 不处理重连
- 忘记关闭连接
```

### 2. 消息处理

```javascript
// ✅ 好的做法
- 验证消息格式
- 处理所有消息类型
- 错误消息友好提示
- 消息去重（如果需要）

// ❌ 不好的做法
- 假设消息格式正确
- 忽略错误消息
- 重复处理相同消息
```

### 3. 性能优化

```javascript
// ✅ 好的做法
- 限制消息历史长度
- 使用虚拟滚动（大量消息）
- 懒加载历史消息
- 压缩语音数据

// ❌ 不好的做法
- 无限累积消息
- 一次加载所有历史
- 发送未压缩的大文件
```

### 4. 用户体验

```javascript
// ✅ 好的做法
- 显示连接状态
- 显示"正在输入"指示器
- 消息发送失败提示
- 自动滚动到最新消息

// ❌ 不好的做法
- 不显示状态
- 没有加载指示
- 静默失败
```

---

## 常见问题

### 1. 连接无法建立

**问题**: WebSocket 连接失败

**排查**:
```javascript
// 检查 URL 是否正确
console.log('WebSocket URL:', wsUrl);

// 检查 token 是否有效
console.log('Token:', token);

// 查看浏览器控制台错误
// Network 标签页检查 WebSocket 连接
```

**解决**:
- 确认 sessionId 和 token 正确
- 检查服务器是否运行
- 确认防火墙未阻止 WebSocket

### 2. 消息发送失败

**问题**: 消息无法发送

**排查**:
```javascript
console.log('ReadyState:', ws.readyState);
// 0: CONNECTING
// 1: OPEN
// 2: CLOSING
// 3: CLOSED
```

**解决**:
- 确认连接状态为 OPEN
- 等待连接建立后再发送
- 实现消息队列（连接建立后发送）

### 3. 语音录制失败

**问题**: 无法访问麦克风

**排查**:
```javascript
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => console.log('麦克风可用'))
  .catch(error => console.error('麦克风不可用:', error));
```

**解决**:
- 确认浏览器有麦克风权限
- 使用 HTTPS（getUserMedia 需要安全上下文）
- 检查麦克风硬件是否正常

### 4. 跨域问题

**问题**: CORS 错误

**解决**:
- WebSocket 不受 CORS 限制
- 如果有问题，检查 Nginx 配置
- 确认服务器地址正确

### 5. 连接频繁断开

**问题**: 连接不稳定

**解决**:
- 实现心跳机制
- 增加心跳频率
- 检查网络状况
- 使用 wss（加密连接）

---

## 下一步

- [API 接口参考](./API_REFERENCE.md) - HTTP API 文档
- [认证流程](./AUTHENTICATION.md) - JWT 认证详解
- [代码示例](./EXAMPLES.md) - 更多完整示例

---

**最后更新**: 2026-02-01
