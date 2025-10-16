import React from 'react';
import { Card, Button, Space, Typography, Tag, Popconfirm } from 'antd';
import { DownloadOutlined, EyeOutlined, DeleteOutlined, PlayCircleOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;

const JobCard = ({ job, onDownload, onDelete, onView, statusIcon, statusText }) => {
  const formatDate = (dateString) => {
    if (!dateString) return '';
    // Many backends return UTC without timezone (e.g., 2025-10-16T15:38:00)
    // If there's no timezone info, interpret as UTC and convert to local
    let normalized = dateString;
    const hasTimezone = /[zZ]|[+-]\d{2}:?\d{2}$/.test(dateString);
    if (!hasTimezone && /T/.test(dateString)) {
      normalized = `${dateString}Z`;
    }
    const dateObj = new Date(normalized);
    return dateObj.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'processing':
        return 'processing';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Card
      className="job-card"
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {statusIcon}
          <Text strong style={{ fontSize: '1rem' }}>
            {job.original_filename}
          </Text>
        </div>
      }
      extra={
        <Tag color={getStatusColor(job.status)}>
          {statusText}
        </Tag>
      }
      actions={[
        // View button (for all statuses)
        <Button
          icon={<PlayCircleOutlined />}
          onClick={() => onView(job.id)}
          size="small"
        >
          View
        </Button>,
        // Download button (only for completed)
        job.status === 'completed' && (
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => onDownload(job.id)}
            size="small"
          >
            Download
          </Button>
        ),
        // Delete button (for all statuses)
        <Popconfirm
          title="Delete this video?"
          description="This action cannot be undone."
          onConfirm={() => onDelete(job.id)}
          okText="Delete"
          cancelText="Cancel"
          okType="danger"
        >
          <Button
            danger
            icon={<DeleteOutlined />}
            size="small"
          >
            Delete
          </Button>
        </Popconfirm>
      ].filter(Boolean)}
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        <div>
          <Text type="secondary" style={{ fontSize: '0.9rem' }}>
            Uploaded: {formatDate(job.created_at)}
          </Text>
        </div>
        
        {job.processing_started_at && (
          <div>
            <Text type="secondary" style={{ fontSize: '0.9rem' }}>
              Started: {formatDate(job.processing_started_at)}
            </Text>
          </div>
        )}
        
        {job.processing_completed_at && (
          <div>
            <Text type="secondary" style={{ fontSize: '0.9rem' }}>
              Completed: {formatDate(job.processing_completed_at)}
            </Text>
          </div>
        )}
        
        {job.error_message && (
          <div>
            <Text type="danger" style={{ fontSize: '0.9rem' }}>
              Error: {job.error_message}
            </Text>
          </div>
        )}
      </Space>
    </Card>
  );
};

export default JobCard;
