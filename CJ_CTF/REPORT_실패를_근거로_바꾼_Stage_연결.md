# CJ 체인 CTF — 실제 문제풀이 흐름 보고서
### "실패를 다음 근거로 바꿔 Stage를 연결했다"

**작성일**: 2026-08-24
**대상**: CJ 체인 (43.200.51.235 → 3.37.135.243 → 13.125.104.131), PRIVATE_STUDY 모드
**목적**: 각 Stage에서 처음 세운 가설이 막혔을 때, 어떤 새로운 근거를 찾아 우회했고, 그 근거를 어떻게 검증해 다음 Stage로 넘겼는지를 증적(Evidence ID) 기준으로 재구성한다.

---

## 0. 읽는 법

각 Stage는 아래 4단계 사이클로 진행된다.

```
가설 → (막힘) → 새 근거 → 검증 → 확보 → 다음 Stage로 Handoff
```

"막힌 가설"은 실패가 아니라 **다음 근거를 찾기 위한 제거 과정**으로 취급한다. 표에 적힌 증적 ID(E01, E02 …)는 각 대상 폴더의 `notes/evidence-index.md`에 그대로 대응한다.

---

## STAGE 1 — 애플리케이션 취약점 (43.200.51.235:8081)

| 단계 | 내용 |
|---|---|
| **막힌 가설** | 공개 CVE (CVE-2024-9264, Grafana SQL Expression RCE)로 바로 RCE를 노림 |
| **새 근거** | 서비스 고유 입력 — 이 서비스만의 커스텀 관리 엔드포인트(`/ops-status/admin/last-login-sort`)가 정렬 파라미터를 그대로 쿼리에 사용하는 정황 |
| **검증** | SQL Injection 경로로 얻은 `svc-monitor` 해시를 직접 크랙·로그인해 실재를 증명 |
| **확보** | 내부 기능(SSRF) 및 저장소 단서(GitHub PAT) 확보 |
| **Handoff** | Stage 2 배포 대상 IP(3.37.135.243) 확인 |

### 상세 흐름

1. **정찰 — 표면 확인**
   `nginx:8081` → robots.txt가 `/grafana/`를 안내. 동시에 FTP 익명 로그인이 열려 있음을 확인 (E01).

2. **막힌 가설: 공개 CVE**
   Grafana OSS 11.2.0에 알려진 CVE-2024-9264(SQL Expression RCE)를 시도. `SELECT 1` 같은 최소 표현식조차 500 에러로 거부됨 → 기능 자체가 비활성화된 것으로 판단하고 **이 경로는 폐기**.
   *판단 근거*: 추가 우회를 시도하지 않고 "비활성" 결론을 내린 것은, 공개 취약점에 매달리기보다 서비스 고유의 약점을 찾는 방향 전환의 트리거가 됨.

3. **새 근거로 전환: 서비스 고유 입력**
   FTP에서 확보한 `.env`(이중 Base64 디코딩 필요)로 Grafana Viewer 계정을 얻고, 대시보드 링크를 따라가 **이 서비스만 갖고 있는 내부 도구** `/ops-status/`를 발견. 그 중 `admin/last-login-sort` 엔드포인트가 정렬 파라미터를 그대로 처리하는 것으로 보아 2차(stored) SQL Injection 가능성을 새 근거로 설정 (E05).

4. **검증**
   이 SQLi 경로로 나왔다는 `svc-monitor` 계정의 bcrypt 해시(cost factor=4, 의도적으로 약하게 설정)를 hashcat(mode 3200, rockyou.txt)으로 직접 크랙 → 평문 획득 (약 18분 소요). 이 평문으로 실제 로그인 요청을 보내 관리자 전용 "Internal Monitor" UI 진입을 **직접 확인** (E06, E07). SQLi 자체의 존재는 힌트 기반이지만, 그 결과물(해시→평문→로그인 성공)은 자체 검증된 사실이므로 이 체인을 근거로 다음 단계를 진행.

