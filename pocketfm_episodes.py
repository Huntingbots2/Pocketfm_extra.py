#!/usr/bin/env python3
"""
Ved Astra Pre-Release Scanner
Episodes 280-290 ke raw WAV files scan karo
"""

import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor

class VedAstraPreReleaseScanner:
    def __init__(self):
        self.show_id = "d568f2636525db484d846b2db5deb2235d73e1ff"
        self.show_name = "Ved Astra"
        
        # Working CDN from previous successes
        self.public_cdn = "http://dbj64m8271a9g.cloudfront.net"
        
        # Known working hashes (from other shows)
        self.known_hashes = [
            "9c1e2eeedf839e455d795e0f454684e74baf8dbd",  # 226 MB WAV
            "ceafa3da031452c8504c1f3526f12bda46b78708",  # 213 MB WAV
            "861570376f42d83d6dd5b9c67266af2fb3ec5642",  # 214 MB WAV
            "b959fe1ed3495cb698ebcc4dfb79e71f37db2d6c",  # MP3 pattern
        ]
        
        self.wav_suffixes = ["LyaBxWjwJS", "NhergD9Ywf", "sbtoAX4YGF"]
        self.mp3_suffix = "VU0asCVaGZ"
        
        os.makedirs("ved_astra_prerelease", exist_ok=True)
        
    def check_episode(self, ep_num):
        """Single episode check karo"""
        
        print(f"\n📡 Episode {ep_num}:")
        
        # Pehle MP3 check karo (fast, small file)
        for hash_val in self.known_hashes:
            mp3_url = f"{self.public_cdn}/{hash_val}_{self.mp3_suffix}.mp3"
            try:
                r = requests.head(mp3_url, timeout=2)
                if r.status_code == 200:
                    size_mb = int(r.headers.get('content-length', 0)) / 1024 / 1024
                    print(f"   📢 MP3 preview: {size_mb:.1f} MB")
                    print(f"      {mp3_url}")
                    
                    # Agar MP3 mila, to WAV bhi ho sakta hai
                    for wav_suffix in self.wav_suffixes:
                        wav_url = f"{self.public_cdn}/{hash_val}_{wav_suffix}.wav"
                        try:
                            r2 = requests.head(wav_url, timeout=2)
                            if r2.status_code == 200:
                                wav_size = int(r2.headers.get('content-length', 0)) / 1024 / 1024
                                if wav_size > 200:
                                    print(f"   ✅ RAW WAV FOUND!")
                                    print(f"      Size: {wav_size:.1f} MB")
                                    print(f"      URL: {wav_url}")
                                    return {
                                        'episode': ep_num,
                                        'mp3_url': mp3_url,
                                        'wav_url': wav_url,
                                        'wav_size': wav_size
                                    }
                        except:
                            pass
            except:
                pass
        
        # Agar MP3 nahi mila to directly WAV check karo
        for hash_val in self.known_hashes:
            for suffix in self.wav_suffixes:
                wav_url = f"{self.public_cdn}/{hash_val}_{suffix}.wav"
                try:
                    r = requests.head(wav_url, timeout=2)
                    if r.status_code == 200:
                        size_mb = int(r.headers.get('content-length', 0)) / 1024 / 1024
                        if size_mb > 200:
                            print(f"   ✅ RAW WAV FOUND!")
                            print(f"      Size: {size_mb:.1f} MB")
                            print(f"      URL: {wav_url}")
                            return {
                                'episode': ep_num,
                                'wav_url': wav_url,
                                'wav_size': size_mb
                            }
                except:
                    pass
        
        print("   ❌ No raw WAV found")
        return None
    
    def scan_range(self, start_ep=280, end_ep=290):
        """Episode range scan karo"""
        
        print("\n" + "=" * 70)
        print(f"🎯 SCANNING {self.show_name} EPISODES {start_ep}-{end_ep}")
        print("=" * 70)
        print(f"Total episodes to scan: {end_ep - start_ep + 1}")
        print("=" * 70)
        
        found = []
        
        for ep in range(start_ep, end_ep + 1):
            result = self.check_episode(ep)
            if result:
                found.append(result)
            time.sleep(0.5)  # Be polite to server
        
        return found
    
    def download_episode(self, episode_info):
        """Found episode download karo"""
        
        ep = episode_info['episode']
        wav_url = episode_info['wav_url']
        size_mb = episode_info['wav_size']
        
        filename = f"ved_astra_prerelease/episode_{ep}_RAW.wav"
        
        print(f"\n📥 Downloading Episode {ep} ({size_mb:.1f} MB)...")
        
        try:
            r = requests.get(wav_url, stream=True)
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
    scanner = VedAstraPreReleaseScanner()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     🎯 VED ASTRA PRE-RELEASE SCANNER                         ║
║     Episodes 280-290 (286 total published)                   ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    found = scanner.scan_range(280, 290)
    
    if found:
        print(f"\n📊 Found {len(found)} raw WAV episodes!")
        for ep in found:
            print(f"   Episode {ep['episode']}: {ep['wav_size']:.1f} MB")
        
        # Download?
        response = input("\n📥 Download all found episodes? (y/n): ").lower()
        if response == 'y':
            for ep_info in found:
                scanner.download_episode(ep_info)
                time.sleep(3)
    else:
        print("\n❌ No raw WAV episodes found in range 280-290")
        print("\n💡 Suggestions:")
        print("1. Try different episode range (e.g., 270-280, 290-300)")
        print("2. Check if show uses different hash pattern")
        print("3. Wait for official release (episodes may not be pre-loaded)")
