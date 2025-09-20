import React, { useState } from 'react';
import { Card, Table, Button, Space, Modal, Form, Input, Select, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tradingPairApi } from '../services/api';
import type { TradingPair } from '../types';

const TradingPairsPage: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingPair, setEditingPair] = useState<TradingPair | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // 獲取交易對列表
  const { data: tradingPairsData, isLoading } = useQuery({
    queryKey: ['trading-pairs'],
    queryFn: () => tradingPairApi.getAll(),
  });

  // 創建交易對
  const createMutation = useMutation({
    mutationFn: (data: Partial<TradingPair>) => tradingPairApi.create(data),
    onSuccess: () => {
      message.success('交易對創建成功！');
      queryClient.invalidateQueries({ queryKey: ['trading-pairs'] });
      setIsModalVisible(false);
      form.resetFields();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '創建失敗');
    },
  });

  // 更新交易對
  const updateMutation = useMutation({
    mutationFn: ({ symbol, data }: { symbol: string; data: Partial<TradingPair> }) =>
      tradingPairApi.update(symbol, data),
    onSuccess: () => {
      message.success('交易對更新成功！');
      queryClient.invalidateQueries({ queryKey: ['trading-pairs'] });
      setIsModalVisible(false);
      setEditingPair(null);
      form.resetFields();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '更新失敗');
    },
  });

  // 刪除交易對
  const deleteMutation = useMutation({
    mutationFn: (symbol: string) => tradingPairApi.delete(symbol),
    onSuccess: () => {
      message.success('交易對刪除成功！');
      queryClient.invalidateQueries({ queryKey: ['trading-pairs'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '刪除失敗');
    },
  });

  const handleAdd = () => {
    setEditingPair(null);
    setIsModalVisible(true);
    form.resetFields();
  };

  const handleEdit = (record: TradingPair) => {
    setEditingPair(record);
    setIsModalVisible(true);
    form.setFieldsValue(record);
  };

  const handleDelete = (symbol: string) => {
    deleteMutation.mutate(symbol);
  };

  const handleModalOk = () => {
    form.validateFields().then((values) => {
      if (editingPair) {
        updateMutation.mutate({ symbol: editingPair.symbol, data: values });
      } else {
        createMutation.mutate(values);
      }
    });
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingPair(null);
    form.resetFields();
  };

  const columns = [
    {
      title: '交易對',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => (
        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>{symbol}</span>
      ),
    },
    {
      title: 'K線週期',
      dataIndex: 'interval',
      key: 'interval',
    },
    {
      title: '精度',
      dataIndex: 'precision',
      key: 'precision',
    },
    {
      title: '平均ATR',
      dataIndex: 'average_atr',
      key: 'average_atr',
      render: (value: number) => value ? value.toFixed(6) : '-',
    },
    {
      title: '連續止損',
      dataIndex: 'consecutive_stop_loss',
      key: 'consecutive_stop_loss',
      render: (count: number) => (
        <span style={{ color: count > 2 ? '#ff4d4f' : count > 0 ? '#faad14' : '#52c41a' }}>
          {count}
        </span>
      ),
    },
    {
      title: '上次交易時間',
      dataIndex: 'last_trade_time',
      key: 'last_trade_time',
      render: (time: string) => time ? new Date(time).toLocaleString() : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: TradingPair) => (
        <Space size="middle">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            編輯
          </Button>
          <Popconfirm
            title="確定要刪除這個交易對嗎？"
            onConfirm={() => handleDelete(record.symbol)}
            okText="確定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
            >
              刪除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="交易對管理"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            添加交易對
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={tradingPairsData?.data || []}
          loading={isLoading}
          rowKey="symbol"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 條記錄`,
          }}
        />
      </Card>

      <Modal
        title={editingPair ? '編輯交易對' : '添加交易對'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="symbol"
            label="交易對符號"
            rules={[{ required: true, message: '請輸入交易對符號！' }]}
          >
            <Input placeholder="例如：BTCUSDT" />
          </Form.Item>

          <Form.Item
            name="interval"
            label="K線週期"
            rules={[{ required: true, message: '請選擇K線週期！' }]}
          >
            <Select placeholder="選擇K線週期">
              <Select.Option value="1m">1分鐘</Select.Option>
              <Select.Option value="5m">5分鐘</Select.Option>
              <Select.Option value="15m">15分鐘</Select.Option>
              <Select.Option value="1h">1小時</Select.Option>
              <Select.Option value="4h">4小時</Select.Option>
              <Select.Option value="1d">1天</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="precision"
            label="數量精度"
            rules={[{ required: true, message: '請輸入數量精度！' }]}
          >
            <Input type="number" placeholder="例如：3" />
          </Form.Item>

          <Form.Item
            name="average_atr"
            label="平均ATR"
          >
            <Input type="number" step="0.000001" placeholder="例如：0.000123" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TradingPairsPage;
