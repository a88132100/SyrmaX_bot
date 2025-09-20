import React, { useState } from 'react';
import { Card, Table, Button, Space, Modal, Form, Input, Select, message, Switch, Tag } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SettingOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { strategyComboApi } from '../services/api';
import type { StrategyCombo } from '../types';

const { TextArea } = Input;

const StrategyPage: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState<StrategyCombo | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // 獲取策略組合列表
  const { data: strategiesData, isLoading } = useQuery({
    queryKey: ['strategy-combos'],
    queryFn: () => strategyComboApi.getAll(),
  });

  // 創建策略組合
  const createMutation = useMutation({
    mutationFn: (data: Partial<StrategyCombo>) => strategyComboApi.create(data),
    onSuccess: () => {
      message.success('策略組合創建成功！');
      queryClient.invalidateQueries({ queryKey: ['strategy-combos'] });
      setIsModalVisible(false);
      form.resetFields();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '創建失敗');
    },
  });

  // 更新策略組合
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<StrategyCombo> }) =>
      strategyComboApi.update(id, data),
    onSuccess: () => {
      message.success('策略組合更新成功！');
      queryClient.invalidateQueries({ queryKey: ['strategy-combos'] });
      setIsModalVisible(false);
      setEditingStrategy(null);
      form.resetFields();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '更新失敗');
    },
  });

  // 刪除策略組合
  const deleteMutation = useMutation({
    mutationFn: (id: number) => strategyComboApi.delete(id),
    onSuccess: () => {
      message.success('策略組合刪除成功！');
      queryClient.invalidateQueries({ queryKey: ['strategy-combos'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '刪除失敗');
    },
  });

  // 啟用策略組合
  const activateMutation = useMutation({
    mutationFn: (id: number) => strategyComboApi.activate(id),
    onSuccess: () => {
      message.success('策略組合啟用成功！');
      queryClient.invalidateQueries({ queryKey: ['strategy-combos'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '啟用失敗');
    },
  });

  const handleAdd = () => {
    setEditingStrategy(null);
    setIsModalVisible(true);
    form.resetFields();
  };

  const handleEdit = (record: StrategyCombo) => {
    setEditingStrategy(record);
    setIsModalVisible(true);
    form.setFieldsValue(record);
  };

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id);
  };

  const handleActivate = (id: number) => {
    activateMutation.mutate(id);
  };

  const handleModalOk = () => {
    form.validateFields().then((values) => {
      if (editingStrategy) {
        updateMutation.mutate({ id: editingStrategy.id, data: values });
      } else {
        createMutation.mutate(values);
      }
    });
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingStrategy(null);
    form.resetFields();
  };

  const getComboModeColor = (mode: string) => {
    switch (mode) {
      case 'aggressive': return 'red';
      case 'balanced': return 'blue';
      case 'conservative': return 'green';
      case 'auto': return 'purple';
      case 'custom': return 'orange';
      default: return 'default';
    }
  };

  const getComboModeText = (mode: string) => {
    switch (mode) {
      case 'aggressive': return '激進';
      case 'balanced': return '平衡';
      case 'conservative': return '保守';
      case 'auto': return '自動';
      case 'custom': return '自定義';
      default: return mode;
    }
  };

  const columns = [
    {
      title: '策略名稱',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <span style={{ fontWeight: 'bold' }}>{name}</span>
      ),
    },
    {
      title: '模式',
      dataIndex: 'combo_mode',
      key: 'combo_mode',
      render: (mode: string) => (
        <Tag color={getComboModeColor(mode)}>
          {getComboModeText(mode)}
        </Tag>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '狀態',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'default'}>
          {active ? '啟用中' : '未啟用'}
        </Tag>
      ),
    },
    {
      title: '創建時間',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: StrategyCombo) => (
        <Space size="middle">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            編輯
          </Button>
          {!record.is_active && (
            <Button
              type="link"
              icon={<SettingOutlined />}
              onClick={() => handleActivate(record.id)}
            >
              啟用
            </Button>
          )}
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            刪除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="策略配置"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            添加策略組合
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={strategiesData?.data || []}
          loading={isLoading}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 條記錄`,
          }}
        />
      </Card>

      <Modal
        title={editingStrategy ? '編輯策略組合' : '添加策略組合'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="策略名稱"
            rules={[{ required: true, message: '請輸入策略名稱！' }]}
          >
            <Input placeholder="例如：我的平衡策略" />
          </Form.Item>

          <Form.Item
            name="combo_mode"
            label="策略模式"
            rules={[{ required: true, message: '請選擇策略模式！' }]}
          >
            <Select placeholder="選擇策略模式">
              <Select.Option value="aggressive">激進模式</Select.Option>
              <Select.Option value="balanced">平衡模式</Select.Option>
              <Select.Option value="conservative">保守模式</Select.Option>
              <Select.Option value="auto">自動模式</Select.Option>
              <Select.Option value="custom">自定義模式</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={3} placeholder="描述這個策略組合的特點和用途" />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="是否啟用"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default StrategyPage;
