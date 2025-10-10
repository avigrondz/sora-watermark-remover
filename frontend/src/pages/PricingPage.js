import React from 'react';
import { Row, Col, Card, Typography, Button, Space, List } from 'antd';
import { CheckOutlined, CrownOutlined, ThunderboltOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const PricingPage = () => {
  const features = [
    'Unlimited video uploads',
    'AI-powered watermark removal',
    'High-quality output (up to 4K)',
    'Fast processing (GPU-accelerated)',
    'Secure cloud processing',
    '7-day file retention',
    'Email notifications',
    'Priority support'
  ];

  const plans = [
    {
      name: 'Free Trial',
      price: '$0',
      period: 'forever',
      description: 'Try our service with limited features',
      features: [
        '1 video per month',
        'Basic watermark removal',
        'Standard quality output',
        'Email support'
      ],
      buttonText: 'Start Free Trial',
      buttonType: 'default',
      popular: false
    },
    {
      name: 'Monthly',
      price: '$12',
      period: 'per month',
      description: 'Perfect for regular content creators',
      features: features,
      buttonText: 'Choose Monthly',
      buttonType: 'primary',
      popular: true
    },
    {
      name: 'Yearly',
      price: '$70',
      period: 'per year',
      description: 'Best value for power users',
      features: features,
      buttonText: 'Choose Yearly',
      buttonType: 'primary',
      popular: false,
      savings: 'Save 51%'
    }
  ];

  const handleSubscribe = (planName) => {
    console.log(`Subscribing to ${planName} plan`);
    
    if (planName === 'Free Trial') {
      // For free trial, just show success message
      alert('Free trial activated! You can now upload and process videos.');
      // Redirect to dashboard
      window.location.href = '/dashboard';
    } else {
      // For paid plans, show coming soon message
      alert('Payment integration coming soon! For now, you can use the free trial.');
      // Redirect to dashboard
      window.location.href = '/dashboard';
    }
  };

  return (
    <div style={{ padding: '48px 24px', background: '#f5f5f5', minHeight: '100vh' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '64px' }}>
          <Title level={1} style={{ marginBottom: '16px' }}>
            Simple, Transparent Pricing
          </Title>
          <Text style={{ fontSize: '1.2rem', color: '#666' }}>
            Choose the plan that fits your needs. Cancel anytime.
          </Text>
        </div>

        {/* Pricing Cards */}
        <Row gutter={[24, 24]} justify="center">
          {plans.map((plan, index) => (
            <Col xs={24} sm={12} lg={8} key={index}>
              <Card
                className={`pricing-card ${plan.popular ? 'featured' : ''}`}
                style={{ 
                  height: '100%',
                  position: 'relative',
                  border: plan.popular ? '2px solid #1890ff' : '1px solid #d9d9d9'
                }}
              >
                {plan.popular && (
                  <div style={{
                    position: 'absolute',
                    top: '-12px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    background: '#1890ff',
                    color: 'white',
                    padding: '4px 16px',
                    borderRadius: '16px',
                    fontSize: '0.9rem',
                    fontWeight: '600'
                  }}>
                    Most Popular
                  </div>
                )}
                
                {plan.savings && (
                  <div style={{
                    position: 'absolute',
                    top: '-12px',
                    right: '16px',
                    background: '#52c41a',
                    color: 'white',
                    padding: '4px 12px',
                    borderRadius: '12px',
                    fontSize: '0.8rem',
                    fontWeight: '600'
                  }}>
                    {plan.savings}
                  </div>
                )}

                <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                  <Title level={3} style={{ marginBottom: '8px' }}>
                    {plan.name}
                  </Title>
                  <div className="pricing-price">
                    {plan.price}
                    <span className="pricing-period">/{plan.period}</span>
                  </div>
                  <Text type="secondary" style={{ fontSize: '1rem' }}>
                    {plan.description}
                  </Text>
                </div>

                <List
                  dataSource={plan.features}
                  renderItem={(feature) => (
                    <List.Item style={{ padding: '8px 0', border: 'none' }}>
                      <Space>
                        <CheckOutlined style={{ color: '#52c41a' }} />
                        <Text>{feature}</Text>
                      </Space>
                    </List.Item>
                  )}
                  style={{ marginBottom: '32px' }}
                />

                <Button
                  type={plan.buttonType}
                  size="large"
                  block
                  style={{ height: '48px', fontSize: '16px', fontWeight: '600' }}
                  onClick={() => handleSubscribe(plan.name)}
                >
                  {plan.buttonText}
                </Button>
              </Card>
            </Col>
          ))}
        </Row>

        {/* Features Section */}
        <div style={{ marginTop: '80px', textAlign: 'center' }}>
          <Title level={2} style={{ marginBottom: '48px' }}>
            Why Choose Our Service?
          </Title>
          
          <Row gutter={[32, 32]}>
            <Col xs={24} md={8}>
              <div style={{ textAlign: 'center' }}>
                <ThunderboltOutlined style={{ fontSize: '3rem', color: '#1890ff', marginBottom: '16px' }} />
                <Title level={4}>AI-Powered</Title>
                <Text type="secondary">
                  Advanced machine learning algorithms ensure 99%+ accuracy in watermark removal
                </Text>
              </div>
            </Col>
            <Col xs={24} md={8}>
              <div style={{ textAlign: 'center' }}>
                <CrownOutlined style={{ fontSize: '3rem', color: '#1890ff', marginBottom: '16px' }} />
                <Title level={4}>High Quality</Title>
                <Text type="secondary">
                  Maintains original video quality with no compression artifacts or blurring
                </Text>
              </div>
            </Col>
            <Col xs={24} md={8}>
              <div style={{ textAlign: 'center' }}>
                <CheckOutlined style={{ fontSize: '3rem', color: '#1890ff', marginBottom: '16px' }} />
                <Title level={4}>Secure & Private</Title>
                <Text type="secondary">
                  Your videos are processed securely and automatically deleted after 7 days
                </Text>
              </div>
            </Col>
          </Row>
        </div>

        {/* FAQ Section */}
        <div style={{ marginTop: '80px' }}>
          <Title level={2} style={{ textAlign: 'center', marginBottom: '48px' }}>
            Frequently Asked Questions
          </Title>
          
          <Row gutter={[32, 32]}>
            <Col xs={24} md={12}>
              <Title level={4}>What video formats are supported?</Title>
              <Text type="secondary">
                We support MP4, MOV, AVI, MKV, and WebM formats. Maximum file size is 500MB.
              </Text>
            </Col>
            <Col xs={24} md={12}>
              <Title level={4}>How long does processing take?</Title>
              <Text type="secondary">
                Processing time depends on video length and complexity. A 1-minute video typically takes 30-60 seconds.
              </Text>
            </Col>
            <Col xs={24} md={12}>
              <Title level={4}>Can I cancel my subscription anytime?</Title>
              <Text type="secondary">
                Yes, you can cancel your subscription at any time. You'll continue to have access until the end of your billing period.
              </Text>
            </Col>
            <Col xs={24} md={12}>
              <Title level={4}>Is my data secure?</Title>
              <Text type="secondary">
                Absolutely. We use enterprise-grade security and automatically delete your videos after 7 days for privacy.
              </Text>
            </Col>
          </Row>
        </div>
      </div>
    </div>
  );
};

export default PricingPage;
