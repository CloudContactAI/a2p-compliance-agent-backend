"""
CloudContactAI A2P 10DLC Compliance Agent - CloudWatch Logger
Copyright (c) 2024 CloudContactAI, LLC. All rights reserved.

CloudWatch logging service for A2P compliance sessions.
Tracks user interactions, compliance results, and system events.
"""
import logging
import json
import hashlib
from datetime import datetime
from typing import Dict, Any

class CloudWatchLogger:
    def __init__(self, log_group='a2p-compliance', log_stream=None):
        self.logger = logging.getLogger('a2p-compliance')
        self.logger.setLevel(logging.INFO)
        
        # Create CloudWatch handler if boto3 is available
        try:
            import boto3
            from watchtower import CloudWatchLogsHandler
            
            # Use IAM role when running in ECS, profile when running locally
            if os.getenv('AWS_EXECUTION_ENV'):
                # Running in ECS - use IAM role
                cloudwatch_client = boto3.client('logs', region_name='us-east-1')
            else:
                # Running locally - use profile
                session = boto3.Session(profile_name='ccai')
                cloudwatch_client = session.client('logs', region_name='us-east-1')
            
            handler = CloudWatchLogsHandler(
                log_group=log_group,
                stream_name=log_stream or f"a2p-{datetime.now().strftime('%Y-%m-%d')}",
                boto3_client=cloudwatch_client
            )
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)
            self.cloudwatch_enabled = True
            print("✅ CloudWatch logging enabled")
            
        except ImportError:
            # Fallback to console logging
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
            self.cloudwatch_enabled = False
            print("CloudWatch logging not available, using console logging")
    
    def get_session_id(self, ip_address: str) -> str:
        """Generate session ID from IP"""
        return hashlib.sha256(ip_address.encode()).hexdigest()[:16]
    
    def log_session_start(self, ip_address: str, submission_data: Dict[str, Any]):
        """Log session start"""
        session_id = self.get_session_id(ip_address)
        log_data = {
            "event": "session_start",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "brand_name": submission_data.get('brand_name', ''),
            "brand_website": submission_data.get('brand_website', ''),
            "use_case": submission_data.get('use_case', ''),
            "ip_hash": session_id
        }
        self.logger.info(json.dumps(log_data))
    
    def log_website_scraping(self, session_id: str, url: str, success: bool, error: str = None):
        """Log website scraping results"""
        log_data = {
            "event": "website_scraping",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "success": success,
            "error": error
        }
        self.logger.info(json.dumps(log_data))
    
    def log_compliance_result(self, session_id: str, compliance_result: Dict[str, Any]):
        """Log compliance analysis results"""
        log_data = {
            "event": "compliance_result",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "status": compliance_result.get('status'),
            "score": compliance_result.get('score'),
            "violations_count": len(compliance_result.get('violations', [])),
            "violations": compliance_result.get('violations', []),
            "recommendations_count": len(compliance_result.get('recommendations', []))
        }
        self.logger.info(json.dumps(log_data))
    
    def log_error(self, session_id: str, error_type: str, error_message: str, context: Dict = None):
        """Log errors with context"""
        log_data = {
            "event": "error",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        self.logger.error(json.dumps(log_data))
    
    def log_chat_interaction(self, session_id: str, user_message: str, response: str):
        """Log chat interactions"""
        log_data = {
            "event": "chat_interaction",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message[:200],  # Truncate long messages
            "response": response[:200]
        }
        self.logger.info(json.dumps(log_data))
