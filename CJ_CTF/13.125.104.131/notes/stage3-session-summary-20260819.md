# Stage 3 (13.125.104.131:30083) 세션 정리 — 2026-08-19/20

## 1. 세션 개요

**대상**: Roundcube Webmail (port 30083, Werkzeug WAF gateway 프론트엔드)  
**기간**: 2026-08-19 16:20 ~ 2026-08-20 00:00+  
**방식**: CVE-2025-49113 (PHP 객체 역직렬화 RCE) via fearsoff_exploit.php  
**상태**: **root 권한 획득 완료, Stage 4 AWS 자격증명 탐색 중 (보류)**

---

## 2. 주요 성과

### ✓ 확정 항목

| 항목 | 증적 | 상태 |
|---|---|---|
| **root 권한 획득** | E17c (타이밍 사이드채널: 3.58s) | [자체 확인] |
| **Flag 파일 위치** | E18-E25 (프로빙 완료) | /usr/share maxdepth 2, *FLAG* 패턴 |
| Flag 내용 | E26-E31 (추출+base64 인코딩) | /tmp/flag_b64_20260819.txt 저장 |
| /root/.profile 존재 | E32 (타이밍) | [자체 확인] |
| AWS 환경변수 | E33 (printenv \| grep AWS) | 존재 확인, 상세 형식 미정 |

### ✗ 미완료 항목

- **Flag 실제 내용**: base64로 /tmp에 저장되었으나, 블라인드 RCE로 stdout 회수 불가
- **AWS 자격증명**: 환경변수는 존재하나 AWS_ACCESS_KEY_ID/SECRET 미설정 → 형식/위치 불명
- **Stage 4 엔드포인트**: AWS KEY 미확보로 차단

---

## 3. 기술 세부사항

### 3.1 root 권한 확인 (E17c)

```bash
sudo -n find /etc/passwd -exec sh -c '
  u=$(id -u)
  if [ "$u" -eq 0 ]; then
    sleep 3
  elif [ "$u" -eq 33 ]; then
    sleep 6
  elif [ "$u" -lt 1000 ]; then
    sleep 9
  else
    sleep 12
  fi
' \;
```

**결과**: 3.580초 (uid==0 구간 매칭) → root 확정

### 3.2 Flag 경로 탐색 프로세스

```
E20: /usr/share 포함 확인 (3.528s)
  ↓
E24: /usr/share/share 하위 확인 (3.531s)
  ↓
E25: maxdepth 1 제외, depth 2+ 확인 (13.3s = else)
  ↓
E29: maxdepth 2 내 *FLAG* 매칭 (11.6s = 5번 분기)
```

**최종**: `/usr/share/*/flag*` 형태, 파일명에 FLAG 포함

### 3.3 AWS 환경변수 탐지

```bash
# E33: 환경변수 존재 타이밍
if [ -n "${AWS_ACCESS_KEY_ID}" ]; then sleep 3;
elif [ -n "${AWS_SECRET_ACCESS_KEY}" ]; then sleep 5;
elif [ -n "${AWS_SESSION_TOKEN}" ]; then sleep 7;
elif printenv | grep -q AWS; then sleep 9;
else sleep 11; fi
```

**결과**: 9.419초 (printenv | grep AWS 매칭) → AWS 관련 환경변수 존재 확인

---

## 4. 블라인드 RCE의 한계

현재 사용 중인 **fearsoff_exploit.php**는:
- ✓ 임의의 쉘 명령 실행 가능 (root)
- ✓ 파일 읽기/쓰기 가능
- ✗ **명령 stdout을 HTTP 응답으로 반환하지 않음** (블라인드)

**결과 회수 방법들**:
1. 타이밍 사이드채널 (진행 중) — 느림, 오류율 있음
2. 파일 저장 후 HTTP GET 재접근 — webroot 경로 불명
3. PHP eval 페이로드 — 현재 가젯 체인 고정, 불가

