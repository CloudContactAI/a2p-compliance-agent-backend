"""
ReadMe.com API Integration for Developer Documentation
"""
import requests
import os
from typing import List, Dict, Optional

class ReadMeIntegration:
    def __init__(self):
        self.api_key = os.getenv('README_API_KEY')
        self.base_url = "https://dash.readme.com/api/v1"
        self.headers = {
            "Authorization": f"Basic {self.api_key}",
            "x-readme-version": "v1.0"  # Update with your version
        }
    
    def search_docs(self, query: str) -> List[Dict]:
        """Search documentation using ReadMe's search API"""
        try:
            response = requests.get(
                f"{self.base_url}/docs/search",
                headers=self.headers,
                params={"search": query}
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"ReadMe search error: {e}")
            return []
    
    def get_doc(self, slug: str) -> Optional[Dict]:
        """Get a specific documentation page"""
        try:
            response = requests.get(
                f"{self.base_url}/docs/{slug}",
                headers=self.headers
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
                headers=self.headers
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
            excerpt = result.get('excerpt', '')
            slug = result.get('slug', '')
            url = f"https://developer.cloudcontactai.com/docs/{slug}"
            
            answer += f"**{title}**\n{excerpt}\n[Read more]({url})\n\n"
        
        return answer
