import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Typography, Steps, Button, message, Progress, Space } from 'antd';
import { PlayCircleOutlined, CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import WatermarkSelector from '../components/WatermarkSelector';
import { videoAPI } from '../services/api';

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
      const response = await videoAPI.getJobStatus(jobId);
      setJob(response.data);
      
      // If job is completed, redirect to dashboard
      if (response.data.status === 'completed') {
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
      await videoAPI.addWatermarkSelections(jobId, { watermarks: selectedWatermarks });
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
      await videoAPI.startProcessing(jobId);
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
        const response = await videoAPI.getJobStatus(jobId);
        const jobStatus = response.data.status;
        
        if (jobStatus === 'completed') {
          clearInterval(interval);
          setIsProcessing(false);
          setProcessingProgress(100);
          message.success('Processing completed!');
          navigate('/dashboard');
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
    console.log('Job data:', job);
    if (job) {
      const videoUrl = `http://localhost:8000/api/videos/${jobId}/stream`;
      console.log('Video URL:', videoUrl);
      return videoUrl;
    }
    return null;
  };

  const steps = [
    {
      title: 'Select Watermarks',
      description: 'Click and drag to select watermark areas',
      icon: <PlayCircleOutlined />
    },
    {
      title: 'Review Selection',
      description: 'Review your watermark selections',
      icon: <CheckCircleOutlined />
    },
    {
      title: 'Processing',
      description: 'AI is removing watermarks',
      icon: isProcessing ? <LoadingOutlined /> : <CheckCircleOutlined />
    }
  ];

  if (!job) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <Title>Loading...</Title>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      <Title level={2}>Process Video</Title>
      <Text type="secondary">Remove watermarks from your video</Text>
      
      <div style={{ marginTop: '30px' }}>
        <Steps current={currentStep} items={steps} />
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
          </Card>
        )}
      </div>
    </div>
  );
};

export default ProcessingPage;