---

## 5. 현재 저장 상태

### 서버 측 (/tmp, root-only accessible)

```
/tmp/flag_b64_20260819.txt       — flag 내용 (base64)
/tmp/flag_stat.txt               — flag 파일 stat 정보
/tmp/profile_b64.txt             — /root/.profile 처음 1000 바이트 (base64)
/tmp/profile_full_b64.txt        — /root/.profile 전체 (base64)
/tmp/profile_grep.txt            — profile grep 결과 (빈 파일 = aws/STAGE 미포함)
/tmp/aws_env.txt                 — env | grep AWS 결과
/tmp/aws_env_b64.txt             — AWS env (base64)
/tmp/flag_paths.txt              — find /usr/share *FLAG* 결과
```

### 로컬 증적 저장 (C:\HTB\13.125.104.131\)

```
logs/E17c_sudo_find_uid_classify_*.log
logs/E18~E25_flag_*_probe*.log
logs/E26_flag_exfil_write_*.log
logs/E27-E31_flag_*.log
logs/E32_profile_timing.log
logs/E33_aws_env_timing.log
logs/E34_aws_env_timing.log
notes/evidence-index.md (E01-E34)
notes/stage3-session-summary-20260819.md (본 파일)
```

---

## 6. 다음 단계 (재개 시)

### 필수 확인사항

1. **Flag 내용 복호화**
   - 서버의 `/tmp/flag_b64_*.txt` 수동 복호화 필요
   - 또는 PHP eval 페이로드 재작성 (현재 가젯 체인 우회)

2. **AWS 자격증명 특정**
   - `/tmp/aws_env.txt` 내용 확인
   - KEY/SECRET 실제 형식 파악
   - Stage 4 AWS 계정 진입 준비

3. **Webroot 경로 확인**
   - Roundcube 실제 document root 찾기
   - `/tmp` HTTP 접근 가능 여부 재확인
   - 파일 복사 → HTTP GET 접근 방식 검토

### 가능한 우회 방안

- **PHP eval 대체**: `echo "..." | base64 -d | php -r "echo system($_GET['x']);"`
- **직렬화 가젯 수정**: PHPGGC로 다른 가젯 체인 생성
- **파일 쓰기 활용**: `/var/www/html` 등 webroot에 PHP 웹셸 배치

---

## 7. 보안 노트

- **가용성 사건**: 2026-08-19 일부 시각에 Stage 3 서버 무응답 (Flask dev 서버 단일 스레드 특성, 프록시 경로 blocking 호출로 워커 점유 추정)
- **자격증명 보안**: /root/.profile, AWS 환경변수 모두 root로만 접근 가능 → 권한상승 필수 (단, 이미 달성)
- **감지 흔적**: sudo 명령 다수(E17c~E34), find 재귀 탐색, grep 패턴 매칭 등 로그에 기록될 가능성

---

## 8. 타임라인

| 시간 | 항목 | 상태 |
|---|---|---|
| 16:20-16:27 | E17c root 권한 획득 | ✓ |
| 16:27-16:37 | E18-E25 flag 경로 프로빙 | ✓ |
| 16:37-16:45 | E26-E31 flag 내용 추출 | ✓ (내용 미회수) |
| 16:45-16:50 | E32-E33 프로필/AWS 탐지 | ✓ |
| 16:50-17:00 | E34 AWS 환경변수 크기 측정 | ✓ (형식 미정) |
| 17:00+ | 블라인드 RCE 한계 → 보류 | — |

---

## 9. 결론

**현재 상태**: Stage 3 **root 접근 완료**, Stage 4 진입 **정보 수집 중**

**즉시 필요**: `/tmp/aws_env.txt` 실제 내용 확인 → AWS 자격증명 추출 → Stage 4 IP/엔드포인트 특정

**재개 코드**: 위 필수 확인사항 1-3번 순서로 진행, 각 단계마다 사용자 승인 재획득
