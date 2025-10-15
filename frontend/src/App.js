import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout, Spin } from 'antd';
import { AuthProvider, useAuth } from './utils/AuthContext';
import { ThemeProvider } from './utils/ThemeContext';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import PricingPage from './pages/PricingPage';
import ProcessingPage from './pages/ProcessingPage';
import ProtectedRoute from './components/ProtectedRoute';

const { Content } = Layout;

const AppContent = () => {
  const { loading } = useAuth();

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Navbar />
      <Content>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/process/:jobId" 
            element={
              <ProtectedRoute>
                <ProcessingPage />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </Content>
    </Layout>
  );
};

const App = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
