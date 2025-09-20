import React from 'react';
import { Card, Form, Switch, Button, InputNumber, message, Space, Divider } from 'antd';
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { traderStatusApi } from '../services/api';

// const { Option } = Select;

const SettingsPage: React.FC = () => {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // 獲取交易員狀態
  const { data: statusData, isLoading } = useQuery({
    queryKey: ['trader-status'],
    queryFn: () => traderStatusApi.getStatus(),
  });

  // 更新交易員狀態
  const updateMutation = useMutation({
    mutationFn: (data: any) => traderStatusApi.updateStatus(data),
    onSuccess: () => {
      message.success('設置保存成功！');
      queryClient.invalidateQueries({ queryKey: ['trader-status'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '保存失敗');
    },
  });

  // 切換交易狀態
  const toggleTradingMutation = useMutation({
    mutationFn: (enabled: boolean) => traderStatusApi.toggleTrading(enabled),
    onSuccess: () => {
      message.success('交易狀態更新成功！');
      queryClient.invalidateQueries({ queryKey: ['trader-status'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '更新失敗');
    },
  });

  const handleSave = (values: any) => {
    updateMutation.mutate(values);
  };

  const handleToggleTrading = (enabled: boolean) => {
    toggleTradingMutation.mutate(enabled);
  };

  return (
    <div>
      <Card title="系統設置" loading={isLoading}>
        <Form
          form={form}
          layout="vertical"
          initialValues={statusData?.data}
          onFinish={handleSave}
        >
          {/* 交易控制 */}
          <Card title="交易控制" size="small" style={{ marginBottom: '16px' }}>
            <Form.Item
              name="is_trading_enabled"
              label="啟用交易"
              valuePropName="checked"
            >
              <Switch
                checkedChildren="啟用"
                unCheckedChildren="禁用"
                onChange={handleToggleTrading}
              />
            </Form.Item>
            
            <Form.Item
              name="stop_signal_received"
              label="停止信號"
              valuePropName="checked"
            >
              <Switch
                checkedChildren="已接收"
                unCheckedChildren="未接收"
              />
            </Form.Item>
          </Card>

          {/* 交易限制 */}
          <Card title="交易限制" size="small" style={{ marginBottom: '16px' }}>
            <Form.Item
              name="hourly_trade_count"
              label="每小時交易次數"
            >
              <InputNumber
                min={0}
                max={1000}
                style={{ width: '100%' }}
                placeholder="例如：10"
              />
            </Form.Item>
            
            <Form.Item
              name="daily_trade_count"
              label="每日交易次數"
            >
              <InputNumber
                min={0}
                max={10000}
                style={{ width: '100%' }}
                placeholder="例如：100"
              />
            </Form.Item>
          </Card>

          <Divider />

          <Space>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              loading={updateMutation.isPending}
            >
              保存設置
            </Button>
            
            <Button
              icon={<ReloadOutlined />}
              onClick={() => form.resetFields()}
            >
              重置
            </Button>
          </Space>
        </Form>
      </Card>
    </div>
  );
};

export default SettingsPage;
