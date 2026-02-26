#!/usr/bin/env python3
"""
Universal Pre-Release Episode Scanner for Any Pocket FM Series
"""

import requests
import json
import os
import time
import re
from concurrent.futures import ThreadPoolExecutor

class UniversalPreReleaseScanner:
    def __init__(self):
        # ===== DISCOVERED CDNs =====
        self.cdns = {
            'public_mp3': 'dbj64m8271a9g.cloudfront.net',     # Direct MP3 (NO AUTH!)
            'public_wav': 'dbj64m8271a9g.cloudfront.net',     # Direct WAV (NO AUTH!)
            'drm_mpd': 'd13yevwzck7i9p.cloudfront.net',       # DRM protected
            'media': 'media.pocketfm.com',                     # Main CDN
        }
        
        # ===== PATTERNS FROM SUCCESSFUL DOWNLOADS =====
        self.public_patterns = [
            # Pattern 1: MP3 format (like Ep 151)
            {
                'cdn': 'dbj64m8271a9g.cloudfront.net',
                'pattern': '/{hash}_{suffix}.mp3',
                'type': 'mp3',
                'auth': False
            },
            # Pattern 2: WAV format (like previous episodes)
            {
                'cdn': 'dbj64m8271a9g.cloudfront.net',
                'pattern': '/{hash}_{suffix}.wav',
                'type': 'wav',
                'auth': False
            }
        ]
        
        self.drm_patterns = [
            # Pattern 1: Standard DRM MPD
            {
                'cdn': 'd13yevwzck7i9p.cloudfront.net',
                'pattern': '/drm-aac/{show_id}/{story_id}/{hash}/h264.mpd',
                'type': 'mpd',
                'auth': True
            },
            # Pattern 2: Alternative DRM MPD
            {
                'cdn': 'd13yevwzck7i9p.cloudfront.net',
                'pattern': '/drm-aac/{show_id}/{story_id}/{hash}/drm_h264.mpd',
                'type': 'mpd',
                'auth': True
            }
        ]
        
        # ===== KNOWN HASHES FROM PREVIOUS SUCCESS =====
        self.known_hashes = [
            "b959fe1ed3495cb698ebcc4dfb79e71f37db2d6c",  # From Ep 151
            "9c1e2eeedf839e455d795e0f454684e74baf8dbd",  # From previous WAV
            "ceafa3da031452c8504c1f3526f12bda46b78708",  # From previous WAV
            "861570376f42d83d6dd5b9c67266af2fb3ec5642",  # From developer's WAV
        ]
        
        self.known_suffixes = [
            "VU0asCVaGZ",      # From Ep 151 MP3
            "LyaBxWjwJS",      # From previous WAV
            "NhergD9Ywf",      # From previous WAV
            "sbtoAX4YGF",      # From developer's WAV
        ]
        
        # Create download directory
        os.makedirs("universal_prerelease", exist_ok=True)
        
    def get_show_info(self, show_id):
        """
        Step 1: Show ki API details fetch karo
        """
        # Try with public API first (no auth)
        url = f"https://api.pocketfm.com/v2/content_api/show.get_details?show_id={show_id}&info_level=max"
        
        print(f"\n📡 Fetching show info for {show_id[:8]}...")
        
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                print(f"✅ Show found!")
                return data
            else:
                print(f"❌ API error: {r.status_code}")
                return None
        except:
            return None
    
    def extract_prerelease_from_json(self, data):
        """
        Step 2: JSON data mein se pre-release episodes nikaalo
        """
        if not data:
            return []
        
        prerelease = []
        
        # Check main episodes
        if 'stories' in data:
            for story in data['stories']:
                # Check for upcoming episodes
                if 'days_since_upload' in story and 'Releasing in' in story.get('days_since_upload', ''):
                    print(f"\n🔮 Found upcoming episode {story.get('seq_number')}: {story.get('days_since_upload')}")
                
                # Check for next_assets (pre-release)
                if 'next_assets' in story:
                    for asset in story['next_assets']:
                        if 'media_url' in asset and asset['media_url']:
                            if self.cdns['public_mp3'] in asset['media_url']:
                                print(f"\n✅ PRE-RELEASE FOUND!")
                                print(f"   Episode: {asset.get('asset_title')}")
                                print(f"   URL: {asset['media_url']}")
                                
                                prerelease.append({
                                    'title': asset.get('asset_title'),
                                    'url': asset['media_url'],
                                    'source': 'json_next_asset'
                                })
        
        return prerelease
    
    def scan_with_patterns(self, show_id, start_ep=1, end_ep=200):
        """
        Step 3: Known patterns se scan karo
        """
        print(f"\n🔍 Scanning episodes {start_ep}-{end_ep} with known patterns...")
        
        found = []
        
        # Try public patterns first (no auth needed)
        for ep in range(start_ep, end_ep + 1):
            # Try with known hashes and suffixes
            for hash_val in self.known_hashes:
                for suffix in self.known_suffixes:
                    for pattern in self.public_patterns:
                        url = f"http://{pattern['cdn']}/{hash_val}_{suffix}.{pattern['type']}"
                        
                        # Try to substitute episode number in hash
                        if str(ep) not in hash_val:
                            # Generate hash from episode number
                            import hashlib
                            ep_hash = hashlib.sha1(f"episode{ep}".encode()).hexdigest()[:40]
                            url2 = f"http://{pattern['cdn']}/{ep_hash}_{suffix}.{pattern['type']}"
                            
                            for test_url in [url, url2]:
                                try:
                                    r = requests.head(test_url, timeout=1)
                                    if r.status_code == 200:
                                        size = r.headers.get('content-length', 0)
                                        print(f"\n✅ Episode {ep} FOUND!")
                                        print(f"   URL: {test_url}")
                                        print(f"   Size: {int(size)/1024/1024:.1f} MB")
                                        
                                        found.append({
                                            'episode': ep,
                                            'url': test_url,
                                            'size': int(size),
                                            'type': pattern['type']
                                        })
                                        break
                                except:
                                    continue
            
            if ep % 20 == 0:
                print(f"   Progress: {ep-start_ep+1}/{end_ep-start_ep+1}", end='\r')
        
        return found
    
    def scan_show(self, show_id, show_name=None, scan_deep=False):
        """
        Main function - kisi bhi show ko scan karo
        """
        print("\n" + "=" * 80)
        print(f"🎯 SCANNING SHOW: {show_name or show_id[:20]}...")
        print("=" * 80)
        
        all_found = []
        
        # Method 1: JSON se pre-release nikaalo
        data = self.get_show_info(show_id)
        if data:
            json_prerelease = self.extract_prerelease_from_json(data)
            all_found.extend(json_prerelease)
        
        # Method 2: Deep scan with patterns
        if scan_deep:
            # Try around episode 150 (common pattern)
            pattern_found = self.scan_with_patterns(show_id, 140, 160)
            all_found.extend(pattern_found)
        
        # Download all found episodes
        if all_found:
            self.download_all(all_found, show_name or show_id[:8])
        
        return all_found
    
    def download_all(self, episodes, show_name):
        """Download all found episodes"""
        
        show_dir = f"universal_prerelease/{show_name}"
        os.makedirs(show_dir, exist_ok=True)
        
        print(f"\n📥 Downloading {len(episodes)} episodes...")
        
        for i, ep in enumerate(episodes, 1):
            if 'url' in ep:
                url = ep['url']
                
                # Determine filename
                if '.mp3' in url:
                    ext = 'mp3'
                elif '.wav' in url:
                    ext = 'wav'
                else:
                    ext = 'bin'
                
                if 'episode' in ep:
                    filename = f"{show_dir}/episode_{ep['episode']}.{ext}"
                else:
                    filename = f"{show_dir}/{show_name}_ep{i}.{ext}"
                
                print(f"\n📥 Downloading: {filename}")
                
                try:
                    r = requests.get(url, stream=True)
                    total = int(r.headers.get('content-length', 0))
                    
                    with open(filename, 'wb') as f:
                        downloaded = 0
                        for chunk in r.iter_content(8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total:
                                    pct = (downloaded / total) * 100
                                    print(f"\r   Progress: {pct:.1f}%", end='')
                    
                    print(f"\n✅ Saved: {filename} ({total/1024/1024:.1f} MB)")
                    time.sleep(1)  # Be nice to server
                    
                except Exception as e:
                    print(f"\n❌ Error: {e}")

# ===== MAIN FUNCTION =====
def main():
    scanner = UniversalPreReleaseScanner()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     🎯 UNIVERSAL PRE-RELEASE EPISODE SCANNER                 ║
║     Kisi bhi Pocket FM series ke pre-release episodes dhundhe ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Popular shows to scan (add more as you find)
    shows_to_scan = [
        {"id": "66e447439b52a78caccea30009ab3c98a39a8734", "name": "The Raichands"},
        {"id": "47251ceab13a93e9762f16122ed1b8f56951af6e", "name": "Mission Mangalsutra"},
        {"id": "431507ef41bdf6f365e2e1801afa3ca450456e5c", "name": "K for King"},
        {"id": "5b2ee241211bb2783b67662120b748d6a67c079c", "name": "Insta Millionaire"},
    ]
    
    while True:
        print("\n" + "=" * 60)
        print("OPTIONS:")
        print("1. Scan a specific show by ID")
        print("2. Scan popular shows list")
        print("3. Add new show to scan")
        print("4. Deep scan episode range")
        print("5. Exit")
        print("=" * 60)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            show_id = input("Enter Pocket FM Show ID: ").strip()
            show_name = input("Enter Show Name (optional): ").strip() or None
            deep = input("Deep scan? (y/n): ").lower() == 'y'
            scanner.scan_show(show_id, show_name, deep)
            
        elif choice == '2':
            for show in shows_to_scan:
                scanner.scan_show(show['id'], show['name'], False)
                time.sleep(3)
                
        elif choice == '3':
            show_id = input("Enter Show ID: ").strip()
            show_name = input("Enter Show Name: ").strip()
            shows_to_scan.append({"id": show_id, "name": show_name})
            print(f"✅ Added {show_name} to scan list")
            
        elif choice == '4':
            show_id = input("Enter Show ID: ").strip()
            start = int(input("Start episode: "))
            end = int(input("End episode: "))
            scanner.scan_with_patterns(show_id, start, end)
            
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
