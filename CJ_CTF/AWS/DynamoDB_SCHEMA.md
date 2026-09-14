# DynamoDB Table Schema: members

---

## Table Metadata

| Property | Value |
|----------|-------|
| **Table Name** | members |
| **Primary Key** | id (String) |
| **Item Count** | 1001 user records + 1 flag record |
| **Encryption** | None (plaintext) |
| **Point-in-time Recovery** | Not enabled |
| **TTL** | None |

---

## Record Schema

### User Record (1001 instances: M0000-M0999)

```json
{
  "id": {
    "S": "M0000"
  },
  "email": {
    "S": "john.doe@example.com"
  },
  "name": {
    "S": "John Doe"
  },
  "phone": {
    "S": "+1-555-123-4567"
  },
  "address": {
    "S": "123 Main Street, Springfield, IL 62701"
  },
  "login_timestamps": {
    "L": [
      {"S": "2026-01-15T10:30:00Z"},
      {"S": "2026-01-16T14:22:15Z"},
      {"S": "2026-01-18T09:45:30Z"}
    ]
  },
  "password_hash": {
    "S": "sha256:5e884898da28047151d0e56f8dc62927..."
  },
  "created_at": {
    "S": "2025-12-01T08:00:00Z"
  },
  "last_login": {
    "S": "2026-01-18T09:45:30Z"
  }
}
```

### Flag Record (1 instance: SSM-FLAG)

```json
{
  "id": {
    "S": "SSM-FLAG"
  },
  "flag": {
    "S": "FLAG{ssm_plaintext_to_pii_exfiltration}"
  },
  "source": {
    "S": "SSM Parameter Store - plaintext storage"
  },
  "severity": {
    "S": "CRITICAL"
  }
}
```

---

## Field Descriptions

### User Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | String | User ID | M0000, M0001, ..., M0999 |
| `email` | String | Work email address | john.doe@example.com |
| `name` | String | Full name | John Doe |
| `phone` | String | Phone number | +1-555-123-4567 |
| `address` | String | Physical address | 123 Main St, City, State ZIP |
| `login_timestamps` | List[String] | ISO 8601 login times | ["2026-01-15T10:30:00Z", ...] |
| `password_hash` | String | SHA256 hash | sha256:5e884898da28047151d0e... |
| `created_at` | String | Account creation | 2025-12-01T08:00:00Z |
| `last_login` | String | Last access time | 2026-01-18T09:45:30Z |

---

## Sample Records

### User M0000
```json
{
  "id": "M0000",
  "email": "john.doe@example.com",
  "name": "John Doe",
  "phone": "+1-555-123-4567",
  "address": "123 Main Street, Springfield, IL 62701",
  "login_timestamps": [
    "2026-01-15T10:30:00Z",
    "2026-01-16T14:22:15Z",
    "2026-01-18T09:45:30Z"
  ],
  "password_hash": "sha256:5e884898da28047151d0e56f8dc629271873ff0...",
  "created_at": "2025-12-01T08:00:00Z",
  "last_login": "2026-01-18T09:45:30Z"
}
```

### User M0500
```json
{
  "id": "M0500",
  "email": "jane.smith@example.com",
  "name": "Jane Smith",
  "phone": "+1-555-987-6543",
  "address": "456 Oak Avenue, Chicago, IL 60601",
  "login_timestamps": [
    "2026-01-14T08:15:00Z",
    "2026-01-17T13:45:30Z",
    "2026-01-19T11:20:00Z"
  ],
  "password_hash": "sha256:6f4a8b9c3d2e1f0a9b8c7d6e5f4a3b2c...",
  "created_at": "2025-12-10T10:00:00Z",
  "last_login": "2026-01-19T11:20:00Z"
}
```

### User M0999 (Last User)
```json
{
  "id": "M0999",
  "email": "alex.johnson@example.com",
  "name": "Alexander Johnson",
  "phone": "+1-555-456-7890",
  "address": "789 Pine Road, Milwaukee, WI 53202",
  "login_timestamps": [
    "2026-01-12T16:30:00Z",
    "2026-01-15T12:00:00Z",
    "2026-01-19T14:15:00Z"
  ],
  "password_hash": "sha256:7g5b9c4e3f2a1d0e9c8b7a6f5e4d3c2b...",
  "created_at": "2026-01-01T00:00:00Z",
  "last_login": "2026-01-19T14:15:00Z"
}
```

---

## Security Issues

### 1. Plaintext Storage
- No encryption at rest
- User data stored in plaintext
- Accessible via DynamoDB API without additional authentication

### 2. Full Table Scan Enabled
- No read throttling
- No row-level security
- No attribute-level encryption

### 3. Default Encryption Disabled
- DynamoDB encryption not configured
- All data readable in transit and at rest

### 4. IAM Overpermissions
- backup-admin role has unlimited DynamoDB read access
- No condition restrictions on scan operations

---

## Exploitation Path

### Scan Query (DynamoDB)

```
Method: Query or Scan
Table: members
Credentials: backup-admin (obtained from S3)
Authentication: SigV4
Region: us-east-1
Action: DynamoDB_20120810.Scan
Parameters:
  TableName: "members"
  Limit: 1000 (max items per request)
  ExclusiveStartKey: (for pagination)
```

### Expected Response Size

- **Records**: 1001 user items + 1 flag item = 1002 total
- **Average item size**: ~500 bytes
- **Total data**: ~500 KB
- **Requests needed**: ~2 requests (with pagination)

---

## Mitigation Recommendations

1. **Enable Encryption**
   - Enable DynamoDB encryption at rest
   - Use KMS keys instead of default encryption

2. **Restrict Access**
   - Implement row-level security
   - Use IAM conditions to limit scan access

3. **Monitor Access**
   - Enable DynamoDB Streams
   - Log all API calls via CloudTrail

4. **Data Retention**
   - Implement TTL on sensitive records
   - Archive old login timestamps

5. **Password Protection**
   - Remove plaintext password hashes
   - Store only bcrypt/argon2 hashes with salts

---

**Last Updated**: 2026-08-20  
**Status**: Schema verified, access path confirmed
