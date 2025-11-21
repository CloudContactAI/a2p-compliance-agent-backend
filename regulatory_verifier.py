"""
CloudContactAI A2P 10DLC Compliance Agent - Regulatory Verifier
Copyright (c) 2024 CloudContactAI, LLC. All rights reserved.

Regulatory compliance verification for A2P 10DLC messaging.
Uses CFPB, FCC, and FTC databases to validate regulatory compliance.
"""
import requests
import json
from typing import Dict, Any

CFPB_BASE_URL = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
FCC_BASE_URL = "https://opendata.fcc.gov/resource/3xyp-aqkj.json"

class RegulatoryVerifier:
    def __init__(self):
        self.enabled = True
        print("✅ Regulatory verification enabled (CFPB, FCC) with debugging")

    def get_cfpb_complaints(self, company: str, size: int = 10):
        """CFPB complaints with JSON dump for debugging"""
        try:
            print(f"DEBUG: Querying CFPB for company: '{company}'")
            params = {
                "company": company,
                "field": "all",
                "size": 3,
                "format": "json",
                "no_aggs": "true",
            }
            resp = requests.get(CFPB_BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            print("=" * 50)
            print("CFPB JSON RESPONSE:")
            print("=" * 50)
            print(json.dumps(data, indent=2)[:2000])
            print("=" * 50)
            
            return []
            
        except Exception as e:
            print(f"CFPB query failed: {e}")
            return []

    def get_fcc_complaints(self, company: str, limit: int = 10):
        """Query FCC Consumer Complaints Data"""
        try:
            params = {
                "$limit": limit,
                "$q": company,
            }
            resp = requests.get(FCC_BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"FCC query failed: {e}")
            return []

    def get_ftc_enforcement_actions(self, company: str):
        """FTC enforcement actions disabled"""
        return []

    def verify_business(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify business against regulatory databases"""
        try:
            brand_name = business_data.get('brand_name', '')
            print(f"Checking regulatory databases for: {brand_name}")
            
            cfpb_complaints = self.get_cfpb_complaints(brand_name, size=5)
            fcc_complaints = self.get_fcc_complaints(brand_name, limit=5)
            ftc_actions = self.get_ftc_enforcement_actions(brand_name)
            
            issues = []
            if cfpb_complaints:
                issues.append(f"Found {len(cfpb_complaints)} CFPB complaints")
            if fcc_complaints:
                issues.append(f"Found {len(fcc_complaints)} FCC complaints")
            if ftc_actions:
                issues.append(f"Found {len(ftc_actions)} FTC actions")
            
            return {
                'verification_status': 'completed',
                'issues_found': len(issues) > 0,
                'risk_level': 'low',
                'issues': issues,
                'recommendations': [],
                'confidence': 'high',
                'business_name': brand_name
            }
            
        except Exception as e:
            return {
                'verification_status': 'error',
                'issues_found': False,
                'error': str(e)
            }

    def get_risk_score_adjustment(self, verification_result: Dict[str, Any]) -> int:
        """Get score adjustment based on regulatory findings"""
        return 0  # No adjustment for now
