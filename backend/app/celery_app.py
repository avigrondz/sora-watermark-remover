from celery import Celery
import os
from dotenv import load_dotenv

# Try to load environment variables, but don't fail if there are encoding issues
try:
    load_dotenv()
except UnicodeDecodeError:
    # If there's an encoding issue, just continue without loading .env files
    pass

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = Celery(
    "watermark_remover",
    broker=redis_url,
    backend=redis_url,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
