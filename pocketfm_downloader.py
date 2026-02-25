#!/usr/bin/env python3
"""
Pocket FM Pre-Release Downloader
Updated for episodes 2697-2720
"""

import requests
import concurrent.futures
import os
from itertools import product

class PreReleaseHunter:
    def __init__(self):
        self.base_cdn = "http://dbj64m8271a9g.cloudfront.net"
        self.session = requests.Session()
        os.makedirs("prerelease_hunter", exist_ok=True)
        
        # 🎯 Pattern 1: Known working hashes
        self.known_hashes = [
            "9c1e2eeedf839e455d795e0f454684e74baf8dbd",
            "ceafa3da031452c8504c1f3526f12bda46b78708"
        ]
        
        # 🎯 Pattern 2: Known working suffixes
        self.known_suffixes = [
            "LyaBxWjwJS",
            "NhergD9Ywf"
        ]
        
        # 🎯 Episode ranges to scan - UPDATED FOR 2697-2720
        self.episode_ranges = [
            (2697, 2700),   # Start range
            (2701, 2710),   # Middle range
            (2711, 2720),   # End range
        ]
        
    def generate_urls(self, ep_num):
        """Generate possible URLs for an episode"""
        urls = []
        
        # Method 1: Same hash, different episode number
        for hash_val, suffix in product(self.known_hashes, self.known_suffixes):
            # Replace episode number in URL
            url = f"{self.base_cdn}/{hash_val}_{suffix}.wav"
            # Try to substitute episode number (pattern from your URLs)
            if '2392' in url:
                url = url.replace('2392', str(ep_num))
            if '2393' in url:
                url = url.replace('2393', str(ep_num))
            urls.append(url)
        
        # Method 2: Sequential hash guessing
        for i, base_hash in enumerate(self.known_hashes):
            try:
                # Convert first 8 chars to number
                hash_int = int(base_hash[:8], 16)
                for offset in [-2, -1, 0, 1, 2]:
                    new_hash_int = hash_int + offset
                    new_hash = hex(new_hash_int)[2:].zfill(8) + base_hash[8:]
                    url = f"{self.base_cdn}/{new_hash}_{self.known_suffixes[i]}.wav"
                    urls.append(url)
            except:
                pass
        
        return list(set(urls))  # Remove duplicates
    
    def check_episode(self, ep_num):
        """Check if episode exists"""
        
        urls = self.generate_urls(ep_num)
        
        for url in urls:
            try:
                # HEAD request is faster
                r = self.session.head(url, timeout=2, allow_redirects=True)
                if r.status_code == 200:
                    size = r.headers.get('content-length', 0)
                    print(f"\n✅ FOUND Episode {ep_num}:")
                    print(f"   URL: {url}")
                    print(f"   Size: {int(size)/1024/1024:.1f} MB")
                    return (ep_num, url, int(size))
                elif r.status_code == 403:
                    # Try with headers
                    headers = {'Referer': 'https://pocketfm.com/'}
                    r2 = self.session.head(url, headers=headers, timeout=2)
                    if r2.status_code == 200:
                        size = r2.headers.get('content-length', 0)
                        print(f"\n✅ FOUND (with headers) Episode {ep_num}:")
                        print(f"   URL: {url}")
                        return (ep_num, url, int(size))
            except:
                continue
        
        return None
    
    def scan_range(self, start, end):
        """Scan episode range"""
        print(f"\n🔍 Scanning episodes {start}-{end}...")
        
        found = []
        total = end - start + 1
        
        for i, ep in enumerate(range(start, end+1), 1):
            result = self.check_episode(ep)
            if result:
                found.append(result)
            
            # Progress indicator
            if i % 10 == 0:
                print(f"   Progress: {i}/{total} ({i/total*100:.1f}%)", end='\r')
        
        return found
    
    def download_episode(self, ep_num, url):
        """Download found episode"""
        filename = f"prerelease_hunter/episode_{ep_num}.wav"
        
        print(f"\n📥 Downloading episode {ep_num}...")
        
        try:
            r = self.session.get(url, stream=True)
            total = int(r.headers.get('content-length', 0))
            
            with open(filename, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = (downloaded/total)*100
                            print(f"\r   Progress: {pct:.1f}%", end='')
            
            print(f"\n✅ Saved: {filename} ({total/1024/1024:.1f} MB)")
            return True
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False
    
    def hunt(self):
        """Main hunting function"""
        
        print("=" * 80)
        print("🔍 PRE-RELEASE EPISODE HUNTER")
        print("=" * 80)
        print(f"CDN: {self.base_cdn}")
        print(f"Target Episodes: 2697 to 2720")
        print(f"Patterns: {len(self.known_hashes)} hashes × {len(self.known_suffixes)} suffixes")
        print("=" * 80)
        
        all_found = []
        
        for start, end in self.episode_ranges:
            found = self.scan_range(start, end)
            all_found.extend(found)
        
        print("\n\n" + "=" * 80)
        print(f"📊 TOTAL FOUND: {len(all_found)} EPISODES")
        print("=" * 80)
        
        for ep_num, url, size in sorted(all_found):
            print(f"\n🎵 Episode {ep_num}")
            print(f"   URL: {url}")
            print(f"   Size: {size/1024/1024:.1f} MB")
            
            # Auto-download
            self.download_episode(ep_num, url)
        
        # Save results
        with open('found_prerelease_2697-2720.txt', 'w') as f:
            for ep_num, url, size in all_found:
                f.write(f"Episode {ep_num}: {url}\n")
        
        print(f"\n📁 Results saved to found_prerelease_2697-2720.txt")
        return all_found

if __name__ == "__main__":
    hunter = PreReleaseHunter()
    hunter.hunt()
