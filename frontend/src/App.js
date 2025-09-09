import { Layout, Menu } from 'antd';
import { HomeOutlined, ToolOutlined, UserOutlined } from '@ant-design/icons';
import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import HelloFromFastAPI from './HelloFromFastAPI';
import HomePage from './pages/HomePage';
import ToolPage from './pages/ToolPage';
import WorkpaperLayout from './pages/workpaper/WorkpaperLayout';
import BasicInfo from './pages/workpaper/BasicInfo';
import TotalOverview from './pages/workpaper/TotalOverview';
import IncomeTaxCalc from './pages/workpaper/calculators/IncomeTaxCalc';
import DeductionsCalc from './pages/workpaper/calculators/DeductionsCalc';
import './App.css';

const { Header, Content, Footer } = Layout;

function TopNav() {
  const location = useLocation();
  const selected = location.pathname.startsWith('/tools') ? 'tools' : 'home';
  return (
    <Header style={{ display: 'flex', alignItems: 'center' }}>
      <img src="/VialtoVixel.svg" alt="Company Logo" style={{ height: 20, marginRight: 16 }} />
      <span style={{ color: '#fff', fontSize: 20, fontWeight: 'bold', marginRight: 24 }}>
        Vi-laver-alt'o 
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
            <Route path="/assignees/:id" element={<WorkpaperLayout />}>
              <Route index element={<Navigate to="basic" replace />} />
              <Route path="basic" element={<BasicInfo />} />
              <Route path="overview" element={<TotalOverview />} />
              <Route path="income-tax" element={<IncomeTaxCalc />} />
              <Route path="deductions" element={<DeductionsCalc />} />
            </Route>
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
