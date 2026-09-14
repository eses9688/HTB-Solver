# 카테고리별 증적 뷰 — HTB Abducted

> 자동 생성 — evidence-index.md가 원본, 직접 편집 금지

## endpoint
- E01: TCP 22/139/445 오픈
- E02: OpenSSH 9.6p1 Ubuntu, Samba smbd 4
- E03: SMB 공유 목록(HP-Reception, projects, transfer, IPC$)
- E04: transfer 공유 익명 접근 거부
- E05: projects 공유 익명 접근 거부
- E08: smbmap 익명 — 전체 NO ACCESS
- E09: SMB2/3만 지원, 추가 취약 스크립트 특이사항 없음
- E12: HP-Reception 인쇄 잡을 통한 아웃바운드 콜백(취약점 endpoint)

## credential
- E06: null 세션으로 scott 계정 확인
- E07: scott Full Name=Scott Mercer
- E13: rclone.conf 원문 및 `rclone reveal` 평문 비밀번호(iXzvcib3SrpZ) 확보 원본 로그
- E14: scott SSH 로그인 성공(비밀번호 재사용 확인)
- E15: 공격자 SSH 공개키를 marcus authorized_keys에 삽입, marcus 접근 확보
- E16: root 권한 확보 경로(자격 증명이 아닌 그룹 권한 악용)
- E17: 자격 증명 확보/재사용 전체 요약

## host-ip
- E01: 대상 10.129.244.177
- E06: 도메인 사용자 RID 열거로 호스트 내부 계정 구조 확인
- E11: /etc/passwd, /etc/group으로 scott/marcus 시스템 계정 및 operators 그룹 확인

## file-path
- E10: /etc/samba/smb.conf, /etc/samba/shares.conf, /usr/local/bin/printaudit
- E11: /srv/transfer, /srv/projects, /home/scott, /home/marcus, /opt/offsite-backup/rclone.conf
- E13: 위 전체의 원본 세션 로그

## process
- E11: nobody(uid=65534) 권한 프로세스로 코드 실행
- E16: smbd 서비스 재시작 과정에서 root 권한 ExecStartPre 실행

## vuln
- E10: CWE-78 — printaudit 스크립트가 인쇄 잡 이름(%J)을 이스케이프 없이 쉘에 전달(커맨드 인젝션)
- E12: 위 취약점의 실제 콜백 기반 실증
- E15: 위험한 서비스 구성 — Samba `wide links`/`allow insecure wide links`/`force user` 조합으로 공유 루트 밖 임의 경로 쓰기
- E16: 위험한 서비스 구성 — `operators` 그룹에 systemd 드롭인 디렉터리 그룹 쓰기 권한 부여 + polkit을 통한 서비스 관리 위임 조합으로 root 권한 상승

## other
- 해당 없음
