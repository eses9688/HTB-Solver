#!/bin/bash
# 내부 프록시의 모든 가능한 엔드포인트 탐색
# 그리고 Roundcube 웹 인터페이스에서 Stage 4 힌트 찾기

TARGET="http://13.125.104.131:30083"

echo "=== 내부 프록시 엔드포인트 탐색 ==="
echo

# 내부 프록시 가능한 경로들
endpoints=(
  "/"
  "/flag"
  "/flags"
  "/stage4"
  "/stage/4"
  "/next"
  "/nextgame"
  "/results"
  "/result"
  "/download"
  "/export"
  "/data"
  "/info"
  "/status"
  "/health"
  "/api"
  "/api/"
  "/api/v1"
  "/api/v1/"
  "/api/stage4"
  "/api/flag"
  "/admin"
  "/admin/"
  "/admin/data"
  "/admin/stage4"
  "/admin/export"
)

echo "[*] Internal Proxy (10.0.1.10:8080) 엔드포인트 시도:"
echo

for endpoint in "${endpoints[@]}"; do
  url="http://10.0.1.10:8080$endpoint"
  
  # HTTP 코드 먼저 확인 (빠름)
  code=$(curl -s -o /dev/null -w "%{http_code}" -m 3 "$url" 2>/dev/null)
  
  if [ "$code" != "000" ]; then
    echo "  [$code] $endpoint"
    
    # 200 또는 201이면 실제 내용 확인
    if [ "$code" = "200" ] || [ "$code" = "201" ]; then
      content=$(curl -s -m 3 "$url" 2>/dev/null | head -100)
      if [ ! -z "$content" ]; then
        echo "       Content: ${content:0:80}"
      fi
    fi
  fi
done

echo
echo "=== Roundcube 웹 UI에서 Stage 4 힌트 찾기 ==="
echo

# Roundcube 특정 페이지들
roundcube_endpoints=(
  "/?_task=about"
  "/?_task=settings"
  "/?_task=settings&_action=preferences"
  "/?_task=addressbook"
  "/?_task=mail"
  "/about"
  "/?_action=about"
)

echo "[*] Roundcube 페이지 탐색:"
echo

for endpoint in "${roundcube_endpoints[@]}"; do
  url="$TARGET$endpoint"
  code=$(curl -s -o /dev/null -w "%{http_code}" -m 3 -b "roundcube_sessauth=pppFdrSD1OslI9oOCaYj4CVgUd-1787101200; roundcube_sessid=i02l4jam87su5mp5mieh6hq9od" "$url" 2>/dev/null)
  
  if [ "$code" != "000" ] && [ "$code" != "404" ]; then
    echo "  [$code] $endpoint"
  fi
done

echo
echo "[+] 탐색 완료"
