import React, { useEffect } from 'react';
import { Card, Form, InputNumber, Typography, Divider, Button, message } from 'antd';
import { useParams } from 'react-router-dom';
import { API_BASE } from '../../../api';

const { Title } = Typography;

function DeductionsCalc() {
  const { id } = useParams();
  const [form] = Form.useForm();

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/assignees/${id}/calc/deductions`);
        const d = await res.json();
        form.setFieldsValue({
          retirement: Number(d.data.retirement || 0),
          health: Number(d.data.health || 0),
          charity: Number(d.data.charity || 0),
        });
      } catch (e) {
        // ignore
      }
    })();
  }, [id, form]);

  const save = async (values) => {
    try {
      await fetch(`${API_BASE}/assignees/${id}/calc/deductions`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: values }),
      });
      message.success('Saved');
    } catch (e) {
      message.error('Save failed');
    }
  };

  const values = Form.useWatch([], form) || {};
  const total = Number(values.retirement || 0) + Number(values.health || 0) + Number(values.charity || 0);

  return (
    <Card>
      <Title level={4} style={{ marginTop: 0 }}>Deductions Inputs</Title>
      <Form layout="vertical" form={form} onFinish={save}>
        <Form.Item name="retirement" label="Retirement Contributions">
          <InputNumber min={0} step={100} style={{ width: 200 }} />
        </Form.Item>
        <Form.Item name="health" label="Health Expenses">
          <InputNumber min={0} step={100} style={{ width: 200 }} />
        </Form.Item>
        <Form.Item name="charity" label="Charitable Donations">
          <InputNumber min={0} step={100} style={{ width: 200 }} />
        </Form.Item>
        <Divider />
        <div>Total deductions = retirement + health + charity = <strong>{total}</strong></div>
        <Divider />
        <Button type="primary" htmlType="submit">Save</Button>
      </Form>
    </Card>
  );
}

export default DeductionsCalc;

