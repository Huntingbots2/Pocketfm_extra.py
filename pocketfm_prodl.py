#!/usr/bin/env python3
"""
================================================================================
🚀 POCKETFM DOWNLOADER PRO - DEVELOPER EDITION v3.0
================================================================================
Features:
✅ Valid Token Auto-Load from sessions.json
✅ Any Show - Just paste URL or ID
✅ Published Episodes + Pre-Release Episodes
✅ Auto API Parsing + Pattern Discovery
✅ Multi-Threaded Downloads
✅ Resume Support + State Management
✅ Automatic Hash Database Building
================================================================================
"""

import requests
import json
import os
import time
import re
import hashlib
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class PocketFMProfessional:
    """
    Developer-level Pocket FM Downloader
    """
    
    def __init__(self):
        print("\n" + "="*80)
        print("🚀 POCKETFM DOWNLOADER PRO - INITIALIZING...")
        print("="*80)
        
        # ===== STEP 1: LOAD VALID TOKEN (SABSE IMPORTANT) =====
        self.load_token()  # Token yahan load hoga
        
        # ===== CONFIGURATION =====
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # ===== DISCOVERED CDNs =====
        self.cdns = {
            'public_wav': 'http://dbj64m8271a9g.cloudfront.net',
            'public_mp3': 'http://dbj64m8271a9g.cloudfront.net',
            'drm_mpd': 'https://d13yevwzck7i9p.cloudfront.net',
            'video_dash': 'https://ddqs490ahjgsl.cloudfront.net',
            'media': 'https://media.pocketfm.com',
            'audio': 'https://audio.pocketfm.com',
        }
        
        # ===== PATTERNS DATABASE (AUTO-GROWING) =====
        self.patterns = {
            'hashes': [
                "b959fe1ed3495cb698ebcc4dfb79e71f37db2d6c",  # K for King Ep151
                "9c1e2eeedf839e455d795e0f454684e74baf8dbd",  # Super Yoddha 2392
                "ceafa3da031452c8504c1f3526f12bda46b78708",  # Super Yoddha 2393
                "861570376f42d83d6dd5b9c67266af2fb3ec5642",  # The Raichands 2351
            ],
            'suffixes': [
                "VU0asCVaGZ",  # MP3
                "LyaBxWjwJS",  # WAV 226MB
                "NhergD9Ywf",  # WAV 213MB
                "sbtoAX4YGF",  # WAV 214MB
            ],
            'api_endpoints': [
                "/v2/content_api/show.get_details",
                "/v2/shows/{show_id}/episodes",
                "/v2/shows/{show_id}/episodes?limit=1000",
                "/v2/shows/{show_id}/episodes?status=all",
            ]
        }
        
        # ===== STATE MANAGEMENT =====
        self.downloaded = set()
        self.discovered = set()
        self.load_state()
        
        # ===== DIRECTORIES =====
        os.makedirs("downloads", exist_ok=True)
        os.makedirs("database", exist_ok=True)
        
        print(f"✅ Token Valid: {self.token_valid}")
        print(f"📊 Hash Database: {len(self.patterns['hashes'])} entries")
        print(f"📊 Suffix Database: {len(self.patterns['suffixes'])} entries")
        print(f"📥 Downloaded: {len(self.downloaded)} episodes")
        print("="*80)
    
    def load_token(self):
        """
        Manually token set karo - APNA TOKEN YAHAN DAALO
        """
        # ===== REPLACE WITH YOUR VALID TOKEN AND UID =====
        self.token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjYXRlZ29yeSI6ImFjY2VzcyIsImRldmljZV9pZCI6IjMxYjNiYzYzZDg3ZjExMTQiLCJleHBpcnkiOjE3NzIzNDE0NjEsImlhdCI6MTc3MjE2ODY2MSwicGxhdGZvcm0iOiJhbmRyb2lkIiwicm9sZSI6Ikxpc3RlbmVyIiwidGVuYW50IjoicG9ja2V0X2ZtIiwidWlkIjoiYTU5MjQ0ZGE0MjAyM2M0ZjBkMTJmODcyMTUyZDk3ZDlhMThmZjc4YyIsInZlcnNpb24iOiJ2MiJ9.CyxQ8zGqyJppIV3QydXp_BCfS6WsN0eSsSjaCHDtaR4"
        self.uid = "a59244da42023c4f0d12f872152d97d9a18ff78c"
        self.token_valid = True
        
        print(f"✅ Token loaded manually!")
        print(f"🆔 UID: {self.uid[:20]}...")
        print(f"🔑 Token: {self.token[:30]}...")
        
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'X-User-Id': self.uid,
            'User-Agent': 'okhttp/4.12.0',
            'Device-Id': '31b3bc63d87f1114',
            'Platform': 'android',
            'Accept': 'application/json',
        }
    
    def load_state(self):
        """Previous state load karo"""
        try:
            if os.path.exists('database/state.json'):
                with open('database/state.json', 'r') as f:
                    state = json.load(f)
                    self.downloaded = set(state.get('downloaded', []))
                    self.discovered = set(state.get('discovered', []))
                    self.patterns['hashes'] = list(set(self.patterns['hashes'] + state.get('hashes', [])))
                    self.patterns['suffixes'] = list(set(self.patterns['suffixes'] + state.get('suffixes', [])))
        except:
            pass
    
    def save_state(self):
        """Current state save karo"""
        try:
            with open('database/state.json', 'w') as f:
                json.dump({
                    'downloaded': list(self.downloaded),
                    'discovered': list(self.discovered),
                    'hashes': self.patterns['hashes'],
                    'suffixes': self.patterns['suffixes'],
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
        except:
            pass
    
    def extract_show_id(self, url_or_id):
        """URL ya ID se show ID extract karo"""
        # Agar direct ID hai (40 chars hex)
        if re.match(r'^[a-f0-9]{40}$', url_or_id):
            return url_or_id
        
        # URL se extract karo
        match = re.search(r'show/([a-f0-9]{40})', url_or_id)
        if match:
            return match.group(1)
        
        # Last part of URL
        parts = url_or_id.split('/')
        for part in parts:
            if re.match(r'^[a-f0-9]{40}$', part):
                return part
        
        return url_or_id
    
    def get_show_info(self, show_id):
        """
        STEP 1: API se show ki complete info le
        (YAHI DEVELOPER KARTA HAI)
        """
        if not self.token_valid:
            print("❌ Token required for API access!")
            return None
        
        print(f"\n📡 FETCHING SHOW INFO FROM API...")
        
        # Try different endpoints
        endpoints = [
            f"https://api.pocketfm.com/v2/content_api/show.get_details?show_id={show_id}&info_level=max&caller_uid={self.uid}",
            f"https://api.pocketfm.com/v2/shows/{show_id}/episodes?limit=1000",
            f"https://api.pocketfm.com/v2/shows/{show_id}/episodes?status=all",
        ]
        
        for endpoint in endpoints:
            try:
                r = self.session.get(endpoint, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    print(f"✅ API Success: {endpoint.split('?')[0]}")
                    return data
                else:
                    print(f"⚠️ {endpoint.split('?')[0]}: {r.status_code}")
            except Exception as e:
                print(f"⚠️ Error: {e}")
        
        return None
    
    def extract_prerelease_from_api(self, data, show_id):
        """
        STEP 2: API response se pre-release episodes nikaal
        (DEVELOPER KA SECRET WEAPON)
        """
        prerelease = []
        
        print(f"\n🔍 SCANNING API RESPONSE FOR PRE-RELEASE...")
        
        # Check stories array
        if 'stories' in data:
            stories = data['stories']
            print(f"📊 Total episodes in API: {len(stories)}")
            
            for story in stories:
                ep_num = story.get('seq_number')
                
                # ===== PRE-RELEASE INDICATORS =====
                # 1. Check next_assets (DIRECT PRE-RELEASE LINKS!)
                if 'next_assets' in story:
                    for asset in story['next_assets']:
                        if 'media_url' in asset and asset['media_url']:
                            url = asset['media_url']
                            
                            print(f"\n🎯 PRE-RELEASE EPISODE FOUND!")
                            print(f"   Episode: {ep_num + 1} - {asset.get('asset_title')}")
                            print(f"   URL: {url}")
                            
                            # Extract hash-suffix for database
                            self.extract_patterns_from_url(url)
                            
                            prerelease.append({
                                'episode': ep_num + 1,
                                'title': asset.get('asset_title'),
                                'url': url,
                                'type': 'pre-release',
                                'source': 'next_assets'
                            })
                
                # 2. Check pseudo_locked (premium/upcoming)
                if story.get('pseudo_locked') or story.get('coins_required', 0) > 0:
                    print(f"\n🔒 Premium/Upcoming Episode {ep_num}")
                    
                    # Try to get media URL
                    for field in ['media_url_enc', 'video_url', 'hls_url']:
                        if field in story and story[field]:
                            url = story[field]
                            print(f"   DRM URL: {url[:100]}...")
                            
                            prerelease.append({
                                'episode': ep_num,
                                'title': story.get('story_title'),
                                'url': url,
                                'type': 'premium',
                                'source': 'locked'
                            })
                            break
        
        # Check episodes array
        elif 'episodes' in data:
            episodes = data['episodes']
            print(f"📊 Total episodes in API: {len(episodes)}")
            
            for ep in episodes:
                ep_num = ep.get('episode_no') or ep.get('seq_number')
                
                # Check for direct media URLs
                for field in ['media_url_enc', 'video_url', 'audio_url']:
                    if field in ep and ep[field]:
                        url = ep[field]
                        if 'drm' in url or 'enc' in field:
                            print(f"\n🔒 DRM Episode {ep_num}: {url[:100]}...")
                            
                            prerelease.append({
                                'episode': ep_num,
                                'title': ep.get('title'),
                                'url': url,
                                'type': 'drm',
                                'source': 'media_enc'
                            })
        
        return prerelease
    
    def extract_patterns_from_url(self, url):
        """
        URL se hash aur suffix nikaal kar database mein add kar
        """
        if 'cloudfront.net' not in url:
            return
        
        # Extract filename
        filename = url.split('/')[-1]
        
        # Check for hash_suffix pattern
        if '_' in filename:
            parts = filename.replace('.mp3', '').replace('.wav', '').replace('.mpd', '').split('_')
            if len(parts) == 2:
                hash_val = parts[0]
                suffix = parts[1]
                
                # Add to database if new
                if len(hash_val) == 40 and hash_val not in self.patterns['hashes']:
                    self.patterns['hashes'].append(hash_val)
                    print(f"   ➕ New hash added to database: {hash_val[:20]}...")
                
                if suffix not in self.patterns['suffixes']:
                    self.patterns['suffixes'].append(suffix)
                    print(f"   ➕ New suffix added: {suffix}")
                
                self.save_state()
    
    def scan_with_patterns(self, show_id, start_ep=1, end_ep=500):
        """
        STEP 3: Pattern-based scanning for more episodes
        """
        print(f"\n🔍 PATTERN-BASED SCANNING {start_ep}-{end_ep}")
        
        found = []
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for ep in range(start_ep, end_ep + 1):
                for hash_val in self.patterns['hashes']:
                    for suffix in self.patterns['suffixes']:
                        # Try WAV
                        url = f"{self.cdns['public_wav']}/{hash_val}_{suffix}.wav"
                        futures.append(executor.submit(self.check_url, ep, url, 'wav'))
                        
                        # Try MP3
                        url2 = f"{self.cdns['public_mp3']}/{hash_val}_{suffix}.mp3"
                        futures.append(executor.submit(self.check_url, ep, url2, 'mp3'))
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                result = future.result()
                if result:
                    found.append(result)
                    self.extract_patterns_from_url(result['url'])
                
                if completed % 100 == 0:
                    print(f"\r   Progress: {completed}/{len(futures)}", end='')
        
        return found
    
    def check_url(self, ep, url, media_type):
        """URL check karo"""
        try:
            r = requests.head(url, timeout=1)
            if r.status_code == 200:
                size = r.headers.get('content-length', 0)
                size_mb = int(size) / 1024 / 1024
                
                print(f"\n✅ Episode {ep} FOUND as {media_type.upper()}!")
                print(f"   Size: {size_mb:.1f} MB")
                print(f"   URL: {url}")
                
                return {
                    'episode': ep,
                    'url': url,
                    'size': size_mb,
                    'type': media_type
                }
        except:
            pass
        return None
    
    def download_episode(self, episode_info, show_name):
        """
        STEP 4: Download episode
        """
        ep = episode_info['episode']
        url = episode_info['url']
        media_type = episode_info.get('type', 'mp3')
        
        # Create show directory
        show_dir = f"downloads/{show_name.replace(' ', '_')}"
        os.makedirs(show_dir, exist_ok=True)
        
        # Determine filename
        if '.mp3' in url:
            ext = 'mp3'
        elif '.wav' in url:
            ext = 'wav'
        elif '.mpd' in url:
            ext = 'mpd'
        else:
            ext = media_type
        
        filename = f"{show_dir}/episode_{ep}.{ext}"
        
        # Check if already downloaded
        if filename in self.downloaded:
            print(f"⏭️ Episode {ep} already downloaded")
            return True
        
        print(f"\n📥 Downloading Episode {ep}...")
        
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
            
            self.downloaded.add(filename)
            self.save_state()
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False
    
    def process_show(self, show_url_or_id):
        """
        MAIN FUNCTION - Sab kuch ek saath
        """
        print("\n" + "🚀"*40)
        print("🚀 PROCESSING SHOW")
        print("🚀"*40)
        
        # Step 0: Token check
        if not self.token_valid:
            print("❌ Cannot proceed without valid token!")
            print("Please login via Telegram bot first.")
            return
        
        # Step 1: Extract show ID
        show_id = self.extract_show_id(show_url_or_id)
        print(f"\n📌 Show ID: {show_id}")
        
        # Step 2: Get show info from API
        api_data = self.get_show_info(show_id)
        
        show_name = "Unknown"
        prerelease = []
        
        if api_data:
            # Try to get show name
            if 'show' in api_data:
                show_name = api_data['show'].get('title', show_id[:12])
            elif 'result' in api_data and len(api_data['result']) > 0:
                show_name = api_data['result'][0].get('show_title', show_id[:12])
            
            # Extract pre-release from API
            prerelease = self.extract_prerelease_from_api(api_data, show_id)
        
        # Step 3: Process pre-release episodes
        if prerelease:
            print(f"\n📊 FOUND {len(prerelease)} PRE-RELEASE EPISODES FROM API!")
            
            for ep in prerelease:
                print(f"\n🎯 {ep['title']}")
                print(f"   URL: {ep['url']}")
                
                # Download
                resp = input(f"\n📥 Download this episode? (y/n): ").lower()
                if resp == 'y':
                    self.download_episode({
                        'episode': ep['episode'],
                        'url': ep['url'],
                        'type': 'mp3' if '.mp3' in ep['url'] else 'wav'
                    }, show_name)
        
        # Step 4: Ask for range scan
        print(f"\n🔍 Current hash database: {len(self.patterns['hashes'])} entries")
        scan_range = input("\nScan episode range? (e.g., 1-100 or 'no'): ").strip()
        
        if scan_range.lower() != 'no':
            try:
                if '-' in scan_range:
                    start, end = map(int, scan_range.split('-'))
                else:
                    start = 1
                    end = int(scan_range)
                
                found = self.scan_with_patterns(show_id, start, end)
                
                if found:
                    print(f"\n📊 Found {len(found)} episodes via pattern scanning!")
                    
                    for ep_info in found:
                        print(f"\nEpisode {ep_info['episode']} - {ep_info['size']:.1f} MB")
                        resp = input("Download? (y/n): ").lower()
                        if resp == 'y':
                            self.download_episode(ep_info, show_name)
            except:
                print("❌ Invalid range")
        
        print(f"\n{'='*80}")
        print(f"✅ SHOW PROCESSING COMPLETE!")
        print(f"📊 Total discovered episodes: {len(self.discovered)}")
        print(f"📥 Total downloaded: {len(self.downloaded)}")
        print(f"📁 Hash database size: {len(self.patterns['hashes'])}")
        print(f"{'='*80}")

# ===== INTERACTIVE MENU =====
def main():
    downloader = PocketFMProfessional()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     🚀 POCKETFM DOWNLOADER PRO - DEVELOPER EDITION           ║
║     Published + Pre-Release Episodes - Any Show              ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    while True:
        print("\n" + "="*60)
        print("OPTIONS:")
        print("1. Download by URL or Show ID")
        print("2. View Database Stats")
        print("3. Add Hash Manually")
        print("4. Add Suffix Manually")
        print("5. Refresh Token")
        print("6. Exit")
        print("="*60)
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            show = input("Enter Pocket FM URL or Show ID: ").strip()
            downloader.process_show(show)
        
        elif choice == '2':
            print(f"\n📊 DATABASE STATS:")
            print(f"   Hashes: {len(downloader.patterns['hashes'])}")
            print(f"   Suffixes: {len(downloader.patterns['suffixes'])}")
            print(f"   Downloaded: {len(downloader.downloaded)}")
            print(f"   Discovered: {len(downloader.discovered)}")
            
            if len(downloader.patterns['hashes']) > 0:
                print(f"\n📋 Last 5 hashes:")
                for h in downloader.patterns['hashes'][-5:]:
                    print(f"   • {h[:30]}...")
            
            if len(downloader.patterns['suffixes']) > 0:
                print(f"\n📋 Suffixes:")
                for s in downloader.patterns['suffixes']:
                    print(f"   • {s}")
        
        elif choice == '3':
            new_hash = input("Enter hash (40 chars hex): ").strip()
            if len(new_hash) == 40 and new_hash not in downloader.patterns['hashes']:
                downloader.patterns['hashes'].append(new_hash)
                downloader.save_state()
                print("✅ Hash added!")
        
        elif choice == '4':
            new_suffix = input("Enter suffix: ").strip()
            if new_suffix not in downloader.patterns['suffixes']:
                downloader.patterns['suffixes'].append(new_suffix)
                downloader.save_state()
                print("✅ Suffix added!")
        
        elif choice == '5':
            downloader.load_token()
            print("✅ Token refreshed!")
        
        elif choice == '6':
            downloader.save_state()
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()
