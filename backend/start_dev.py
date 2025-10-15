"""
Development Server Startup
This version doesn't require Redis/Celery
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set development environment
os.environ.setdefault('DATABASE_URL', 'sqlite:///./local_test.db')
os.environ.setdefault('SECRET_KEY', 'dev-secret-key-12345')

# Disable Celery for development
os.environ.setdefault('CELERY_BROKER_URL', 'memory://')
os.environ.setdefault('CELERY_RESULT_BACKEND', 'cache+memory://')

try:
    from main import app
    import uvicorn
    
    print("🚀 Starting Sora Watermark Remover (Development Mode)")
    print("📍 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("💾 Storage: Local storage (no S3 required)")
    print("⚡ Processing: Synchronous (no Redis required)")
    print("\n" + "="*60)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the backend directory and have installed requirements")
    print("Run: pip install -r requirements.txt")
    
except Exception as e:
    print(f"❌ Server startup error: {e}")
    print("Check your configuration and try again")
