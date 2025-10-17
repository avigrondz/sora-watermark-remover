import React from 'react';
import { Row, Col, Typography, Button, Card, Space } from 'antd';
import { 
  PlayCircleOutlined, 
  ThunderboltOutlined, 
  SafetyOutlined,
  CloudUploadOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import VideoUploader from '../components/VideoUploader';

const { Title, Paragraph } = Typography;

const HomePage = () => {
  const navigate = useNavigate();
  const { isAuthenticated, isSubscribed } = useAuth();

  const embedCode = `<!-- Sora Watermark Remover Widget -->
<div id="sora-watermark-widget" style="
  max-width: 600px;
  margin: 0 auto;
  background: #2a2a2a;
  border: 2px dashed #404040;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
">
  <div style="color: #8b5cf6; font-size: 4rem; margin-bottom: 1.5rem;">📹</div>
  <h3 style="color: white; margin-bottom: 1rem; font-size: 1.2rem;">Remove Watermarks with AI Precision</h3>
  <p style="color: #a0a0a0; margin-bottom: 2rem;">Upload your video to remove watermarks instantly</p>
  
  <input type="file" id="video-upload" accept="video/*" style="display: none;">
  <button onclick="document.getElementById('video-upload').click()" style="
    background: #8b5cf6;
    color: white;
    border: none;
    padding: 12px 32px;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    margin-bottom: 2rem;
  ">Upload Video</button>
  
  <div style="display: flex; justify-content: center; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap;">
    <span style="background: #f0f0f0; color: #333; padding: 8px 16px; border-radius: 20px; font-size: 0.9rem;">≤ 2K</span>
    <span style="background: #f0f0f0; color: #333; padding: 8px 16px; border-radius: 20px; font-size: 0.9rem;">≤ 500MB</span>
  </div>
  
  <div style="display: flex; justify-content: center; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap;">
    <span style="color: #a0a0a0; font-size: 0.9rem;">Supported formats:</span>
    <span style="background: #f0f0f0; color: #333; padding: 8px 16px; border-radius: 20px; font-size: 0.9rem;">mp4</span>
    <span style="background: #f0f0f0; color: #333; padding: 8px 16px; border-radius: 20px; font-size: 0.9rem;">m4v</span>
  </div>
  
  <p style="font-size: 0.85rem; color: #888; margin-top: 1rem;">
    By uploading a video you agree to our Terms of Use and Privacy Policy.
  </p>
</div>

<script>
// Auto-detect environment URLs
const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const BACKEND_URL = isLocalhost ? 'http://localhost:8000' : 'https://api.sorawatermarks.com';
const FRONTEND_URL = isLocalhost ? 'http://localhost:3000' : 'https://app.sorawatermarks.com';

console.log('Embed detected environment:', { isLocalhost, BACKEND_URL, FRONTEND_URL });

document.getElementById('video-upload').addEventListener('change', function(e) {
  const file = e.target.files[0];
  if (!file) return;
  
  // Validate file type and size
  if (!file.type.startsWith('video/')) {
    alert('Please select a video file');
    return;
  }
  
  const maxSize = 500 * 1024 * 1024; // 500MB
  if (file.size > maxSize) {
    alert('File size must be less than 500MB');
    return;
  }
  
  // Show progress
  const button = document.querySelector('button');
  const originalText = button.textContent;
  button.textContent = 'Uploading...';
  button.disabled = true;
  
  // Upload file
  const formData = new FormData();
  formData.append('file', file);
  
  fetch(BACKEND_URL + '/api/public/upload', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.job_id) {
      // Navigate to processing page in same tab
      window.location.href = FRONTEND_URL + '/process/' + data.job_id;
    } else {
      throw new Error(data.message || 'Upload failed');
    }
  })
  .catch(error => {
    alert('Upload failed: ' + error.message);
    button.textContent = originalText;
    button.disabled = false;
  });
});
</script>`;

  const features = [
    {
      icon: <ThunderboltOutlined className="feature-icon" />,
      title: 'AI-Powered Removal',
      description: 'Advanced machine learning algorithms detect and remove watermarks with 99%+ accuracy'
    },
    {
      icon: <SafetyOutlined className="feature-icon" />,
      title: 'Secure Processing',
      description: 'Your videos are processed securely and automatically deleted after 7 days'
    },
    {
      icon: <CloudUploadOutlined className="feature-icon" />,
      title: 'Cloud-Based',
      description: 'No software installation required. Process videos directly in your browser'
    },
    {
      icon: <CheckCircleOutlined className="feature-icon" />,
      title: 'High Quality',
      description: 'Maintains original video quality with no compression artifacts'
    }
  ];

  return (
    <div>
      {/* Hero Section */}
      <div className="hero-section">
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 24px' }}>
          <Title className="hero-title">
            Remove Watermarks with AI Precision
          </Title>
          <Paragraph className="hero-subtitle">
            Eliminate TikTok, Sora, and other watermarks from your videos with our state-of-the-art AI technology. Get clean, professional results in seconds.
          </Paragraph>
          
          {/* Upload Area */}
          <div className="upload-section">
            <VideoUploader 
              onUploadSuccess={(data) => {
                if (isAuthenticated()) {
                  window.location.href = '/dashboard';
                } else if (data?.job_id) {
                  // Anonymous flow: go straight to processing page for preview + selection
                  window.location.href = `/process/${data.job_id}`;
                }
              }}
              onUploadError={(error) => {
                console.error('Upload error:', error);
              }}
            />
          </div>
          
          {/* Embed Code Section */}
          <div className="embed-code-section">
            <h3 style={{ color: 'white', marginBottom: '1rem', textAlign: 'center' }}>
              Embed This Upload Widget
            </h3>
            <div className="code-block-container">
              <div className="code-block-header">
                <span style={{ color: '#888', fontSize: '0.9rem' }}>HTML Embed Code</span>
                <button 
                  className="copy-button"
                  onClick={() => {
                    navigator.clipboard.writeText(embedCode);
                    alert('Code copied to clipboard!');
                  }}
                >
                  Copy
                </button>
              </div>
              <pre className="code-block">
                <code>{embedCode}</code>
              </pre>
            </div>
          </div>
          
          {isAuthenticated() ? (
            <Space size="large" style={{ marginTop: '2rem' }}>
              <Button 
                type="primary" 
                size="large"
                onClick={() => navigate('/dashboard')}
              >
                Go to Dashboard
              </Button>
              {!isSubscribed() && (
                <Button 
                  size="large"
                  onClick={() => navigate('/pricing')}
                >
                  View Pricing
                </Button>
              )}
            </Space>
          ) : (
            <Space size="large" style={{ marginTop: '2rem' }}>
              <Button 
                type="primary" 
                size="large"
                onClick={() => navigate('/register')}
              >
                Get Started Free
              </Button>
              <Button 
                size="large"
                onClick={() => navigate('/pricing')}
              >
                View Pricing
              </Button>
            </Space>
          )}
        </div>
      </div>

      {/* Features Section */}
      <div className="section-white" style={{ padding: '80px 24px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <Title level={2} style={{ textAlign: 'center', marginBottom: '48px' }}>
            Why Choose Our Watermark Remover?
          </Title>
          <Row gutter={[24, 24]}>
            {features.map((feature, index) => (
              <Col xs={24} sm={12} lg={6} key={index}>
                <Card className="feature-card">
                  {feature.icon}
                  <Title level={4}>{feature.title}</Title>
                  <Paragraph>{feature.description}</Paragraph>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="section-gray" style={{ padding: '80px 24px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <Title level={2} style={{ textAlign: 'center', marginBottom: '48px' }}>
            How It Works
          </Title>
          <Row gutter={[24, 24]} align="middle">
            <Col xs={24} md={12}>
              <Title level={3}>1. Upload Your Video</Title>
              <Paragraph>
                Simply drag and drop your video file or click to browse. 
                We support MP4, MOV, AVI, and other popular formats.
              </Paragraph>
            </Col>
            <Col xs={24} md={12}>
              <div style={{ textAlign: 'center' }}>
                <CloudUploadOutlined style={{ fontSize: '4rem', color: '#1890ff' }} />
              </div>
            </Col>
          </Row>
          
          <Row gutter={[24, 24]} align="middle" style={{ marginTop: '48px' }}>
            <Col xs={24} md={12} order={{ xs: 2, md: 1 }}>
              <div style={{ textAlign: 'center' }}>
                <ThunderboltOutlined style={{ fontSize: '4rem', color: '#1890ff' }} />
              </div>
            </Col>
            <Col xs={24} md={12} order={{ xs: 1, md: 2 }}>
              <Title level={3}>2. AI Processing</Title>
              <Paragraph>
                Our advanced AI detects watermarks frame by frame and 
                intelligently reconstructs the background for seamless removal.
              </Paragraph>
            </Col>
          </Row>
          
          <Row gutter={[24, 24]} align="middle" style={{ marginTop: '48px' }}>
            <Col xs={24} md={12}>
              <Title level={3}>3. Download Clean Video</Title>
              <Paragraph>
                Get your watermark-free video in high quality. 
                Download instantly or save to your account for later access.
              </Paragraph>
            </Col>
            <Col xs={24} md={12}>
              <div style={{ textAlign: 'center' }}>
                <CheckCircleOutlined style={{ fontSize: '4rem', color: '#52c41a' }} />
              </div>
            </Col>
          </Row>
        </div>
      </div>

    </div>
  );
};

export default HomePage;
