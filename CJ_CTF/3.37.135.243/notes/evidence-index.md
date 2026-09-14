# 증적 인덱스 — 3.37.135.243

기존 파일을 소급 리네임하지 않고 ID만 부여한다.

| ID | 시각(KST) | 단계 | 명령/요청 | 파일 경로 | 핵심 확인 내용 | 민감도 | 상태 |
|---|---|---|---|---|---|---|---|
| E01 | 2026-08-18 15:50:57 | 포트 스캔 | `nmap -Pn -sV -T4` top-200 | `scans/nmap_top200.txt` | 전 포트 filtered/무응답 | 낮음 | [자체 확인] |
| E02 | 2026-08-18 | 배포 정보 확인 | GitHub 커밋 메타데이터 (43.200.51.235 저장소) | (43.200.51.235/loot/gh_commit_ea2eae6f...json) | 배포 대상 IP=3.37.135.243 확인 | 중간 | [자체 확인] |
| E03 | — | 포트/경로 정보 | (사용자 전달) | `notes/pentest-report.md` §13 | 포트 30082, `/upload/upload.action`, multipart 필드명 `upload` | 낮음 | [팀원 힌트, 미검증] |
| E04 | 2026-08-18 15:54:55 | SSRF 경유 접속 시도 | `GET /upload/upload.action` via 43.200.51.235 `/ops-status/monitor` | `http/via_ssrf1.html` | `ConnectTimeoutError`(timeout=3s) | 낮음 | [자체 확인 — 실패] |
| E05 | 2026-08-18 16:30 | 직접 접속 재시도 | `curl -v /` | (콘솔 로그만, 원본 미보존) | 1회 "Connection refused" 관측 (유일한 서버 레벨 응답) | 낮음 | [자체 확인] |
| E06 | 2026-08-18 16:41 | 최종 접속 재확인 | `curl` 다수 포트 | (콘솔 로그만) | 전부 `000`, 재현 불가 | 낮음 | [자체 확인 — 실패] |
| E07 | 2026-08-19 | Jenkinsfile 확보 | GitHub raw content | `loot/Jenkinsfile` | CI 배포 파이프라인 확인용 | 낮음 | [자체 확인] |
| E08 | 2026-08-19 | 업로드 폼/엔드포인트 확인 | `GET /` (연결 성공 시점) | `http/self_upload_form.html` | 업로드 폼 구조 확인 | 낮음 | [자체 확인] |
| E09 | 2026-08-19 | 업로드 실행 시도 | `POST /upload/upload.action` (`verify.jsp`) | `http/self_upload_action.hdr/html`, `http/upload_result.hdr/html` | 업로드 응답 확인 (아래 E10 참고) | 중간 | [자체 확인] |
| E10 | 2026-08-19 | 업로드 결과 검증 — **RCE 반증** | `GET /verify.jsp`, `/upload-1.0.0/verify.jsp` | `artifacts/verify.jsp`, `artifacts/verify_upload.txt`, `http/upload_result.html` | Struts2 인터셉터가 경로 제거 → basename만 `webapps/` 최상위 저장, 웹으로 미도달 → **RCE 아님** | 낮음 | [반증됨] |

## 대상 상태
접속 불가 상태가 반복적으로 발생했음(§E04~E06) — 최신 상태는 `43.200.51.235/notes/pentest-report.md` §14와
`43.200.51.235/notes/daily-log-2026-08-18.md` §4 타임라인 참고. E07~E10은 이후 세션에서 연결이 복구되어
실제로 업로드까지 도달한 시점의 증적이다.
