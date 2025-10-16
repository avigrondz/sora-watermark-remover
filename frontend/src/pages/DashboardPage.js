import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Row, Col, Card, Typography, Button, Space, message, Empty, Alert, Tag } from 'antd';
import { 
  UploadOutlined, 
  DownloadOutlined, 
  EyeOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CrownOutlined,
  CheckCircleFilled
} from '@ant-design/icons';
import { useAuth } from '../utils/AuthContext';
import { videoAPI } from '../services/api';
import VideoUploader from '../components/VideoUploader';
import JobCard from '../components/JobCard';

const { Title, Text } = Typography;

const DashboardPage = () => {
  const { user, isSubscribed } = useAuth();
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);

  useEffect(() => {
    fetchJobs();
    fetchSubscriptionStatus();
    
    // Check for URL parameters to show success/error messages
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('subscription') === 'success') {
      message.success('Subscription activated successfully! Welcome to premium!');
    }
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await videoAPI.getUserJobs();
      setJobs(response.data);
    } catch (error) {
      message.error('Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  const fetchSubscriptionStatus = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/subscription/status`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSubscriptionStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch subscription status:', error);
    }
  };

  const handleUploadSuccess = (data) => {
    message.success('Video uploaded successfully! Redirecting to processing...');
    setUploading(false);
    // Redirect to processing page
    navigate(`/process/${data.job_id}`);
  };

  const handleUploadError = (error) => {
    message.error('Upload failed');
    setUploading(false);
  };

  const handleDownload = async (jobId) => {
    try {
      const response = await videoAPI.downloadVideo(jobId);
      const link = document.createElement('a');
      link.href = response.data.download_url;
      link.download = `processed_video_${jobId}.mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      message.error('Download failed');
    }
  };

  const handleDelete = async (jobId) => {
    try {
      await videoAPI.deleteJob(jobId);
      message.success('Video deleted successfully');
      fetchJobs(); // Refresh the jobs list
    } catch (error) {
      message.error('Failed to delete video');
    }
  };

  const handleView = (jobId) => {
    const streamUrl = videoAPI.getVideoStream(jobId);
    window.open(streamUrl, '_blank');
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <ClockCircleOutlined className="status-pending" />;
      case 'processing':
        return <ClockCircleOutlined className="status-processing" />;
      case 'completed':
        return <CheckCircleOutlined className="status-completed" />;
      case 'failed':
        return <ExclamationCircleOutlined className="status-failed" />;
      default:
        return <ClockCircleOutlined />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending':
        return 'Pending';
      case 'processing':
        return 'Processing';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  if (!isSubscribed()) {
    return (
      <div style={{ padding: '48px 24px', textAlign: 'center' }}>
        <Card style={{ maxWidth: '600px', margin: '0 auto' }}>
          <Title level={2}>Subscription Required</Title>
          <Text type="secondary" style={{ fontSize: '1.1rem', display: 'block', marginBottom: '24px' }}>
            You need an active subscription to upload and process videos.
          </Text>
          <Button type="primary" size="large" href="/pricing">
            View Pricing Plans
          </Button>
        </Card>
      </div>
    );
  }

  const getSubscriptionTag = () => {
    if (!subscriptionStatus) return null;
    
    const tier = subscriptionStatus.subscription_tier;
    const expiresAt = subscriptionStatus.expires_at;
    
    let color = 'default';
    let text = tier;
    let icon = null;
    
    if (tier === 'free') {
      color = 'default';
      text = 'Free Trial';
    } else if (tier === 'monthly') {
      color = 'blue';
      text = 'Monthly Plan';
      icon = <CrownOutlined />;
    } else if (tier === 'yearly') {
      color = 'gold';
      text = 'Yearly Plan';
      icon = <CrownOutlined />;
    }
    
    return (
      <Tag color={color} icon={icon} style={{ fontSize: '14px', padding: '4px 12px' }}>
        {text}
      </Tag>
    );
  };

  return (
    <div className="dashboard-container" style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <Title level={2} className="dashboard-title" style={{ margin: 0 }}>Dashboard</Title>
          {getSubscriptionTag()}
        </div>
        <Text className="dashboard-text" type="secondary">
          Welcome back, {user?.email}! Upload videos to remove watermarks.
        </Text>
        
        {/* Subscription Status Alert */}
        {subscriptionStatus && subscriptionStatus.subscription_tier !== 'free' && (
          <Alert
            message="Premium Active"
            description={`Your ${subscriptionStatus.subscription_tier} subscription is active. Enjoy unlimited video processing!`}
            type="success"
            icon={<CheckCircleFilled />}
            style={{ marginTop: '16px' }}
            showIcon
          />
        )}
      </div>

      {/* Upload Section */}
      <Card 
        title="Upload Video" 
        style={{ marginBottom: '32px' }}
        extra={
          <Button 
            type="primary" 
            icon={<UploadOutlined />}
            onClick={() => setUploading(true)}
            disabled={uploading}
          >
            Upload Video
          </Button>
        }
      >
        <VideoUploader
          onUploadSuccess={handleUploadSuccess}
          onUploadError={handleUploadError}
        />
      </Card>

      {/* Jobs Section */}
      <Card title="Processing History">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '48px' }}>
            <Text>Loading...</Text>
          </div>
        ) : jobs.length === 0 ? (
          <Empty
            description="No videos uploaded yet"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={() => setUploading(true)}>
              Upload Your First Video
            </Button>
          </Empty>
        ) : (
          <Row gutter={[16, 16]}>
            {jobs.map((job) => (
              <Col xs={24} sm={12} lg={8} key={job.id}>
                <JobCard
                  job={job}
                  onDownload={handleDownload}
                  onDelete={handleDelete}
                  onView={handleView}
                  statusIcon={getStatusIcon(job.status)}
                  statusText={getStatusText(job.status)}
                />
              </Col>
            ))}
          </Row>
        )}
      </Card>
    </div>
  );
};

export default DashboardPage;
