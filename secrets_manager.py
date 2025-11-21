"""
CloudContactAI A2P 10DLC Compliance Agent - Secrets Manager
Copyright (c) 2024 CloudContactAI, LLC. All rights reserved.

AWS Secrets Manager utility for secure environment variable management.
Loads API keys and sensitive configuration from AWS Secrets Manager.
"""
import json
import os
import boto3
from botocore.exceptions import ClientError

def load_secrets():
    """Load secrets from AWS Secrets Manager or fallback to .env file"""
    try:
        # Use IAM role when running in ECS, profile when running locally
        if os.getenv('AWS_EXECUTION_ENV'):
            # Running in ECS - use IAM role
            client = boto3.client('secretsmanager', region_name='us-east-1')
        else:
            # Running locally - use profile
            session = boto3.Session(profile_name='ccai')
            client = session.client('secretsmanager', region_name='us-east-1')
        
        response = client.get_secret_value(SecretId='a2p-compliance-env')
        secrets = json.loads(response['SecretString'])
        
        # Set environment variables
        for key, value in secrets.items():
            os.environ[key] = value
            
        print("✅ Secrets loaded from AWS Secrets Manager")
        return True
        
    except ClientError as e:
        print(f"⚠️ Could not load secrets from AWS: {e}")
        print("📝 Falling back to .env file")
        return False
    except Exception as e:
        print(f"⚠️ Error loading secrets: {e}")
        print("📝 Falling back to .env file")
        return False

def get_openai_key():
    """Get OpenAI API key from environment"""
    return os.getenv('OPENAI_API_KEY')
