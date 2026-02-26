#!/usr/bin/env python3
"""
Super Yoddha Hash Discovery Tool
MP3 se hash pattern nikaalo aur raw WAV dhundho
"""

import requests
import re

class SuperYoddhaHashDiscovery:
    def __init__(self):
        self.cdn = "http://dbj64m8271a9g.cloudfront.net"
        
        # Episode numbers from screenshot
        self.episodes = [2692, 2693, 2694, 2695, 2696, 2697]
        
        # Known suffixes (same pattern)
        self.suffixes = ["LyaBxWjwJS", "NhergD9Ywf", "sbtoAX4YGF"]
        
        # Store discovered hashes
        self.discovered_hashes = set()
    
    def discover_from_mp3(self):
        """
        Step 1: MP3 files se hashes discover karo
        """
        print("\n" + "=" * 70)
        print("🔍 STEP 1: DISCOVERING HASHES FROM MP3s")
        print("=" * 70)
        
        # Try common hash patterns with MP3
        test_hashes = [
            "b959fe1ed3495cb698ebcc4dfb79e71f37db2d6c",  # Known MP3 hash
        ]
        
        for ep in self.episodes:
            print(f"\n📡 Episode {ep}:")
            
            for test_hash in test_hashes:
                # Try MP3 with episode number in hash
                modified_hash = test_hash.replace('151', str(ep)[-3:])  # Last 3 digits
                url = f"{self.cdn}/{modified_hash}_VU0asCVaGZ.mp3"
                
                try:
                    r = requests.head(url, timeout=2)
                    if r.status_code == 200:
                        size = int(r.headers.get('content-length', 0)) / 1024 / 1024
                        if 16 <= size <= 19:  # MP3 size range
                            print(f"   ✅ Found MP3!")
                            print(f"   URL: {url}")
                            print(f"   Size: {size:.1f} MB")
                            print(f"   Hash: {modified_hash}")
                            self.discovered_hashes.add(modified_hash)
                except:
                    pass
    
    def try_hash_variations(self, base_hash):
        """
        Step 2: Hash variations try karo
        """
        print("\n" + "=" * 70)
        print("🔍 STEP 2: TRYING HASH VARIATIONS")
        print("=" * 70)
        
        variations = []
        
        # Convert hash to number and try variations
        try:
            hash_int = int(base_hash[:8], 16)
            for offset in [-2, -1, 0, 1, 2]:
                new_hash_int = hash_int + offset
                new_hash = hex(new_hash_int)[2:].zfill(8) + base_hash[8:]
                variations.append(new_hash)
        except:
            pass
        
        # Add some common variations
        variations.extend([
            base_hash,
            base_hash[:-4] + "abcd",
            base_hash[:-4] + "1234",
        ])
        
        return variations
    
    def scan_raw_wav(self, hash_val):
        """
        Step 3: Hash ke saath raw WAV scan karo
        """
        print(f"\n📡 Testing hash: {hash_val[:20]}...")
        
        for ep in self.episodes:
            for suffix in self.suffixes:
                url = f"{self.cdn}/{hash_val}_{suffix}.wav"
                
                try:
                    r = requests.head(url, timeout=2)
                    if r.status_code == 200:
                        size_mb = int(r.headers.get('content-length', 0)) / 1024 / 1024
                        if size_mb > 200:  # Raw WAV
                            print(f"\n✅✅ RAW WAV FOUND!")
                            print(f"   Episode: {ep}")
                            print(f"   URL: {url}")
                            print(f"   Size: {size_mb:.1f} MB")
                            print(f"   Hash: {hash_val}")
                            print(f"   Suffix: {suffix}")
                            return True
                except:
                    pass
        return False
    
    def run(self):
        """
        Main discovery function
        """
        print("""
╔═══════════════════════════════════════════════════════════════╗
║     🎯 SUPER YODDHA HASH DISCOVERY TOOL                      ║
║     MP3 se hash nikaalo aur raw WAV dhundho                  ║
╚═══════════════════════════════════════════════════════════════╝
        """)
        
        # Step 1: Discover hashes from MP3
        self.discover_from_mp3()
        
        if not self.discovered_hashes:
            print("\n❌ No MP3 hashes found. Using known hashes as base.")
            self.discovered_hashes = set([
                "9c1e2eeedf839e455d795e0f454684e74baf8dbd",
                "ceafa3da031452c8504c1f3526f12bda46b78708",
                "861570376f42d83d6dd5b9c67266af2fb3ec5642",
            ])
        
        # Step 2: Try variations and scan for raw WAV
        print(f"\n📊 Found {len(self.discovered_hashes)} base hashes to test")
        
        all_hashes_to_test = set()
        for base_hash in self.discovered_hashes:
            variations = self.try_hash_variations(base_hash)
            all_hashes_to_test.update(variations)
        
        print(f"\n🔍 Testing {len(all_hashes_to_test)} hash variations...")
        
        found = False
        for hash_val in all_hashes_to_test:
            if self.scan_raw_wav(hash_val):
                found = True
        
        if not found:
            print("\n❌ No raw WAV episodes found")
            print("\n💡 Suggestions:")
            print("1. Try different episode range")
            print("2. Check if episodes are actually available")
            print("3. Show might use completely different hash pattern")

if __name__ == "__main__":
    discover = SuperYoddhaHashDiscovery()
    discover.run()
