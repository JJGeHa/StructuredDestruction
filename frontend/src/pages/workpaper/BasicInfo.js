import React from 'react';
import { Descriptions, Card } from 'antd';
import { useOutletContext } from 'react-router-dom';

function BasicInfo() {
  const { assignee } = useOutletContext();
  return (
    <Card title="Basic Information">
      <Descriptions bordered column={1} size="small">
        <Descriptions.Item label="Assignee Name">{assignee.name}</Descriptions.Item>
        <Descriptions.Item label="Assignee Email">{assignee.email || '—'}</Descriptions.Item>
        <Descriptions.Item label="Client">{assignee.client.name}</Descriptions.Item>
        <Descriptions.Item label="Client Owner">{assignee.client.owner || '—'}</Descriptions.Item>
        <Descriptions.Item label="Created">
          {new Date(assignee.created_at).toLocaleString()}
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );
}

export default BasicInfo;

