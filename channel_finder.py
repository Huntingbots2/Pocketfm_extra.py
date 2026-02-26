# channel_finder.py
import requests
import re
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_channel(url, hd_number):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.sundirectgo.in/",
        "Origin": "https://www.sundirectgo.in"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code != 200:
            return None
            
        content = r.text
        
        # Extract KID
        kid_match = re.search(r'default_KID=[\"\']([^\"\']+)[\"\']', content, re.IGNORECASE)
        kid = kid_match.group(1) if kid_match else "Unknown"
        
        # Extract audio languages
        audio_langs = re.findall(r'lang="([^"]+)"', content)
        audio_langs = list(set(audio_langs)) if audio_langs else ["Unknown"]
        
        # Check for channel name in MPD
        channel_name = "Unknown"
        if "sony" in content.lower():
            channel_name = "Sony"
        elif "dangal" in content.lower():
            channel_name = "Dangal"
        elif "zeetv" in content.lower() or "zee" in content.lower():
            channel_name = "Zee TV"
        elif "star" in content.lower():
            channel_name = "Star"
        elif "colors" in content.lower():
            channel_name = "Colors"
            
        return {
            "hd": hd_number,
            "url": url,
            "kid": kid,
            "languages": audio_langs,
            "channel": channel_name,
            "content_length": len(content)
        }
    except:
        return None

# Read working URLs
with open('working_urls.txt', 'r') as f:
    urls = [line.strip() for line in f if line.strip()]

results = []
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = []
    for url in urls:
        hd = re.search(r'hd(\d+)', url).group(1)
        futures.append(executor.submit(check_channel, url, hd))
    
    for future in as_completed(futures):
        result = future.result()
        if result:
            results.append(result)
            print(f"HD{result['hd']}: {result['channel']} - KID: {result['kid'][:20]}... - Lang: {result['languages']}")

# Save results
import json
with open('channel_mapping.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n✅ Results saved to channel_mapping.json")
