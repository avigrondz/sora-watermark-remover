"""
AWS S3 Setup Script
This script will create the S3 bucket and configure it properly
"""

import boto3
import os
from botocore.exceptions import ClientError
from botocore.config import Config

def create_s3_bucket():
    """Create the S3 bucket for the application"""
    
    # Get AWS credentials from environment
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    bucket_name = os.getenv('S3_BUCKET_NAME', 'sorawatermarks-storage')
    
    print(f"🔧 Setting up S3 bucket: {bucket_name}")
    print(f"📍 Region: {aws_region}")
    
    if not aws_access_key or not aws_secret_key:
        print("❌ AWS credentials not found in environment variables")
        print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        return False
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region,
            config=Config(signature_version='s3v4')
        )
        
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket {bucket_name} already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"📦 Creating bucket {bucket_name}...")
            else:
                print(f"❌ Error checking bucket: {e}")
                return False
        
        # Create bucket
        if aws_region == 'us-east-1':
            # us-east-1 doesn't need LocationConstraint
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': aws_region}
            )
        
        print(f"✅ Bucket {bucket_name} created successfully!")
        
        # Set up CORS configuration
        cors_configuration = {
            'CORSRules': [
                {
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
                    'AllowedOrigins': ['*'],
                    'ExposeHeaders': ['ETag'],
                    'MaxAgeSeconds': 3000
                }
            ]
        }
        
        s3_client.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_configuration)
        print("✅ CORS configuration set")
        
        # Set up lifecycle policy for automatic cleanup
        lifecycle_policy = {
            'Rules': [
                {
                    'ID': 'FreeTrialCleanup',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'uploads/free/'},
                    'Expiration': {'Days': 7}
                },
                {
                    'ID': 'PaidUserOriginalCleanup',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'uploads/paid/original/'},
                    'Expiration': {'Days': 30}
                },
                {
                    'ID': 'PaidUserProcessedCleanup',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'uploads/paid/processed/'},
                    'Expiration': {'Days': 90}
                },
                {
                    'ID': 'FailedJobsCleanup',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'uploads/failed/'},
                    'Expiration': {'Days': 1}
                }
            ]
        }
        
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_policy
        )
        print("✅ Lifecycle policy configured")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error creating bucket: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_s3_connection():
    """Test S3 connection and permissions"""
    
    bucket_name = os.getenv('S3_BUCKET_NAME', 'sorawatermarks-storage')
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        # Test bucket access
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 connection successful - bucket {bucket_name} is accessible")
        
        # Test upload permissions
        test_key = "test/connection-test.txt"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=b"Test upload",
            ContentType="text/plain"
        )
        print("✅ Upload test successful")
        
        # Clean up test file
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)
        print("✅ Delete test successful")
        
        return True
        
    except ClientError as e:
        print(f"❌ S3 connection test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AWS S3 Setup for Sora Watermark Remover")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('config.local.env')
    
    # Create bucket
    if create_s3_bucket():
        print("\n🧪 Testing S3 connection...")
        if test_s3_connection():
            print("\n🎉 S3 setup completed successfully!")
            print("✅ Your uploads should work now")
        else:
            print("\n⚠️  S3 setup completed but connection test failed")
    else:
        print("\n❌ S3 setup failed")
        print("💡 Check your AWS credentials and try again")