5. **확보 — 내부 기능과 저장소 단서**
   `Internal Monitor`가 `target=host:port&path=...` 형태로 서버측 아웃바운드 요청(SSRF)을 수행함을 `ConnectTimeoutError` 스택트레이스로 직접 확인 (E08). 이를 이용해 `127.0.0.1:9091/admin/dump-config`를 조회 → 응답 JSON의 `hint` 필드가 실제 백업 파일 경로(`backups/cj-ops-ci.bak`)를 지시 (E09).
   다운로드 엔드포인트의 경로 필터는 단순 `../`만 차단 → `....//`(중첩 점 표기)로 우회 성공, 백업 파일에서 **GitHub Personal Access Token**을 확보 (E10, E11).

6. **Handoff → Stage 2**
   PAT로 GitHub API 인증 시 `private: true` 저장소에 대해 admin/maintain/push 등 전권을 확인. 커밋 히스토리의 `chore: point CI deploy target at 3.37.135.243` 커밋에서 **Stage 2 배포 IP(3.37.135.243)**를 확정 (E12, E13).

---

## STAGE 2 — Gateway + 업로드 서비스 (3.37.135.243:30082)

| 단계 | 내용 |
|---|---|
| **막힌 가설** | `/upload` 경로 직접 접근 시 404·연결 불가(포트 필터링, SSRF 경유 타임아웃) |
| **새 근거** | GitHub 저장소(private-test)의 실제 배포 메타데이터를 재조회해 **버전이 붙은 실제 배포 컨텍스트**(`/upload-1.0.0/upload.action`)를 재식별 |
| **검증** | 비실행 Proof 파일을 1회만 업로드해 쓰기 가능 여부를 확인 |
| **확보** | Root 권한(uid=0) 및 다음 저장소 단서 확보 |
| **Handoff** | Stage 3 대상(13.125.104.131) 정보로 연결되는 두 번째 저장소 단서 확보 |

### 상세 흐름

1. **막힌 가설: `/upload` 404 / 접속 불가**
   Stage 1에서 얻은 힌트(`/upload/upload.action`, 포트 30082)로 SSRF 경유 접속을 시도했으나 `ConnectTimeoutError`(E04), 직접 재시도에서도 `Connection refused`가 1회 관측된 뒤 이후 요청은 전부 무응답(`000`)으로 재현 불가 (E05, E06). **막힌 가설: 알려진 경로 그대로는 서비스가 응답하지 않는다.**

2. **새 근거: 실제 배포 컨텍스트 재식별**
   Stage 1에서 확보한 PAT로 `private-test` 저장소의 `pom.xml`을 조회 → 이 애플리케이션이 Struts 기반이며 **artifact 이름=`upload`, 버전=`1.0.0`**임을 확인. Tomcat/Struts는 WAR 배포 시 `war_context_path`가 `/upload-1.0.0`이 되는 구조이므로, 힌트로 받은 `/upload/upload.action`이 아니라 **실제로는 `/upload-1.0.0/upload.action`**이 진짜 경로라는 새 근거를 도출 (S2-01, E07: Jenkinsfile로 CI 배포 파이프라인 교차 확인).

3. **검증 — Gateway 헬스체크 및 컨텍스트 확인**
   `/health` 200 OK, `/upload-1.0.0/upload.action` 프로브 성공(Tomcat 9.0.121, multipart/form-data 폼 구조 확인) (S2-02, E08).

4. **검증 — 쓰기 1회 실행 (S2-067 / CVE-2024-53677)**
   Struts `FileUploadInterceptor` 파일명 injection(CVE-2024-53677) 취약점에 대해 **비실행 Proof 파일을 정확히 1회만 업로드**하는 절제된 방식으로 검증 (재실행 금지 원칙 적용, S2-03). 업로드는 200 OK로 성공했으나, 후속 검증(`/verify.jsp`, `/upload-1.0.0/verify.jsp`)에서 Struts2 인터셉터가 경로 구분자를 제거해 파일이 `webapps/` 최상위에 basename으로만 저장됨을 확인 — **이 업로드 경로 자체는 웹에서 실행 가능한 RCE가 아님을 반증**했다 (E10, `[반증됨]`). 즉 "파일 쓰기는 된다"는 사실만 확정하고, "웹으로 실행된다"는 결론은 폐기.

