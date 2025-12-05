"""
CloudContactAI A2P 10DLC Compliance Agent - Clean Site Generator
Copyright (c) 2024 CloudContactAI, LLC. All rights reserved.

Generates cleaned versions of websites by:
1. Downloading HTML pages (homepage, privacy policy, terms & conditions)
2. Downloading all assets (CSS, JavaScript, images)
3. Removing debt-related content from text
4. Uploading everything to S3 for public access

The cleaned sites are completely self-contained and don't depend on the original domain.
"""
import re
import boto3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import mimetypes
import hashlib

class CleanSiteGenerator:
    """
    Generates cleaned, debt-free versions of websites for compliance review.
    
    Attributes:
        session: HTTP session for downloading content
        s3_client: Boto3 S3 client for uploading to AWS
        bucket_name: S3 bucket where cleaned sites are stored
        downloaded_assets: Cache to avoid downloading duplicate assets
        domain: Current domain being processed
        base_url: Base URL of the site being cleaned
    """
    
    def __init__(self):
        """Initialize the site generator with AWS credentials and HTTP session."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        self.bucket_name = 'a2p-compliance-websites'
        self.downloaded_assets = {}
        
    def generate_clean_site(self, submission_id, tracker):
        """
        Generate a cleaned website for a submission.
        
        Args:
            submission_id: DynamoDB submission ID
            tracker: SubmissionTracker instance for database access
            
        Returns:
            str: Public URL of the generated site
            
        Raises:
            ValueError: If submission not found or missing website URL
        """
        # Get submission data from DynamoDB
        submission = tracker.get_submission_by_id(submission_id)
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")
        
        submission_data = json.loads(submission.get('submission_data', '{}'))
        website_url = submission_data.get('brand_website', '')
        
        if not website_url:
            raise ValueError("No website URL in submission")
        
        # Ensure URL has protocol
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        # Extract domain for S3 directory structure
        self.domain = urlparse(website_url).netloc.replace('www.', '')
        self.base_url = website_url
        
        print(f"Generating clean site for {self.domain}")
        
        # Process homepage
        index_html = self._clean_and_download_assets(website_url, 'index.html')
        self._upload_to_s3(f"{self.domain}/index.html", index_html, 'text/html')
        
        # Find and process policy pages
        soup = BeautifulSoup(index_html, 'html.parser')
        privacy_url = self._find_policy_url(soup, website_url, ['privacy', 'privacy-policy'])
        terms_url = self._find_policy_url(soup, website_url, ['terms', 'terms-of-service', 'terms-conditions'])
        
        # Process privacy policy
        if privacy_url:
            try:
                privacy_html = self._clean_and_download_assets(privacy_url, 'privacy.html')
                self._upload_to_s3(f"{self.domain}/privacy.html", privacy_html, 'text/html')
            except Exception as e:
                print(f"Failed to clean privacy page: {e}")
        
        # Process terms & conditions
        if terms_url:
            try:
                terms_html = self._clean_and_download_assets(terms_url, 'terms.html')
                self._upload_to_s3(f"{self.domain}/terms.html", terms_html, 'text/html')
            except Exception as e:
                print(f"Failed to clean terms page: {e}")
        
        # Return public S3 URL
        return f"http://{self.bucket_name}.s3-website-us-east-1.amazonaws.com/{self.domain}/index.html"
    
    def _clean_and_download_assets(self, url, page_name):
        """
        Download a page, clean its content, and download all referenced assets.
        
        Args:
            url: URL of the page to download
            page_name: Name for logging purposes
            
        Returns:
            str: Cleaned HTML with rewritten asset URLs
        """
        response = self.session.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Download and rewrite CSS files
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href'):
                css_url = urljoin(url, link['href'])
                new_path = self._download_asset(css_url, 'css')
                if new_path:
                    link['href'] = new_path
        
        # Download and rewrite images
        for img in soup.find_all('img'):
            if img.get('src'):
                img_url = urljoin(url, img['src'])
                new_path = self._download_asset(img_url, 'images')
                if new_path:
                    img['src'] = new_path
        
        # Download and rewrite JavaScript files
        for script in soup.find_all('script', src=True):
            script_url = urljoin(url, script['src'])
            new_path = self._download_asset(script_url, 'js')
            if new_path:
                script['src'] = new_path
        
        # Remove debt-related content from text
        debt_terms = [
            r'\bdebt\b', r'\bcollection\b', r'\bcollector\b', r'\bcollecting\b',
            r'\bowe\b', r'\bowed\b', r'\bowing\b',
            r'\bpayment\b', r'\bpayments\b', r'\bpay\b',
            r'\bdefault\b', r'\bdelinquent\b', r'\bpast due\b',
            r'\bcredit repair\b', r'\bskip.?trac\w+\b'
        ]
        
        for element in soup.find_all(text=True):
            # Skip script and style tags
            if element.parent.name in ['script', 'style']:
                continue
            
            text = element.string
            if text:
                # Replace debt terms with [REDACTED]
                for pattern in debt_terms:
                    if re.search(pattern, text, re.IGNORECASE):
                        text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
                element.replace_with(text)
        
        return str(soup)
    
    def _download_asset(self, url, asset_type):
        """
        Download an asset (CSS, JS, image) and upload to S3.
        
        Args:
            url: URL of the asset to download
            asset_type: Type of asset ('css', 'js', 'images')
            
        Returns:
            str: Relative path to the asset in S3, or None if download failed
        """
        # Skip data URLs (inline images)
        if url.startswith('data:'):
            return url
        
        # Return cached path if already downloaded
        if url in self.downloaded_assets:
            return self.downloaded_assets[url]
        
        try:
            # Generate unique filename based on URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            ext = url.split('?')[0].split('.')[-1][:4]
            filename = f"{url_hash}.{ext}"
            
            # Download asset
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            # Determine content type
            content_type = response.headers.get('content-type', 
                                               mimetypes.guess_type(url)[0] or 
                                               'application/octet-stream')
            
            # Upload to S3
            s3_key = f"{self.domain}/assets/{asset_type}/{filename}"
            self._upload_to_s3(s3_key, response.content, content_type)
            
            # Store relative path for HTML rewriting
            relative_path = f"assets/{asset_type}/{filename}"
            self.downloaded_assets[url] = relative_path
            
            return relative_path
            
        except Exception as e:
            print(f"Failed to download asset {url}: {e}")
            return None
    
    def _find_policy_url(self, soup, base_url, keywords):
        """
        Find privacy policy or terms & conditions URL in page links.
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for resolving relative links
            keywords: List of keywords to search for in links
            
        Returns:
            str: Full URL of the policy page, or None if not found
        """
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            text = link.get_text().lower()
            
            for keyword in keywords:
                if keyword in href or keyword in text:
                    return urljoin(base_url, link['href'])
        return None
    
    def _upload_to_s3(self, key, content, content_type):
        """
        Upload content to S3 bucket.
        
        Args:
            key: S3 object key (path)
            content: Content to upload (string or bytes)
            content_type: MIME type of the content
        """
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content.encode('utf-8') if isinstance(content, str) else content,
            ContentType=content_type,
            
        )
        print(f"Uploaded {key} to S3")
