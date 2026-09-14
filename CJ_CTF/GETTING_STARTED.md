# 🎯 CJ-CTF: 시작 가이드

**이 문서를 읽고 Stage 1부터 4까지 손으로 직접 풀 수 있습니다.**

---

## 📂 폴더 구조

```
CJ_CTF/
├── README.md                      ← 프로젝트 개요
├── GETTING_STARTED.md             ← 이 파일
│
├── STAGE1_OUTLINE.md              ← Stage 1 개요 (동료 자료 참고)
├── STAGE2_OUTLINE.md              ← Stage 2 개요 (동료 자료 참고)
├── STAGE3_DETAILED_WRITEUP.md     ← Stage 3 상세 공략 ⭐
├── STAGE4_DETAILED_WRITEUP.md     ← Stage 4 상세 공략 ⭐
│
├── 43.200.51.235/                 ← Stage 1 데이터
├── 3.37.135.243/                  ← Stage 2 데이터
├── 13.125.104.131/                ← Stage 3 데이터 (공략에 사용)
├── AWS/                           ← Stage 4 자료
│   ├── README.md
│   ├── DynamoDB_SCHEMA.md
│   └── AWS_SigV4_Implementation.md
│
├── stage3_final_status.txt        ← Stage 3 검증 보고서
└── stage4_rce_attack.md           ← Stage 4 요약
```

---

## 🚀 단계별 가이드

### Phase 1: 동료 자료를 통해 Stage 1, 2 이해하기

**소요 시간**: 30분

1. **README.md 읽기**
   - 전체 CTF 목표 이해
   - 4개 Stage의 공략 체인 파악

2. **STAGE1_OUTLINE.md 읽기**
   - Grafana (43.200.51.235:8081) 공략 개요
   - 동료 자료 위치: `43.200.51.235/artifacts/`

3. **STAGE2_OUTLINE.md 읽기**
   - AWS IMDS (3.37.135.243) 공략 개요
   - SSRF/RCE를 통한 메타데이터 접근 방법
   - 동료 자료 위치: `3.37.135.243/artifacts/`

**핵심**: Stage 1, 2는 동료 자료를 참고하면 됩니다.

---

### Phase 2: Stage 3 실습 - Roundcube RCE 공격

**소요 시간**: 2-3시간 (직접 실행 시 더 오래 걸릴 수 있음)

**STAGE3_DETAILED_WRITEUP.md를 순서대로 따라하면 됩니다.**

#### Step 1: 환경 준비
```bash
cd /c/HTB/CJ_CTF
# Roundcube 서버 13.125.104.131:30083에 접근 가능한지 확인
curl -v http://13.125.104.131:30083/
```

#### Step 2: 취약점 이해
- CVE-2025-49113 (PHP 객체 역직렬화)
- Crypt_GPG_Engine 가젯 체인
- Base32 페이로드 인코딩

#### Step 3: RCE 실행
- Multipart form으로 악의적인 PHP 객체 전송
- 타이밍 차이로 명령 실행 확인
- 파일에 출력하여 결과 획득

#### Step 4: 권한 상승
- `sudo /usr/bin/find`로 GTFOBins shell escape
- Root 권한 확보

#### Step 5: AWS 자격증명 추출
- `/etc/sudoers` 파일 읽기
- AWS_ACCESS_KEY_ID와 AWS_SECRET_ACCESS_KEY 획득

#### Step 6: Flag 위치 확인
- `/var/www/FLAG.txt` 심볼릭 링크 확인
- Flag 위치, 크기, 해시 기록

---

### Phase 3: Stage 4 실습 - AWS API 체인

**소요 시간**: 1-2시간

**STAGE4_DETAILED_WRITEUP.md를 순서대로 따라하면 됩니다.**

**전제 조건**: Stage 3에서 획득한 AWS 자격증명 필요

#### Step 1: SigV4 서명 구현
- HMAC-SHA256 기반 AWS API 인증
- `AWS_SigV4_Implementation.md` 참고
- Python 또는 bash로 구현

#### Step 2: S3에서 backup-admin 자격증명 조회
```python
# SigV4로 서명된 S3 GetObject 요청
curl https://s3.us-east-1.amazonaws.com/backup-bucket/backup-admin/backup-credentials.json
```

#### Step 3: DynamoDB 전체 스캔
- backup-admin 자격증명으로 DynamoDB Scan 실행
- 1001개 사용자 기록 조회
- 페이지 나누기(pagination) 처리

#### Step 4: 최종 Flag 추출
```
FLAG{ssm_plaintext_to_pii_exfiltration}
```

#### Step 5: PII 데이터 분석
- 1001명 사용자 정보 통계
- 개인정보 유출 영향도 평가

---

## 💡 핵심 학습 포인트

### CVE-2025-49113 (PHP 역직렬화)
```
untrusted object
    ↓
unserialize() 함수
    ↓
Crypt_GPG_Engine gadget
    ↓
base32 디코딩
    ↓
shell 명령 실행
```

### GTFOBins (find -exec shell escape)
```
sudo /usr/bin/find / -maxdepth 0 -exec /bin/sh -c 'COMMAND' \;
```

### AWS SigV4 서명
```
Canonical Request
    ↓ SHA256
String to Sign
    ↓ HMAC-SHA256
Signature
    ↓
Authorization Header
```

### DynamoDB Scan Pagination
```
첫 번째 요청 (limit: 1000)
    ↓
LastEvaluatedKey 있으면 계속
    ↓
ExclusiveStartKey로 다음 페이지 조회
    ↓
LastEvaluatedKey 없을 때까지 반복
```

