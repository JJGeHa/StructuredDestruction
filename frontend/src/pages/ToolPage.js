import React, { useState } from 'react';
import { Tabs, Form, Input, Button, Space, message, Upload, Card, Typography } from 'antd';
import { API_BASE } from '../api';
import Ideas from '../Ideas';

const { Title } = Typography;

function CoverLetterTool() {
  const [form] = Form.useForm();
  const [content, setContent] = useState('');
  const onFinish = async (values) => {
    try {
      const highlights = (values.highlights || '').split('\n').map(s => s.trim()).filter(Boolean);
      const res = await fetch(`${API_BASE}/tools/cover-letter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_name: values.candidateName,
          role: values.role,
          company: values.company,
          highlights,
        }),
      });
      const data = await res.json();
      setContent(data.content || '');
    } catch (e) {
      message.error('Failed to generate');
    }
  };
  return (
    <Space direction="vertical" style={{ display: 'flex' }} size="large">
      <Card>
        <Title level={4} style={{ marginTop: 0 }}>Cover Letter Generator</Title>
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="candidateName" label="Your Name" rules={[{ required: true }]}>
            <Input placeholder="Jane Doe" />
          </Form.Item>
          <Form.Item name="role" label="Role" rules={[{ required: true }]}>
            <Input placeholder="Senior Analyst" />
          </Form.Item>
          <Form.Item name="company" label="Company" rules={[{ required: true }]}>
            <Input placeholder="Contoso" />
          </Form.Item>
          <Form.Item name="highlights" label="Highlights (one per line)">
            <Input.TextArea rows={4} placeholder="Led X project...\nImproved Y by Z%..." />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">Generate</Button>
          </Form.Item>
        </Form>
      </Card>
      {content && (
        <Card>
          <Title level={5}>Generated Letter</Title>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{content}</pre>
        </Card>
      )}
    </Space>
  );
}

function PdfTool() {
  const [form] = Form.useForm();
  const onFinish = async (values) => {
    try {
      let fields = {};
      try { fields = JSON.parse(values.fieldsJson || '{}'); } catch (e) { throw new Error('Invalid JSON'); }
      const res = await fetch(`${API_BASE}/tools/pdf-fill`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: values.title || 'Generated Form', fields }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'PDF generation failed');
      }
      const data = await res.json();
      const blob = b64ToBlob(data.content_b64, 'application/pdf');
      triggerDownload(blob, data.filename || 'form.pdf');
      message.success('PDF generated');
    } catch (e) {
      message.error(e.message || 'Failed');
    }
  };
  return (
    <Card>
      <Title level={4} style={{ marginTop: 0 }}>PDF Form Filler</Title>
      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Form.Item name="title" label="Document Title">
          <Input placeholder="Generated Form" />
        </Form.Item>
        <Form.Item name="fieldsJson" label="Fields (JSON object)" rules={[{ required: true }]}>
          <Input.TextArea rows={6} placeholder='{"Name":"Jane Doe","ID":"12345"}' />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit">Generate PDF</Button>
        </Form.Item>
      </Form>
    </Card>
  );
}

function EmailTool() {
  const [form] = Form.useForm();
  const [files, setFiles] = useState([]);
  const toBase64 = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
  const onFinish = async (values) => {
    try {
      const attachments = await Promise.all(
        files.map(async (f) => ({ filename: f.name, content_b64: await toBase64(f), mimetype: f.type || 'application/octet-stream' }))
      );
      const res = await fetch(`${API_BASE}/tools/send-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ to: (values.to || '').split(',').map(s => s.trim()).filter(Boolean), subject: values.subject, body: values.body, attachments }),
      });
      const data = await res.json();
      if (data.status === 'sent') message.success('Email sent');
      else message.info('Preview only (SMTP not configured)');
    } catch (e) {
      message.error('Failed to send');
    }
  };
  return (
    <Card>
      <Title level={4} style={{ marginTop: 0 }}>Email Sender</Title>
      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Form.Item name="to" label="To (comma-separated)" rules={[{ required: true }]}>
          <Input placeholder="user1@example.com, user2@example.com" />
        </Form.Item>
        <Form.Item name="subject" label="Subject" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="body" label="Body" rules={[{ required: true }]}>
          <Input.TextArea rows={6} />
        </Form.Item>
        <Form.Item label="Attachments">
          <Upload beforeUpload={() => false} multiple fileList={files} onChange={({ fileList }) => setFiles(fileList.map(f => f.originFileObj))}>
            <Button>Select Files</Button>
          </Upload>
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit">Send</Button>
        </Form.Item>
      </Form>
    </Card>
  );
}

function b64ToBlob(base64, type) {
  const byteCharacters = atob(base64);
  const byteNumbers = new Array(byteCharacters.length);
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  return new Blob([byteArray], { type });
}

function triggerDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

function ToolPage() {
  return (
    <Tabs
      defaultActiveKey="cover"
      items={[
        { key: 'cover', label: 'Cover Letter', children: <CoverLetterTool /> },
        { key: 'pdf', label: 'PDF Filler', children: <PdfTool /> },
        { key: 'email', label: 'Email Sender', children: <EmailTool /> },
        { key: 'ideas', label: 'Ideas (Sample Tool)', children: <Ideas /> },
      ]}
    />
  );
}

export default ToolPage;
