# 🗄️ AWS S3 Storage Strategy for Sora Watermark Remover

## 📊 **Storage Architecture Overview**

### **File Organization Structure**
```
s3://your-bucket/
├── uploads/
│   ├── free/           # Free trial users (7-day retention)
│   │   └── {user_id}/
│   │       ├── original_video.mp4
│   │       └── processed_video.mp4
│   ├── paid/           # Paid users (30-90 day retention)
│   │   └── {user_id}/
│   │       ├── original_video.mp4
│   │       └── processed_video.mp4
│   └── failed/         # Failed jobs (1-day retention)
│       └── {user_id}/
│           └── original_video.mp4
```

## 🎯 **Business Model Storage Strategy**

### **Free Trial Users**
- ✅ **1 free upload** allowed
- ✅ **7-day retention** for both original and processed videos
- ✅ **1GB storage limit** per user
- ✅ **Automatic cleanup** after 7 days
- ✅ **Must sign up** to download processed video

### **Paid Users**
- ✅ **Unlimited uploads** (within subscription limits)
- ✅ **30-day retention** for original videos
- ✅ **90-day retention** for processed videos
- ✅ **50GB storage limit** per user
- ✅ **Priority processing**

### **Failed Jobs**
- ✅ **24-hour retention** for debugging
- ✅ **Immediate cleanup** of processed files
- ✅ **Minimal storage usage**

## ⚙️ **Implementation Details**

### **1. S3 Lifecycle Policies**
```json
{
  "Rules": [
    {
      "ID": "FreeTrialCleanup",
      "Status": "Enabled",
      "Filter": {"Prefix": "uploads/free/"},
      "Expiration": {"Days": 7}
    },
    {
      "ID": "PaidUserOriginalCleanup", 
      "Status": "Enabled",
      "Filter": {"Prefix": "uploads/paid/original/"},
      "Expiration": {"Days": 30}
    },
    {
      "ID": "PaidUserProcessedCleanup",
      "Status": "Enabled", 
      "Filter": {"Prefix": "uploads/paid/processed/"},
      "Expiration": {"Days": 90}
    },
    {
      "ID": "FailedJobsCleanup",
      "Status": "Enabled",
      "Filter": {"Prefix": "uploads/failed/"},
      "Expiration": {"Days": 1}
    }
  ]
}
```

### **2. Cost Optimization**
- **Free users**: ~$0.01 per video (7-day storage)
- **Paid users**: ~$0.05 per video (30-90 day storage)
- **Failed jobs**: ~$0.001 per video (1-day storage)

### **3. Automatic Cleanup Schedule**
- **Daily at 2 AM**: Clean up expired files
- **Every 6 hours**: Check storage limits
- **Hourly**: Clean up failed jobs

## 🚀 **Setup Instructions**

### **Step 1: Run Database Migration**
```bash
cd backend
python migrations/add_free_trial_columns.py
```

### **Step 2: Configure S3 Lifecycle Policy**
```python
from services.storage_manager import storage_manager
storage_manager.setup_s3_lifecycle_policy()
```

### **Step 3: Start Cleanup Tasks**
```bash
# Start Celery worker for cleanup tasks
celery -A app.cleanup_tasks worker --loglevel=info
```

## 📈 **Expected Storage Costs**

### **Monthly Cost Estimates** (based on usage)
| User Type | Videos/Month | Storage Cost | Total Cost |
|-----------|--------------|--------------|------------|
| **Free Users** | 100 videos | $1.00 | $1.00 |
| **Paid Users** | 500 videos | $25.00 | $25.00 |
| **Failed Jobs** | 50 videos | $0.05 | $0.05 |
| **Total** | 650 videos | $26.05 | **$26.05/month** |

### **Cost Per Video**
- **Free trial**: $0.01 per video
- **Paid user**: $0.05 per video
- **Failed job**: $0.001 per video

## 🔧 **Configuration Options**

### **Environment Variables**
```env
# Storage limits
MAX_VIDEO_SIZE_MB=500
MAX_VIDEO_DURATION_SECONDS=600

# Retention periods (days)
FREE_TRIAL_RETENTION_DAYS=7
PAID_USER_ORIGINAL_RETENTION_DAYS=30
PAID_USER_PROCESSED_RETENTION_DAYS=90
FAILED_JOB_RETENTION_DAYS=1

# Storage limits (GB)
FREE_USER_STORAGE_LIMIT_GB=1
PAID_USER_STORAGE_LIMIT_GB=50
```

### **Free Trial Settings**
```python
# In your config
FREE_UPLOADS_LIMIT = 1  # 1 free upload
FREE_TRIAL_DURATION_DAYS = 7  # 7 days to download
```

## 🎯 **Business Benefits**

### **For Free Users**
- ✅ Try the service risk-free
- ✅ See quality before paying
- ✅ Must sign up to download
- ✅ Low storage costs

### **For Paid Users**
- ✅ Unlimited processing
- ✅ Long-term storage
- ✅ Priority support
- ✅ Higher storage limits

### **For You**
- ✅ Low storage costs for free users
- ✅ Revenue from paid users
- ✅ Automatic cleanup reduces costs
- ✅ Scalable storage strategy

## 🚨 **Important Notes**

1. **Free users must sign up** to download processed videos
2. **Files are automatically deleted** after retention period
3. **Storage limits prevent abuse**
4. **Failed jobs are cleaned up quickly**
5. **S3 lifecycle policies provide automatic cleanup**

This strategy balances user experience with cost efficiency while encouraging conversions to paid plans! 🎯
