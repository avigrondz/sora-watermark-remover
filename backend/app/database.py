from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables - try local first, then fallback to config.env
load_dotenv("config.local.env")
load_dotenv("config.env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/sora_watermark_remover")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
