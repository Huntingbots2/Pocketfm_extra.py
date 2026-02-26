#!/usr/bin/env python3
"""
Scan Super Yoddha for pre-release episodes 2697-2710
"""

import requests
import time

# Configuration
SHOW_ID = "f629196ee7df34287ef2672e91fda9f939e9d02d"
SHOW_NAME = "Super Yoddha"
CDN = "http://dbj64m8271a9g.cloudfront.net"

# Known working patterns from previous successes
HASHES = [
    "b959fe1ed3495cb698ebcc4dfb79e71f37db2d6c",
    "9c1e2eeedf839e455d795e0f454684e74baf8dbd",
    "ceafa3da031452c8504c1f3526f12bda46b78708",
    "861570376f42d83d6dd5b9c67266af2fb3ec5642",
]

SUFFIXES = [
    "VU0asCVaGZ",  # MP3 pattern
    "LyaBxWjwJS",  # WAV pattern 1
    "NhergD9Ywf",  # WAV pattern 2
    "sbtoAX4YGF",  # WAV pattern 3
]

print("=" * 70)
print(f"🎯 SCANNING {SHOW_NAME} - EPISODES 2697-2710")
print("=" * 70)

found_episodes = []

for ep in range(2697, 2711):
    print(f"\r📡 Scanning episode {ep}...", end="", flush=True)
    
    for hash_val in HASHES:
        for suffix in SUFFIXES:
            # Try MP3
            url = f"{CDN}/{hash_val}_{suffix}.mp3"
            try:
                r = requests.head(url, timeout=1)
                if r.status_code == 200:
                    size = r.headers.get('content-length', 0)
                    print(f"\n✅ Episode {ep} FOUND as MP3!")
                    print(f"   URL: {url}")
                    print(f"   Size: {int(size)/1024/1024:.1f} MB")
                    found_episodes.append({'ep': ep, 'url': url, 'type': 'mp3'})
            except:
                pass
            
            # Try WAV
            url = f"{CDN}/{hash_val}_{suffix}.wav"
            try:
                r = requests.head(url, timeout=1)
                if r.status_code == 200:
                    size = r.headers.get('content-length', 0)
                    print(f"\n✅ Episode {ep} FOUND as WAV!")
                    print(f"   URL: {url}")
                    print(f"   Size: {int(size)/1024/1024:.1f} MB")
                    found_episodes.append({'ep': ep, 'url': url, 'type': 'wav'})
            except:
                pass
    
    time.sleep(0.2)  # Small delay to be polite

print(f"\n\n{'='*70}")
print(f"📊 SCAN COMPLETE - Found {len(found_episodes)} pre-release files")
print('='*70)

for ep in found_episodes:
    print(f"Episode {ep['ep']}: {ep['type'].upper()} - {ep['url']}")
