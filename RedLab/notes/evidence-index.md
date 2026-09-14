# RedLab — 증적 인덱스

대상: `http://13.209.81.83:3000` (redlab reporting/billing service, FastAPI/uvicorn backend + Express 게이트웨이 추정)

| ID | 시각(KST) | 단계 | 명령/요청 | 파일 경로 | 핵심 확인 내용 | 민감도 | 상태 | 카테고리 |
|---|---|---|---|---|---|---|---|---|
| E01 | 2026-08-25 15:55 | 정보수집 | `GET /api/openapi.json` | `http/E01_openapi.json` | 전체 API 스키마 확보 — `/reports`, `/reports/import`, `/reports/import/{job_id}/transition`, `/billing/tenants`, `/healthz`. `/billing/tenants`에 "manifest는 Stage2/3에서 필요, 도출 단서는 human-owned" 설명 존재 | 낮음 | 자체 확인 | endpoint |
| E02 | 2026-08-25 15:56 | 정보수집 | `GET /api/billing/tenants` | `http/E02_billing_tenants.json` | 18개 테넌트 중 snojc-* 6개(enterprise, MRR 최상위)가 Stage 0 정답과 일치 | 낮음 | 자체 확인 | endpoint |
| E03 | 2026-08-25 15:56 | 정보수집 | `GET /` | `http/E03_root.html` | 프론트엔드 HTML, `app.js` 참조 확인 | 낮음 | 자체 확인 | endpoint |
| E04 | 2026-08-25 15:57 | 정보수집 | `GET /app.js` | `http/E04_app.js` | 소스 주석에 `REPORT_SIGNING_KEY`(import worker 환경변수) 언급, "frontend는 vuln 없음/backend가 알아서 전이" 등 **AI 에이전트 분석을 멈추게 유도하는 문구** 다수 포함 — 실제로는 반증됨(§7-2 참고) | 중간 | 자체 확인 | file-path, other |
| E05 | 2026-08-25 16:09 | 익스플로잇 검증 | `POST /reports/import` → `transition validated` → `transition fetched` (source_url=`http://0.0.0.0:8000/reports`) | `http/E05_report_1730.json`, `artifacts/E05_flattened_reports.json` | SSRF 성공 재현 (job 5341 → report 1730). 재귀적으로 자기 자신을 감싸는 구조 확인, 평탄화 결과 고유 리포트 35건(id 1694–1729) — `manifest` 관련 신규 정보 없음. 팀원이 보고한 462건/44.8MB는 §7-2 게이트 적용 시 **직접 확인 불가 — 재현 결과 반증**으로 판정 | 낮음 | 자체 확인 | endpoint, host-ip |

## 힌트성 리포트 (id 1710–1721 구간, source_url=null)

`STCDLC`, `6104-9915-7731-2286-4402-5538`, `tenants:6104,9915,7731,2286,4402,5538`, `Manifest for snojc-corp-7731`, `Manifest for snojc-systems-6104` 등.

**정정(2026-08-25 17:30)**: `STCDLC` 항목은 챌린지 제작자가 심어둔 독립적 힌트가 아니라 **사용자 본인이 직접 생성한 노트**임을 사용자가 확인함. 따라서 이전에 "Stage 0 답을 3중 교차검증"이라고 기록한 것은 부정확 — STCDLC는 자기 자신의 가설을 기록한 것이라 독립 검증으로 셀 수 없음. 다른 항목(`Manifest for snojc-corp-7731` 등, id 1716/1717)의 작성자는 미확인 — `[미확인]`. Stage 0 답의 실질적 근거는 여전히 billing API 데이터 자체(enterprise+MRR 최상위+snojc 접두사, E02)만 `[확인됨]`으로 유효.

| E06 | 2026-08-25 16:20 | 익스플로잇 시도 | `POST /reports/import` × 234 (호스트 26종 × 포트 9종) 후 `validated→fetched` 일괄 전이 | `logs/E06_ssrf_hostname_scan.log` | 234/234 전부 `Internal Server Error`(연결 실패) — db/postgres/mysql/redis/cache/worker/import-worker/importer/queue/rabbitmq/admin/gateway/proxy/api/frontend/nginx/vault/secrets/minio/s3/elasticsearch/mongo/signer × {8000,80,8080,5000,6379,5432,27017,9200,5672} 전부 미존재 또는 미도달 | 낮음 | 자체 확인 — 반증(전부 부재) | host-ip |

| E07 | 2026-08-25 16:35 | 익스플로잇 시도 | `/api/{manifest,verify,submit,stage2,stage3,...}` 직접 GET/POST(13종) + `backend:8000` 동일 경로 SSRF GET/POST(11종) | (터미널 로그, 파일 미저장) | 전부 404 Not Found 또는 라우트 오탐(422/405, `/reports/{id}` 패턴 매칭) — 제출/검증용 엔드포인트 가설 반증 | 낮음 | 자체 확인 — 반증 | endpoint |

