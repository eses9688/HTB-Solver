#!/bin/bash
set -e
HOST="billing.nexus.htb"
IP=10.129.12.96
JAR=/mnt/c/HTB/Nexus/loot/E13_cookies.txt
rm -f "$JAR"

PAGE=$(curl -sS -c "$JAR" -b "$JAR" -H "Host: $HOST" "http://$IP/admin/login")
TOKEN=$(echo "$PAGE" | grep -oE 'name="_token" value="[^"]+"' | head -1 | sed -E 's/.*value="([^"]+)".*/\1/')
echo "TOKEN=$TOKEN"

curl -sS -o /dev/null -c "$JAR" -b "$JAR" -H "Host: $HOST" \
  -X POST "http://$IP/admin/login" \
  --data-urlencode "_token=$TOKEN" \
  --data-urlencode "email=j.matthew@nexus.htb" \
  --data-urlencode "password=N27xh!!2ucY04"

echo "=== dashboard immediately after (same jar, same script) ==="
curl -sS -i -c "$JAR" -b "$JAR" -H "Host: $HOST" "http://$IP/admin/dashboard" -o /mnt/c/HTB/Nexus/http/E13_dashboard.html
head -c 300 /mnt/c/HTB/Nexus/http/E13_dashboard.html
echo
echo "=== second dashboard fetch, same jar again ==="
curl -sS -i -c "$JAR" -b "$JAR" -H "Host: $HOST" "http://$IP/admin/dashboard" -o /mnt/c/HTB/Nexus/http/E13_dashboard2.html
head -c 300 /mnt/c/HTB/Nexus/http/E13_dashboard2.html
