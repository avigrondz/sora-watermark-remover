import React, { useState, useCallback } from 'react';
import { Upload, message, Progress, Button, Typography } from 'antd';
import { VideoCameraOutlined, UploadOutlined } from '@ant-design/icons';
import { videoAPI, publicVideoAPI } from '../services/api';

const { Dragger } = Upload;
const { Text } = Typography;

const VideoUploader = ({ onUploadSuccess, onUploadError }) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [redirecting, setRedirecting] = useState(false);

  // No react-dropzone; rely solely on AntD Upload.Dragger to avoid double file dialogs

  const handleUpload = async (file) => {
    if (!file) return;

    // Validate file size (500MB limit)
    const maxSize = 500 * 1024 * 1024; // 500MB
    if (file.size > maxSize) {
      message.error('File size must be less than 500MB');
      return;
    }

    // Validate file type
    if (!file.type.startsWith('video/')) {
      message.error('Please select a video file');
      return;
    }

    setUploading(true);
    setProgress(0);

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            return prev; // Keep at 90% until upload completes
          }
          return prev + Math.random() * 10;
        });
      }, 200);

      const isLoggedIn = !!localStorage.getItem('token');
      const response = isLoggedIn
        ? await videoAPI.upload(file)
        : await publicVideoAPI.upload(file);
      
      clearInterval(progressInterval);
      setProgress(100);
      setRedirecting(true);
      
      message.success('Video uploaded successfully! Redirecting...');
      
      // Redirect immediately - no delay needed
      if (onUploadSuccess) {
        onUploadSuccess(response.data);
      } else {
        // If no handler provided, navigate to processing when anonymous
        if (!localStorage.getItem('token') && response.data?.job_id) {
          window.location.href = `/process/${response.data.job_id}`;
        }
      }
      
    } catch (error) {
      message.error(error.response?.data?.detail || 'Upload failed');
      
      if (onUploadError) {
        onUploadError(error);
      }
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const uploadProps = {
    name: 'file',
    multiple: false,
    showUploadList: false,
    disabled: uploading || redirecting,
    beforeUpload: (file) => {
      if (!uploading && !redirecting) {
        handleUpload(file);
      }
      return false; // Prevent default upload
    },
    accept: 'video/*'
  };

  return (
    <div>
      <Dragger
        {...uploadProps}
        className="upload-area"
        disabled={uploading || redirecting}
        onClick={(e) => { if (uploading || redirecting) { e.preventDefault(); e.stopPropagation(); } }}
      >
        <p className="ant-upload-drag-icon">
          <VideoCameraOutlined className="upload-icon" />
        </p>
        <p className="ant-upload-text">Click or drag video to upload</p>
        
        <button className="upload-button" type="button">
          Upload Video
        </button>
        
        <div className="upload-specs">
          <div className="spec-item">up to resolution: ≤ 2K</div>
          <div className="spec-item">≤ 500MB</div>
        </div>
        
        <div className="upload-specs">
          <div className="spec-item">Supported formats:</div>
          <div className="spec-item">mp4</div>
          <div className="spec-item">m4v</div>
        </div>
        
        <p className="upload-terms">
          By uploading a video you agree to our Terms of Use and Privacy Policy.
        </p>
        
        {uploading && (
          <div style={{ marginTop: '16px' }}>
            <Progress 
              percent={Math.round(progress)} 
              status={progress === 100 ? 'success' : 'active'}
              strokeColor="#8b5cf6"
            />
            <Text style={{ fontSize: '0.9rem', color: '#a0a0a0' }}>
              {progress === 100 ? 'Processing...' : 'Uploading...'}
            </Text>
          </div>
        )}
      </Dragger>
    </div>
  );
};

export default VideoUploader;