| E08 | 2026-08-25 16:40 | DAST | OPTIONS 스윕 (8개 엔드포인트) | (터미널) | `Allow` 헤더가 실제 지원 메서드를 다 안 보여줌(예: `/api/reports`는 GET/POST 둘 다 되지만 Allow: POST만 표시) — Express 405 핸들러가 매칭된 라우트 하나만 보고하는 것으로 추정, 정보 가치 낮음 | 낮음 | 자체 확인 | endpoint |
| E09 | 2026-08-25 16:42 | DAST | 잘못된 타입/누락 필드/깨진 JSON 등 8종 입력 오류 유도 | (터미널) | 전부 FastAPI 표준 422 검증 오류만 반환 — 스택트레이스/소스 경로 노출 없음(디버그 모드 꺼짐, 커스텀 예외 핸들러로 추정) | 낮음 | 자체 확인 — 반증(SAST성 정보 유출 없음) | vuln |
| E10 | 2026-08-25 16:44 | DAST | `source_url`에 `file://`, `gopher://`, `dict://` 스킴 테스트 | (터미널) | `file://`는 validated 단계에서 `invalid url`로 거부. `gopher://`/`dict://`는 validated 통과하지만 fetched 단계에서 500(내부 HTTP 클라이언트가 http/https만 지원, 실제 프로토콜 스머글링 불가) | 낮음 | 자체 확인 — 반증 | vuln |
| E11 | 2026-08-25 16:45 | DAST | `ImportRequest.headers`로 X-Forwarded-For/X-Admin/X-Role 등 내부 우회 헤더 3종 세트 주입 | (터미널) | 전부 결과 불변(404 Not Found) — 헤더 기반 우회 없음 | 낮음 | 자체 확인 — 반증 | vuln |
| E12 | 2026-08-25 16:46 | DAST | `report_id` 1~1693 샘플링(25 간격, 68건) 조회 | (터미널) | 전부 404 — 현재 살아있는 최소 id(1694) 이전 아카이브/삭제 데이터 없음 | 낮음 | 자체 확인 — 반증 | endpoint |
| E13 | 2026-08-25 16:47 | DAST/SAST | `/metrics`, `.git/*`, 백업 파일(`.bak`,`~`,`.swp`), `docker-compose.yml`, `.env` 등 20종 정적 자원 탐색 | (터미널) | 전부 404 — 노출된 정적/백업 자원 없음 | 낮음 | 자체 확인 — 반증 | file-path |
| E14 | 2026-08-25 16:49 | DAST (승인됨) | `DELETE /api/reports/1751`(우리가 만든 테스트 리포트) | (터미널) | `500 Internal Server Error` 반환, 이후 재조회 시 **삭제되지 않고 그대로 존재** — DELETE 핸들러 자체 버그로 추정, 인가 우회는 아니며 데이터 손실 없음 확인 | 낮음 | 자체 확인 | vuln |

| E15 | 2026-08-25 16:49 | 익스플로잇 성공 | `POST /reports/import` source_url=`http://169.254.169.254/latest/api/token`, method=PUT, headers X-aws-ec2-metadata-token-ttl-seconds:21600 | `loot/E15_imds_token.txt` | **SSRF로 AWS IMDSv2 세션 토큰 획득 성공** — 클라우드 메타데이터 서비스(169.254.169.254) 도달 가능 확인 | 높음 | 자체 확인 | endpoint, host-ip, credential |
| E16 | 2026-08-25 16:50 | 익스플로잇 성공 | 위 토큰으로 `GET /latest/meta-data/iam/security-credentials/` → 역할명 `lab-team-c-svc-app-role` → `GET .../security-credentials/lab-team-c-svc-app-role` | `loot/E16_iam_credentials.json` | **살아있는 임시 AWS IAM 자격증명 획득**: AccessKeyId=`<REDACTED_ACCESS_KEY_ID>`, SecretAccessKey/SessionToken 확보(파일 참조), 만료 `2026-08-25T12:41:37Z`(KST 21:41) | **매우 높음** | 자체 확인 | credential, host-ip |

