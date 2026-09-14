# HTB Abducted

- 플랫폼: Hack The Box — Machines
- 난이도: Unknown · Linux
- 상태: Completed (root flag 획득)
- Write-up: [HTB_Abducted_Writeup.md](HTB_Abducted_Writeup.md)
- Flag: [loot/](loot/) (PRIVATE_STUDY, 민감 정보)

## 한 줄 공격 체인

익명 프린터 공유 커맨드 인젝션(nobody) → rclone 백업 비밀번호 복호화·재사용(scott) → Samba wide-links 심링크로 SSH 키 주입(marcus) → operators 그룹의 systemd 드롭인 권한 악용(root)

## 폴더 구조

- `scans/` — nmap 원본 결과
- `http/` — 커맨드 인젝션 콜백 로그, 세션 정리본
- `logs/` — 리버스쉘 원본 세션 로그, 행동 타임라인(`action-log.md`)
- `scripts/` — 익스플로잋/자동화 스크립트 원본
- `notes/` — 증적 인덱스(`evidence-index.md`, `evidence-by-category.md`)
- `loot/` — 획득한 자격 증명, user/root flag
