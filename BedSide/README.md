# HTB BedSide

- 플랫폼: Hack The Box — Machines
- 난이도: Unknown
- 상태: 진행중 (root/user flag 미획득)
- Write-up: [HTB_BedSide_Writeup.md](HTB_BedSide_Writeup.md)

## 폴더 구조

- `scans/` — nmap 원본 결과 (E01 전체 TCP 포트 스캔, `.nmap`/`.gnmap`/`.xml`)
- `http/` — `bedside.htb`, `research.bedside.htb` 두 vhost의 원본 페이지 응답 (E03, E06)
- `scripts/` — 정찰 스크립트(E01, E02, E04, E05, E07)와 pickle 역직렬화/PDF 파싱 RCE 시도 스크립트(E15~E22)

## 참고

- `loot/`, flag 파일, root/user 권한 획득 증적은 존재하지 않는다.
- `scripts/`의 E15~E22 익스플로잇 스크립트는 코드 자체만 남아 있고, 실행 결과(stdout, HTTP 응답, 대상 마커 파일 확인 등)를 기록한 별도 증적 파일은 이 폴더에 없다 — 실제 성공/실패 여부는 `HTB_BedSide_Writeup.md`의 "막힌 지점" 절 참고.