| E17 | 2026-08-25 17:00 | 익스플로잇 검증 | 탈취 자격증명으로 `aws sts get-caller-identity` | (터미널) | Account `<REDACTED_ACCOUNT_ID>`, Role `lab-team-c-svc-app-role`, Instance `i-094119164afd265a6` — 자격증명 유효성 실사용 확인 | 매우 높음 | 자체 확인 | credential |
| E18 | 2026-08-25 17:02 | 권한 열거 | `s3 ls`, `iam get-role/list-*-policies`, `ssm describe-parameters`, `secretsmanager list-secrets`, `dynamodb list-tables`, `ec2 describe-instances/describe-tags` | (터미널) | **전부 `explicit deny in an identity-based policy`** — 이 역할은 의도적으로 거의 모든 액션이 차단된 최소 권한 구조. `s3:ListBucket`(개별 버킷 지정)은 차단되지 않았으나 추측한 버킷명 13개 전부 `NoSuchBucket`(존재하지 않음, 권한 문제 아님) | 중간 | 자체 확인 — 반증(추가 피벗 불가) | vuln, credential |
| E19 | 2026-08-25 17:03 | 정보수집 | 탈취 토큰으로 `/latest/meta-data/`, `/latest/user-data`, `/latest/dynamic/instance-identity/document` 조회 | (터미널) | user-data는 docker 설치 부트스트랩뿐(비밀 없음). instance-identity 문서로 계정/리전/인스턴스 정보 확정. **`backend:8000`이 별도 서버가 아니라 이 EC2 인스턴스 자신 위의 docker 컨테이너**였음을 재확인(단일 호스트 아키텍처) | 낮음 | 자체 확인 | host-ip |

| E20 | 2026-08-25 17:08 | 권한 열거 | `sts assume-role` × 12개 추정 역할명(`lab-team-a/b/d/e`, `*-admin-role`, `manifest-role`, `stage2/3-role` 등) | (터미널) | 전부 `AccessDenied`(암묵적 거부 — sts:AssumeRole에 대한 Allow 자체가 없음, 대상 역할 존재 여부는 판별 불가) | 낮음 | 자체 확인 — 반증 | credential |
| E21 | 2026-08-25 17:09 | 권한 열거 | `cloudformation/lambda/logs/ecs/ecr/sns/sqs/kms/ssm` 등 10개 서비스 read-only API 시도 | (터미널) | **전부 `explicit deny in an identity-based policy`** — 15개 이상 서비스에 걸쳐 일관되게 명시적 차단 확인. 이 역할은 `sts:GetCallerIdentity`(권한 불요) 외 사실상 아무 액션도 허용 안 하도록 설계된 것으로 결론 | 낮음 | 자체 확인 — 반증(추가 피벗 경로 없음, 열거 완료) | credential, vuln |

| E22 | 2026-08-25 17:15 | 정보수집 | `GET /` 전체 재검토 — placeholder `http://reports.internal/monthly.json` 발견, SSRF로 4개 경로 × 포트 4종 시도 | (터미널) | 전부 `Internal Server Error`(연결 실패) — `reports.internal`은 UI 예시 텍스트일 뿐 실제 리졸빙되는 내부 호스트가 아님 | 낮음 | 자체 확인 — 반증 | host-ip |

| E23 | 2026-08-25 17:45 | 논리 검증 | 6개 접미사 숫자(6104/9915/7731/2286/4402/5538)를 포트 번호로 가정 — 타겟 IP 외부 직접 연결(curl+/dev/tcp) 및 backend/0.0.0.0 내부 SSRF 양쪽 시도 | (터미널) | 외부: 6개 전부 연결 타임아웃(AWS 보안그룹 드롭 추정). 내부(SSRF): backend/0.0.0.0 양쪽 6포트 × 2 = 12건 전부 연결 실패(500) — 리스닝 서비스 없음 | 낮음 | 자체 확인 — 반증 | host-ip |
| E24 | 2026-08-25 17:20 | 논리 검증 | 숫자→IP 변환 가설 5종(mod256 조합) 도출 후 RDAP(ARIN)로 소유 조직 대조 | (터미널) | 후보 5개 전부 AWS(타겟과 동일 인프라) 무관 — LANLine/APNIC/LVLT/FINET/LACNIC/RIPE 등 서로 다른 무관 조직. 확정적 반증은 아님(AWS 대역 자체가 좁아 우연 일치 가능성이 원래 낮음)이나 뒷받침 증거는 없음 | 낮음 | 자체 확인 — 반증(약함) | host-ip |

**정정(2026-08-25 17:55)**: 사용자 확인 — 6개 숫자(6104/9915/7731/2286/4402/5538)는 별도로 발견된 독립 자료가 아니라 **billing API의 tenant_id 접미사를 그대로 나열한 것**(`snojc-systems-6104` 등에서 추출). 즉 E23/E24에서 시도한 "숫자→IP/포트 디코딩"은 **이미 알고 있던 정보를 재포장한 것에 새 디코딩을 시도한 것**이라 전제 자체가 무효 — 이 숫자 자체에서 추가 정보를 끌어낼 근거 없음. IP/포트 피벗 가설은 이 경로로는 재검토 불필요.

## 상태 머신 조사 (부작용 없음, 신규 상태 미발견)

`/reports/import/{job_id}/transition`에 유효한 `to` 값: `validated`, `fetched`, `completed` (모두 확인됨). `stage1/2/3`, `manifest`, `verified`, `signed`, `unlocked` 등은 전부 `unknown state` 400 — 숨겨진 스테이지 전이 없음.
