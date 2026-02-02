# API 接口参考 - 前端开发指南

本文档为前端开发者提供 hereOffer 后端 API 的详细接口说明。

## 目录

- [基础信息](#基础信息)
- [认证接口](#认证接口)
- [岗位接口](#岗位接口)
- [投递接口](#投递接口)
- [Admin 投递管理接口](#admin-投递管理接口)
- [对话接口](#对话接口)
- [WebSocket 接口](#websocket-接口)
- [错误处理](#错误处理)

---

## 基础信息

### Base URL

```
# 开发环境
http://localhost:8000

# 生产环境
https://api.hereoffer.com
```

### 认证方式

使用 JWT (JSON Web Token) 进行身份验证：

```http
Authorization: Bearer <your_jwt_token>
```

### 通用响应格式

所有 API 响应均遵循以下格式：

**成功响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": { ... },
  "request_id": "uuid-string"
}
```

**错误响应**:
```json
{
  "code": 1001,
  "message": "Invalid credentials",
  "data": null,
  "request_id": "uuid-string"
}
```

### 常用错误码

| 错误码 | 说明                     |
| ------ | ------------------------ |
| 0      | 成功                     |
| 1001   | 认证失败                 |
| 1002   | 权限不足                 |
| 1003   | 资源不存在               |
| 1004   | 参数验证失败             |
| 1005   | 资源冲突（如邮箱已存在） |
| 5000   | 服务器内部错误           |

---

## 认证接口

### 用户注册

**端点**: `POST /auth/register`

**描述**: 注册新用户（candidate 或 admin）

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "user_type": "candidate"  // "candidate" 或 "admin"
}
```

**响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "user_id": 1,
    "email": "user@example.com",
    "user_type": "candidate"
  },
  "request_id": "..."
}
```

**示例（JavaScript）**:
```javascript
async function register(email, password, userType) {
  const response = await fetch('http://localhost:8000/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      password: password,
      user_type: userType
    })
  });
  
  const data = await response.json();
  if (data.code === 0) {
    console.log('注册成功:', data.data);
  } else {
    console.error('注册失败:', data.message);
  }
}
```

---

### 用户登录

**端点**: `POST /auth/login`

**描述**: 用户登录并获取 JWT token

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "user_id": 1,
      "email": "user@example.com",
      "user_type": "candidate"
    }
  },
  "request_id": "..."
}
```

**示例（JavaScript）**:
```javascript
async function login(email, password) {
  const response = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      password: password
    })
  });
  
  const data = await response.json();
  if (data.code === 0) {
    // 保存 token 到 localStorage
    localStorage.setItem('access_token', data.data.access_token);
    localStorage.setItem('user', JSON.stringify(data.data.user));
    return data.data;
  } else {
    throw new Error(data.message);
  }
}
```

---

## 岗位接口

### 创建岗位（Admin）

**端点**: `POST /admin/jobs`

**描述**: 管理员创建新岗位

**权限**: 需要 admin 角色

**请求头**:
```http
Authorization: Bearer <admin_token>
```

**请求体**:
```json
{
  "title": "高级后端工程师",
  "jd_text": "岗位职责：\n1. 负责后端系统开发...",
  "threshold_score": 70
}
```

**响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "job_id": 1,
    "title": "高级后端工程师",
    "jd_text": "岗位职责：\n1. 负责后端系统开发...",
    "threshold_score": 70,
    "is_active": true,
    "created_at": "2026-02-01T10:00:00",
    "question_bank": null
  },
  "request_id": "..."
}
```

**示例（JavaScript）**:
```javascript
async function createJob(title, jdText, thresholdScore) {
  const token = localStorage.getItem('access_token');
  const response = await fetch('http://localhost:8000/admin/jobs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      title: title,
      jd_text: jdText,
      threshold_score: thresholdScore
    })
  });
  
  const data = await response.json();
  if (data.code === 0) {
    return data.data;
  } else {
    throw new Error(data.message);
  }
}
```

---

### 获取岗位列表

**端点**: `GET /admin/jobs`

**描述**: 获取岗位列表（支持分页和筛选）

**权限**: 
- Admin: 可查看所有岗位
- Candidate: 只能查看激活的岗位

**请求参数**:
| 参数        | 类型    | 必填 | 说明                          |
| ----------- | ------- | ---- | ----------------------------- |
| page        | integer | 否   | 页码（默认 1）                |
| page_size   | integer | 否   | 每页数量（默认 20，最大 100） |
| is_active   | boolean | 否   | 是否激活（仅 admin）          |

**示例请求**:
```http
GET /admin/jobs?page=1&page_size=20&is_active=true
Authorization: Bearer <token>
```

**响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "job_id": 1,
        "title": "高级后端工程师",
        "jd_text": "...",
        "threshold_score": 70,
        "is_active": true,
        "created_at": "2026-02-01T10:00:00",
        "question_bank": {
          "version": 1,
          "questions_json": [...]
        }
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
  },
  "request_id": "..."
}
```

