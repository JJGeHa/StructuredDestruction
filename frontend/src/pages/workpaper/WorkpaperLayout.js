import React, { useEffect, useState } from 'react';
import { Layout, Menu, Typography, Spin } from 'antd';
import { Link, Outlet, useLocation, useParams } from 'react-router-dom';
import { API_BASE } from '../../api';

const { Sider, Content } = Layout;
const { Title } = Typography;

function WorkpaperLayout() {
  const { id } = useParams();
  const location = useLocation();
  const [assignee, setAssignee] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/assignees/${id}`);
        const data = await res.json();
        setAssignee(data);
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [id]);

  const selected = (() => {
    if (location.pathname.endsWith('/overview')) return 'overview';
    if (location.pathname.endsWith('/income-tax')) return 'income-tax';
    if (location.pathname.endsWith('/deductions')) return 'deductions';
    return 'basic';
  })();

  return (
    <Layout style={{ background: '#fff', minHeight: 'calc(100vh - 120px)' }}>
      <Sider width={260} theme="light" style={{ borderRight: '1px solid #eee' }}>
        <div style={{ padding: 16 }}>
          <Title level={4} style={{ margin: 0 }}>{assignee ? assignee.name : 'Assignee'}</Title>
          <div style={{ color: '#888' }}>{assignee ? assignee.client.name : ''}</div>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selected]}
          items={[
            { key: 'basic', label: <Link to="basic">Basic Information</Link> },
            { key: 'overview', label: <Link to="overview">Total Overview</Link> },
            { type: 'divider' },
            { key: 'income-tax', label: <Link to="income-tax">Income Tax</Link> },
            { key: 'deductions', label: <Link to="deductions">Deductions</Link> },
          ]}
        />
      </Sider>
      <Content style={{ padding: 24 }}>
        {loading ? <Spin /> : <Outlet context={{ assignee }} />}
      </Content>
    </Layout>
  );
}

export default WorkpaperLayout;

