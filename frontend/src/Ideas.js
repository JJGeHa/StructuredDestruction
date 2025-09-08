import React, { useEffect, useMemo, useState } from 'react';
import { Table, Tag, Form, Input, Button, Space, message, Typography, Card } from 'antd';
import { API_BASE } from './api';

const { Title, Paragraph } = Typography;

// Use shared API base

function Ideas() {
  const [ideas, setIdeas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form] = Form.useForm();

  const fetchIdeas = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/ideas`);
      const data = await res.json();
      setIdeas(data);
    } catch (e) {
      message.error('Failed to load ideas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIdeas();
  }, []);

  const onCreate = async (values) => {
    setCreating(true);
    try {
      const res = await fetch(`${API_BASE}/ideas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to create');
      }
      form.resetFields();
      message.success('Idea added');
      fetchIdeas();
    } catch (e) {
      message.error(e.message || 'Failed to create');
    } finally {
      setCreating(false);
    }
  };

  const onDelete = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/ideas/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete');
      message.success('Idea deleted');
      setIdeas((prev) => prev.filter((i) => i.id !== id));
    } catch (e) {
      message.error('Delete failed');
    }
  };

  const columns = useMemo(
    () => [
      { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
      {
        title: 'Title',
        dataIndex: 'title',
        key: 'title',
        render: (text) => <strong>{text}</strong>,
      },
      { title: 'Description', dataIndex: 'description', key: 'description' },
      {
        title: 'Score',
        dataIndex: 'score',
        key: 'score',
        width: 120,
        render: (score) => {
          let color = 'blue';
          if (score >= 10) color = 'red';
          else if (score >= 6) color = 'orange';
          else if (score >= 3) color = 'green';
          return <Tag color={color}>{score}</Tag>;
        },
      },
      { title: 'Created', dataIndex: 'created_at', key: 'created_at', width: 180 },
      {
        title: 'Actions',
        key: 'actions',
        width: 140,
        render: (_, record) => (
          <Space>
            <Button danger size="small" onClick={() => onDelete(record.id)}>
              Delete
            </Button>
          </Space>
        ),
      },
    ],
    []
  );

  return (
    <Space direction="vertical" size="large" style={{ display: 'flex' }}>
      <Card>
        <Title level={3} style={{ marginTop: 0 }}>Submit an Idea</Title>
        <Paragraph type="secondary">
          Enter a title and description. The backend will compute a simple
          priority score using keywords (e.g., risk, impact, urgent).
        </Paragraph>
        <Form form={form} layout="vertical" onFinish={onCreate}>
          <Form.Item name="title" label="Title" rules={[{ required: true, message: 'Please enter a title' }]}>
            <Input placeholder="Short, descriptive title" maxLength={120} />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea placeholder="Add context, risks, impact, etc." rows={4} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={creating}>
              Add Idea
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card>
        <Title level={3} style={{ marginTop: 0 }}>Ideas</Title>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={ideas}
          loading={loading}
          pagination={{ pageSize: 5 }}
        />
      </Card>
    </Space>
  );
}

export default Ideas;