**示例（JavaScript）**:
```javascript
async function getJobs(page = 1, pageSize = 20, isActive = null) {
  const token = localStorage.getItem('access_token');
  const params = new URLSearchParams({
    page: page,
    page_size: pageSize
  });
  
  if (isActive !== null) {
    params.append('is_active', isActive);
  }
  
  const response = await fetch(
    `http://localhost:8000/admin/jobs?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  const data = await response.json();
  if (data.code === 0) {
    return data.data;
  } else {
    throw new Error(data.message);
  }
}
```

---

### 更新岗位题库（Admin）

**端点**: `PATCH /admin/jobs/{job_id}/questions`

**描述**: 更新岗位的面试题库

**权限**: 需要 admin 角色

**请求体**:
```json
{
  "questions_json": [
    {
      "question": "请介绍一下你的项目经验",
      "type": "open",
      "category": "experience"
    },
    {
      "question": "你对 Python 有多少年的使用经验？",
      "type": "single_choice",
      "options": ["<1年", "1-3年", "3-5年", ">5年"]
    }
  ]
}
```

**响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "job_id": 1,
    "version": 2,
    "questions_json": [...]
  },
  "request_id": "..."
}
```

---

## 投递接口

### 创建投递（Candidate）

**端点**: `POST /applications`

**描述**: 求职者提交简历申请岗位

**权限**: 需要 candidate 角色

**请求类型**: `multipart/form-data`

**请求体**:
| 字段         | 类型   | 必填 | 说明             |
| ------------ | ------ | ---- | ---------------- |
| job_id       | int    | 是   | 岗位 ID          |
| resume_file  | file   | 是   | 简历文件（PDF/DOCX/TXT） |

**示例请求（JavaScript）**:
```javascript
async function createApplication(jobId, resumeFile) {
  const token = localStorage.getItem('access_token');
  const formData = new FormData();
  formData.append('job_id', jobId);
  formData.append('resume_file', resumeFile);
  
  const response = await fetch('http://localhost:8000/applications', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  const data = await response.json();
  if (data.code === 0) {
    return data.data;
  } else {
    throw new Error(data.message);
  }
}

// 使用示例（配合文件选择器）
document.getElementById('resumeInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  const jobId = 1; // 从页面获取
  
  try {
    const application = await createApplication(jobId, file);
    console.log('投递成功:', application);
    alert(`投递成功！申请 ID: ${application.application_id}`);
  } catch (error) {
    alert(`投递失败: ${error.message}`);
  }
});
```

**响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "application_id": 123,
    "user_id": 1,
    "job_id": 1,
    "job_title": "高级后端工程师",
    "status": "PARSING",
    "resume_path": "resumes/user_1/123_resume.pdf",
    "created_at": "2026-02-01T14:30:00",
    "updated_at": "2026-02-01T14:30:00"
  },
  "request_id": "..."
}
```

---

### 获取投递详情

**端点**: `GET /applications/{application_id}`

**描述**: 获取单个投递的详细信息

**权限**: 
- Candidate: 只能查看自己的投递
- Admin: 可查看所有投递

**响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "application_id": 123,
    "user_id": 1,
    "job_id": 1,
    "job_title": "高级后端工程师",
    "status": "QUESTIONS_READY",
    "resume_path": "resumes/user_1/123_resume.pdf",
    "resume_json": {
      "name": "张三",
      "email": "zhangsan@example.com",
      "skills": ["Python", "FastAPI", "MySQL"]
    },
    "score_json": {
      "total_score": 85,
      "dimensions": {
        "education": 90,
        "experience": 80,
        "skills": 88
      }
    },
    "questions_json": [
      {
        "question": "请介绍你在 FastAPI 方面的项目经验",
        "type": "open"
      }
    ],
    "created_at": "2026-02-01T14:30:00",
    "updated_at": "2026-02-01T14:35:00"
  },
  "request_id": "..."
}
```

