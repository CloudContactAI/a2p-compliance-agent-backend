"""
ReadMe.com API Integration for Developer Documentation
"""
import requests
import os
from typing import List, Dict, Optional
import base64

class ReadMeIntegration:
    def __init__(self):
        api_key = os.getenv('README_API_KEY', '')
        # ReadMe uses Basic Auth with API key as username and empty password
        credentials = f"{api_key}:"
        self.auth_header = base64.b64encode(credentials.encode()).decode()
        self.base_url = "https://dash.readme.com/api/v1"
        self.headers = {
            "Authorization": f"Basic {self.auth_header}",
            "x-readme-version": "v1.0"
        }
    
    def search_docs(self, query: str) -> List[Dict]:
        """Search documentation using ReadMe's API"""
        try:
            # Try to get all docs and filter locally
            response = requests.get(
                f"{self.base_url}/docs",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                all_docs = response.json()
                # Simple keyword matching
                query_lower = query.lower()
                results = []
                for doc in all_docs:
                    title = doc.get('title', '').lower()
                    excerpt = doc.get('excerpt', '').lower()
                    if query_lower in title or query_lower in excerpt:
                        results.append(doc)
                return results[:5]  # Top 5 matches
            return []
        except Exception as e:
            print(f"ReadMe search error: {e}")
            return []
    
    def get_doc(self, slug: str) -> Optional[Dict]:
        """Get a specific documentation page"""
        try:
            response = requests.get(
                f"{self.base_url}/docs/{slug}",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"ReadMe get doc error: {e}")
            return None
    
    def get_all_docs(self) -> List[Dict]:
        """Get all documentation pages"""
        try:
            response = requests.get(
                f"{self.base_url}/docs",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"ReadMe get all docs error: {e}")
            return []
    
    def format_answer(self, results: List[Dict], query: str) -> str:
        """Format search results into a readable answer"""
        if not results:
            return f"I couldn't find specific documentation about '{query}'. Please visit https://developer.cloudcontactai.com for more information."
        
        answer = f"Here's what I found about '{query}':\n\n"
        for result in results[:3]:  # Top 3 results
            title = result.get('title', 'Untitled')
            excerpt = result.get('excerpt', result.get('body', '')[:200])
            slug = result.get('slug', '')
            url = f"https://developer.cloudcontactai.com/docs/{slug}"
            
            answer += f"**{title}**\n{excerpt}\n[Read more]({url})\n\n"
        
        return answer
