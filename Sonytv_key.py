# sony_hd_keys.py
import requests
import re
import base64

url = "https://sundirectgo-live.pc.cdn.bitgravity.com/hd874/dth.mpd"
headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.sundirectgo.in/",
    "Origin": "https://www.sundirectgo.in"
}

r = requests.get(url, headers=headers)
content = r.text

# Extract KID
kid_match = re.search(r'default_KID=[\"\']([^\"\']+)[\"\']', content, re.IGNORECASE)
if kid_match:
    kid = kid_match.group(1).replace('-', '')
    print(f"✅ KID: {kid}")
    
    # Generate PSSH
    system_id = 'edef8ba979d64acea3c827dcd51d21ed'
    kid_bytes = bytes.fromhex(kid)
    pssh_bytes = bytes([0x00, 0x00, 0x00, 0x20 + len(kid_bytes)]) + b'pssh' + \
                bytes([0x00, 0x00, 0x00, 0x00]) + bytes.fromhex(system_id) + \
                bytes([0x00, 0x00, 0x00, 0x01]) + kid_bytes
    pssh_b64 = base64.b64encode(pssh_bytes).decode('utf-8')
    print(f"✅ PSSH: {pssh_b64}")

# Extract direct PSSH if available
pssh_match = re.search(r'<cenc:pssh[^>]*>(.*?)</cenc:pssh>', content, re.DOTALL)
if pssh_match:
    print(f"✅ Direct PSSH: {pssh_match.group(1).strip()}")