**示例（JavaScript）**:
```javascript
async function getApplication(applicationId) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(
    `http://localhost:8000/applications/${applicationId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  const data = await response.json();
  if (data.code === 0) {
    return data.data;
  } else {
    throw new Error(data.message);
  }
}

// 轮询检查状态更新
async function pollApplicationStatus(applicationId, interval = 3000) {
  const finalStatuses = [
    'QUESTIONS_READY',
    'INTERVIEW_SCHEDULED',
    'INTERVIEW_COMPLETED',
    'PASSED',
    'REJECTED',
    'HUMAN_REVIEW'
  ];
  
  return new Promise((resolve, reject) => {
    const timer = setInterval(async () => {
      try {
        const app = await getApplication(applicationId);
        console.log(`当前状态: ${app.status}`);
        
        if (finalStatuses.includes(app.status)) {
          clearInterval(timer);
          resolve(app);
        }
      } catch (error) {
        clearInterval(timer);
        reject(error);
      }
    }, interval);
  });
}
```

---

### 获取投递列表

**端点**: `GET /applications`

**描述**: 获取当前用户的投递列表

**权限**: candidate 角色

**请求参数**:
| 参数        | 类型    | 必填 | 说明                          |
| ----------- | ------- | ---- | ----------------------------- |
| page        | integer | 否   | 页码（默认 1）                |
| page_size   | integer | 否   | 每页数量（默认 20）           |
| status      | string  | 否   | 状态筛选                      |

**响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "application_id": 123,
        "job_id": 1,
        "job_title": "高级后端工程师",
        "status": "QUESTIONS_READY",
        "created_at": "2026-02-01T14:30:00"
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20
  },
  "request_id": "..."
}
```

---

## Admin 投递管理接口

### 获取所有投递（Admin）

**端点**: `GET /admin/applications`

**描述**: 管理员查看所有投递（支持筛选）

**权限**: 需要 admin 角色

**请求参数**:
| 参数        | 类型    | 必填 | 说明                |
| ----------- | ------- | ---- | ------------------- |
| page        | integer | 否   | 页码（默认 1）      |
| page_size   | integer | 否   | 每页数量（默认 20） |
| job_id      | integer | 否   | 岗位 ID 筛选        |
| status      | string  | 否   | 状态筛选            |
| min_score   | integer | 否   | 最低分数筛选        |

**响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "application_id": 123,
        "user_id": 1,
        "job_id": 1,
        "job_title": "高级后端工程师",
        "status": "SCORED",
        "score": 85,
        "created_at": "2026-02-01T14:30:00"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  },
  "request_id": "..."
}
```

---

### 更新投递状态（Admin）

**端点**: `PATCH /admin/applications/{application_id}/status`

**描述**: 管理员手动更新投递状态

**权限**: 需要 admin 角色

**请求体**:
```json
{
  "status": "INTERVIEW_SCHEDULED",
  "notes": "已安排面试时间：2026-02-05 10:00"
}
```

**响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "application_id": 123,
    "status": "INTERVIEW_SCHEDULED",
    "updated_at": "2026-02-01T15:00:00"
  },
  "request_id": "..."
}
```

---

### 获取统计数据（Admin）

**端点**: `GET /admin/applications/stats`

**描述**: 获取投递统计数据

**权限**: 需要 admin 角色

**请求参数**:
| 参数   | 类型    | 必填 | 说明        |
| ------ | ------- | ---- | ----------- |
| job_id | integer | 否   | 岗位 ID 筛选 |

