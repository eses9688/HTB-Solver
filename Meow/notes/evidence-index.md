# 증적 인덱스 — HTB Meow

| ID | 시각 (UTC) | 단계 | 명령/요청 | 파일 경로 | 핵심 확인 내용 | 민감도 | 상태 |
|----|-----------|------|-----------|-----------|----------------|--------|------|
| E01 | 2026-08-14 07:26 | 정보 수집 | `nmap -sT -p- --min-rate 3000 -Pn $TARGET` | `scans/E01_nmap_full_tcp.txt` | 전체 65535 TCP 포트 중 23/tcp만 open | 낮음 | 확인됨 |
| E02 | 2026-08-14 07:27 | 정보 수집 | `nmap -sT -sV -sC -p 23 -Pn $TARGET` | `scans/E02_nmap_p23_service.txt` | 23/tcp = Linux telnetd | 낮음 | 확인됨 |
| E03 | 2026-08-14 07:30 | 초기 접근 / 권한 확인 | `telnet $TARGET` → `root` 로그인 → `id`, `hostname`, `cat /root/flag.txt` | `logs/E03_telnet_root_access.log` | `uid=0(root) gid=0(root)`, hostname `Meow`, root flag 획득 | 높음(플래그 포함, PRIVATE_STUDY) | 확인됨 |

## 참고

- $TARGET = `10.129.59.55` (풀이 당시 세션 종속 값, HTB Starting Point 리셋 후 재할당된 IP)
- $LHOST = `10.10.14.221` (Starting Point VPN, `tun0`)
- 세션 중 VPN을 "Machines" 풀(AU Machines 2)에서 "Starting Point" 풀(US StartingPoint 2)로 전환한 이력이 있다. 상세는 Write-up 12절 참고.
