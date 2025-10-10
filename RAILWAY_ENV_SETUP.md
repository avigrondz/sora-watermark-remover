# Railway Environment Variables Setup

## Required Environment Variables for Railway

Set these in your Railway project dashboard:

### Database
```
DATABASE_URL=postgresql://postgres:password@host:port/railway
```

### Security
```
SECRET_KEY=your-production-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### AWS S3
```
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name
```

### Redis
```
REDIS_URL=redis://host:port
```

### Stripe
```
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_key
STRIPE_SECRET_KEY=sk_live_your_stripe_secret
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

### Email
```
SENDGRID_API_KEY=your_sendgrid_api_key
FROM_EMAIL=noreply@yourdomain.com
```

### App Settings
```
MAX_VIDEO_SIZE_MB=500
MAX_VIDEO_DURATION_SECONDS=600
PROCESSING_TIMEOUT_SECONDS=1800
```

### Frontend URL
```
REACT_APP_API_URL=https://your-backend.railway.app
```

## How to Set Environment Variables in Railway

1. Go to your Railway project dashboard
2. Click on your backend service
3. Go to "Variables" tab
4. Add each variable with its value
5. Click "Deploy" to apply changes

## Security Notes

- Never commit real API keys to git
- Use different keys for development and production
- Rotate keys regularly
- Use Railway's built-in secret management