**响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "total": 150,
    "by_status": {
      "RESUME_UPLOADED": 10,
      "PARSING": 5,
      "PARSED": 8,
      "SCORING": 3,
      "SCORED": 20,
      "QUESTIONS_READY": 30,
      "INTERVIEW_SCHEDULED": 15,
      "PASSED": 25,
      "REJECTED": 30,
      "HUMAN_REVIEW": 4
    },
    "average_score": 72.5,
    "pass_rate": 0.25
  },
  "request_id": "..."
}
```

---

## 对话接口

### 创建对话会话

**端点**: `POST /chat/sessions`

**描述**: 创建新的对话会话

**权限**: candidate 角色

**请求体**:
```json
{
  "job_id": 1,
  "session_type": "interview"  // "interview" 或 "consultation"
}
```

**响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "session_id": 456,
    "user_id": 1,
    "job_id": 1,
    "session_type": "interview",
    "is_active": true,
    "created_at": "2026-02-01T16:00:00"
  },
  "request_id": "..."
}
```

---

### 发送文本消息

**端点**: `POST /chat/sessions/{session_id}/messages`

**描述**: 向对话会话发送文本消息并获取 AI 回复

**权限**: candidate 角色（仅限自己的会话）

**请求体**:
```json
{
  "content": "你好，我想了解一下这个岗位的要求"
}
```

**响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "user_message": {
      "message_id": 789,
      "role": "user",
      "content": "你好，我想了解一下这个岗位的要求",
      "created_at": "2026-02-01T16:01:00"
    },
    "ai_message": {
      "message_id": 790,
      "role": "assistant",
      "content": "您好！这个岗位主要要求...",
      "citations_json": null,
      "audio_url": null,
      "created_at": "2026-02-01T16:01:02"
    }
  },
  "request_id": "..."
}
```

**示例（JavaScript）**:
```javascript
async function sendChatMessage(sessionId, content) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(
    `http://localhost:8000/chat/sessions/${sessionId}/messages`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ content: content })
    }
  );
  
  const data = await response.json();
  if (data.code === 0) {
    return data.data;
  } else {
    throw new Error(data.message);
  }
}
```

---

### 获取对话历史

**端点**: `GET /chat/sessions/{session_id}/messages`

**描述**: 获取对话会话的消息历史

**权限**: candidate 角色（仅限自己的会话）

**请求参数**:
| 参数  | 类型    | 必填 | 说明                    |
| ----- | ------- | ---- | ----------------------- |
| limit | integer | 否   | 返回消息数量（默认 50） |

**响应**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "message_id": 789,
        "role": "user",
        "content": "你好，我想了解一下这个岗位的要求",
        "created_at": "2026-02-01T16:01:00"
      },
      {
        "message_id": 790,
        "role": "assistant",
        "content": "您好！这个岗位主要要求...",
        "created_at": "2026-02-01T16:01:02"
      }
    ],
    "total": 10
  },
  "request_id": "..."
}
```

---

## WebSocket 接口

### 建立 WebSocket 连接

**端点**: `ws://localhost:8000/ws/chat/{session_id}?token=<jwt_token>`

**描述**: 建立 WebSocket 连接进行实时对话

**参数**:
- `session_id`: 对话会话 ID
- `token`: JWT token（作为查询参数）

**示例（JavaScript）**:
```javascript
function connectWebSocket(sessionId, token) {
  const ws = new WebSocket(
    `ws://localhost:8000/ws/chat/${sessionId}?token=${token}`
  );
  
  ws.onopen = () => {
    console.log('WebSocket 连接已建立');
    
    // 发送文本消息
    ws.send(JSON.stringify({
      type: 'text',
      content: '你好'
    }));
  };
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('收到消息:', message);
    
    if (message.type === 'text') {
      // 显示文本消息
      displayMessage(message.content, message.role);
    } else if (message.type === 'audio') {
      // 播放语音消息
      playAudio(message.audio_url);
      displayMessage(message.text, message.role);
    } else if (message.type === 'error') {
      console.error('错误:', message.content);
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket 错误:', error);
  };
  
  ws.onclose = () => {
    console.log('WebSocket 连接已关闭');
  };
  
  return ws;
}
```

---

### 消息格式

#### 1. 发送文本消息

```json
{
  "type": "text",
  "content": "你好，我想了解这个岗位"
}
```

#### 2. 发送语音消息

```json
{
  "type": "audio",
  "audio_data": "base64_encoded_audio_data"
}
```

#### 3. 接收文本回复

```json
{
  "type": "text",
  "role": "assistant",
  "content": "您好！这个岗位主要负责..."
}
```

#### 4. 接收语音回复

```json
{
  "type": "audio",
  "role": "assistant",
  "text": "您好！这个岗位主要负责...",
  "audio_url": "https://minio/voices/session_456/msg_790.mp3"
}
```

#### 5. 心跳消息

客户端发送：
```json
{
  "type": "ping"
}
```

服务器响应：
```json
{
  "type": "pong"
}
```

#### 6. 错误消息

```json
{
  "type": "error",
  "content": "语音识别失败，请重试"
}
```

---

### 完整的聊天组件示例（React）

```jsx
import React, { useState, useEffect, useRef } from 'react';

