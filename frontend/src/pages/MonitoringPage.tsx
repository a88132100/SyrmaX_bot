import React from 'react';
import { Card, Row, Col, Progress, Typography, Table, Tag, Statistic } from 'antd';
import { 
  MonitorOutlined, 
  AlertOutlined, 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined 
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { systemApi } from '../services/api';

const { Title } = Typography;

const MonitoringPage: React.FC = () => {
  // 獲取系統健康狀態
  const { data: healthData, isLoading: healthLoading } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => systemApi.getHealth(),
    refetchInterval: 5000, // 5秒刷新一次
  });

  // 獲取監控儀表板數據
  // const { isLoading: dashboardLoading } = useQuery({
  //   queryKey: ['monitoring-dashboard'],
  //   queryFn: () => systemApi.getDashboard(),
  //   refetchInterval: 10000, // 10秒刷新一次
  // });

  // 獲取告警列表
  const { isLoading: alertsLoading } = useQuery({
    queryKey: ['monitoring-alerts'],
    queryFn: () => systemApi.getAlerts(),
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'WARNING':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case 'CRITICAL':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <AlertOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'HEALTHY': return '#52c41a';
      case 'WARNING': return '#faad14';
      case 'CRITICAL': return '#ff4d4f';
      default: return '#d9d9d9';
    }
  };

  const getAlertLevelColor = (level: string) => {
    switch (level) {
      case 'INFO': return 'blue';
      case 'WARNING': return 'orange';
      case 'CRITICAL': return 'red';
      case 'EMERGENCY': return 'red';
      default: return 'default';
    }
  };

  // 模擬告警數據（實際應該從API獲取）
  const mockAlerts = [
    {
      id: 1,
      level: 'WARNING',
      message: 'CPU使用率超過80%',
      timestamp: new Date().toISOString(),
      status: 'ACTIVE',
    },
    {
      id: 2,
      level: 'INFO',
      message: '系統正常運行',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      status: 'RESOLVED',
    },
    {
      id: 3,
      level: 'CRITICAL',
      message: '內存使用率超過90%',
      timestamp: new Date(Date.now() - 600000).toISOString(),
      status: 'ACTIVE',
    },
  ];

  const alertColumns = [
    {
      title: '級別',
      dataIndex: 'level',
      key: 'level',
      render: (level: string) => (
        <Tag color={getAlertLevelColor(level)}>
          {level}
        </Tag>
      ),
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'ACTIVE' ? 'red' : 'green'}>
          {status === 'ACTIVE' ? '活躍' : '已解決'}
        </Tag>
      ),
    },
    {
      title: '時間',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (time: string) => new Date(time).toLocaleString(),
    },
  ];

  return (
    <div>
      <Title level={2}>系統監控</Title>
      
      {/* 系統狀態概覽 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="系統狀態"
              value={healthData?.data?.status || 'UNKNOWN'}
              prefix={getStatusIcon(healthData?.data?.status || 'UNKNOWN')}
              valueStyle={{ color: getStatusColor(healthData?.data?.status || 'UNKNOWN') }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="網絡狀態"
              value={healthData?.data?.network_status || 'UNKNOWN'}
              prefix={<MonitorOutlined />}
              valueStyle={{ 
                color: healthData?.data?.network_status === 'ONLINE' ? '#52c41a' : '#ff4d4f' 
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活躍告警"
              value={mockAlerts.filter(alert => alert.status === 'ACTIVE').length}
              prefix={<AlertOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="最後更新"
              value={healthData?.data?.last_updated ? 
                new Date(healthData.data.last_updated).toLocaleTimeString() : 
                '未知'
              }
              prefix={<MonitorOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 資源使用情況 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={8}>
          <Card title="CPU 使用率" loading={healthLoading}>
            <Progress
              percent={healthData?.data?.cpu_percent || 0}
              status={(healthData?.data?.cpu_percent || 0) > 80 ? 'exception' : 'active'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
            <div style={{ marginTop: '8px', textAlign: 'center' }}>
              {healthData?.data?.cpu_percent || 0}%
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card title="內存使用率" loading={healthLoading}>
            <Progress
              percent={healthData?.data?.memory_percent || 0}
              status={(healthData?.data?.memory_percent || 0) > 80 ? 'exception' : 'active'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
            <div style={{ marginTop: '8px', textAlign: 'center' }}>
              {healthData?.data?.memory_percent || 0}%
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card title="磁盤使用率" loading={healthLoading}>
            <Progress
              percent={healthData?.data?.disk_percent || 0}
              status={(healthData?.data?.disk_percent || 0) > 80 ? 'exception' : 'active'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
            <div style={{ marginTop: '8px', textAlign: 'center' }}>
              {healthData?.data?.disk_percent || 0}%
            </div>
          </Card>
        </Col>
      </Row>

      {/* 告警列表 */}
      <Card title="系統告警" loading={alertsLoading}>
        <Table
          columns={alertColumns}
          dataSource={mockAlerts}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
};

export default MonitoringPage;
