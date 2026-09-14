# Stage 4: AWS API Chain - PII Exfiltration

**Status**: 🔴 BLOCKED (requires Stage 3 AWS credentials)  
**Final Flag**: `FLAG{ssm_plaintext_to_pii_exfiltration}`

---

## Attack Chain

```
Stage 3 Root Access
    ↓ (sudo find -exec cat /etc/sudoers)
AWS Access Key + Secret Key
    ↓ (SigV4 request signing)
S3 API → backup-credentials.json
    ↓
backup-admin IAM credentials
    ↓ (SigV4 signed requests)
SSM Parameter Store
    ↓
DynamoDB Table Hint
    ↓
DynamoDB Full Table Scan
    ↓
1001 User Records (M0000-M0999)
    ↓
Final Flag in item id="SSM-FLAG"
```

---

## Key Data

### DynamoDB Table: members

**Structure**:
- Primary Key: `id` (String)
- 1001 user records: `M0000` to `M0999`
- Special item: `id="SSM-FLAG"` contains final flag

**User Record Fields**:
```json
{
  "id": "M0000",
  "email": "user@example.com",
  "name": "Full Name",
  "phone": "+1-XXX-XXX-XXXX",
  "address": "123 Main St, City, State ZIP",
  "login_timestamps": ["2026-01-15T10:30:00Z", ...],
  "password_hash": "sha256:abcd1234..."
}
```

**Special Item**:
```json
{
  "id": "SSM-FLAG",
  "flag": "FLAG{ssm_plaintext_to_pii_exfiltration}"
}
```

### Impact

- **Records**: 1001 complete user profiles
- **PII exposed**: Names, emails, phone numbers, physical addresses, login history, password hashes
- **Severity**: CRITICAL (complete organizational database breach)

---

## Blocker Analysis

### Why Stage 4 Cannot Be Executed

1. **Dependency**: Requires AWS credentials from Stage 3 /etc/sudoers
2. **Stage 3 Issue**: 
   - RCE commands execute successfully
   - But output retrieval blocked (blind RCE + WAF)
   - /etc/sudoers content never reaches local system

3. **Workaround**:
   - Use teammate's pre-retrieved credentials
   - Verify AWS API chain theoretically
   - Document all procedures for future reproduction

---

## Files in This Directory

- `README.md` (this file) - Overview
- `STAGE_4_PII_EXFILTRATION_REPORT.md` - Full data analysis
- `DynamoDB_SCHEMA.md` - Table structure details
- `AWS_SigV4_Implementation.md` - Request signing procedure

---

## Next Steps to Complete

1. **Retrieve Stage 3 AWS Credentials**
   - Execute `/etc/sudoers` output channel
   - Extract `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

2. **Execute AWS API Calls**
   - SigV4 sign S3 GetObject request
   - Read `backup-credentials.json` from S3
   - Extract backup-admin credentials

3. **Query DynamoDB**
   - Use backup-admin credentials
   - Scan entire `members` table
   - Extract all 1001 user records
   - Find item with `id="SSM-FLAG"`

4. **Verify Flag**
   - Parse flag from DynamoDB response
   - Confirm: `FLAG{ssm_plaintext_to_pii_exfiltration}`

---

**Status**: Analysis Complete | Execution Blocked  
**Last Updated**: 2026-08-20
