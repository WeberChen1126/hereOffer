import React, { useState } from 'react';
import { Card, Form, Input, Button, message, Tabs } from 'antd';
import { useNavigate } from 'react-router-dom';
import { auth } from '../services/api';

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: any, type: 'login' | 'register') => {
    setLoading(true);
    try {
      if (type === 'login') {
        const res = await auth.login(values);
        console.log('Login response:', res); // 调试日志
        
        // 保存 token
        localStorage.setItem('token', res.data.access_token);
        
        // 保存用户信息（如果存在）
        const userInfo = {
          email: values.email,
          user_type: res.data.user_type || 'candidate',
          user_id: res.data.user_id
        };
        localStorage.setItem('user', JSON.stringify(userInfo));
        
        message.success('登录成功');
        navigate('/');
      } else {
        await auth.register({ ...values, user_type: 'candidate' }); // 默认注册为 candidate
        message.success('注册成功，请登录');
      }
    } catch (error) {
      // 错误已在拦截器处理
      console.error('Login/Register error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 400 }}>
        <Tabs items={[
          {
            key: 'login',
            label: '登录',
            children: (
              <Form onFinish={(v) => onFinish(v, 'login')}>
                <Form.Item name="email" rules={[{ required: true, message: '请输入邮箱' }]}>
                  <Input placeholder="邮箱" />
                </Form.Item>
                <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
                  <Input.Password placeholder="密码" />
                </Form.Item>
                <Form.Item>
                  <Button type="primary" htmlType="submit" loading={loading} block>登录</Button>
                </Form.Item>
              </Form>
            )
          },
          {
            key: 'register',
            label: '注册',
            children: (
              <Form onFinish={(v) => onFinish(v, 'register')}>
                <Form.Item name="email" rules={[{ required: true, message: '请输入邮箱' }]}>
                  <Input placeholder="邮箱" />
                </Form.Item>
                <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
                  <Input.Password placeholder="密码" />
                </Form.Item>
                <Form.Item>
                  <Button type="primary" htmlType="submit" loading={loading} block>注册</Button>
                </Form.Item>
              </Form>
            )
          }
        ]} />
      </Card>
    </div>
  );
};

export default Login;
