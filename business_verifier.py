"""
CloudContactAI A2P 10DLC Compliance Agent - Business Verifier
Copyright (c) 2024 CloudContactAI, LLC. All rights reserved.

Business information verification module for A2P 10DLC compliance.
Uses OpenAI to validate business legitimacy and compliance requirements.
"""
import json
from typing import Dict, Any, Optional

class BusinessVerifier:
    def __init__(self):
        self.enabled = False
        print("⚠️ Business verification disabled - OpenAI cannot access real-time business records")
    
    def verify_business(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify business information for compliance issues"""
        if not self.enabled:
            return {
                'verification_status': 'skipped',
                'issues_found': False,
                'message': 'Business verification not available'
            }
        
        try:
            brand_name = business_data.get('brand_name', '')
            street_address = business_data.get('street_address', '')
            support_phone = business_data.get('support_phone', '')
            brand_website = business_data.get('brand_website', '')
            
            # Create verification prompt
            verification_prompt = f"""
You are a compliance verification specialist. Analyze this business information for potential regulatory or compliance issues:

Business Name: {brand_name}
Address: {street_address}
Phone: {support_phone}
Website: {brand_website}

Check for:
1. Known regulatory violations or enforcement actions
2. Consumer complaints or legal issues
3. Debt collection or financial services violations
4. TCPA, FDCPA, or CFPB enforcement actions
5. State or federal sanctions
6. Business license issues
7. Bankruptcy or financial distress

Respond in JSON format:
{{
    "issues_found": true/false,
    "risk_level": "low/medium/high",
    "issues": ["list of specific issues found"],
    "recommendations": ["list of recommendations"],
    "confidence": "low/medium/high"
}}

If no issues are found, return issues_found: false with empty arrays.
"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a compliance verification specialist with access to public regulatory and legal databases. Provide accurate, factual information about business compliance issues."},
                    {"role": "user", "content": verification_prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            # Parse JSON response
            result_text = response.choices[0].message.content
            print(f"DEBUG: OpenAI raw response: {result_text}")
            
            try:
                result = json.loads(result_text)
                print(f"DEBUG: Parsed result: {result}")
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                result = {
                    'issues_found': False,
                    'risk_level': 'unknown',
                    'issues': [],
                    'recommendations': [],
                    'confidence': 'low',
                    'raw_response': result_text
                }
            
            result['verification_status'] = 'completed'
            result['business_name'] = brand_name
            
            return result
            
        except Exception as e:
            print(f"Business verification error: {e}")
            return {
                'verification_status': 'error',
                'issues_found': False,
                'error': str(e),
                'message': 'Business verification failed'
            }
    
    def get_risk_score_adjustment(self, verification_result: Dict[str, Any]) -> int:
        """Get score adjustment based on verification results"""
        if not verification_result.get('issues_found', False):
            return 0
        
        risk_level = verification_result.get('risk_level', 'low')
        
        if risk_level == 'high':
            return -25  # Major penalty for high-risk businesses
        elif risk_level == 'medium':
            return -10  # Moderate penalty for medium-risk businesses
        else:
            return -5   # Minor penalty for low-risk issues
        
    def format_verification_report(self, verification_result: Dict[str, Any]) -> str:
        """Format verification results for display"""
        if verification_result.get('verification_status') == 'skipped':
            return "Business verification skipped (OpenAI not available)"
        
        if verification_result.get('verification_status') == 'error':
            return f"Business verification failed: {verification_result.get('error', 'Unknown error')}"
        
        if not verification_result.get('issues_found', False):
            return "✅ No compliance issues found for this business"
        
        issues = verification_result.get('issues', [])
        risk_level = verification_result.get('risk_level', 'unknown')
        
        report = f"⚠️ Business verification found {len(issues)} issue(s) - Risk Level: {risk_level.upper()}\n"
        
        for i, issue in enumerate(issues, 1):
            report += f"{i}. {issue}\n"
        
        recommendations = verification_result.get('recommendations', [])
        if recommendations:
            report += "\nRecommendations:\n"
            for i, rec in enumerate(recommendations, 1):
                report += f"• {rec}\n"
        
        return report
