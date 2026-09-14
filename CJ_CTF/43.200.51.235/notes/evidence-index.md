# 증적 인덱스 — 43.200.51.235

기존 파일을 소급 리네임하지 않고 ID만 부여한다. 상세 서술은 `notes/pentest-report.md`,
`notes/daily-log-2026-08-18.md` 참조.

| ID | 시각(KST) | 단계 | 명령/요청 | 파일 경로 | 핵심 확인 내용 | 민감도 | 상태 |
|---|---|---|---|---|---|---|---|
| E01 | 2026-08-18 | 초기 정찰 | ffuf/curl/feroxbuster | `notes/recon-summary.md` | nginx 1.27.5, robots.txt→Grafana 안내, 익명 FTP 배너 | 낮음 | [자체 확인] |
| E02 | 2026-08-18 | FTP 자격증명 확보 | `ftp` 익명 로그인 → `.env` 다운로드 | `loot/env_file.txt`, `loot/backup-policy.txt`, `loot/maintenance-log.txt`, `loot/readme.txt` | 이중 Base64 → `ops-viewer`/`N0vaOps2024!` | **높음(자격증명)** | [자체 확인] |
| E03 | 2026-08-18 | Grafana 로그인 | POST 로그인 | (원본 미보존 — 재확인 시 저장 권장) | Viewer 권한 로그인 성공, `/ops-status/` 링크 발견 | 중간 | [자체 확인] |
| E04 | 2026-08-18 | CVE-2024-9264 시도 | SQL Expression 페이로드 | (미보존) | `SELECT 1` 500 에러 → 비활성 판단, 실패 사례 | 낮음 | [자체 확인 — 실패] |
| E05 | — | 2차 SQLi 존재 주장 | (미실행) | `notes/pentest-report.md` §4 | `/ops-status/admin/last-login-sort`, PostgreSQL superuser 추출 주장 | 중간 | [팀원 힌트, 재현 필요] |
| E06 | — | svc-monitor 해시 | (미실행 — 힌트로 전달받음) | `loot/svc-monitor.hash` | `$2b$04$lCXs...` bcrypt 해시 | **높음** | [팀원 힌트] |
| E07 | 2026-08-18 | bcrypt 크랙 | hashcat -m 3200 rockyou.txt | (로컬 hashcat 세션, 로그 미보존) | `svc-monitor`/`novise` | **높음** | [자체 확인] |
| E08 | 2026-08-18 | 관리자 SSRF 확인 | `GET /ops-status/monitor?target=...` | `http/monitor.html`, `http/monitor_test.html`, `http/monitor_test2.html` | `HTTPConnectionPool`/`ConnectTimeoutError` — 서버측 아웃바운드 요청 확인 | 중간 | [자체 확인] |
| E09 | 2026-08-18 | 내부 admin 덤프 | SSRF → `127.0.0.1:9091/admin/dump-config` | `http/dumpconfig.html`, `http/dumpconfig3.html` | `internal-metrics-admin` 서비스, backups/ 힌트 노출 | 중간 | [좌표: 팀원 힌트 / 실행: 자체 확인] |
| E10 | 2026-08-18 | Path Traversal 실패 사례 | `GET /ops-status/download?file=../backups/cj-ops-ci.bak` | `loot/cj-ops-ci.bak` | 404, 필터 차단 (207 bytes) | 낮음 | [자체 확인 — 실패] |
| E11 | 2026-08-18 | Path Traversal 우회 성공 | `....//backups/cj-ops-ci.bak` | `loot/cj-ops-ci-v2.bak` | 200 OK, 431 bytes, GitHub PAT 포함 | **높음(PAT)** | [자체 확인] |
| E12 | 2026-08-18 | GitHub 저장소 접근 | GitHub API (PAT 인증) | `loot/gh_repo_check.json`, `loot/gh_repo_auth.json` | `private:true`, admin/maintain/push/triage/pull 전권 | **높음** | [자체 확인] |
| E13 | 2026-08-18 | 커밋 히스토리 분석 | GitHub API `commits` | `loot/gh_commits.json`, `loot/gh_commit_creds.json`, `loot/gh_commit_ea2eae6f...json` | `X-Node-Secret: relay-legacy-2023` 하드코딩, 배포 IP(3.37.135.243) 확인 | **높음** | [자체 확인] |
| E14 | 2026-08-18 | 취약 업로드 소스 확보 | GitHub raw content | `loot/Upload.java` | `uploadFileName` 무검증 — 정적분석상 위험 | 낮음 | [반증됨 — §19-2 동적검증에서 부정] |
| E15 | 2026-08-18 | IDOR | `GET /ops-status/reports/62` | `http/report_62.html` | 무인증 접근 가능, "Service Account Audit" 노출 | 중간 | [자체 확인] |
| E16 | 2026-08-19 | SAST — struts.xml | GitHub raw + `?debug=command&expression=1%2B1` | `notes/pentest-report.md` §19-1 | devMode=true, OGNL 평가 가능하나 static 메서드 차단 확인 | 낮음 | [자체 확인] |
| E17 | 2026-08-19 | Upload.java 동적 재검증 | multipart 업로드 (`upload-1.0.0/verify.jsp`) | `3.37.135.243/http/upload_result.html` (대상 폴더에 보존) | Struts2 인터셉터가 basename만 사용 → RCE 아님, **정적분석 결론 반증** | 낮음 | [반증됨] |
| E18 | 2026-08-19 | vhost/디렉터리 재탐색 | ffuf(Host 헤더) + feroxbuster | (일지 §1 참고, 원본 콘솔 로그만 존재) | 신규 vhost/경로 없음 확인 | 낮음 | [자체 확인] |

## 참고
- E03, E04, E20 등 일부 항목은 원본 요청/응답 파일이 별도 저장되지 않아 `notes/pentest-report.md` 서술에만 의존한다 — 재확인 시 `tee`로 원본 보존 권장.
