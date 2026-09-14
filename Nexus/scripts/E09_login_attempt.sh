#!/bin/bash
set -e
COOKIEJAR=/mnt/c/HTB/Nexus/http/E09_cookies.txt
rm -f "$COOKIEJAR"
HOST="billing.nexus.htb"
IP=10.129.12.96

# Get login page + token
PAGE=$(curl -sS -c "$COOKIEJAR" -H "Host: $HOST" "http://$IP/admin/login")
TOKEN=$(echo "$PAGE" | grep -oE 'name="_token" value="[^"]+"' | head -1 | sed -E 's/.*value="([^"]+)".*/\1/')
echo "TOKEN=$TOKEN"

curl -sS -i -c "$COOKIEJAR" -b "$COOKIEJAR" -H "Host: $HOST" \
  -X POST "http://$IP/admin/login" \
  --data-urlencode "_token=$TOKEN" \
  --data-urlencode "email=admin@nexus.htb" \
  --data-urlencode "password=N27xh!!2ucY04" \
  -o /mnt/c/HTB/Nexus/http/E09_login_response.html \
  -D /mnt/c/HTB/Nexus/http/E09_login_headers.txt

cat /mnt/c/HTB/Nexus/http/E09_login_headers.txt
