import React, { useEffect, useState } from 'react';
import { Card, Descriptions, Table, Typography, message } from 'antd';
import { useOutletContext, useParams } from 'react-router-dom';
import { API_BASE } from '../../api';

const { Title } = Typography;

function TotalOverview() {
  const { assignee } = useOutletContext();
  const { id } = useParams();
  const [data, setData] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/assignees/${id}/overview`);
        const d = await res.json();
        setData(d);
      } catch (e) {
        message.error('Failed to load overview');
      }
    })();
  }, [id]);

  if (!data) return null;

  const incomeRows = Object.entries(data.inputs.income || {}).map(([k, v]) => ({ key: k, item: k, amount: Number(v) }));
  const dedRows = Object.entries(data.inputs.deductions || {}).map(([k, v]) => ({ key: k, item: k, amount: Number(v) }));

  return (
    <div>
      <Title level={4}>Total Overview</Title>
      <Card style={{ marginBottom: 16 }}>
        <Descriptions bordered size="small" column={2}>
          <Descriptions.Item label="Income Total">{data.income_total}</Descriptions.Item>
          <Descriptions.Item label="Deductions Total">{data.deductions_total}</Descriptions.Item>
          <Descriptions.Item label="Taxable Income">{data.taxable_income}</Descriptions.Item>
          <Descriptions.Item label="Estimated Tax (25%)">{data.estimated_tax}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="Income inputs" style={{ marginBottom: 16 }}>
        <Table dataSource={incomeRows} pagination={false} size="small"
               columns={[{ title: 'Item', dataIndex: 'item' }, { title: 'Amount', dataIndex: 'amount' }]} />
      </Card>
      <Card title="Deductions inputs">
        <Table dataSource={dedRows} pagination={false} size="small"
               columns={[{ title: 'Item', dataIndex: 'item' }, { title: 'Amount', dataIndex: 'amount' }]} />
      </Card>
    </div>
  );
}

export default TotalOverview;

