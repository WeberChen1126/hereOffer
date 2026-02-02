import React from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { Layout, Menu, theme, message } from 'antd';
import { UserOutlined, ProfileOutlined, LogoutOutlined, SettingOutlined, FileTextOutlined, MessageOutlined, BookOutlined } from '@ant-design/icons';
import Login from './pages/Login';
import JobList from './pages/JobList';
import ApplicationList from './pages/ApplicationList';
import Chat from './pages/Chat';
import AdminJobManagement from './pages/AdminJobManagement';
import AdminApplicationManagement from './pages/AdminApplicationManagement';
import AdminKnowledgeManagement from './pages/AdminKnowledgeManagement';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? <>{children}</> : <Navigate to="/login" />;
};

const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const {
    token: { colorBgContainer },
  } = theme.useToken();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    message.success('已退出登录');
    navigate('/login');
  };

  // 安全地获取用户信息
  const getUserInfo = () => {
    try {
      const userStr = localStorage.getItem('user');
      if (!userStr) return {};
      return JSON.parse(userStr);
    } catch (e) {
      console.error('Failed to parse user info:', e);
      return {};
    }
  };
  
  const user = getUserInfo();
  const isAdmin = user.user_type === 'admin';

  // 根据用户类型显示不同菜单
  const menuItems = isAdmin ? [
    {
      key: '/admin/jobs',
      icon: <SettingOutlined />,
      label: '职位管理',
      onClick: () => navigate('/admin/jobs'),
    },
    {
      key: '/admin/applications',
      icon: <FileTextOutlined />,
      label: '投递管理',
      onClick: () => navigate('/admin/applications'),
    },
    {
      key: '/admin/knowledge',
      icon: <BookOutlined />,
      label: '知识库管理',
      onClick: () => navigate('/admin/knowledge'),
    },
    {
      key: '/jobs',
      icon: <ProfileOutlined />,
      label: '职位列表',
      onClick: () => navigate('/jobs'),
    },
    {
      key: '/applications',
      icon: <UserOutlined />,
      label: '我的投递',
      onClick: () => navigate('/applications'),
    },
    {
      key: '/chat',
      icon: <MessageOutlined />,
      label: 'AI客服',
      onClick: () => navigate('/chat'),
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ] : [
    {
      key: '/jobs',
      icon: <ProfileOutlined />,
      label: '职位列表',
      onClick: () => navigate('/jobs'),
    },
    {
      key: '/applications',
      icon: <UserOutlined />,
      label: '我的投递',
      onClick: () => navigate('/applications'),
    },
    {
      key: '/chat',
      icon: <MessageOutlined />,
      label: 'AI客服',
      onClick: () => navigate('/chat'),
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Sider collapsible>
        <div style={{ height: 32, margin: 16, background: 'rgba(255, 255, 255, 0.2)', textAlign: 'center', color: '#fff', lineHeight: '32px', fontWeight: 'bold' }}>
          hereOffer
        </div>
        <Menu 
          theme="dark" 
          selectedKeys={[location.pathname]} 
          mode="inline" 
          items={menuItems}
        />
      </Layout.Sider>
      <Layout>
        <Layout.Header style={{ padding: '0 24px', background: colorBgContainer, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: 16, fontWeight: 'bold' }}>
            {isAdmin ? '🔧 管理员面板' : '👤 求职者中心'}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span><UserOutlined /> {user.email || '用户'}</span>
            <span style={{ 
              padding: '2px 8px', 
              background: isAdmin ? '#1890ff' : '#52c41a',
              color: 'white',
              borderRadius: 4,
              fontSize: 12
            }}>
              {isAdmin ? 'Admin' : 'Candidate'}
            </span>
          </div>
        </Layout.Header>
        <Layout.Content style={{ margin: '16px' }}>
          <div style={{ padding: 24, minHeight: 360, background: colorBgContainer }}>
            {children}
          </div>
        </Layout.Content>
      </Layout>
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/jobs" replace />} />
      
      {/* Candidate Routes */}
      <Route path="/jobs" element={
        <PrivateRoute>
          <MainLayout>
            <JobList />
          </MainLayout>
        </PrivateRoute>
      } />
      
      <Route path="/applications" element={
        <PrivateRoute>
          <MainLayout>
            <ApplicationList />
          </MainLayout>
        </PrivateRoute>
      } />
      
      {/* AI客服 - 通用聊天，不绑定job */}
      <Route path="/chat" element={
        <PrivateRoute>
          <MainLayout>
            <Chat />
          </MainLayout>
        </PrivateRoute>
      } />
      
      {/* 旧的job相关聊天路由，保留兼容性 */}
      <Route path="/chat/:sessionId" element={
        <PrivateRoute>
          <Chat />
        </PrivateRoute>
      } />
      
      {/* Admin Routes */}
      <Route path="/admin/jobs" element={
        <PrivateRoute>
          <MainLayout>
            <AdminJobManagement />
          </MainLayout>
        </PrivateRoute>
      } />
      
      <Route path="/admin/applications" element={
        <PrivateRoute>
          <MainLayout>
            <AdminApplicationManagement />
          </MainLayout>
        </PrivateRoute>
      } />
      
      <Route path="/admin/knowledge" element={
        <PrivateRoute>
          <MainLayout>
            <AdminKnowledgeManagement />
          </MainLayout>
        </PrivateRoute>
      } />
    </Routes>
  );
};

export default App;
