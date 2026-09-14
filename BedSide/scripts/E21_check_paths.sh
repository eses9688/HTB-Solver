#!/bin/bash
cd /home/kali/bedside
for p in uploads/test.pdf files/test.pdf test.pdf static/uploads/test.pdf research/test.pdf uploads/ files/; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://research.bedside.htb/$p")
  echo "$p -> $code"
done
