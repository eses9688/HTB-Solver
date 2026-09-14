# RedLab

- 플랫폼: Custom AWS-hosted 챌린지 (multi-tenant SaaS 시뮬레이션, HTB 외부)
- 난이도: Unknown
- 상태: 진행중 (flag 미획득) — Stage 0(테넌트 식별)·SSRF·AWS IAM 자격증명 획득까지 확인, Stage 2/3 진입 조건("manifest") 미해결
- Write-up: [WRITEUP.md](WRITEUP.md)
- 민감 정보(IAM 임시 자격증명 등): `loot/`, `notes/evidence-index.md` (PRIVATE_STUDY, 세션 종속 값이며 만료됨)

## 폴더 구조

- `http/` — 원본 API/HTTP 요청·응답 (E01 openapi.json, E02 billing/tenants, E03 root.html, E04 app.js, E05 SSRF 테스트 리포트)
- `artifacts/` — E05 리포트 콘텐츠 평탄화 결과
- `loot/` — SSRF로 획득한 IMDSv2 토큰, IAM 임시 자격증명(E15, E16, E29), user-data, aws 환경변수, 힌트성 리포트 원문(E27, E28)
- `scripts/` — SSRF 탐색에 사용한 스크립트(ssrf_probe.sh, ssrf_probe2.sh, vpc_sweep.sh)
- `logs/action-log.md` — 대상에 보낸 행동의 시간순 로그(E05까지만 기록됨, 이후 행동은 notes에만 서술 — WRITEUP.md §12 참고)
- `notes/` — 원본 작업 노트 (WRITEUP.md가 이를 통합한 최종본). 개별 파일 간 일부 내용이 상충하며, WRITEUP.md에서 `notes/evidence-index.md`(가장 최신·정정 포함)를 우선 자료로 채택했다.
  - `evidence-index.md` — 증적 인덱스, E01~E24 및 2건의 정정 기록 포함(가장 신뢰도 높은 자료)
  - `evidence-summary.md`, `TENANTS_TABLE.md` — Stage 0/SSRF 기술 분석 상세본
  - `FINAL_FINDINGS.md`, `PROGRESS_SUMMARY_20260826.md` — 초기/중간 정리본(일부 내용이 evidence-index.md 정정 이전 상태로 남아 있음)
  - `VERIFIED_EVIDENCE_ONLY.md` — 검증된 사실만 별도 정리한 체크리스트
- `openapi_latest.json` — E01과 동일 내용의 재확인용 스냅샷
- `session2_cjctf_merge/` — 동일 대상을 처음부터 다시 푼 2번째 세션의 증적(원래 `CJ_CTF/13.209.81.83/`에 있었으나 동일 챌린지로 확인되어 병합). `PROGRESS.md`, `OBJECTIVE_FINDINGS_20260826.md` 및 해당 세션의 원본 API/IMDS 캡처. 이 세션에서만 발견된 것: 다른 팀 리포트(#2061)를 통해 확인된 `cjons-*`(snojc 역순) 테넌트 ID 형식과 `/tenants/cjons-*/manifest`·`/flag` 경로가 모두 404라는 점(§ WRITEUP.md 참고).
