import { Layout, Menu } from 'antd';
import { HomeOutlined, ToolOutlined, UserOutlined } from '@ant-design/icons';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import HelloFromFastAPI from './HelloFromFastAPI';
import HomePage from './pages/HomePage';
import ToolPage from './pages/ToolPage';
import './App.css';

const { Header, Content, Footer } = Layout;

function TopNav() {
  const location = useLocation();
  const selected = location.pathname.startsWith('/tools') ? 'tools' : 'home';
  return (
    <Header style={{ display: 'flex', alignItems: 'center' }}>
      <UserOutlined style={{ fontSize: 28, color: '#fff', marginRight: 12 }} />
      <span style={{ color: '#fff', fontSize: 20, fontWeight: 'bold', marginRight: 24 }}>
        Company Portal
      </span>
      <Menu
        theme="dark"
        mode="horizontal"
        selectedKeys={[selected]}
        items={[
          {
            key: 'home',
            icon: <HomeOutlined />,
            label: <Link to="/">Home</Link>,
          },
          {
            key: 'tools',
            icon: <ToolOutlined />,
            label: <Link to="/tools">Tool Page</Link>,
          },
        ]}
        style={{ flex: 1 }}
      />
    </Header>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Layout style={{ minHeight: '100vh' }}>
        <TopNav />
        <Content style={{ padding: '24px' }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/tools" element={<ToolPage />} />
            <Route path="/hello" element={<HelloFromFastAPI />} />
          </Routes>
        </Content>
        <Footer style={{ textAlign: 'center' }}>
          ©2025 Company Name. All rights reserved.
        </Footer>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
