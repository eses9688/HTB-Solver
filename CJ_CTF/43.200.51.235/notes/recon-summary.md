# 43.200.51.235:8081 — 사용자 제공 정찰 요약 (PRIVATE_STUDY)

## 1. 초기 웹 서비스
- 대상: 43.200.51.235, HTTP 8081/tcp, nginx 1.27.5
- 여러 Host 헤더로도 동일 200/1281 bytes → 단순 vhost 탐색 무효

## 2. robots.txt
- /robots.txt 200 OK
- 내용: Grafana 모니터링 데모 인스턴스, 정식 프록시 라우팅 미완성, /grafana/ 경로로 임시 프록시 중

## 3. Grafana
- http://43.200.51.235:8081/grafana/ — 로그인 페이지
- /grafana/api/health → {"database":"ok","version":"11.2.0"}
- 익명 접근 비활성화, 주요 API 401

## 4. FTP
- ftp 43.200.51.235, banner: "220 CJ internal file transfer"
- 익명 로그인: ftp/ftp 성공
- 루트 파일: backup-policy.txt, maintenance-log.txt, readme.txt

## 5. backup-policy.txt
- 힌트: 자격증명 파일은 .env (정기 로테이션 예정, 수동 정리 필요)
- 웹에서 .env는 404였지만 FTP로는 직접 다운로드 가능

## 6. .env (FTP로 확보, Base64)
- 디코딩 결과: Grafana Viewer 계정
  - Username: ops-viewer
  - Password: N0vaOps2024!

## 7. Grafana 로그인
- ops-viewer / N0vaOps2024! 로그인 성공, Viewer 권한
- Viewer로도 대시보드 1개 노출: "Internal Ops"

## 8. Internal Ops 대시보드
- 내부 링크 발견: /ops-status/
- 새 자체 웹앱: 로그인, 리포트 목록, 리포트 다운로드, monitor 폼(핑/모니터링 추정)

## 9. /ops-status/download?file=
- 리포트 다운로드가 file 파라미터로 서버측 경로를 받는 구조로 보임 → Path Traversal 후보
- 정상 다운로드 확인 → 경로 조작 테스트 → 추가 파일 접근 테스트 순서로 진행 예정 (여기서 이어감)
