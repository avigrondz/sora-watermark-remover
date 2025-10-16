import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import App from './App';
import './styles/global.css';

// Suppress benign ResizeObserver loop errors that can occur with dynamic layouts
if (typeof window !== 'undefined') {
  const originalError = window.onerror;
  window.onerror = function (message, source, lineno, colno, error) {
    if (String(message || '').includes('ResizeObserver loop') ||
        String(error || '').includes('ResizeObserver loop')) {
      return true; // prevent logging
    }
    if (originalError) return originalError(message, source, lineno, colno, error);
  };

  const originalRejection = window.onunhandledrejection;
  window.onunhandledrejection = function (event) {
    if (String(event?.reason || '').includes('ResizeObserver loop')) {
      event.preventDefault();
      return true;
    }
    if (originalRejection) return originalRejection(event);
  };
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: '#1890ff',
            borderRadius: 8,
          },
        }}
      >
        <App />
      </ConfigProvider>
    </BrowserRouter>
  </React.StrictMode>
);
