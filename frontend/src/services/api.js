import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (userData) => api.post('/api/auth/register', userData),
  login: (credentials) => api.post('/api/auth/login', credentials),
  getMe: () => api.get('/api/auth/me'),
};

export const videoAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/videos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 60 second timeout
    });
  },
  getJobStatus: (jobId) => api.get(`/api/jobs/${jobId}/status`),
  getUserJobs: () => api.get('/api/jobs'),
  downloadVideo: (jobId) => api.get(`/api/jobs/${jobId}/download`),
  deleteJob: (jobId) => api.delete(`/api/jobs/${jobId}`),
  getVideoStream: (jobId) => `${API_BASE_URL}/api/videos/${jobId}/stream`,
  addWatermarkSelections: (jobId, watermarkData) => api.post(`/api/jobs/${jobId}/watermarks`, watermarkData),
  getWatermarkSelections: (jobId) => api.get(`/api/jobs/${jobId}/watermarks`),
  startProcessing: (jobId) => api.post(`/api/jobs/${jobId}/process`),
};

export const publicVideoAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/public/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
  },
  getJobStatus: (jobId) => api.get(`/api/public/jobs/${jobId}/status`),
  addWatermarkSelections: (jobId, data) => api.post(`/api/public/jobs/${jobId}/watermarks`, data),
  startProcessing: (jobId) => api.post(`/api/public/jobs/${jobId}/process`),
  getPreviewStreamUrl: (jobId) => `${API_BASE_URL}/api/videos/${jobId}/stream?preview=1`,
};

export const subscriptionAPI = {
  createSubscription: (priceId) => api.post('/api/subscriptions', { price_id: priceId }),
  getSubscription: () => api.get('/api/subscriptions/me'),
  cancelSubscription: () => api.delete('/api/subscriptions/me'),
};

export default api;
