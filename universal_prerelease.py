#!/usr/bin/env python3
"""
================================================================================
🎯 POCKET FM UNIVERSAL PRE-RELEASE DOWNLOADER
================================================================================
Kisi bhi show ke pre-release episodes automatically dhundhe aur download kare
Author: Based on successful reverse engineering of dbj64m8271a9g.cloudfront.net
================================================================================
"""

import requests
import json
import time
import os
import re
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import hashlib

class UniversalPreReleaseDownloader:
    """
    Main class for downloading pre-release episodes from any Pocket FM show
    """
    
    def __init__(self):
        # ===== CONFIGURATION =====
        self.output_dir = "prerelease_downloads"
        self.max_workers = 5
        self.request_timeout = 5
        self.download_timeout = 30
        self.retry_count = 3
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        # ===== DISCOVERED CDNs FROM PREVIOUS SUCCESS =====
        self.known_cdns = [
            'dbj64m8271a9g.cloudfront.net',    # Working pre-release CDN (no auth)
            'media.pocketfm.com',               # Main CDN (needs auth)
            'd13yevwzck7i9p.cloudfront.net',    # DRM CDN (needs auth)
            'ddqs490ahjgsl.cloudfront.net',      # DASH CDN (needs auth)
            'audio.pocketfm.com',                # Audio CDN (needs auth)
        ]
        
        # ===== PATTERNS FROM WORKING PRE-RELEASE =====
        self.known_patterns = [
            # Pattern 1: Direct WAV files (like your successful downloads)
            {
                'type': 'wav',
                'pattern': '/{hash}_{suffix}.wav',
                'auth_needed': False,
                'cdns': ['dbj64m8271a9g.cloudfront.net']
            },
            # Pattern 2: MPD manifests
            {
                'type': 'mpd',
                'pattern': '/episodes/{show_id}_{ep_num}/manifest.mpd',
                'auth_needed': True,
                'cdns': ['media.pocketfm.com']
            },
            # Pattern 3: DRM MPD
            {
                'type': 'drm_mpd',
                'pattern': '/drm-aac/{show_id}/{unique_id}/h264.mpd',
                'auth_needed': True,
                'cdns': ['d13yevwzck7i9p.cloudfront.net']
            }
        ]
        
        # ===== KNOWN HASHES FROM YOUR SUCCESSFUL DOWNLOADS =====
        self.known_hashes = [
            "9c1e2eeedf839e455d795e0f454684e74baf8dbd",
            "ceafa3da031452c8504c1f3526f12bda46b78708"
        ]
        
        self.known_suffixes = [
            "LyaBxWjwJS",
            "NhergD9Ywf"
        ]
        
    # ======================================================================
    # STEP 1: SHOW INFORMATION FETCH KARO
    # ======================================================================
    
    def get_show_info(self, show_id):
        """
        Pocket FM API se show ki details fetch karo
        """
        api_url = f"https://api.pocketfm.com/v2/content_api/show.get_details?show_id={show_id}&info_level=max"
        
        print(f"\n📡 Fetching show info for ID: {show_id}")
        
        try:
            r = self.session.get(api_url, timeout=self.request_timeout)
            
            if r.status_code == 200:
                data = r.json()
                
                # Extract show metadata
                show_info = {}
                episodes = []
                
                if 'show' in data:
                    show_info = data['show']
                elif 'data' in data and 'show' in data['data']:
                    show_info = data['data']['show']
                
                if 'episodes' in data:
                    episodes = data['episodes']
                elif 'data' in data and 'episodes' in data['data']:
                    episodes = data['data']['episodes']
                
                show_name = show_info.get('title', 'Unknown')
                total_eps = show_info.get('total_episodes', len(episodes))
                
                print(f"✅ Show: {show_name}")
                print(f"📊 Total Episodes: {total_eps}")
                print(f"📥 Episodes in response: {len(episodes)}")
                
                return {
                    'id': show_id,
                    'name': show_name,
                    'total_episodes': total_eps,
                    'episodes': episodes,
                    'raw_data': data
                }
            else:
                print(f"❌ API error: HTTP {r.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching show info: {e}")
            return None
    
    # ======================================================================
    # STEP 2: EPISODE GAPS DETECT KARO (PRE-RELEASE INDICATOR)
    # ======================================================================
    
    def find_episode_gaps(self, show_info):
        """
        API response mein episode numbers ke beech gaps dhundho
        Ye gaps pre-release episodes ke indicators hote hain
        """
        if not show_info or 'episodes' not in show_info:
            return []
        
        episodes = show_info['episodes']
        ep_numbers = []
        
        for ep in episodes:
            ep_no = ep.get('episode_no') or ep.get('episodeNumber')
            if ep_no:
                ep_numbers.append(int(ep_no))
        
        if not ep_numbers:
            return []
        
        ep_numbers.sort()
        
        print(f"\n🔍 Analyzing episode gaps...")
        print(f"   Episode range: {ep_numbers[0]} to {ep_numbers[-1]}")
        print(f"   Total episodes in API: {len(ep_numbers)}")
        
        # Find missing episode numbers
        all_possible = set(range(ep_numbers[0], ep_numbers[-1] + 1))
        existing = set(ep_numbers)
        gaps = sorted(list(all_possible - existing))
        
        if gaps:
            print(f"🎯 Found {len(gaps)} missing episodes (potential pre-release):")
            print(f"   {gaps[:20]}..." if len(gaps) > 20 else f"   {gaps}")
        else:
            print(f"✅ No gaps found - all episodes consecutive")
        
        return gaps
    
    # ======================================================================
    # STEP 3: CDN PATTERNS DISCOVER KARO
    # ======================================================================
    
    def discover_cdn_patterns(self, show_info):
        """
        Existing episodes se CDN patterns discover karo
        """
        if not show_info or 'episodes' not in show_info:
            return []
        
        episodes = show_info['episodes']
        discovered_patterns = []
        discovered_cdns = set()
        
        print(f"\n🔍 Discovering CDN patterns from existing episodes...")
        
        for ep in episodes[:10]:  # Check first 10 episodes
            ep_no = ep.get('episode_no') or ep.get('episodeNumber')
            
            # Check all possible URL fields
            for field in ['media_url_enc', 'video_url', 'audio_url', 'stream_url', 'mpd_url']:
                if field in ep and ep[field]:
                    url = ep[field]
                    
                    # Extract CDN domain
                    parsed = urlparse(url)
                    cdn = parsed.netloc
                    
                    if cdn and cdn not in discovered_cdns:
                        discovered_cdns.add(cdn)
                        print(f"✅ Found CDN: {cdn}")
                    
                    # Extract path pattern
                    path = parsed.path
                    
                    # Try to identify pattern
                    if '_' in path and 'episode' in path:
                        pattern = {
                            'cdn': cdn,
                            'path_template': path,
                            'has_episode_num': True,
                            'example_url': url
                        }
                        discovered_patterns.append(pattern)
                        print(f"   Pattern: {path[:100]}...")
        
        return list(discovered_cdns), discovered_patterns
    
    # ======================================================================
    # STEP 4: EPISODE URLS GENERATE KARO
    # ======================================================================
    
    def generate_urls_for_episode(self, show_id, ep_num, cdns=None, patterns=None):
        """
        Episode number ke liye possible URLs generate karo
        """
        urls = []
        
        # Method 1: Try known CDNs with standard patterns
        standard_cdns = cdns or self.known_cdns
        standard_patterns = [
            f"/episodes/{show_id}_{ep_num}/manifest.mpd",
            f"/episodes/{show_id}/{ep_num}/master.mpd",
            f"/shows/{show_id}/episodes/{ep_num}.mpd",
            f"/content/{show_id}/episode_{ep_num}.mpd",
        ]
        
        for cdn in standard_cdns:
            for pattern in standard_patterns:
                url = f"https://{cdn}{pattern}"
                urls.append({
                    'url': url,
                    'cdn': cdn,
                    'pattern': pattern,
                    'auth_needed': 'media' in cdn or 'd13' in cdn
                })
        
        # Method 2: Try the successful WAV pattern
        if 'dbj64m8271a9g.cloudfront.net' in standard_cdns:
            for hash_val in self.known_hashes:
                for suffix in self.known_suffixes:
                    # Try to substitute episode number in hash (if pattern matches)
                    if '2392' in hash_val:
                        modified_hash = hash_val.replace('2392', str(ep_num).zfill(4))
                        url = f"http://dbj64m8271a9g.cloudfront.net/{modified_hash}_{suffix}.wav"
                        urls.append({
                            'url': url,
                            'cdn': 'dbj64m8271a9g.cloudfront.net',
                            'pattern': f"/{modified_hash}_{suffix}.wav",
                            'auth_needed': False
                        })
        
        # Method 3: Try hash generation from episode number
        for cdn in ['dbj64m8271a9g.cloudfront.net']:
            # Generate hash from episode number
            ep_hash = hashlib.sha1(f"episode{ep_num}".encode()).hexdigest()[:40]
            for suffix in self.known_suffixes:
                url = f"http://{cdn}/{ep_hash}_{suffix}.wav"
                urls.append({
                    'url': url,
                    'cdn': cdn,
                    'pattern': f"/{ep_hash}_{suffix}.wav",
                    'auth_needed': False
                })
        
        return urls
    
    # ======================================================================
    # STEP 5: EPISODE CHECK KARO
    # ======================================================================
    
    def check_episode(self, show_id, ep_num, cdns=None):
        """
        Check if episode exists and return working URL
        """
        urls_to_try = self.generate_urls_for_episode(show_id, ep_num, cdns)
        
        for url_info in urls_to_try:
            url = url_info['url']
            auth_needed = url_info.get('auth_needed', False)
            
            try:
                # First try HEAD request (faster)
                r = self.session.head(url, timeout=self.request_timeout, allow_redirects=True)
                
                if r.status_code == 200:
                    size = r.headers.get('content-length', 0)
                    return {
                        'episode': ep_num,
                        'url': url,
                        'size': int(size) if size else 0,
                        'auth_needed': False,
                        'cdn': url_info['cdn'],
                        'status': 'available'
                    }
                elif r.status_code == 403 and not auth_needed:
                    # Try with referer header
                    headers = {'Referer': 'https://pocketfm.com/'}
                    r2 = self.session.head(url, headers=headers, timeout=self.request_timeout)
                    if r2.status_code == 200:
                        size = r2.headers.get('content-length', 0)
                        return {
                            'episode': ep_num,
                            'url': url,
                            'size': int(size) if size else 0,
                            'auth_needed': False,
                            'cdn': url_info['cdn'],
                            'status': 'available'
                        }
                elif r.status_code == 403 and auth_needed:
                    return {
                        'episode': ep_num,
                        'url': url,
                        'size': 0,
                        'auth_needed': True,
                        'cdn': url_info['cdn'],
                        'status': 'protected'
                    }
                elif r.status_code == 404:
                    continue
                    
            except Exception:
                continue
        
        return None
    
    # ======================================================================
    # STEP 6: EPISODE DOWNLOAD KARO
    # ======================================================================
    
    def download_episode(self, episode_info, show_name):
        """
        Download episode with progress bar
        """
        ep_num = episode_info['episode']
        url = episode_info['url']
        
        # Create show directory
        show_dir = os.path.join(self.output_dir, self.sanitize_filename(show_name))
        os.makedirs(show_dir, exist_ok=True)
        
        # Determine filename
        if '.wav' in url:
            ext = '.wav'
        elif '.mpd' in url:
            ext = '.mpd'
        else:
            ext = '.mp4'
        
        filename = os.path.join(show_dir, f"episode_{ep_num}{ext}")
        
        print(f"\n📥 Downloading Episode {ep_num}...")
        
        for attempt in range(self.retry_count):
            try:
                r = self.session.get(url, stream=True, timeout=self.download_timeout)
                
                if r.status_code == 200:
                    total = int(r.headers.get('content-length', 0))
                    
                    with open(filename, 'wb') as f:
                        downloaded = 0
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total:
                                    pct = (downloaded / total) * 100
                                    print(f"\r   Progress: {pct:.1f}% ({downloaded/1024/1024:.1f} MB)", end='')
                    
                    print(f"\n✅ Saved: {filename} ({total/1024/1024:.1f} MB)")
                    return True
                    
                elif r.status_code == 403 and attempt < self.retry_count - 1:
                    wait = 5 * (attempt + 1)
                    print(f"\n🔒 Rate limited. Waiting {wait} seconds...")
                    time.sleep(wait)
                else:
                    print(f"\n❌ HTTP {r.status_code}")
                    return False
                    
            except Exception as e:
                if attempt < self.retry_count - 1:
                    print(f"\n⚠️ Attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(3)
                else:
                    print(f"\n❌ Error: {e}")
                    return False
        
        return False
    
    def sanitize_filename(self, name):
        """Remove invalid characters from filename"""
        return re.sub(r'[^\w\-_\. ]', '_', name)
    
    # ======================================================================
    # STEP 7: COMPLETE SCAN FOR A SHOW
    # ======================================================================
    
    def scan_show(self, show_id, show_name=None, scan_range=None, auto_download=True):
        """
        Complete scan for any show
        """
        print("\n" + "=" * 80)
        print(f"🎯 SCANNING SHOW: {show_name or show_id}")
        print("=" * 80)
        
        # Step 1: Get show info
        show_info = self.get_show_info(show_id)
        if not show_info:
            print("❌ Failed to get show info")
            return []
        
        show_name = show_name or show_info['name']
        
        # Step 2: Find episode gaps
        gaps = self.find_episode_gaps(show_info)
        
        # Step 3: Discover CDNs
        cdns, patterns = self.discover_cdn_patterns(show_info)
        
        if not cdns:
            print("\n⚠️ No CDNs discovered, using known CDNs")
            cdns = self.known_cdns
        
        # Step 4: Determine episodes to scan
        episodes_to_scan = []
        
        if scan_range:
            # User specified range
            start, end = scan_range
            episodes_to_scan = list(range(start, end + 1))
        else:
            # Scan gaps + surrounding episodes
            if gaps:
                episodes_to_scan = gaps
                # Add some buffer episodes
                if gaps:
                    min_gap = min(gaps)
                    max_gap = max(gaps)
                    buffer_start = max(1, min_gap - 20)
                    buffer_end = max_gap + 20
                    for ep in range(buffer_start, buffer_end + 1):
                        if ep not in episodes_to_scan:
                            episodes_to_scan.append(ep)
                    episodes_to_scan.sort()
        
        if not episodes_to_scan:
            print("\n❌ No episodes to scan")
            return []
        
        print(f"\n🔍 Scanning {len(episodes_to_scan)} episodes...")
        
        # Step 5: Scan episodes
        found_episodes = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ep = {
                executor.submit(self.check_episode, show_id, ep, cdns): ep 
                for ep in episodes_to_scan[:100]  # Limit to first 100
            }
            
            completed = 0
            for future in as_completed(future_to_ep):
                completed += 1
                ep = future_to_ep[future]
                result = future.result()
                
                if result:
                    found_episodes.append(result)
                    status = "🔓" if not result['auth_needed'] else "🔒"
                    print(f"\n{status} Episode {result['episode']}: {result['cdn']}")
                
                if completed % 10 == 0:
                    print(f"\r   Progress: {completed}/{len(episodes_to_scan)}", end='')
        
        print(f"\n\n📊 Found {len(found_episodes)} pre-release episodes:")
        
        for ep in sorted(found_episodes, key=lambda x: x['episode']):
            lock = "🔓 PUBLIC" if not ep['auth_needed'] else "🔒 PROTECTED"
            print(f"   {lock} Episode {ep['episode']:4d}: {ep['cdn']}")
        
        # Step 6: Download if found
        if auto_download and found_episodes:
            print(f"\n📥 Downloading {len(found_episodes)} episodes...")
            
            for ep_info in sorted(found_episodes, key=lambda x: x['episode']):
                if not ep_info['auth_needed']:  # Only download public ones
                    self.download_episode(ep_info, show_name)
                    time.sleep(2)  # Be nice to server
                else:
                    print(f"\n🔒 Episode {ep_info['episode']} is protected - needs auth token")
        
        # Save results
        self.save_results(show_name, show_id, found_episodes)
        
        return found_episodes
    
    def save_results(self, show_name, show_id, found_episodes):
        """Save scan results to file"""
        results = {
            'show': {
                'name': show_name,
                'id': show_id,
                'scan_time': datetime.now().isoformat()
            },
            'found_episodes': found_episodes
        }
        
        filename = f"{self.output_dir}/{self.sanitize_filename(show_name)}_results.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📁 Results saved to {filename}")

