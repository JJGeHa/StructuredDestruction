import React, { useEffect, useMemo, useState } from 'react';
import { Card, Col, Row, List, Typography, Input, Table, Button, Space, Tag, message } from 'antd';
import { API_BASE } from '../api';
import { Link } from 'react-router-dom';

const { Title, Text } = Typography;
// Use shared API base

function HomePage() {
  const [overview, setOverview] = useState({ my_clients: [], awaiting_clients: [], stats: {} });
  const [myAssignees, setMyAssignees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [q, setQ] = useState('');
  const [results, setResults] = useState([]);

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/home/overview?owner=demo`);
      const data = await res.json();
      setOverview(data);
    } catch (e) {
      message.error('Failed to load overview');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/home/my-assignees?owner=demo`);
        const data = await res.json();
        setMyAssignees(data);
      } catch (e) {
        // ignore for now
      }
    })();
  }, []);

  const onSearch = async (value) => {
    try {
      const res = await fetch(`${API_BASE}/clients/search?q=${encodeURIComponent(value)}`);
      const data = await res.json();
      setResults(data);
    } catch (e) {
      message.error('Search failed');
    }
  };

  const onAssign = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/clients/${id}/assign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ owner: 'demo' }),
      });
      if (!res.ok) throw new Error('Assign failed');
      message.success('Client assigned to you');
      fetchOverview();
    } catch (e) {
      message.error('Failed to assign');
    }
  };

  const columns = useMemo(
    () => [
      { title: 'Client', dataIndex: 'name', key: 'name' },
      {
        title: 'Owner',
        dataIndex: 'owner',
        key: 'owner',
        width: 160,
        render: (owner) => (owner ? <Tag color="blue">{owner}</Tag> : <Tag>unassigned</Tag>),
      },
      {
        title: 'Action',
        key: 'action',
        width: 260,
        render: (_, record) => (
          <Space>
            <Button type="primary" disabled={record.owner === 'demo'} onClick={() => onAssign(record.id)}>
              {record.owner === 'demo' ? 'Assigned' : 'Add to My Clients'}
            </Button>
            <Link to="/assignees/1">Open Workpaper</Link>
          </Space>
        ),
      },
    ],
    []
  );

  return (
    <Space direction="vertical" size="large" style={{ display: 'flex' }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card loading={loading} title={<Title level={4} style={{ margin: 0 }}>My Assignees</Title>}>
            <List
              dataSource={myAssignees}
              renderItem={(item) => (
                <List.Item>
                  <Link to={`/assignees/${item.id}`}>{item.name} - {item.client_name}</Link>
                </List.Item>
              )}
              locale={{ emptyText: 'No assignees yet' }}
            />
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card loading={loading} title={<Title level={4} style={{ margin: 0 }}>Clients with Awaiting Tasks</Title>}>
            <List
              dataSource={overview.awaiting_clients}
              renderItem={(item) => <List.Item>{item.name}</List.Item>}
              locale={{ emptyText: 'No awaiting tasks' }}
            />
            <div style={{ marginTop: 12 }}>
              <Text type="secondary">Awaiting tasks: {overview.stats.awaiting_tasks_count || 0}</Text>
            </div>
          </Card>
        </Col>
      </Row>

      <Card>
        <Title level={4} style={{ marginTop: 0 }}>Find New Clients</Title>
        <Input.Search
          placeholder="Search clients by name"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onSearch={onSearch}
          enterButton
          allowClear
          style={{ maxWidth: 520 }}
        />
        <div style={{ height: 12 }} />
        <Table rowKey="id" columns={columns} dataSource={results} pagination={{ pageSize: 5 }} />
      </Card>
    </Space>
  );
}

export default HomePage;