5. **확보 — Root 권한 (self-delete JSP 방식)**
   쓰기 자체는 가능하다는 사실을 바탕으로, 흔적을 남기지 않는 **자가 삭제(self-delete) JSP** 1회 실행으로 실행 계정을 확인 → `uid=0`(root), 작업 디렉터리 `/usr/local/tomcat` 확인 후 즉시 자가 삭제하여 지속성 없음을 보장 (S2-04). Stage 2 로컬 flag는 발견되지 않음.

6. **Handoff → Stage 3**
   환경 토폴로지 확인(S2-05) 결과 별도 secret/data/challenge 볼륨은 없었고, 인접 서비스(`struts-app`, `gateway`)만 확인. 대신 GitHub 조사 과정에서 **`private-test2` 저장소**가 다음 단계 진입점으로 지목되었고, 이를 통해 **Stage 3 대상(13.125.104.131:30083)**으로 연결됨.

---

## STAGE 3 — Webmail + WAF (13.125.104.131:30083)

| 단계 | 내용 |
|---|---|
| **막힌 가설** | RCE 페이로드를 실행해도 **결과 파일이나 stdout으로 직접 증명(Proof)할 방법이 없음** (Blind RCE) |
| **새 근거** | 명령 실행 시간에 따른 **응답 지연(Timing) 차이**를 관찰 채널로 활용 |
| **검증** | `sleep N` 명령의 실행 시간을 baseline과 비교해 RCE를 수학적으로 증명 (Timing Proof) |
| **확보** | RCE 확정 → sudo 오분류(GTFOBins) 경유 **Root 권한 확보** |
| **최종 가능성** | RCE + Root 권한 확보, Flag 파일까지 도달 (콘텐츠 반출은 blind RCE 한계로 별도 처리) |

### 상세 흐름

1. **정찰**
   GitHub 태그의 어노테이트 메시지("urgent fix on 13.125.104.131 after alert")로 대상 발견 (E01). 30083 포트만 열려 있고 Roundcube 1.6.10 로그인 페이지, `/health` 응답으로 **WAF 게이트웨이(`cj-webmail-waf`) 존재**를 확인 (E02, E03). 테스트 계정 MD5 해시를 크랙해(`testpass`) 로그인 성공, Inbox 진입 (E04, E05).

2. **가젯 재검토**
   초기에는 `enigma` 플러그인이 비활성으로 보여 CVE-2025-49113의 `Crypt_GPG_Engine` 가젯을 못 쓴다고 판단했으나, GitHub의 `composer.json-dist`를 직접 조회해 `pear/crypt_gpg`가 **플러그인이 아니라 코어 의존성**임을 확인 → "가젯 사용 불가"라는 이전 결론을 정정 (E06, E07).

3. **PoC 검증 및 WAF 우회**
   공개 PoC 3종을 비교해 오탈자(`O:17:` → 올바른 `O:16:`)와 따옴표 이스케이프 누락 버그를 찾아내고, 원저자(fearsoff)의 `serialize()` 기반 PoC를 최종 채택 (E08~E10). `_from` 파라미터 이중 전송과 `Content-Disposition` 속성 순서/대소문자 변경 기법으로 WAF를 우회해 403 → 200 OK로 페이로드를 무결하게 전달 (E11).

4. **막힌 가설: 결과 파일 Proof 없음**
   RCE 페이로드(`fearsoff_exploit.php`)는 명령을 실제로 실행시키지만 **stdout을 응답으로 반환하지 않는다.** 파일 쓰기로 결과를 증명하려 했으나 웹 루트(`/var/www`)에 도달하지 않아 HTTP로 직접 확인할 방법이 없었음 — "실행됐다는 증거를 눈으로 볼 수 없다"는 막다른 지점.

5. **새 근거: 응답·Timing 차이**
   명령 실행이 서버 응답 시간에 비례해 지연을 만든다는 점에 착안, `sleep N` 명령을 페이로드에 실어 **응답 지연 자체를 오라클(oracle)로 사용**하는 방향으로 전환.

