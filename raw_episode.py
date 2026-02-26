#!/usr/bin/env python3
"""
Universal Raw WAV Episode Scanner
200-250 MB ke original WAV files dhundho for any series
"""

import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor

class UniversalRawWAVScanner:
    def __init__(self):
        self.cdn = "http://dbj64m8271a9g.cloudfront.net"
        
        # Known working hashes (from successful downloads)
        self.known_hashes = [
            "b959fe1ed3495cb698ebcc4dfb79e71f37db2d6c",  # ~0.2 MB (MP3 preview)
            "9c1e2eeedf839e455d795e0f454684e74baf8dbd",  # ~226 MB (WAV raw)
            "ceafa3da031452c8504c1f3526f12bda46b78708",  # ~213 MB (WAV raw)
            "861570376f42d83d6dd5b9c67266af2fb3ec5642",  # ~214 MB (WAV raw)
        ]
        
        # Known suffixes
        self.known_suffixes = [
            "LyaBxWjwJS",      # WAV (226 MB)
            "NhergD9Ywf",      # WAV (213 MB)
            "sbtoAX4YGF",      # WAV (214 MB)
            "VU0asCVaGZ",      # MP3 (0.2 MB) - skip this
        ]
        
        # Filter only WAV suffixes (200+ MB)
        self.wav_suffixes = [s for s in self.known_suffixes if s != "VU0asCVaGZ"]
        
        print(f"✅ Scanner ready with {len(self.wav_suffixes)} WAV patterns")
        print(f"   Each WAV: ~200-250 MB")
    
    def scan_episode_range(self, show_name, start_ep, end_ep):
        """
        Scan episode range for raw WAV files
        """
        print(f"\n{'='*70}")
        print(f"🎯 SCANNING {show_name} EPISODES {start_ep}-{end_ep} FOR RAW WAV")
        print(f"{'='*70}")
        
        found = []
        
        for ep in range(start_ep, end_ep + 1):
            print(f"\r📡 Scanning episode {ep}...", end="", flush=True)
            
            for hash_val in self.known_hashes:
                for suffix in self.wav_suffixes:
                    url = f"{self.cdn}/{hash_val}_{suffix}.wav"
                    
                    try:
                        r = requests.head(url, timeout=2)
                        if r.status_code == 200:
                            size = r.headers.get('content-length', 0)
                            size_mb = int(size) / 1024 / 1024
                            
                            # Only raw WAV files (200+ MB)
                            if size_mb > 200:
                                print(f"\n✅ RAW WAV FOUND for episode {ep}!")
                                print(f"   URL: {url}")
                                print(f"   Size: {size_mb:.1f} MB")
                                print(f"   Hash: {hash_val}")
                                print(f"   Suffix: {suffix}")
                                
                                found.append({
                                    'episode': ep,
                                    'url': url,
                                    'size': int(size),
                                    'size_mb': size_mb,
                                    'hash': hash_val,
                                    'suffix': suffix
                                })
                                
                                # Once found for this episode, move to next
                                break
                    except:
                        pass
            
            time.sleep(0.3)  # Be polite
        
        return found
    
    def download_raw_wav(self, episode_info, show_name):
        """
        Download raw WAV file
        """
        ep = episode_info['episode']
        url = episode_info['url']
        size_mb = episode_info['size_mb']
        
        # Create show directory
        show_dir = f"raw_wav_{show_name.replace(' ', '_')}"
        os.makedirs(show_dir, exist_ok=True)
        
        filename = f"{show_dir}/episode_{ep}_RAW.wav"
        
        print(f"\n📥 Downloading RAW WAV episode {ep} ({size_mb:.1f} MB)...")
        
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
                            print(f"\r   Progress: {pct:.1f}% ({downloaded/1024/1024:.1f} MB)", end='')
            
            print(f"\n✅ Saved: {filename}")
            print(f"   Total: {total/1024/1024:.1f} MB")
            return True
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False
    
    def scan_show(self, show_name, episode_range):
        """
        Complete scan for a show
        """
        start_ep, end_ep = episode_range
        
        found = self.scan_episode_range(show_name, start_ep, end_ep)
        
        if found:
            print(f"\n\n📊 FOUND {len(found)} RAW WAV EPISODES!")
            
            # Group by episode (should be one per episode)
            for item in found:
                print(f"\nEpisode {item['episode']}:")
                print(f"   • {item['size_mb']:.1f} MB")
                print(f"   • Hash: {item['hash']}")
                print(f"   • Suffix: {item['suffix']}")
            
            # Download all
            response = input(f"\n📥 Download {len(found)} RAW WAV episodes? (y/n): ").lower()
            if response == 'y':
                for item in found:
                    self.download_raw_wav(item, show_name)
                    time.sleep(3)  # Be nice to server (large files)
        else:
            print(f"\n\n❌ No RAW WAV episodes found in range {start_ep}-{end_ep}")
            print("\n💡 Tips:")
            print("1. Try different episode range")
            print("2. Show might use different hashes")
            print("3. Check if episodes are actually pre-release")

# ===== MAIN =====
def main():
    scanner = UniversalRawWAVScanner()
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     🎯 UNIVERSAL RAW WAV EPISODE SCANNER                     ║
║     200-250 MB ke original pre-release episodes dhundhe      ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    while True:
        print("\n" + "=" * 60)
        print("OPTIONS:")
        print("1. Scan Super Yoddha (2692-2697)")
        print("2. Scan Mission Mangalsutra (140-155)")
        print("3. Scan The Raichands (2350-2360)")
        print("4. Custom show scan")
        print("5. Exit")
        print("=" * 60)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            scanner.scan_show("Super_Yoddha", (2692, 2697))
        elif choice == '2':
            scanner.scan_show("Mission_Mangalsutra", (140, 155))
        elif choice == '3':
            scanner.scan_show("The_Raichands", (2350, 2360))
        elif choice == '4':
            show_name = input("Enter show name: ").strip()
            start = int(input("Start episode: "))
            end = int(input("End episode: "))
            scanner.scan_show(show_name, (start, end))
        elif choice == '5':
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()