---

## 📋 체크리스트

### Stage 1 (Grafana - 동료 자료)
- [ ] `43.200.51.235/artifacts/` 파일들 확인
- [ ] 취약점 파악
- [ ] Stage 2 정보 획득

### Stage 2 (IMDS - 동료 자료)
- [ ] `3.37.135.243/artifacts/` 파일들 확인
- [ ] SSRF/RCE 취약점 이해
- [ ] AWS IAM 자격증명 획득

### Stage 3 (Roundcube RCE) ⭐
- [ ] STAGE3_DETAILED_WRITEUP.md Step 1-7 따라하기
- [ ] RCE 확인 (타이밍 기반)
- [ ] Root 권한 확보
- [ ] /etc/sudoers에서 AWS 키 추출
- [ ] /var/www/FLAG.txt 위치 확인
- [ ] stage3_final_status.txt로 결과 검증

### Stage 4 (AWS API) ⭐
- [ ] STAGE4_DETAILED_WRITEUP.md Step 1-7 따라하기
- [ ] SigV4 구현 및 테스트
- [ ] S3에서 backup-credentials.json 조회
- [ ] DynamoDB members 테이블 스캔
- [ ] 1001개 사용자 기록 수집
- [ ] 최종 FLAG 추출: `FLAG{ssm_plaintext_to_pii_exfiltration}`

---

## 🔧 도구 설정

### Python 환경
```bash
python3 --version  # 3.6 이상 필요
pip install requests  # AWS API 요청용
```

### Curl 확인
```bash
curl --version  # HTTP 요청용
```

### Base32 인코딩 (bash 내장)
```bash
echo -n "command" | base32
```

### JSON 파싱
```bash
# bash: jq 설치
pip install jq

# Python: 내장 json 모듈
python3 -c "import json; ..."
```

---

## 📝 추천 기록 방식

각 단계마다 기록하면 나중에 증명할 때 유용합니다:

### Stage 3
```bash
# Step 3: RCE 확인
echo "타이밍 차이 측정 결과" > /tmp/stage3_timing.txt
# time curl ... >> /tmp/stage3_timing.txt

# Step 5: Root 권한 확인
echo "id 명령 결과" > /tmp/stage3_root_proof.txt
# RCE로 "id > /tmp/stage3_root_proof.txt" 실행

# Step 6: AWS 자격증명
echo "AWS_ACCESS_KEY_ID=..." > /tmp/stage3_aws.txt
echo "AWS_SECRET_ACCESS_KEY=..." >> /tmp/stage3_aws.txt
```

### Stage 4
```bash
# Step 5: DynamoDB 스캔 결과
python3 stage4_scan.py > /tmp/stage4_dynamodb_result.txt

# Step 6: Flag 추출
grep "FLAG{" /tmp/stage4_dynamodb_result.txt > /tmp/stage4_flag.txt
```

---

## 🆘 문제 해결

### Blind RCE (Stage 3)
**문제**: RCE는 되는데 출력을 받을 수 없음  
**해결**: 파일에 출력하고 RCE로 다시 읽기

### HTTP 접근 불가 (Stage 3)
**문제**: /tmp의 파일을 HTTP로 다운로드할 수 없음  
**해결**: RCE 명령어로 직접 파일 내용 확인

### AWS 인증 실패 (Stage 4)
**문제**: SigV4 서명이 잘못되었을 수 있음  
**해결**: 
- Canonical Request 형식 재확인
- 타임스탬프 UTC 확인
- 페이로드 해시 재계산

### DynamoDB 스캔 느림 (Stage 4)
**문제**: 1001개 기록 조회에 시간 소요  
**해결**: 
- 요청 사이에 1초 대기 (API 레이트 제한)
- Pagination 정확히 구현
- 부분 스캔이 아닌 전체 스캔 확인

---

## 📚 참고 자료

### Stage별 상세 가이드
- STAGE1_OUTLINE.md - Grafana 개요 + 동료 자료
- STAGE2_OUTLINE.md - IMDS 개요 + 동료 자료
- STAGE3_DETAILED_WRITEUP.md - Roundcube RCE 완전 가이드
- STAGE4_DETAILED_WRITEUP.md - AWS API 완전 가이드

### AWS 자료
- AWS/README.md - Stage 4 개요
- AWS/DynamoDB_SCHEMA.md - 테이블 구조 및 데이터 예시
- AWS/AWS_SigV4_Implementation.md - API 서명 구현

### 검증 자료
- stage3_final_status.txt - Stage 3 검증 보고서
- stage4_rce_attack.md - Stage 4 요약

---

## 🎯 최종 목표

```
ALL 4 STAGES COMPLETE
│
├── Stage 1: Grafana 공략 ✓
├── Stage 2: AWS IMDS 공략 ✓
├── Stage 3: Roundcube RCE ✓
│   └── AWS 자격증명 획득
│
└── Stage 4: DynamoDB PII 유출 ✓
    └── FLAG{ssm_plaintext_to_pii_exfiltration}
```

---

## ⏱️ 예상 소요 시간

- **공부**: 30분 (Stage 1, 2 동료 자료 + 개요)
- **Stage 3 실습**: 2-3시간 (직접 실행)
- **Stage 4 실습**: 1-2시간 (AWS API + DynamoDB)
- **총 소요 시간**: 3-5시간

---

**준비 완료!** 이제 STAGE3_DETAILED_WRITEUP.md부터 시작하세요.

