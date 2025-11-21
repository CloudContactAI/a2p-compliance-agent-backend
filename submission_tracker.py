"""
CloudContactAI A2P 10DLC Compliance Agent - Submission Tracker
Copyright (c) 2024 CloudContactAI, LLC. All rights reserved.

DynamoDB-based submission tracking for A2P compliance sessions.
Stores and retrieves compliance analysis results and submission history.
"""
import boto3
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

class SubmissionTracker:
    def __init__(self, table_name='a2p-submissions'):
        self.table_name = table_name
        self.dynamodb = None
        self.table = None
        self.enabled = False
        
        try:
            session = boto3.Session(profile_name='ccai')
            self.dynamodb = session.resource('dynamodb', region_name='us-east-1')
            self.table = self.dynamodb.Table(table_name)
            # Test connection
            self.table.table_status
            self.enabled = True
            print("✅ DynamoDB connected successfully")
        except Exception as e:
            print(f"⚠️  DynamoDB not available: {e}")
            print("📝 Running in local mode - submissions won't be stored")
            self.enabled = False
    
    def _generate_session_id(self, ip_address: str) -> str:
        """Generate consistent session ID from IP address"""
        return hashlib.sha256(ip_address.encode()).hexdigest()[:16]
    
    def store_submission(self, ip_address: str, submission_data: Dict[str, Any], 
                        compliance_result: Dict[str, Any]) -> Optional[str]:
        """Store submission with compliance results"""
        if not self.enabled:
            print("📝 DynamoDB disabled - skipping storage")
            return None
            
        try:
            session_id = self._generate_session_id(ip_address)
            submission_id = f"{session_id}_{int(datetime.now().timestamp())}"
            
            # Extract business verification results
            business_verification = compliance_result.get('business_verification', {})
            
            item = {
                'submission_id': submission_id,
                'session_id': session_id,
                'ip_address_hash': session_id,
                'timestamp': datetime.now().isoformat(),
                'brand_name': submission_data.get('brand_name', ''),
                'brand_website': submission_data.get('brand_website', ''),
                'use_case': submission_data.get('use_case', ''),
                'compliance_score': compliance_result.get('score', 0),
                'compliance_status': compliance_result.get('status', 'unknown'),
                'violations_count': len(compliance_result.get('violations', [])),
                'violations': compliance_result.get('violations', []),
                'recommendations_count': len(compliance_result.get('recommendations', [])),
                'submission_data': json.dumps(submission_data),
                'compliance_result': json.dumps(compliance_result),
                # Business verification fields
                'business_verification_status': business_verification.get('verification_status', 'not_run'),
                'business_issues_found': business_verification.get('issues_found', False),
                'business_risk_level': business_verification.get('risk_level', 'unknown'),
                'business_verification_json': json.dumps(business_verification)
            }
            
            self.table.put_item(Item=item)
            return submission_id
        except Exception as e:
            print(f"❌ Failed to store submission: {e}")
            return None
    
    def get_user_submissions(self, ip_address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent submissions for this IP/session"""
        if not self.enabled:
            return []
            
        try:
            session_id = self._generate_session_id(ip_address)
            
            response = self.table.query(
                IndexName='session-timestamp-index',
                KeyConditionExpression='session_id = :sid',
                ExpressionAttributeValues={':sid': session_id},
                ScanIndexForward=False,
                Limit=limit
            )
            
            return response.get('Items', [])
        except Exception as e:
            print(f"❌ Failed to get submissions: {e}")
            return []
    
    def get_all_submissions(self):
        """Get all submissions for admin dashboard"""
        if not self.enabled:
            return []
            
        try:
            response = self.table.scan()
            items = response.get('Items', [])
            
            # Convert Decimal objects to regular numbers for JSON serialization
            import json
            from decimal import Decimal
            
            def decimal_default(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                raise TypeError
            
            # Convert through JSON to handle Decimals
            json_str = json.dumps(items, default=decimal_default)
            return json.loads(json_str)
            
        except Exception as e:
            print(f"Error getting all submissions: {e}")
            return []
    
    def get_submission_stats(self, ip_address: str) -> Dict[str, Any]:
        """Get submission statistics for this user"""
        if not self.enabled:
            return {'total_submissions': 0, 'note': 'DynamoDB not available'}
            
        try:
            submissions = self.get_user_submissions(ip_address, limit=50)
            
            if not submissions:
                return {'total_submissions': 0}
            
            total = len(submissions)
            compliant = sum(1 for s in submissions if s.get('compliance_score', 0) >= 80)
            avg_score = sum(s.get('compliance_score', 0) for s in submissions) / total
            
            return {
                'total_submissions': total,
                'compliant_submissions': compliant,
                'compliance_rate': round(compliant / total * 100, 2),
                'average_score': round(avg_score, 1),
                'last_submission': submissions[0].get('timestamp') if submissions else None
            }
        except Exception as e:
            print(f"❌ Failed to get stats: {e}")
            return {'total_submissions': 0, 'error': str(e)}
