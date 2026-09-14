# 2026-08-19 Stage 3 주소 — 팀 공유용

- 작성 기준: 2026-08-19 KST에 본인(자체) 세션에서 수행한 작업만 포함
- 대상: `13.125.104.131:30083`
- 관련 소스 저장소: `drkim-dev/private-test` (팀원이 보고한 `private-test2`와는 별개 저장소)

이 문서에는 GitHub PAT, 세션 쿠키 원문을 포함하지 않는다. 원시 응답 파일은
`C:\HTB\13.125.104.131\http\`, `C:\HTB\43.200.51.235\loot\`, `C:\HTB\43.200.51.235\scripts\`에 보관.

## 1. 요약

`drkim-dev/private-test` 저장소의 태그 메타데이터에서 Stage 3 후보 IP를
발견하고, 실제 포트 스캔·서비스 식별·팀원 힌트(MD5 테스트 계정)의 크랙·
로그인까지 전 과정을 자체적으로 재현/검증했다.

핵심 결과:

- `v1.2.1-hotfix` 태그의 **어노테이트 태그 메시지**(트리/커밋 내용이 아님)에서
`13.125.104.131` 확보
- 해당 IP에서 `30083`만 열려 있고 나머지 확인 포트는 전부 필터링/타임아웃
- `30083`은 Roundcube 1.6.10 기반 웹메일이며, 앞단에 `cj-webmail-waf`라는
이름의 Flask(Werkzeug) 게이트웨이가 있음을 `/health` 엔드포인트로 확인
- 팀원이 공유한 테스트 계정 MD5 해시(`179ad45c6ce2cb97cf1029e212046e81`)를
사전 대입으로 크랙 → 평문 `testpass`
- `testuser` / `testpass`로 실제 로그인 성공, Roundcube Inbox 진입까지 확인

## 2. 발견 경위 — GitHub 태그 메타데이터

### 2.1 배경

팀원 힌트: "Stage 3 직접 주소는 없지만, main 히스토리에 포함 안 된 태그
(`v1.2.1-hotfix`, `1.1.2`, `1.1.1`)가 있으니 각 태그의 독립 tree를 확인하라."

### 2.2 태그 목록 및 트리 확인

`GET /repos/drkim-dev/private-test/tags`로 3개 태그 확인, 각 태그가 가리키는
커밋의 tree를 재귀 조회:


| 태그              | 대상 커밋         | 내용                                                                                   |
| --------------- | ------------- | ------------------------------------------------------------------------------------ |
| `1.1.1`         | `6d2a6ae7...` | main과 무관한 별도 orphan 히스토리, `README.md`만 존재 (더미)                                       |
| `1.1.2`         | `3a4fee46...` | 위 orphan 히스토리 위, `README.md` + `dd`(내용 `zz`) — 더미                                    |
| `v1.2.1-hotfix` | `e28c075...`  | main 히스토리에 실제로 존재하는 "archive legacy source" 커밋과 동일 tree (`.gitignore`, `README.md`만) |


트리 내용만으로는 세 태그 모두 유의미한 정보가 없었다.

### 2.3 태그 객체 자체 확인 — 결정적 단서

`GET /repos/drkim-dev/private-test/git/refs`로 전체 ref를 다시 조회한 결과,
`v1.2.1-hotfix`는 일반 커밋이 아니라 **어노테이트 태그 객체**
(`sha: 2479ccecdde0f923bf0db5408ac18a5f901296b8`, `type: "tag"`)였다.
이 사실은 `/repos/.../tags` 목록 API 응답에서는 드러나지 않는다 (해당 API가
태그를 자동으로 대상 커밋으로 역참조해서 보여주기 때문).

`GET /repos/drkim-dev/private-test/git/tags/2479ccecdde0f923bf0db5408ac18a5f901296b8`
직접 조회 결과:

```
tagger: drkim-dev <drkim@example.com>  2026-08-16T13:08:54Z
tag: v1.2.1-hotfix
message: "urgent fix on 13.125.104.131 after alert"
object: e28c075309fb7842e6d3cff105971101146489ea (commit)
```

→ **Stage 3 후보 IP `13.125.104.131` 확보** (재현 스크립트:
`C:\HTB\43.200.51.235\scripts\gh_tags_explore.js`, 09:32 KST 작성/실행)

## 3. 포트/서비스 식별

`13.125.104.131`에 대해 curl로 직접 확인 (nmap 미사용 대체):


| 포트                                                       | 결과                                  |
| -------------------------------------------------------- | ----------------------------------- |
| 80, 443, 8080, 8081, 8443, 3000, 9091, 30082, 5000, 8888 | 전부 connection timeout               |
| **30083**                                                | HTTP 200, Roundcube Webmail 로그인 페이지 |


`30083` 응답 헤더에 `Server: Werkzeug/3.1.8 Python/3.12.14`와
`Server: Apache/2.4.62 (Debian)`가 중복으로 찍혀 있어, 3.37.135.243과 동일한
Flask 게이트웨이 + 백엔드(Apache/PHP) 구조로 추정.

로그인 페이지 JS 환경변수에서 `"rcversion":10610` → **Roundcube 1.6.10**
(CVE-2025-49113 취약 버전 범위 `<1.6.11`과 일치, 별도 검증 필요 항목).

### 3.1 `/health` 확인 — CJ 인프라 소속 확정

```
GET http://13.125.104.131:30083/health
200 OK
{"service":"cj-webmail-waf","status":"ok"}
```

서비스명이 `cj-webmail-waf`로 명시되어, 이 IP가 CJ 체인의 일부임을
[자체 확인] 수준으로 확정.

## 4. 팀원 힌트 교차 검증

팀원이 공유한 (출처: `drkim-dev/private-test2` 저장소, README 이력) 내용:

- 서비스명: `nginx-config-relay-mail`, Rainloop → Roundcube로 전환
- 배포: `http://<STAGE3_HOST>:30083` (호스트 scrub됨)
- 테스트 계정: `testuser` / MD5 `179ad45c6ce2cb97cf1029e212046e81`
- "Root shell access is required to obtain AWS credentials"

