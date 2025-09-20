import React from 'react';
import { Card, Typography, Space } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const TestPage: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%', textAlign: 'center' }}>
          <CheckCircleOutlined style={{ fontSize: '64px', color: '#52c41a' }} />
          <Title level={2}>前端運行正常！</Title>
          <Paragraph>
            恭喜！您的 React 前端已經成功啟動並可以正常顯示。
          </Paragraph>
          <Paragraph>
            現在您可以：
          </Paragraph>
          <ul style={{ textAlign: 'left', maxWidth: '400px', margin: '0 auto' }}>
            <li>查看儀表板</li>
            <li>管理交易對</li>
            <li>監控持倉</li>
            <li>查看交易記錄</li>
            <li>配置策略</li>
            <li>系統監控</li>
          </ul>
        </Space>
      </Card>
    </div>
  );
};

export default TestPage;
