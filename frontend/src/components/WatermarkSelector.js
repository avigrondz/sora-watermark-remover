import React, { useState, useRef, useEffect } from 'react';
import { Button, Card, Typography, Space, message } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, CheckOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const WatermarkSelector = ({ videoUrl, onWatermarksSelected, onNext }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [watermarks, setWatermarks] = useState([]);
  const [isSelecting, setIsSelecting] = useState(false);
  const [currentSelection, setCurrentSelection] = useState(null);
  const [videoSize, setVideoSize] = useState({ width: 0, height: 0 });
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleMouseDown = (e) => {
    if (!isSelecting) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setCurrentSelection({ startX: x, startY: y, endX: x, endY: y });
  };

  const handleMouseMove = (e) => {
    if (!isSelecting || !currentSelection) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setCurrentSelection({ ...currentSelection, endX: x, endY: y });
  };

  const handleMouseUp = () => {
    if (!isSelecting || !currentSelection) return;
    
    const { startX, startY, endX, endY } = currentSelection;
    const width = Math.abs(endX - startX);
    const height = Math.abs(endY - startY);
    
    if (width > 10 && height > 10) { // Minimum selection size
      const watermark = {
        id: Date.now(),
        x: Math.min(startX, endX),
        y: Math.min(startY, endY),
        width,
        height,
        timestamp: videoRef.current ? videoRef.current.currentTime : 0
      };
      
      setWatermarks([...watermarks, watermark]);
    }
    
    setCurrentSelection(null);
    setIsSelecting(false);
  };

  const removeWatermark = (id) => {
    setWatermarks(watermarks.filter(w => w.id !== id));
  };

  const startSelection = () => {
    setIsSelecting(true);
    message.info('Click and drag to select watermarks in the video');
  };

  const handleNext = () => {
    if (watermarks.length === 0) {
      message.warning('Please select at least one watermark area');
      return;
    }

    // Scale selections from displayed size to the source video resolution
    const videoEl = videoRef.current;
    const displayedWidth = videoEl ? videoEl.clientWidth : 0;
    const displayedHeight = videoEl ? videoEl.clientHeight : 0;
    const sourceWidth = videoEl ? videoEl.videoWidth : 0;
    const sourceHeight = videoEl ? videoEl.videoHeight : 0;

    let scaled = watermarks;
    if (displayedWidth > 0 && displayedHeight > 0 && sourceWidth > 0 && sourceHeight > 0) {
      const scaleX = sourceWidth / displayedWidth;
      const scaleY = sourceHeight / displayedHeight;
      scaled = watermarks.map(w => {
        const x = Math.max(0, Math.round(w.x * scaleX));
        const y = Math.max(0, Math.round(w.y * scaleY));
        const width = Math.max(1, Math.round(w.width * scaleX));
        const height = Math.max(1, Math.round(w.height * scaleY));
        return { id: w.id, x, y, width, height, timestamp: w.timestamp };
      });
    }

    onWatermarksSelected(scaled);
    onNext();
  };

  const drawSelections = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw existing watermarks
    watermarks.forEach(watermark => {
      ctx.strokeStyle = '#ff4d4f';
      ctx.lineWidth = 2;
      ctx.strokeRect(watermark.x, watermark.y, watermark.width, watermark.height);
      
      ctx.fillStyle = 'rgba(255, 77, 79, 0.2)';
      ctx.fillRect(watermark.x, watermark.y, watermark.width, watermark.height);
    });
    
    // Draw current selection
    if (currentSelection) {
      const { startX, startY, endX, endY } = currentSelection;
      ctx.strokeStyle = '#1890ff';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.strokeRect(
        Math.min(startX, endX),
        Math.min(startY, endY),
        Math.abs(endX - startX),
        Math.abs(endY - startY)
      );
      ctx.setLineDash([]);
    }
  };

  useEffect(() => {
    drawSelections();
  }, [watermarks, currentSelection, videoSize]);

  useEffect(() => {
    const syncCanvasToDisplayedSize = () => {
      if (!videoRef.current || !canvasRef.current || !containerRef.current) return;
      const { clientWidth, clientHeight } = videoRef.current;
      canvasRef.current.width = clientWidth;
      canvasRef.current.height = clientHeight;
      setVideoSize({ width: clientWidth, height: clientHeight });
    };

    // Sync on load and resize
    const videoEl = videoRef.current;
    if (videoEl) {
      videoEl.addEventListener('loadedmetadata', syncCanvasToDisplayedSize);
      videoEl.addEventListener('loadeddata', syncCanvasToDisplayedSize);
      window.addEventListener('resize', syncCanvasToDisplayedSize);
      // Initial sync
      setTimeout(syncCanvasToDisplayedSize, 0);
    }
    return () => {
      if (videoEl) {
        videoEl.removeEventListener('loadedmetadata', syncCanvasToDisplayedSize);
        videoEl.removeEventListener('loadeddata', syncCanvasToDisplayedSize);
      }
      window.removeEventListener('resize', syncCanvasToDisplayedSize);
    };
  }, [videoUrl]);

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <Card>
        <Title level={3}>Select Watermarks to Remove</Title>
        <Text type="secondary">
          Click and drag to select watermark areas in the video. You can select multiple areas.
        </Text>
        
        <div style={{ marginTop: '20px' }}>
          <div 
            ref={containerRef}
            style={{ 
              position: 'relative', 
              display: 'inline-block',
              border: '2px solid #d9d9d9',
              borderRadius: '8px',
              overflow: 'hidden'
            }}
          >
            <video
              ref={videoRef}
              src={videoUrl}
              style={{ 
                width: '100%', 
                height: 'auto',
                maxWidth: '600px',
                display: 'block'
              }}
              controls
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onError={(e) => {
                console.error('Video load error:', e);
                console.error('Video URL:', videoUrl);
              }}
              onLoadStart={() => console.log('Video loading started:', videoUrl)}
              onCanPlay={() => console.log('Video can play:', videoUrl)}
              onLoadedData={() => console.log('Video data loaded:', videoUrl)}
            />
            {/* Selection overlay to capture precise mouse events when selecting */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                cursor: isSelecting ? 'crosshair' : 'default',
                pointerEvents: isSelecting ? 'auto' : 'none',
                zIndex: 2
              }}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
            />
            <canvas
              ref={canvasRef}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                pointerEvents: 'none',
                zIndex: 3
              }}
            />
          </div>
        </div>
        
        <div style={{ marginTop: '20px' }}>
          <Space>
            <Button 
              icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={handlePlayPause}
            >
              {isPlaying ? 'Pause' : 'Play'}
            </Button>
            
            <Button 
              type={isSelecting ? 'primary' : 'default'}
              onClick={startSelection}
              disabled={isSelecting}
            >
              {isSelecting ? 'Selecting...' : 'Select Watermark'}
            </Button>
            
            <Button 
              type="primary" 
              icon={<CheckOutlined />}
              onClick={handleNext}
              disabled={watermarks.length === 0}
            >
              Next ({watermarks.length} selected)
            </Button>
          </Space>
        </div>
        
        {watermarks.length > 0 && (
          <div style={{ marginTop: '20px' }}>
            <Title level={5}>Selected Watermarks:</Title>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
              {watermarks.map((watermark, index) => (
                <div
                  key={watermark.id}
                  style={{
                    padding: '8px 12px',
                    background: '#f0f0f0',
                    borderRadius: '4px',
                    border: '1px solid #d9d9d9',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <Text>Watermark {index + 1}</Text>
                  <Button 
                    size="small" 
                    type="text" 
                    danger
                    onClick={() => removeWatermark(watermark.id)}
                  >
                    ×
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default WatermarkSelector;
