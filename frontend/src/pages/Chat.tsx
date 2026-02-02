import React, { useState, useEffect, useRef } from 'react';
import { Layout, Input, Button, List, message, Avatar, Spin } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, LoadingOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import { chat as chatApi } from '../services/api';

const { Content, Footer } = Layout;

interface Message {
  id?: number;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  isLoading?: boolean;  // 标记正在生成
}

const Chat: React.FC = () => {
  const { sessionId: urlSessionId } = useParams<{ sessionId?: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);  // AI正在生成回复
  const [sessionId, setSessionId] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatIntervalRef = useRef<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const token = localStorage.getItem('token');
  const userInfo = JSON.parse(localStorage.getItem('user') || '{}');
  const userName = userInfo.email?.split('@')[0] || '用户';

  // 初始化会话
  useEffect(() => {
    const initSession = async () => {
      if (urlSessionId) {
        setSessionId(parseInt(urlSessionId));
      } else {
        try {
          setIsLoading(true);
          const res = await chatApi.createSession({ 
            job_id: null,
            session_type: 'consultation' 
          });
          const newSessionId = res.data.id;
          setSessionId(newSessionId);
          console.log('Created new AI customer service session:', newSessionId);
        } catch (error) {
          console.error('Failed to create session:', error);
          message.error('创建会话失败');
        } finally {
          setIsLoading(false);
        }
      }
    };

    initSession();
  }, [urlSessionId]);

  // 加载历史消息（最近10轮 = 20条消息）
  useEffect(() => {
    const loadHistory = async () => {
      if (!sessionId) {
        console.log('No sessionId, skipping history load');
        return;
      }

      try {
        setIsLoading(true);
        console.log('Loading history for session:', sessionId);
        const res = await chatApi.getHistory(sessionId);
        console.log('History API full response:', res);
        console.log('History API data:', res.data);
        
        // 后端返回 res.data 直接是消息数组
        const historyMessages = Array.isArray(res.data) ? res.data : [];
        console.log('History messages array:', historyMessages);
        
        if (historyMessages.length === 0) {
          console.log('No history messages found');
        }
        
        // 只取最近20条消息（10轮对话）
        const recentMessages = historyMessages.slice(-20).map((msg: any) => ({
          id: msg.id,
          content: msg.content,
          role: msg.role,
          timestamp: new Date(msg.created_at)
        }));
        
        setMessages(recentMessages);
        console.log(`✅ Loaded ${recentMessages.length} history messages:`, recentMessages);
      } catch (error: any) {
        console.error('Failed to load history:', error);
        console.error('Error details:', error.response?.data || error.message);
        // 不显示错误提示，静默失败
      } finally {
        setIsLoading(false);
      }
    };

    loadHistory();
  }, [sessionId]);

  // 建立WebSocket连接
  useEffect(() => {
    if (!sessionId || !token) {
      return;
    }

    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${wsProtocol}://${window.location.host}/ws/chat/${sessionId}?token=${token}`;
    
    console.log('Connecting to WebSocket:', wsUrl.replace(token, 'TOKEN_HIDDEN'));

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket Connected');
      setIsConnected(true);
      startHeartbeat();
    };

    ws.onmessage = (event) => {
      console.log('WebSocket message:', event.data);
      try {
        const msg = JSON.parse(event.data);
        handleMessage(msg);
      } catch (error) {
        console.error('Failed to parse message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      message.error('连接错误');
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code);
      setIsConnected(false);
      stopHeartbeat();
    };

    wsRef.current = ws;

    return () => {
      stopHeartbeat();
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.close(1000, 'Component unmounting');
      }
    };
  }, [sessionId, token]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const startHeartbeat = () => {
    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  };

  const stopHeartbeat = () => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
  };

  const handleMessage = (msg: any) => {
    switch (msg.type) {
      case 'text':
        // 移除加载占位符，添加真实AI回复
        setMessages(prev => prev.filter(m => !m.isLoading));
        setIsGenerating(false);
        addMessage(msg.content, msg.role || 'assistant');
        break;
      case 'error':
        const errorMsg = msg.message || msg.content || 'Unknown error';
        console.error('Server error:', errorMsg);
        setIsGenerating(false);
        setMessages(prev => prev.filter(m => !m.isLoading));
        message.error(`错误: ${errorMsg}`);
        break;
      case 'system':
        // 忽略系统欢迎消息
        break;
      case 'pong':
        console.log('Heartbeat OK');
        break;
      default:
        console.warn('Unknown message type:', msg.type);
    }
  };

  const addMessage = (content: string, role: any) => {
    setMessages(prev => {
      const newMessages = [...prev, {
        content,
        role,
        timestamp: new Date()
      }];
      // 保持最多20条消息（10轮对话）
      return newMessages.slice(-20);
    });
  };

  const sendTextMessage = async () => {
    if (!inputText.trim()) return;

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // 立即显示用户消息
      addMessage(inputText, 'user');
      
      // 添加"正在生成"占位符
      setIsGenerating(true);
      setMessages(prev => [...prev, {
        content: '正在生成回复...',
        role: 'assistant',
        timestamp: new Date(),
        isLoading: true
      }]);

      // 发送消息
      wsRef.current.send(JSON.stringify({
        type: 'text',
        content: inputText
      }));

      setInputText('');
    } else {
      message.error('连接未建立');
    }
  };

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  return (
    <Layout style={{ height: 'calc(100vh - 64px)', background: '#fff' }}>
      {/* Header */}
      <div style={{ 
        padding: '16px 24px', 
        borderBottom: '1px solid #e8e8e8',
        background: '#fff',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Avatar icon={<RobotOutlined />} style={{ background: '#1890ff' }} />
          <div>
            <div style={{ fontWeight: 600, fontSize: 16 }}>AI 招聘助手</div>
            <div style={{ fontSize: 12, color: '#999' }}>
              {isConnected ? '🟢 在线' : '🔴 离线'}
            </div>
          </div>
        </div>
      </div>
      
      {/* Messages Area - ChatGPT Style */}
      <Content style={{ 
        padding: '24px 0', 
        overflowY: 'auto',
        background: '#f7f7f8'
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto', padding: '0 24px' }}>
          {messages.length === 0 && !isLoading && (
            <div style={{ 
              textAlign: 'center', 
              color: '#999', 
              marginTop: 100,
              fontSize: 14 
            }}>
              <RobotOutlined style={{ fontSize: 48, marginBottom: 16, display: 'block' }} />
              <div>开始与 AI 招聘助手对话</div>
              <div style={{ fontSize: 12, marginTop: 8 }}>我可以帮助您了解招聘流程、职位要求等信息</div>
            </div>
          )}
          
          <List
            dataSource={messages}
            renderItem={(item) => (
              <div style={{ 
                marginBottom: 24,
                display: 'flex',
                gap: 12,
                flexDirection: item.role === 'user' ? 'row-reverse' : 'row'
              }}>
                {/* Avatar */}
                <Avatar 
                  icon={item.role === 'user' ? <UserOutlined /> : (item.isLoading ? <LoadingOutlined spin /> : <RobotOutlined />)}
                  style={{ 
                    background: item.role === 'user' ? '#52c41a' : '#1890ff',
                    flexShrink: 0
                  }}
                />
                
                {/* Message Content */}
                <div style={{ flex: 1, maxWidth: '70%' }}>
                  {/* Name Label */}
                  <div style={{ 
                    fontSize: 12, 
                    color: '#666',
                    marginBottom: 4,
                    fontWeight: 500,
                    textAlign: item.role === 'user' ? 'right' : 'left'
                  }}>
                    {item.role === 'user' ? userName : 'AI 助手'}
                  </div>
                  
                  {/* Message Bubble */}
                  <div style={{
                    background: item.role === 'user' ? '#fff' : '#f4f6f8',
                    padding: '12px 16px',
                    borderRadius: 8,
                    wordBreak: 'break-word',
                    whiteSpace: 'pre-wrap',
                    lineHeight: 1.6,
                    color: item.isLoading ? '#999' : '#262626',
                    fontStyle: item.isLoading ? 'italic' : 'normal',
                    border: item.role === 'user' ? '1px solid #e8e8e8' : 'none'
                  }}>
                    {item.content}
                  </div>
                  
                  {/* Timestamp */}
                  <div style={{ 
                    fontSize: 11, 
                    color: '#999', 
                    marginTop: 4,
                    textAlign: item.role === 'user' ? 'right' : 'left'
                  }}>
                    {item.timestamp.toLocaleTimeString('zh-CN', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </div>
                </div>
              </div>
            )}
          />
          <div ref={messagesEndRef} />
        </div>
      </Content>

      {/* Input Footer - ChatGPT Style */}
      <Footer style={{ 
        background: '#fff', 
        borderTop: '1px solid #e8e8e8', 
        padding: '16px 24px'
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <div style={{ 
            display: 'flex', 
            gap: 12,
            background: '#fff',
            border: '1px solid #d9d9d9',
            borderRadius: 8,
            padding: '8px 12px'
          }}>
            <Input.TextArea
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  sendTextMessage();
                }
              }}
              placeholder="输入消息... (Shift+Enter 换行)"
              autoSize={{ minRows: 1, maxRows: 5 }}
              disabled={!isConnected || isGenerating}
              bordered={false}
              style={{ resize: 'none' }}
            />
            <Button 
              type="primary" 
              icon={<SendOutlined />} 
              onClick={sendTextMessage}
              disabled={!isConnected || !inputText.trim() || isGenerating}
              loading={isGenerating}
              style={{ 
                alignSelf: 'flex-end',
                borderRadius: 6
              }}
            >
              发送
            </Button>
          </div>
          <div style={{ 
            textAlign: 'center', 
            color: '#999', 
            fontSize: 12, 
            marginTop: 8 
          }}>
            {!isConnected ? '正在连接...' : isGenerating ? '正在生成回复...' : ''}
          </div>
        </div>
      </Footer>
    </Layout>
  );
};

export default Chat;
