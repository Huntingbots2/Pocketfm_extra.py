#!/usr/bin/env python3
"""
Super Yoddha Pre-Release Downloader
Episodes 2695-2697 (jo API mein available hain)
"""

import requests
import os
import time

class SuperYoddhaDownloader:
    def __init__(self):
        self.show_id = "f629196ee7df34287ef2672e91fda9f939e9d02d"
        self.show_name = "Super Yoddha"
        self.cdn = "http://dbj64m8271a9g.cloudfront.net"
        
        # Known working patterns
        self.known_hashes = [
            "b959fe1ed3495cb698ebcc4dfb79e71f37db2d6c",
            "9c1e2eeedf839e455d795e0f454684e74baf8dbd",
            "ceafa3da031452c8504c1f3526f12bda46b78708",
            "861570376f42d83d6dd5b9c67266af2fb3ec5642",
        ]
        
        self.known_suffixes = [
            "VU0asCVaGZ",      # MP3
            "LyaBxWjwJS",      # WAV
            "NhergD9Ywf",      # WAV
            "sbtoAX4YGF",      # WAV
        ]
        
        os.makedirs("super_yoddha", exist_ok=True)
    
    def scan_episodes(self, start_ep=2695, end_ep=2697):
        """Scan for pre-release episodes"""
        
        print(f"\n{'='*60}")
        print(f"🎯 SCANNING SUPER YODDHA EPISODES {start_ep}-{end_ep}")
        print(f"{'='*60}")
        
        found = []
        
        for ep in range(start_ep, end_ep + 1):
            print(f"\n📡 Checking episode {ep}...")
            
            for hash_val in self.known_hashes:
                for suffix in self.known_suffixes:
                    # Try MP3
                    url = f"{self.cdn}/{hash_val}_{suffix}.mp3"
                    try:
                        r = requests.head(url, timeout=2)
                        if r.status_code == 200:
                            size = r.headers.get('content-length', 0)
                            print(f"   ✅ MP3: {size/1024/1024:.1f} MB")
                            found.append({
                                'ep': ep,
                                'url': url,
                                'size': int(size),
                                'type': 'mp3'
                            })
                    except:
                        pass
                    
                    # Try WAV
                    url = f"{self.cdn}/{hash_val}_{suffix}.wav"
                    try:
                        r = requests.head(url, timeout=2)
                        if r.status_code == 200:
                            size = r.headers.get('content-length', 0)
                            print(f"   ✅ WAV: {size/1024/1024:.1f} MB")
                            found.append({
                                'ep': ep,
                                'url': url,
                                'size': int(size),
                                'type': 'wav'
                            })
                    except:
                        pass
            
            time.sleep(1)
        
        return found
    
    def download_episode(self, ep_info):
        """Download episode"""
        ep = ep_info['ep']
        url = ep_info['url']
        ext = ep_info['type']
        
        filename = f"super_yoddha/episode_{ep}.{ext}"
        
        print(f"\n📥 Downloading episode {ep} ({ext.upper()})...")
        
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
            return True
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False

if __name__ == "__main__":
    downloader = SuperYoddhaDownloader()
    
    # Scan episodes 2695-2697
    found = downloader.scan_episodes(2695, 2697)
    
    if found:
        print(f"\n📊 Found {len(found)} files!")
        
        # Group by episode
        episodes = {}
        for f in found:
            if f['ep'] not in episodes:
                episodes[f['ep']] = []
            episodes[f['ep']].append(f)
        
        for ep, files in sorted(episodes.items()):
            print(f"\nEpisode {ep}:")
            for f in files:
                print(f"   • {f['type'].upper()}: {f['size']/1024/1024:.1f} MB")
        
        # Download largest format for each episode
        for ep, files in sorted(episodes.items()):
            largest = max(files, key=lambda x: x['size'])
            downloader.download_episode(largest)
            time.sleep(2)
    else:
        print("\n❌ No pre-release episodes found")
        print("Episodes 2695-2697 may not be available yet")
