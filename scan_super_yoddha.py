#!/usr/bin/env python3
"""
Super Yoddha Pre-Release Scanner
Episodes 2690-2700 (current pre-release range)
Based on working patterns from 2392-2393
"""

import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor

class SuperYoddhaPreReleaseScanner:
    def __init__(self):
        self.show_name = "Super Yoddha"
        self.cdn = "http://dbj64m8271a9g.cloudfront.net"
        
        # Working hashes from successful downloads
        self.known_hashes = [
            "9c1e2eeedf839e455d795e0f454684e74baf8dbd",  # Episode 2392
            "ceafa3da031452c8504c1f3526f12bda46b78708",  # Episode 2393
            "861570376f42d83d6dd5b9c67266af2fb3ec5642",  # From previous
        ]
        
        # Working suffixes from successful downloads
        self.known_suffixes = [
            "LyaBxWjwJS",      # Episode 2392
            "NhergD9Ywf",      # Episode 2393
            "sbtoAX4YGF",      # From previous
        ]
        
        # Episode range to scan
        self.start_ep = 2690
        self.end_ep = 2700
        
        os.makedirs("super_yoddha_prerelease", exist_ok=True)
        
        print(f"✅ Scanner initialized with {len(self.known_hashes)} patterns")
        print(f"📊 Scanning episodes {self.start_ep}-{self.end_ep}")
    
    def check_episode(self, ep_num):
        """
        Single episode check karo
        """
        print(f"\n📡 Episode {ep_num}:", end="", flush=True)
        
        for hash_val in self.known_hashes:
            for suffix in self.known_suffixes:
                url = f"{self.cdn}/{hash_val}_{suffix}.wav"
                
                # Try with episode number substitution in hash
                # (if hash contains 2392 or 2393)
                if '2392' in hash_val:
                    modified_hash = hash_val.replace('2392', str(ep_num))
                    url2 = f"{self.cdn}/{modified_hash}_{suffix}.wav"
                elif '2393' in hash_val:
                    modified_hash = hash_val.replace('2393', str(ep_num))
                    url2 = f"{self.cdn}/{modified_hash}_{suffix}.wav"
                else:
                    url2 = url
                
                # Try both URLs
                for test_url in [url, url2]:
                    try:
                        r = requests.head(test_url, timeout=2)
                        if r.status_code == 200:
                            size_mb = int(r.headers.get('content-length', 0)) / 1024 / 1024
                            if size_mb > 200:  # Raw WAV file
                                print(f"\n   ✅ RAW WAV FOUND!")
                                print(f"      URL: {test_url}")
                                print(f"      Size: {size_mb:.1f} MB")
                                print(f"      Hash: {hash_val}")
                                print(f"      Suffix: {suffix}")
                                return {
                                    'episode': ep_num,
                                    'url': test_url,
                                    'size_mb': size_mb,
                                    'hash': hash_val,
                                    'suffix': suffix
                                }
                    except:
                        pass
        
        print("   ❌ No raw WAV found")
        return None
    
    def scan_range(self):
        """
        Episode range scan karo
        """
        print("\n" + "=" * 70)
        print(f"🎯 SCANNING {self.show_name} EPISODES {self.start_ep}-{self.end_ep}")
        print("=" * 70)
        print(f"Total episodes to scan: {self.end_ep - self.start_ep + 1}")
        print("=" * 70)
        
        found = []
        
        for ep in range(self.start_ep, self.end_ep + 1):
            result = self.check_episode(ep)
            if result:
                found.append(result)
            time.sleep(0.5)  # Be polite to server
        
        return found
    
    def download_episode(self, episode_info):
        """
        Found episode download karo
        """
        ep = episode_info['episode']
        url = episode_info['url']
        size_mb = episode_info['size_mb']
        
        filename = f"super_yoddha_prerelease/episode_{ep}_RAW.wav"
        
        print(f"\n📥 Downloading Episode {ep} ({size_mb:.1f} MB)...")
        
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
            
            print(f"\n✅ Saved: {filename}")
            return True
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False

if __name__ == "__main__":
    scanner = SuperYoddhaPreReleaseScanner()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     🎯 SUPER YODDHA PRE-RELEASE SCANNER                      ║
║     Episodes 2690-2700 (current pre-release range)           ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    found = scanner.scan_range()
    
    if found:
        print(f"\n📊 Found {len(found)} raw WAV episodes!")
        for ep in sorted(found, key=lambda x: x['episode']):
            print(f"   Episode {ep['episode']}: {ep['size_mb']:.1f} MB")
        
        # Download all?
        response = input("\n📥 Download all found episodes? (y/n): ").lower()
        if response == 'y':
            for ep_info in sorted(found, key=lambda x: x['episode']):
                scanner.download_episode(ep_info)
                time.sleep(3)
    else:
        print("\n❌ No raw WAV episodes found in range 2690-2700")
        print("\n💡 Suggestions:")
        print("1. Try different range (e.g., 2680-2690, 2700-2710)")
        print("2. Check if episodes use different hash pattern")
        print("3. Wait for official release (episodes may not be pre-loaded)")
