#!/usr/bin/env python3
"""
Super Yoddha - Find Working URL Pattern
"""

import requests
import json

class SuperYoddhaURLFinder:
    def __init__(self):
        self.show_id = "f629196ee7df34287ef2672e91fda9f939e9d02d"
        self.api_url = f"https://api.pocketfm.com/v2/content_api/show.get_details?show_id={self.show_id}&info_level=max"
        
    def get_api_data(self):
        """API se show details fetch karo"""
        
        print("\n📡 Fetching Super Yoddha API data...")
        
        try:
            r = requests.get(self.api_url, timeout=5)
            print(f"Status: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                
                # Save for analysis
                with open('super_yoddha_api.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print("✅ API data saved to super_yoddha_api.json")
                
                # Extract episode URLs if any
                self.extract_urls(data)
                
                return data
            else:
                print(f"❌ API error: {r.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def extract_urls(self, data):
        """API response mein se URLs nikaalo"""
        
        urls = []
        
        # Check various paths
        if 'stories' in data:
            for story in data['stories']:
                # Check for media URLs
                for field in ['media_url_enc', 'media_url', 'hls_url', 'video_url']:
                    if field in story and story[field]:
                        url = story[field]
                        if 'cloudfront' in url:
                            print(f"\n✅ Found URL in story:")
                            print(f"   {url}")
                            urls.append(url)
                
                # Check next_assets (pre-release)
                if 'next_assets' in story:
                    for asset in story['next_assets']:
                        if 'media_url' in asset and asset['media_url']:
                            url = asset['media_url']
                            if 'cloudfront' in url:
                                print(f"\n🔮 Found pre-release URL in next_assets:")
                                print(f"   {url}")
                                urls.append(url)
        
        return urls

if __name__ == "__main__":
    finder = SuperYoddhaURLFinder()
    finder.get_api_data()
