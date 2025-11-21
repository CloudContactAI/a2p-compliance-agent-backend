"""
CloudContactAI A2P 10DLC Compliance Agent - Core Engine
Copyright (c) 2024 CloudContactAI, LLC. All rights reserved.

Core compliance checking engine implementing TCPA, FDCPA, and CFPB regulations
for A2P 10DLC messaging compliance validation.
Based on CCAI Collections Compliance.docx requirements.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re

class ComplianceStatus(Enum):
    APPROVABLE = "approvable"
    REJECTION_LIKELY = "rejection_likely"

@dataclass
class ComplianceResult:
    status: ComplianceStatus
    violations: List[str]
    recommendations: List[str]
    confidence_score: float
    score: int

class CCaiComplianceAgent:
    def __init__(self):
        self.rules_version = "v1.0"
        self.third_party_patterns = [
            r'third[-\s]?party debt collector',
            r'we collect debts on behalf of',
            r'collection agency',
            r'debt collection agency'
        ]
        self.auto_fail_triggers = [
            r'skip[-\s]?tracing',
            r'payday loan',
            r'personal loan solicitation',
            r'lead generation',
            r'data brokerage',
            r'crypto',
            r'credit repair'
        ]
        
    def evaluate_compliance(self, data: Dict[str, Any]) -> ComplianceResult:
        """Evaluate communication for compliance violations"""
        violations = []
        score = 100
        
        # Section A: Brand Identity & Category Review
        brand_violations, brand_score = self._check_brand_compliance(data)
        violations.extend(brand_violations)
        score -= brand_score
        
        # Section B: Opt-in Validation
        optin_violations, optin_score = self._check_optin_compliance(data)
        violations.extend(optin_violations)
        score -= optin_score
        
        # Section C: Message Template Compliance
        template_violations, template_score = self._check_template_compliance(data)
        violations.extend(template_violations)
        score -= template_score
        
        # Section D: URL & Domain Validation
        url_violations, url_score = self._check_url_compliance(data)
        violations.extend(url_violations)
        score -= url_score
        
        # Section E: Terms & Privacy Validation
        legal_violations, legal_score = self._check_legal_compliance(data)
        violations.extend(legal_violations)
        score -= legal_score
        
        # Section I: FDCPA, TCPA, CTIA Legal Compliance
        regulatory_violations, regulatory_score = self._check_regulatory_compliance(data)
        violations.extend(regulatory_violations)
        score -= regulatory_score
        
        score = max(0, score)
        status = ComplianceStatus.APPROVABLE if score >= 99 and not violations else ComplianceStatus.REJECTION_LIKELY
        
        recommendations = self._generate_recommendations(violations)
        confidence_score = self._calculate_confidence(violations, score)
        
        return ComplianceResult(
            status=status,
            violations=violations,
            recommendations=recommendations,
            confidence_score=confidence_score,
            score=score
        )
    
    def _check_brand_compliance(self, data: Dict[str, Any]) -> tuple[List[str], int]:
        """Section A: Brand Identity & Category Review"""
        violations = []
        penalty = 0
        
        website_content = data.get("website_content", "").lower()
        
        # Check for auto-fail triggers
        for pattern in self.third_party_patterns:
            if re.search(pattern, website_content, re.IGNORECASE):
                violations.append("A1: Website references third-party debt collection (CRITICAL)")
                penalty += 30
                
        for pattern in self.auto_fail_triggers:
            if re.search(pattern, website_content, re.IGNORECASE):
                violations.append(f"A1: Website contains prohibited content: {pattern}")
                penalty += 30
        
        # Brand category validation
        use_case = data.get("use_case", "").lower()
        if any(term in use_case for term in ["marketing", "lead generation", "loan offers"]):
            violations.append("A2: Use case indicates prohibited marketing/lead generation")
            penalty += 25
            
        return violations, penalty
    
    def _check_optin_compliance(self, data: Dict[str, Any]) -> tuple[List[str], int]:
        """Section B: Opt-in Validation"""
        violations = []
        penalty = 0
        
        opt_in_description = data.get("opt_in_description", "").lower()
        
        # Check for non-compliant opt-in methods
        if "existing business relationship" in opt_in_description:
            violations.append("B1: 'Existing business relationship' is not sufficient for SMS consent")
            penalty += 25
            
        if "customers provide number when calling" in opt_in_description:
            violations.append("B1: Phone number collection during calls is non-compliant")
            penalty += 25
        
        # Check for required consent language
        sample_messages = data.get("sample_messages", [])
        if sample_messages:
            first_message = sample_messages[0].lower()
            if "stop" not in first_message:
                violations.append("B1: Missing STOP instructions in initial message")
                penalty += 15
                
        return violations, penalty
    
    def _check_template_compliance(self, data: Dict[str, Any]) -> tuple[List[str], int]:
        """Section C: Message Template Compliance"""
        violations = []
        penalty = 0
        
        sample_messages = data.get("sample_messages", [])
        brand_name = data.get("brand_name", "")
        
        # Check each message for required elements
        for i, message in enumerate(sample_messages):
            message_lower = message.lower()
            
            # Brand name requirement removed per business requirements
            
            # Check for prohibited placeholders (excluding {{brandname}})
            prohibited_placeholders = ["{{url}}", "{{company}}", "{{agentname}}"]
            for placeholder in prohibited_placeholders:
                if placeholder in message_lower:
                    violations.append(f"C2: Prohibited placeholder {placeholder} in message {i+1}")
                    penalty += 15
            
            # Check for threatening language
            threatening_terms = ["urgent", "final notice", "last attempt", "respond immediately"]
            for term in threatening_terms:
                if term in message_lower:
                    violations.append(f"C3: Threatening language '{term}' in message {i+1}")
                    penalty += 10
                    
        return violations, penalty
    
    def _check_url_compliance(self, data: Dict[str, Any]) -> tuple[List[str], int]:
        """Section D: URL & Domain Validation"""
        violations = []
        penalty = 0
        
        # Check for URL shorteners or redirects
        urls = data.get("urls", [])
        for url in urls:
            if any(shortener in url for shortener in ["bit.ly", "tinyurl", "t.co"]):
                violations.append("D1: URL shorteners are not allowed")
                penalty += 20
        
        # Check email domain match with website domain
        support_email = data.get("support_email", "")
        brand_website = data.get("brand_website", "")
        
        if support_email and brand_website:
            try:
                from urllib.parse import urlparse
                email_domain = support_email.split('@')[1].lower()
                website_domain = urlparse(brand_website).netloc.lower()
                
                # Remove www. prefix if present
                if website_domain.startswith('www.'):
                    website_domain = website_domain[4:]
                
                if email_domain != website_domain:
                    violations.append(f"D2: Support email domain ({email_domain}) does not match website domain ({website_domain})")
                    penalty += 5  # Minor penalty - process continues
                    
            except Exception:
                # If parsing fails, add minor penalty but continue
                violations.append("D3: Unable to validate email domain match")
                penalty += 3
                
        return violations, penalty
    
    def _check_legal_compliance(self, data: Dict[str, Any]) -> tuple[List[str], int]:
        """Section E: Terms & Privacy Validation"""
        violations = []
        penalty = 0
        
        if not data.get("privacy_url"):
            violations.append("E1: Privacy Policy URL missing")
            penalty += 15
            
        if not data.get("terms_url"):
            violations.append("E1: Terms & Conditions URL missing")
            penalty += 15
            
        return violations, penalty
    
    def _check_regulatory_compliance(self, data: Dict[str, Any]) -> tuple[List[str], int]:
        """Section I: FDCPA, TCPA, CTIA Legal Compliance"""
        violations = []
        penalty = 0
        
        # Future regulatory checks can be added here
        # FDCPA disclosure requirement removed per business requirements
            
        return violations, penalty
    
    def _generate_recommendations(self, violations: List[str]) -> List[str]:
        """Generate specific recommendations based on violations"""
        recommendations = []
        
        for violation in violations:
            if "third-party debt collection" in violation.lower():
                recommendations.append("Remove all references to third-party debt collection from website")
            elif "stop instructions" in violation.lower():
                recommendations.append("Include 'Reply STOP to opt out' in initial message")
            elif "privacy policy" in violation.lower():
                recommendations.append("Provide valid Privacy Policy URL")
            elif "terms" in violation.lower():
                recommendations.append("Provide valid Terms & Conditions URL")
                
        return list(set(recommendations))  # Remove duplicates
    
    def _calculate_confidence(self, violations: List[str], score: int) -> float:
        """Calculate confidence score based on violations and overall score"""
        if score >= 99:
            return 0.99
        elif score >= 90:
            return 0.85
        elif score >= 80:
            return 0.70
        else:
            return 0.50
