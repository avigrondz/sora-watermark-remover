import React from 'react';
import { Layout, Menu, Button, Space, Typography, Dropdown, Switch } from 'antd';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  UserOutlined, 
  LogoutOutlined, 
  DashboardOutlined,
  CrownOutlined,
  SunOutlined,
  MoonOutlined
} from '@ant-design/icons';
import { useAuth } from '../utils/AuthContext';
import { useTheme } from '../utils/ThemeContext';

const { Header } = Layout;
const { Text } = Typography;

const Navbar = () => {
  const { user, logout, isAuthenticated, isSubscribed } = useAuth();
  const { isDarkMode, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const userMenuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
      onClick: () => navigate('/dashboard')
    },
    {
      key: 'pricing',
      icon: <CrownOutlined />,
      label: 'Pricing',
      onClick: () => navigate('/pricing')
    },
    {
      type: 'divider'
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: handleLogout
    }
  ];

  const menuItems = [
    {
      key: '/',
      label: <Link to="/">Home</Link>
    },
    {
      key: '/pricing',
      label: <Link to="/pricing">Pricing</Link>
    }
  ];

  return (
    <Header style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between',
      background: 'white',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      zIndex: 1000
    }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <Link to="/" style={{ textDecoration: 'none' }}>
          <Text strong style={{ fontSize: '1.5rem', color: '#1890ff' }}>
            Sora Watermark Remover
          </Text>
        </Link>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <Menu
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ 
            border: 'none', 
            background: 'transparent',
            minWidth: '200px'
          }}
        />

        <Space>
          <Switch
            checked={isDarkMode}
            onChange={toggleTheme}
            checkedChildren={<MoonOutlined />}
            unCheckedChildren={<SunOutlined />}
            style={{ marginRight: '8px' }}
          />
          
          {isAuthenticated() ? (
            <>
              {isSubscribed() && (
                <Button type="primary" size="small" icon={<CrownOutlined />}>
                  Pro
                </Button>
              )}
              <Dropdown
                menu={{ items: userMenuItems }}
                placement="bottomRight"
                arrow
              >
                <Button type="text" icon={<UserOutlined />}>
                  {user?.email}
                </Button>
              </Dropdown>
            </>
          ) : (
            <>
              <Button onClick={() => navigate('/login')}>
                Login
              </Button>
              <Button type="primary" onClick={() => navigate('/register')}>
                Sign Up
              </Button>
            </>
          )}
        </Space>
      </div>
    </Header>
  );
};

export default Navbar;
