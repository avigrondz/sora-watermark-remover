import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Typography, Steps, Button, message, Progress, Space, Alert } from 'antd';
import { PlayCircleOutlined, CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import WatermarkSelector from '../components/WatermarkSelector';
import { videoAPI, publicVideoAPI } from '../services/api';
import { API_BASE_URL } from '../config/api';

const { Title, Text } = Typography;
const { Step } = Steps;

const ProcessingPage = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [job, setJob] = useState(null);
  const [watermarks, setWatermarks] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);

  useEffect(() => {
    fetchJobDetails();
  }, [jobId]);

  const fetchJobDetails = async () => {
    try {
      const isLoggedIn = !!localStorage.getItem('token');
      const response = isLoggedIn
        ? await videoAPI.getJobStatus(jobId)
        : await publicVideoAPI.getJobStatus(jobId);
      setJob(response.data);
      // Only redirect auto for logged-in users
      if (isLoggedIn && response.data.status === 'completed') {
        navigate('/dashboard');
      }
    } catch (error) {
      message.error('Failed to fetch job details');
      console.error('Error fetching job:', error);
    }
  };

  const handleWatermarksSelected = async (selectedWatermarks) => {
    try {
      setWatermarks(selectedWatermarks);
      
      // Save watermark selections to backend
      const isLoggedIn = !!localStorage.getItem('token');
      if (isLoggedIn) {
        await videoAPI.addWatermarkSelections(jobId, { watermarks: selectedWatermarks });
      } else {
        await publicVideoAPI.addWatermarkSelections(jobId, { watermarks: selectedWatermarks });
      }
      message.success('Watermark selections saved');
      
      setCurrentStep(1);
    } catch (error) {
      message.error('Failed to save watermark selections');
      console.error('Error saving watermarks:', error);
    }
  };

  const handleStartProcessing = async () => {
    try {
      setIsProcessing(true);
      setCurrentStep(2);
      
      // Start processing
      const isLoggedIn = !!localStorage.getItem('token');
      if (isLoggedIn) {
        await videoAPI.startProcessing(jobId);
      } else {
        await publicVideoAPI.startProcessing(jobId);
      }
      message.success('Processing started');
      
      // Poll for status updates
      pollJobStatus();
    } catch (error) {
      message.error('Failed to start processing');
      console.error('Error starting processing:', error);
      setIsProcessing(false);
    }
  };

  const pollJobStatus = () => {
    const interval = setInterval(async () => {
      try {
        const isLoggedIn = !!localStorage.getItem('token');
        const response = isLoggedIn
          ? await videoAPI.getJobStatus(jobId)
          : await publicVideoAPI.getJobStatus(jobId);
        const jobStatus = response.data.status;
        
        if (jobStatus === 'completed') {
          clearInterval(interval);
          setIsProcessing(false);
          setProcessingProgress(100);
          message.success('Processing completed!');
          if (isLoggedIn) {
            navigate('/dashboard');
          } else {
            // Stay on page for guests; show CTA to login for download
            setCurrentStep(2);
          }
        } else if (jobStatus === 'failed') {
          clearInterval(interval);
          setIsProcessing(false);
          message.error('Processing failed');
        } else if (jobStatus === 'processing') {
          // Simulate progress
          setProcessingProgress(prev => Math.min(prev + 10, 90));
        }
      } catch (error) {
        console.error('Error polling job status:', error);
      }
    }, 2000);
  };

  const getVideoUrl = () => {
    if (!job) return null;
    const isLoggedIn = !!localStorage.getItem('token');
    
    // Show original (unblurred) for watermark selection
    // Show blurred preview ONLY after processing is complete and user is not logged in
    const showBlurredPreview = !isLoggedIn && job.status === 'completed';
    
    if (showBlurredPreview) {
      return publicVideoAPI.getPreviewStreamUrl(jobId);
    } else {
      return `${API_BASE_URL}/api/videos/${jobId}/stream`;
    }
  };

  const steps = [
    {
      title: 'Select Watermarks',
      description: 'Click and drag to select watermark areas',
      icon: <PlayCircleOutlined style={{ color: '#1890ff' }} />
    },
    {
      title: 'Review Selection',
      description: 'Review your watermark selections',
      icon: <CheckCircleOutlined style={{ color: '#1890ff' }} />
    },
    {
      title: 'Processing',
      description: 'AI is removing watermarks',
      icon: isProcessing ? <LoadingOutlined style={{ color: '#1890ff' }} /> : <CheckCircleOutlined style={{ color: '#1890ff' }} />
    }
  ];

  if (!job) {
    return (
      <div className="processing-page-container processing-page-loading">
        <Title>Loading...</Title>
      </div>
    );
  }

  return (
    <div className="processing-page-container">
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <Title level={2} style={{ marginBottom: '10px' }}>Process Video</Title>
        <Text className="processing-page-subtitle">Remove watermarks from your video</Text>
      </div>
      
      <div style={{ marginBottom: '30px', width: '100%', display: 'flex', justifyContent: 'center' }}>
        <div style={{ 
          display: 'flex', 
          gap: '40px', 
          margin: '0', 
          padding: '0',
          alignItems: 'flex-start'
        }}>
          {steps.map((step, index) => (
            <div key={index} style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              margin: '0',
              padding: '0 10px',
              minWidth: '150px'
            }}>
              <div style={{ 
                color: '#1890ff', 
                fontSize: '20px', 
                marginBottom: '16px'
              }}>
                {step.icon}
              </div>
              <div style={{ 
                color: 'white', 
                fontSize: '16px', 
                fontWeight: '600',
                marginBottom: '12px',
                lineHeight: '1.6'
              }}>
                {step.title}
              </div>
              <div style={{ 
                color: '#e0e0e0', 
                fontSize: '14px',
                lineHeight: '1.6'
              }}>
                {step.description}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div style={{ marginTop: '30px' }}>
        {currentStep === 0 && (
          <WatermarkSelector
            videoUrl={getVideoUrl()}
            onWatermarksSelected={handleWatermarksSelected}
            onNext={() => setCurrentStep(1)}
          />
        )}
        
        {currentStep === 1 && (
          <Card>
            <Title level={3}>Review Your Selections</Title>
            <Text>You have selected {watermarks.length} watermark areas.</Text>
            
            <div style={{ marginTop: '20px' }}>
              <Space>
                <Button onClick={() => setCurrentStep(0)}>
                  Back to Selection
                </Button>
                <Button 
                  type="primary" 
                  onClick={handleStartProcessing}
                  loading={isProcessing}
                >
                  Start Processing
                </Button>
                {!localStorage.getItem('token') && (
                  <Button
                    onClick={() => {
                      // Send user to login, then to dashboard after login
                      window.location.href = `/login?next=/dashboard`;
                    }}
                  >
                    Login to Download
                  </Button>
                )}
              </Space>
            </div>
          </Card>
        )}
        
        {currentStep === 2 && (
          <Card>
            <Title level={3}>Processing Your Video</Title>
            <Text>AI is removing watermarks from your video. This may take a few minutes.</Text>
            
            <div style={{ marginTop: '20px' }}>
              <Progress 
                percent={processingProgress} 
                status={isProcessing ? 'active' : 'success'}
                strokeColor="#1890ff"
              />
            </div>
            
            <div style={{ marginTop: '20px' }}>
              <Text type="secondary">
                {isProcessing ? 'Processing...' : 'Processing completed!'}
              </Text>
            </div>

            {!localStorage.getItem('token') && !isProcessing && (
              <div style={{ marginTop: '24px' }}>
                <Alert
                  message="🎉 Processing Complete! Login to Download"
                  description="You can see a preview above (blurred for security). Sign up or log in to download your watermark-free video in full quality!"
                  type="success"
                  showIcon
                />
                <div style={{ marginTop: '16px', textAlign: 'center' }}>
                  <Space size="large">
                    <Button type="primary" size="large" onClick={() => (window.location.href = '/register?next=/dashboard')}>
                      Sign Up Free
                    </Button>
                    <Button size="large" onClick={() => (window.location.href = '/login?next=/dashboard')}>
                      Login
                    </Button>
                  </Space>
                </div>
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  );
};

export default ProcessingPage;
