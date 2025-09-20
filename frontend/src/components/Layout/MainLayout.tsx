import React, { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown, Button, Space, Typography, Badge } from 'antd';
import {
  DashboardOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
// import { useQuery } from '@tanstack/react-query';
// import { systemApi } from '../../services/api';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // 獲取系統健康狀態
  // const { data: healthData } = useQuery({
  //   queryKey: ['system-health'],
  //   queryFn: () => systemApi.getHealth(),
  //   refetchInterval: 30000, // 30秒刷新一次
  // });

  // 菜單項配置
  const menuItems = [
    {
      key: '/test',
      icon: <DashboardOutlined />,
      label: '測試頁面',
    },
  ];

  // 用戶下拉菜單
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '個人資料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '設置',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '登出',
      onClick: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        navigate('/login');
      },
    },
  ];

  // 獲取系統狀態顏色 (暫時註釋掉，避免未使用變量錯誤)
  // const getStatusColor = (status?: string) => {
  //   switch (status) {
  //     case 'HEALTHY': return '#52c41a';
  //     case 'WARNING': return '#faad14';
  //     case 'CRITICAL': return '#ff4d4f';
  //     default: return '#d9d9d9';
  //   }
  // };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{
          background: '#fff',
          boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
        }}
      >
        <div style={{
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: '1px solid #f0f0f0',
        }}>
          <Text strong style={{ fontSize: collapsed ? '16px' : '18px', color: '#1890ff' }}>
            {collapsed ? 'SX' : 'SyrmaX'}
          </Text>
        </div>
        
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ border: 'none' }}
        />
      </Sider>

      <Layout>
        <Header style={{
          padding: '0 24px',
          background: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }}>
          <Space>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{ fontSize: '16px' }}
            />
            
            <Text strong style={{ fontSize: '18px' }}>
              交易機器人控制台
            </Text>
          </Space>

          <Space size="middle">
            {/* 系統狀態指示器 */}
            <Space>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: '#52c41a',
              }} />
              <Text type="secondary">
                系統狀態: 正常
              </Text>
            </Space>

            {/* 通知鈴鐺 */}
            <Badge count={0} size="small">
              <Button type="text" icon={<BellOutlined />} />
            </Badge>

            {/* 用戶頭像和下拉菜單 */}
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              arrow
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} />
                <Text>管理員</Text>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        <Content style={{
          margin: '24px',
          padding: '24px',
          background: '#fff',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          minHeight: 'calc(100vh - 112px)',
        }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
