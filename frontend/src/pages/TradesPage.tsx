import React from 'react';
import { Card, Table, Tag, Typography, Space, DatePicker, Select, Input } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { tradeApi } from '../services/api';

const { Title } = Typography;
const { RangePicker } = DatePicker;

const TradesPage: React.FC = () => {
  // 獲取交易記錄
  const { data: tradesData, isLoading } = useQuery({
    queryKey: ['trades'],
    queryFn: () => tradeApi.getTrades({ page: 1, page_size: 50 }),
  });

  const columns = [
    {
      title: '交易對',
      dataIndex: 'trading_pair',
      key: 'trading_pair',
      render: (symbol: string) => (
        <Tag color="blue">{symbol}</Tag>
      ),
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'BUY' ? 'green' : 'red'}>
          {side === 'BUY' ? '買入' : '賣出'}
        </Tag>
      ),
    },
    {
      title: '開倉價格',
      dataIndex: 'entry_price',
      key: 'entry_price',
      render: (price: number) => `$${price.toFixed(2)}`,
    },
    {
      title: '平倉價格',
      dataIndex: 'exit_price',
      key: 'exit_price',
      render: (price: number) => `$${price.toFixed(2)}`,
    },
    {
      title: '數量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '損益',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <span style={{ color: pnl >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)} USDT
        </span>
      ),
    },
    {
      title: '平倉原因',
      dataIndex: 'reason',
      key: 'reason',
      render: (reason: string) => (
        <Tag color={reason.includes('stop') ? 'red' : 'green'}>
          {reason}
        </Tag>
      ),
    },
    {
      title: '交易時間',
      dataIndex: 'trade_time',
      key: 'trade_time',
      render: (time: string) => new Date(time).toLocaleString(),
    },
  ];

  return (
    <div>
      <Title level={2}>交易記錄</Title>
      
      {/* 搜索和篩選 */}
      <Card style={{ marginBottom: '16px' }}>
        <Space wrap>
          <Input
            placeholder="搜索交易對"
            prefix={<SearchOutlined />}
            style={{ width: 200 }}
          />
          <Select placeholder="選擇方向" style={{ width: 120 }}>
            <Select.Option value="BUY">買入</Select.Option>
            <Select.Option value="SELL">賣出</Select.Option>
          </Select>
          <RangePicker placeholder={['開始日期', '結束日期']} />
        </Space>
      </Card>

      {/* 交易記錄表格 */}
      <Card title="交易記錄">
        <Table
          columns={columns}
          dataSource={tradesData?.results || []}
          loading={isLoading}
          rowKey="id"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 條記錄`,
          }}
        />
      </Card>
    </div>
  );
};

export default TradesPage;
