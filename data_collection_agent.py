"""
CloudContactAI A2P 10DLC Compliance Agent - Data Collection Module
Copyright (c) 2024 CloudContactAI, LLC. All rights reserved.

Automated data collection agent for A2P 10DLC campaign registration.
Collects required information for Brand and Campaign submissions.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import Dict, List, Optional, Tuple

class A2PDataCollectionAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
    def collect_submission_data(self) -> Dict:
        """Interactive data collection for A2P submission"""
        print("A2P Brand & Campaign Submission Data Collection")
        print("=" * 50)
        
        data = {}
        
        # Brand Information
        print("\n📋 BRAND INFORMATION")
        data['brand_name'] = input("Brand Name: ").strip()
        data['brand_website'] = input("Brand Website URL: ").strip()
        data['legal_entity'] = input("Legal Entity Name: ").strip()
        data['vertical'] = input("Vertical (e.g., Financial Services - Collections): ").strip()
        
        # Campaign Information
        print("\n📱 CAMPAIGN INFORMATION")
        data['use_case'] = input("Use Case (e.g., Debt Servicing / Account Notifications): ").strip()
        data['campaign_description'] = input("Campaign Description: ").strip()
        
        # Contact Information
        print("\n📞 SUPPORT INFORMATION")
        data['support_email'] = input("Support Email: ").strip()
        data['support_phone'] = input("Support Phone: ").strip()
        
        # Opt-in Information
        print("\n✅ OPT-IN INFORMATION")
        data['opt_in_description'] = input("Describe opt-in process: ").strip()
        data['opt_in_channels'] = input("Opt-in channels (web,phone,email,sms): ").strip().split(',')
        
        # Message Templates
        print("\n💬 MESSAGE TEMPLATES")
        messages = []
        while True:
            msg = input(f"Sample Message {len(messages)+1} (or 'done'): ").strip()
            if msg.lower() == 'done':
                break
            messages.append(msg)
        data['sample_messages'] = messages
        
        # Additional URLs
        print("\n🔗 ADDITIONAL URLS (optional)")
        data['additional_urls'] = []
        while True:
            url = input("Additional URL (or 'done'): ").strip()
            if url.lower() == 'done':
                break
            data['additional_urls'].append(url)
            
        return data
    
    def scrape_website(self, url: str) -> Dict:
        """Scrape website content and find key pages"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text content with section mapping
            sections = {}
            
            # Get page title and meta description
            title = soup.title.string if soup.title else "Untitled"
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                sections['Meta Description'] = meta_desc.get('content')
            
            # Extract headings and their content
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
                heading_text = heading.get_text().strip()
                if heading_text:
                    # Get content under this heading
                    content_parts = []
                    for sibling in heading.find_next_siblings():
                        if sibling.name in ['h1', 'h2', 'h3', 'h4']:
                            break
                        if sibling.get_text().strip():
                            content_parts.append(sibling.get_text().strip())
                    
                    sections[heading_text] = ' '.join(content_parts)
            
            # Get ALL visible text from body (removes scripts/styles but keeps everything else)
            body = soup.find('body')
            if body:
                for script in body(["script", "style", "noscript"]):
                    script.decompose()
                sections['Full Body Text'] = body.get_text(separator=' ', strip=True)
            
            # Clean up text content - combine all sections
            full_text = ' '.join([str(content) for content in sections.values()])
            clean_text = ' '.join(full_text.split())
            
            # Find privacy and terms links
            privacy_url = self._find_policy_url(soup, url, ['privacy', 'privacy-policy'])
            terms_url = self._find_policy_url(soup, url, ['terms', 'terms-of-service', 'terms-conditions'])
            
            return {
                'url': url,
                'status_code': response.status_code,
                'text_content': clean_text,
                'sections': sections,
                'title': title,
                'privacy_url': privacy_url,
                'terms_url': terms_url
            }
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'status_code': 0
            }
    
    def _find_policy_url(self, soup: BeautifulSoup, base_url: str, keywords: List[str]) -> Optional[str]:
        """Find privacy/terms policy URLs"""
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            text = link.get_text().lower()
            
            for keyword in keywords:
                if keyword in href or keyword in text:
                    return urljoin(base_url, link['href'])
        return None
    
    def scrape_policy_pages(self, privacy_url: str = None, terms_url: str = None) -> Dict:
        """Scrape privacy and terms pages"""
        policies = {}
        
        if privacy_url:
            policies['privacy'] = self.scrape_website(privacy_url)
            
        if terms_url:
            policies['terms'] = self.scrape_website(terms_url)
            
        return policies
    
    def analyze_website_compliance(self, website_data: Dict) -> Dict:
        """Analyze website content for compliance issues with detailed match reporting"""
        content = website_data.get('text_content', '').lower()
        sections = website_data.get('sections', {})
        issues = []
        violation_locations = []
        
        # Enhanced auto-fail patterns with context capture
        auto_fail_patterns = [
            (r'third[-\s]?party debt collector', 'third-party debt collector'),
            (r'we collect debts on behalf of', 'third-party debt collection'),
            (r'skip[-\s]?tracing', 'skip-tracing services'),
            (r'payday loan', 'payday loan content'),
            (r'lead generation', 'lead generation services'),
            (r'data brokerage', 'data brokerage services'),
            (r'debt collection agency', 'debt collection agency'),
            (r'collection services', 'collection services'),
            (r'\bcrypto\b(?!graphic)', 'cryptocurrency content'),
            (r'credit repair', 'credit repair services')
        ]
        
        # Check for auto-fail triggers with exact match details
        for pattern, description in auto_fail_patterns:
            matches = list(re.finditer(pattern, content))
            if matches:
                for match in matches:
                    # Get surrounding context (50 chars before and after)
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    context = content[start:end].strip()
                    
                    # Find which section this appears in
                    section_found = 'main_content'
                    for section_name, section_content in sections.items():
                        if re.search(pattern, section_content.lower()):
                            section_found = section_name
                            break
                    
                    violation_locations.append({
                        'violation_type': 'auto_fail_trigger',
                        'description': description,
                        'matched_text': match.group(),
                        'context': f"...{context}...",
                        'section': section_found,
                        'url': website_data.get('url'),
                        'page_title': website_data.get('title', 'Unknown'),
                        'character_position': match.start()
                    })
                    
                issues.append(f"Auto-fail trigger detected: {description} - '{match.group()}'")
        
        # Enhanced debt + marketing detection with specific matches
        debt_patterns = [r'\bdebt\b', r'\bcollection\b', r'\bowe\b', r'\bpayment\b']
        marketing_patterns = [r'\bmarketing\b', r'\badvertising\b', r'\bpromotion\b', r'\bcampaign\b']
        
        debt_matches = []
        marketing_matches = []
        
        # Debug: Print first 500 chars of content being analyzed
        print(f"DEBUG: Analyzing content preview: {content[:500]}...")
        
        # Find all debt-related content with context
        for pattern in debt_patterns:
            for match in re.finditer(pattern, content):
                start = max(0, match.start() - 30)
                end = min(len(content), match.end() + 30)
                context = content[start:end].strip()
                
                print(f"DEBUG: Found debt match '{match.group()}' at position {match.start()}: {context}")
                
                debt_matches.append({
                    'matched_text': match.group(),
                    'context': f"...{context}...",
                    'position': match.start()
                })
        
        # Find all marketing-related content with context
        for pattern in marketing_patterns:
            for match in re.finditer(pattern, content):
                start = max(0, match.start() - 30)
                end = min(len(content), match.end() + 30)
                context = content[start:end].strip()
                
                print(f"DEBUG: Found marketing match '{match.group()}' at position {match.start()}: {context}")
                
                marketing_matches.append({
                    'matched_text': match.group(),
                    'context': f"...{context}...",
                    'position': match.start()
                })
        
        # Check for proximity between debt and marketing content
        if debt_matches and marketing_matches:
            for debt_match in debt_matches:
                for marketing_match in marketing_matches:
                    # If within 200 characters of each other
                    if abs(debt_match['position'] - marketing_match['position']) < 200:
                        violation_locations.append({
                            'violation_type': 'debt_marketing_proximity',
                            'description': 'Marketing language detected near debt content',
                            'debt_match': debt_match,
                            'marketing_match': marketing_match,
                            'url': website_data.get('url'),
                            'page_title': website_data.get('title', 'Unknown')
                        })
                        issues.append(f"Marketing + debt content: '{marketing_match['matched_text']}' near '{debt_match['matched_text']}'")
                        break
            
        return {
            'compliance_issues': issues,
            'violation_locations': violation_locations,
            'risk_level': 'HIGH' if violation_locations else 'LOW',
            'website_content': content,  # Include for address verification
            'debt_matches_found': len(debt_matches),
            'marketing_matches_found': len(marketing_matches),
            'total_violations': len(violation_locations)
        }
    
    def verify_phone_number(self, phone: str) -> Dict:
        """Verify phone number format is valid"""
        if not phone:
            return {'valid': False, 'error': 'No phone number provided'}
        
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
        
        # Valid US area codes (NPA - Numbering Plan Area)
        # Area codes cannot start with 0 or 1, and second digit cannot be 9
        valid_area_codes = set()
        for first in range(2, 10):  # 2-9
            for second in range(0, 9):  # 0-8 (not 9)
                for third in range(0, 10):  # 0-9
                    valid_area_codes.add(f"{first}{second}{third}")
        
        # Check if it's a valid US/international format
        if re.match(r'^\+?1?(\d{10})$', cleaned):
            # Extract the 10-digit number
            match = re.search(r'(\d{10})$', cleaned)
            if match:
                number = match.group(1)
                area_code = number[:3]
                
                # Check if area code is valid
                if area_code not in valid_area_codes:
                    return {
                        'valid': False,
                        'phone': phone,
                        'error': f'Invalid US area code: {area_code}'
                    }
                
                return {'valid': True, 'phone': phone, 'format': 'US', 'area_code': area_code}
        elif re.match(r'^\+\d{10,15}$', cleaned):
            return {'valid': True, 'phone': phone, 'format': 'International'}
        
        return {
            'valid': False,
            'phone': phone,
            'error': 'Invalid phone format (expected 10-digit US or international with +)'
        }
    
    def verify_email_domain(self, email: str) -> Dict:
        """Verify email domain has a working website"""
        if not email or '@' not in email:
            return {'valid': False, 'error': 'Invalid email format'}
        
        domain = email.split('@')[1]
        
        # Try both https and http
        for protocol in ['https://', 'http://']:
            try:
                url = f"{protocol}{domain}"
                response = self.session.get(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    return {
                        'valid': True,
                        'domain': domain,
                        'url': url,
                        'status_code': response.status_code
                    }
            except Exception as e:
                continue
        
        return {
            'valid': False,
            'domain': domain,
            'error': f'Domain {domain} does not return 200 status'
        }
    
    def verify_address_in_content(self, address: str, website_data: Dict, policy_data: Dict) -> bool:
        """Verify address appears in website or policy content"""
        if not address:
            return False
            
        # Get all content
        website_content = website_data.get('text_content', '')
        privacy_content = policy_data.get('privacy', {}).get('text_content', '')
        terms_content = policy_data.get('terms', {}).get('text_content', '')
        
        # Extract key parts of address for matching
        address_parts = []
        
        # Extract street number
        street_num = re.search(r'\b\d+\b', address)
        if street_num:
            address_parts.append(street_num.group())
        
        # Extract ZIP code
        zip_code = re.search(r'\b\d{5}(-\d{4})?\b', address)
        if zip_code:
            address_parts.append(zip_code.group())
        
        # Check all content sources
        all_content = ' '.join([website_content, privacy_content, terms_content]).lower()
        
        # Must find at least 2 address components
        matches = sum(1 for part in address_parts if part.lower() in all_content)
        return matches >= 2
    
    def generate_submission_package(self, collected_data: Dict) -> Dict:
        """Generate complete submission package with scraped data"""
        print("\n🔍 Scraping website and policy pages...")
        
        try:
            # Scrape main website
            website_url = collected_data.get('brand_website', '')
            if not website_url:
                raise ValueError("No brand website provided")
            
            # Add protocol if missing
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
                
            print(f"Scraping main website: {website_url}")
            website_data = self.scrape_website(website_url)
            
            if website_data.get('error'):
                print(f"Website scraping error: {website_data['error']}")
                website_data = {
                    'url': website_url,
                    'status_code': 0,
                    'text_content': '',
                    'sections': {},
                    'title': 'Error loading page',
                    'privacy_url': None,
                    'terms_url': None
                }
            
            # Extract policy URLs from scraped data or use provided ones
            privacy_url = website_data.get('privacy_url') or collected_data.get('privacy_url')
            terms_url = website_data.get('terms_url') or collected_data.get('terms_url')
            
            print(f"Found privacy URL: {privacy_url}")
            print(f"Found terms URL: {terms_url}")
            
            # Scrape policy pages
            policy_data = {}
            if privacy_url:
                try:
                    policy_data['privacy'] = self.scrape_website(privacy_url)
                except Exception as e:
                    print(f"Error scraping privacy page: {e}")
                    policy_data['privacy'] = {'error': str(e)}
                    
            if terms_url:
                try:
                    policy_data['terms'] = self.scrape_website(terms_url)
                except Exception as e:
                    print(f"Error scraping terms page: {e}")
                    policy_data['terms'] = {'error': str(e)}
            
            # Analyze compliance on main website
            print("Analyzing website compliance...")
            compliance_analysis = self.analyze_website_compliance(website_data)
            
            # Also analyze privacy and terms pages
            if privacy_url and 'privacy' in policy_data and not policy_data['privacy'].get('error'):
                print("Analyzing privacy policy...")
                privacy_analysis = self.analyze_website_compliance(policy_data['privacy'])
                compliance_analysis['debt_matches_found'] += privacy_analysis['debt_matches_found']
                compliance_analysis['marketing_matches_found'] += privacy_analysis['marketing_matches_found']
                compliance_analysis['total_violations'] += privacy_analysis['total_violations']
                compliance_analysis['compliance_issues'].extend(privacy_analysis['compliance_issues'])
                compliance_analysis['violation_locations'].extend(privacy_analysis['violation_locations'])
            
            if terms_url and 'terms' in policy_data and not policy_data['terms'].get('error'):
                print("Analyzing terms & conditions...")
                terms_analysis = self.analyze_website_compliance(policy_data['terms'])
                compliance_analysis['debt_matches_found'] += terms_analysis['debt_matches_found']
                compliance_analysis['marketing_matches_found'] += terms_analysis['marketing_matches_found']
                compliance_analysis['total_violations'] += terms_analysis['total_violations']
                compliance_analysis['compliance_issues'].extend(terms_analysis['compliance_issues'])
                compliance_analysis['violation_locations'].extend(terms_analysis['violation_locations'])
            
            # Update risk level based on total violations
            if compliance_analysis['total_violations'] > 0:
                compliance_analysis['risk_level'] = 'HIGH'
            
            # Verify phone number format
            support_phone = collected_data.get('support_phone', '')
            if support_phone:
                print(f"Verifying phone number: {support_phone}")
                phone_verification = self.verify_phone_number(support_phone)
                compliance_analysis['phone_verified'] = phone_verification['valid']
                if not phone_verification['valid']:
                    compliance_analysis['compliance_issues'].append(
                        f"Phone number validation failed: {phone_verification.get('error', 'Invalid format')}"
                    )
                    compliance_analysis['total_violations'] += 1
            
            # Verify email domain
            support_email = collected_data.get('support_email', '')
            if support_email:
                print(f"Verifying email domain: {support_email}")
                email_verification = self.verify_email_domain(support_email)
                compliance_analysis['email_domain_verified'] = email_verification['valid']
                if not email_verification['valid']:
                    compliance_analysis['compliance_issues'].append(
                        f"Email domain verification failed: {email_verification.get('error', 'Unknown error')}"
                    )
                    compliance_analysis['total_violations'] += 1
                    compliance_analysis['risk_level'] = 'HIGH'
            
            # Verify address appears on website/policies
            address = collected_data.get('street_address', '')
            if address:
                address_verified = self.verify_address_in_content(address, website_data, policy_data)
                compliance_analysis['address_verified'] = address_verified
                if not address_verified:
                    compliance_analysis['compliance_issues'].append("Address not found on website or policy pages")
            
            # Build complete package
            submission_package = {
                **collected_data,
                'website_content': website_data.get('text_content', ''),
                'privacy_url': privacy_url,
                'terms_url': terms_url,
                'website_data': website_data,
                'policy_data': policy_data,
                'compliance_analysis': compliance_analysis,
                'urls': [website_url] + collected_data.get('additional_urls', [])
            }
            
            print("Submission package generated successfully")
            return submission_package
            
        except Exception as e:
            print(f"Error generating submission package: {e}")
            # Return minimal package to avoid complete failure
            return {
                **collected_data,
                'website_content': '',
                'website_data': {'error': str(e)},
                'policy_data': {},
                'compliance_analysis': {'compliance_issues': [f"Website scraping failed: {str(e)}"], 'risk_level': 'HIGH'},
                'urls': [collected_data.get('brand_website', '')]
            }

def main():
    agent = A2PDataCollectionAgent()
    
    # Collect data interactively
    collected_data = agent.collect_submission_data()
    
    # Generate complete package with scraped data
    submission_package = agent.generate_submission_package(collected_data)
    
    print("\n📊 SUBMISSION PACKAGE GENERATED")
    print("=" * 40)
    print(f"Brand: {submission_package['brand_name']}")
    print(f"Website Status: {submission_package['website_data'].get('status_code', 'Error')}")
    print(f"Privacy URL: {submission_package.get('privacy_url', 'Not found')}")
    print(f"Terms URL: {submission_package.get('terms_url', 'Not found')}")
    print(f"Risk Level: {submission_package['compliance_analysis']['risk_level']}")
    
    if submission_package['compliance_analysis']['compliance_issues']:
        print("\n⚠️  COMPLIANCE ISSUES DETECTED:")
        for issue in submission_package['compliance_analysis']['compliance_issues']:
            print(f"  • {issue}")
    
    return submission_package

if __name__ == "__main__":
    main()
