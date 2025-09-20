import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, message, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../services/api';

const { Title, Text } = Typography;

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const response = await authApi.login(values.username, values.password);
      // API直接返回 {access: "...", refresh: "..."} 格式
      if (response && response.access && response.refresh) {
        localStorage.setItem('access_token', response.access);
        localStorage.setItem('refresh_token', response.refresh);
        message.success('登入成功！');
        navigate('/dashboard');
      } else {
        message.error('登入失敗：無效的響應格式');
      }
    } catch (error: any) {
      console.error('登入錯誤:', error);
      message.error(error.response?.data?.detail || error.response?.data?.message || '登入失敗，請檢查用戶名和密碼');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px'
    }}>
      <Card
        style={{
          width: '100%',
          maxWidth: 400,
          boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
          borderRadius: '12px'
        }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ margin: 0, color: '#1890ff' }}>
              SyrmaX 交易機器人
            </Title>
            <Text type="secondary">
              智能加密貨幣交易系統
            </Text>
          </div>

          <Form
            name="login"
            onFinish={onFinish}
            layout="vertical"
            size="large"
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: '請輸入用戶名！' }]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="用戶名"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '請輸入密碼！' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密碼"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                style={{ width: '100%', height: '40px' }}
              >
                登入
              </Button>
            </Form.Item>
          </Form>

          <div style={{ textAlign: 'center' }}>
            <Text type="secondary">
              還沒有帳號？{' '}
              <Button 
                type="link" 
                style={{ padding: 0 }}
                onClick={() => {
                  message.info('註冊功能開發中，請使用測試帳號登入');
                }}
              >
                立即註冊
              </Button>
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default LoginPage;
