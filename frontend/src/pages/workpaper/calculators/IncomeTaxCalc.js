import React, { useEffect } from 'react';
import { Card, Form, InputNumber, Typography, Divider, Button, message } from 'antd';
import { useParams } from 'react-router-dom';
import { API_BASE } from '../../../api';

const { Title } = Typography;

function IncomeTaxCalc() {
  const { id } = useParams();
  const [form] = Form.useForm();

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/assignees/${id}/calc/income-tax`);
        const d = await res.json();
        form.setFieldsValue({
          salary: Number(d.data.salary || 0),
          bonus: Number(d.data.bonus || 0),
          other: Number(d.data.other || 0),
        });
      } catch (e) {
        // ignore
      }
    })();
  }, [id, form]);

  const save = async (values) => {
    try {
      await fetch(`${API_BASE}/assignees/${id}/calc/income-tax`, {
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
  const incomeTotal = Number(values.salary || 0) + Number(values.bonus || 0) + Number(values.other || 0);

  return (
    <Card>
      <Title level={4} style={{ marginTop: 0 }}>Income Tax Inputs</Title>
      <Form layout="vertical" form={form} onFinish={save}>
        <Form.Item name="salary" label="Salary">
          <InputNumber min={0} step={100} style={{ width: 200 }} />
        </Form.Item>
        <Form.Item name="bonus" label="Bonus">
          <InputNumber min={0} step={100} style={{ width: 200 }} />
        </Form.Item>
        <Form.Item name="other" label="Other Income">
          <InputNumber min={0} step={100} style={{ width: 200 }} />
        </Form.Item>
        <Divider />
        <div>Income total = salary + bonus + other = <strong>{incomeTotal}</strong></div>
        <Divider />
        <Button type="primary" htmlType="submit">Save</Button>
      </Form>
    </Card>
  );
}

export default IncomeTaxCalc;