6. **검증: Timing Proof**
   `true`(baseline) = 0.519s, `sleep 3` = 3.558s, `sleep 7` = 7.422s로 **선형적으로 스케일링**함을 확인 (E12) → Blind RCE를 수치로 확정. 이후 오라클 자체의 버그 2건(`<` 리다이렉션이 명령을 깨뜨림, 크기 기반 판정의 false-positive)을 순차로 격리·수정해 오라클 신뢰도를 높였다 (E13, E14).

7. **확보: 권한 상승 → Root**
   실행 계정이 `www-data`(root 아님, webroot 쓰기 불가)임을 timing 오라클로 확인 (E15). `sudo -n -l`로 `find`가 NOPASSWD로 등록된 것을 확인(팀원 힌트 → 자체 재현, E16) 후 GTFOBins의 `find -exec sh` 기법 적용.
   1차 시도(E17)는 sleep이 발생하지 않아 원인 불명 상태였으나, `-exec` 구조 자체를 무조건 sleep으로 재검증(E17b, 6.252s 정상 확인)한 뒤, **uid 값에 따라 다른 sleep 시간을 분기**시키는 조건부 페이로드로 재시도 →
   `3.580s` 응답 → `uid==0` 구간(3초)에 정확히 매칭, 6/9/12초 구간과 명확히 구분됨 → **root 권한 획득을 timing 사이드채널로 최종 확정** (E17c).

8. **최종 가능성: Flag 위치 및 한계**
   root 권한으로 `/usr/share -maxdepth 2` 트리 탐색을 timing 오라클로 반복해 flag 파일 위치를 특정(E18~E25), `cat + base64` 인코딩까지 서버 `/tmp`에 저장 완료(E26~E31). 다만 **blind RCE 특성상 인코딩된 내용을 HTTP 응답으로 직접 회수할 방법이 없어**, 콘텐츠 자체의 로컬 반출은 별도 채널(웹 접근 가능한 경로 확보 등)이 필요한 상태로 남았다. AWS 환경변수 존재는 확인했으나(E33) 값 포맷 미확인으로 Stage 4 자격증명 준비는 부분 완료(E34)로 종료.

---

## 요약 — Stage 간 연결 논리

```
Stage 1: 공개 CVE 실패 → 서비스 고유 입력(SQLi) → 해시 크랙·로그인 검증
          → SSRF·Path Traversal로 GitHub PAT 확보 → Stage 2 IP 확정

Stage 2: 힌트 경로 404 → GitHub pom.xml로 배포 컨텍스트 재식별(/upload-1.0.0)
          → 비실행 Proof 1회 업로드로 쓰기 가능성 검증(RCE 경로는 반증)
          → self-delete JSP로 uid=0 확인 → private-test2 저장소로 Stage 3 연결

Stage 3: Blind RCE(결과 확인 불가) → sleep 기반 Timing Proof로 실행 확정
          → 오라클 버그 2건 수정 → sudo find(GTFOBins) uid 분기 timing으로 Root 확정
          → Flag 위치 특정 및 서버측 인코딩까지 완료
```

각 Stage는 "처음 세운 가설이 막혔다"는 사실 자체를 버리지 않고, **왜 막혔는지에서 다음 근거를 역산**해 다음 Stage로 넘어가는 방식으로 진행되었다. 이 과정에서 팀원 힌트와 자체 검증을 구분해 태깅(`[자체 확인]`/`[팀원 힌트]`/`[재현 필요]`/`[반증됨]`)한 것이, 어느 지점이 "확정"이고 어느 지점이 "가정"인지를 추적 가능하게 만든 핵심 장치였다.

---

## 참고 원본 문서
- Stage 1: `C:\HTB\CJ_CTF\43.200.51.235\Stage1-Writeup.md`, `43.200.51.235\notes\evidence-index.md`
- Stage 2: `3.37.135.243\WRITEUP_STAGE2.md`, `3.37.135.243\notes\evidence-index.md`
- Stage 3: `C:\HTB\CJ_CTF\13.125.104.131\WRITEUP_STAGE3.md`, `13.125.104.131\notes\evidence-index.md`