# ======================================================================
# MAIN FUNCTION
# ======================================================================

def main():
    """Main function to run the scanner"""
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     🎯 POCKET FM UNIVERSAL PRE-RELEASE DOWNLOADER            ║
║     Kisi bhi show ke pre-release episodes download karein    ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    downloader = UniversalPreReleaseDownloader()
    
    # Popular shows to scan
    popular_shows = [
        {"id": "66e447439b52a78caccea30009ab3c98a39a8734", "name": "The Raichands"},
        {"id": "47251ceab13a93e9762f16122ed1b8f56951af6e", "name": "Mission Mangalsutra"},
        {"id": "5b2ee241211bb2783b67662120b748d6a67c079c", "name": "Insta Millionaire"},
    ]
    
    while True:
        print("\n" + "=" * 60)
        print("OPTIONS:")
        print("1. Scan a specific show by ID")
        print("2. Scan popular shows")
        print("3. Scan custom episode range")
        print("4. Exit")
        print("=" * 60)
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            show_id = input("Enter Pocket FM Show ID: ").strip()
            show_name = input("Enter Show Name (optional): ").strip() or None
            downloader.scan_show(show_id, show_name)
            
        elif choice == '2':
            for show in popular_shows:
                downloader.scan_show(show['id'], show['name'])
                time.sleep(5)  # Delay between shows
                
        elif choice == '3':
            show_id = input("Enter Show ID: ").strip()
            start = int(input("Start episode: "))
            end = int(input("End episode: "))
            downloader.scan_show(show_id, scan_range=(start, end))
            
        elif choice == '4':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
