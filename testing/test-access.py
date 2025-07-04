#!/usr/bin/env python3
"""
Quick test to see if we can access the site with requests
"""
import requests
from bs4 import BeautifulSoup

def test_site_access():
    url = "https://www.bilibili.com/opus/763979363954720774?spm_id_from=333.1387.0.0"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    try:
        print(f"Testing access to: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status code: {response.status_code}")
        print(f"Content length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the expected elements
            title_elem = soup.select('.opus-module-title__text')
            content_elem = soup.select('.opus-module-content')
            collection_elem = soup.select('.opus-collection__content')
            
            print(f"\nFound elements:")
            print(f"  Title elements: {len(title_elem)}")
            print(f"  Content elements: {len(content_elem)}")
            print(f"  Collection elements: {len(collection_elem)}")
            
            if title_elem:
                print(f"  Title text: {title_elem[0].get_text()[:100]}...")
            
            # Print a sample of the HTML to see what we got
            print(f"\nFirst 500 chars of response:")
            print(response.text[:500])
        
    except Exception as e:
        print(f"Error accessing site: {e}")

if __name__ == "__main__":
    test_site_access()