이 내용은 **내가 발견한 `13.125.104.131:30083`과 포트·서비스 성격이 정확히
일치**하지만, 팀원 쪽 저장소(`private-test2`)에는 실제 호스트가 없는 상태였다.
서로 다른 두 개의 별도 저장소(`private-test` vs `private-test2`)에서 독립적으로
나온 단서가 같은 서비스를 가리킨다는 점에서 교차 검증됨.

## 5. 테스트 계정 크랙 및 로그인 검증 

### 5.1 MD5 크랙

사전 대입 스크립트(`C:\HTB\43.200.51.235\scripts\md5_crack.js`, 09:48:53 KST 작성):

```
target: 179ad45c6ce2cb97cf1029e212046e81
match : testpass
```

### 5.2 로그인 검증


| 단계  | 요청                                                         | 결과                                                            | 시각(KST)  |
| --- | ---------------------------------------------------------- | ------------------------------------------------------------- | -------- |
| 1   | `GET /?_task=login` (CSRF 토큰/세션 확보)                        | 200                                                           | 09:49:09 |
| 2   | `POST /?_task=login&_action=login` (`testuser`/`testpass`) | 302 → `Location: /?_task=mail...`, `roundcube_sessauth` 쿠키 발급 | 09:49:38 |
| 3   | `GET /?_task=mail` (발급된 세션으로)                              | 200, `<title>Roundcube Webmail :: Inbox</title>`              | 09:49:43 |


원본 응답 파일: `C:\HTB\13.125.104.131\http\login_page.html`,
`login_result.html`, `mail_inbox.html`, `rc_cookie.txt`

→ `testuser` / `testpass` 계정으로 **Roundcube 로그인 성공 및 Inbox 진입까지 확인**.

## 6. 현재 상태

- Stage 3 주소: `**13.125.104.131:30083**` — 확정 [자체 확인]
- 인증 세션: 확보 (테스트 계정, 낮은 권한 추정)
- 다음 단계 후보 (미실행, 승인 대기):
  - CVE-2025-49113 (`_from` 파라미터 이중 전송 WAF 우회 + PHP 역직렬화) 시도
  - Inbox 내 다른 단서(메일 내용, 첨부파일 등) 확인
- 오늘 이 세션에서 수행한 요청: GitHub API GET, 포트 확인용 curl 다수,
Roundcube 로그인 요청 2회(토큰 조회 + 로그인) — 파괴적/상태 변경 요청 없음