function ChatComponent({ sessionId, token }) {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  
  useEffect(() => {
    // 建立 WebSocket 连接
    const ws = new WebSocket(
      `ws://localhost:8000/ws/chat/${sessionId}?token=${token}`
    );
    
    ws.onopen = () => {
      console.log('Connected');
      addSystemMessage('已连接到服务器');
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'text') {
        addMessage(message.content, message.role);
      } else if (message.type === 'audio') {
        addMessage(message.text, message.role, message.audio_url);
      } else if (message.type === 'error') {
        addSystemMessage(`错误: ${message.content}`);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      addSystemMessage('连接错误');
    };
    
    ws.onclose = () => {
      addSystemMessage('连接已关闭');
    };
    
    wsRef.current = ws;
    
    return () => {
      ws.close();
    };
  }, [sessionId, token]);
  
  const addMessage = (content, role, audioUrl = null) => {
    setMessages(prev => [...prev, { content, role, audioUrl, timestamp: new Date() }]);
  };
  
  const addSystemMessage = (content) => {
    setMessages(prev => [...prev, { content, role: 'system', timestamp: new Date() }]);
  };
  
  const sendTextMessage = () => {
    if (!inputText.trim()) return;
    
    wsRef.current.send(JSON.stringify({
      type: 'text',
      content: inputText
    }));
    
    addMessage(inputText, 'user');
    setInputText('');
  };
  
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
        const reader = new FileReader();
        
        reader.onloadend = () => {
          const base64Audio = reader.result.split(',')[1];
          wsRef.current.send(JSON.stringify({
            type: 'audio',
            audio_data: base64Audio
          }));
        };
        
        reader.readAsDataURL(audioBlob);
      };
      
      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
    } catch (error) {
      console.error('录音失败:', error);
      addSystemMessage('无法访问麦克风');
    }
  };
  
  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };
  
  return (
    <div className="chat-container">
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
        />
        <button onClick={sendTextMessage}>发送</button>
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={isRecording ? 'recording' : ''}
        >
          {isRecording ? '停止录音' : '语音输入'}
        </button>
      </div>
    </div>
  );
}

export default ChatComponent;
```

---

## 错误处理

### 常见错误及处理

#### 1. 401 Unauthorized

**原因**: Token 无效或已过期

**处理**:
```javascript
if (response.status === 401) {
  // 清除本地 token
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  
  // 跳转到登录页
  window.location.href = '/login';
}
```

#### 2. 403 Forbidden

**原因**: 权限不足（如 candidate 访问 admin 接口）

**处理**:
```javascript
if (data.code === 1002) {
  alert('您没有权限执行此操作');
  window.location.href = '/';
}
```

#### 3. 404 Not Found

**原因**: 资源不存在

**处理**:
```javascript
if (data.code === 1003) {
  alert('资源不存在');
  // 返回列表页
}
```

#### 4. 422 Validation Error

**原因**: 请求参数验证失败

**处理**:
```javascript
if (response.status === 422) {
  const data = await response.json();
  // FastAPI 返回的验证错误详情
  console.error('Validation errors:', data.detail);
  
  // 显示错误信息
  data.detail.forEach(error => {
    alert(`${error.loc.join('.')}: ${error.msg}`);
  });
}
```

---

## 下一步

- [WebSocket 使用指南](./WEBSOCKET.md) - WebSocket 详细说明
- [认证流程](./AUTHENTICATION.md) - JWT 认证详解
- [代码示例](./EXAMPLES.md) - 更多完整示例

---

**最后更新**: 2026-02-01
