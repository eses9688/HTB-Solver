# Lab1 — ES-Ops Grafana (Easy / Single Stage)

## 시나리오

ES 인프라팀이 운영 중인 모니터링 대시보드가 외부에 노출되어 있는 것으로 추정된다.
접근 가능 여부와 정보 노출 수준을 점검하라.

- 대상: `<VM_외부_IP>:3000`
- 난이도: Easy
- 스테이지: 1개 (단일 flag, 다만 익스플로잇은 다단계)

## 공격 체인

1. **버전 확인**: `/api/health` 등 미인증 엔드포인트로 Grafana 8.3.0임을 확인.
2. **CVE 검증**: Grafana 8.0.0-beta1~8.3.0에 존재하는 **CVE-2021-43798**(미인증 경로 순회 → 임의 파일 읽기)임을 확인.
3. **익스플로잇**: 내장 플러그인 경로(`/public/plugins/alertlist/`)를 통한 경로 순회로 `/etc/grafana/grafana.ini`를 미인증 상태로 읽는다.

   ```bash
   curl --path-as-is \
     "http://<TARGET>:3000/public/plugins/alertlist/../../../../../../../../etc/grafana/grafana.ini"
   ```
4. **자격증명 추출**: 읽어낸 `grafana.ini`의 `[security]` 섹션에서 평문 `admin_password` 확보.
5. **로그인**: 해당 자격증명으로 Grafana 관리자 로그인.
6. **flag 획득**: `ES-Ops Internal Notes` 대시보드에서 flag 확인.

## 구성

- `grafana/grafana:8.3.0` — CVE-2021-43798에 실제로 취약한 버전. 전용 Docker 브리지 네트워크(`lab1-net`)에 격리.
- 관리자 계정은 환경변수가 아니라 **평문 자격증명이 든 `config/grafana.ini`**로 부팅(CWE-256/CWE-798류 설정 노출과 CVE를 함께 학습).
- 로그인 성공 시 `ES-Ops Internal Notes` 대시보드에서 flag 확인 가능.

## 배포 방법

```bash
cd ES_Lab/lab1
docker compose up -d
```

## 초기화(재시작) 방법

```bash
cd ES_Lab/lab1
docker compose down -v
docker compose up -d --force-recreate
```

flag와 취약점은 모두 고정 구성이므로 몇 번을 초기화해도 동일하게 재현됩니다.

## 정답 확인 (Instructor 전용)

- 익스플로잇 후 확보되는 자격증명: `admin` / `Es0psTemp!2026` (`config/grafana.ini`에 정의)
- flag: `esfg{V2VsbCBkb25lISBFUy1PcHMgTGFiMSBjbGVhci4=}` (base64 디코딩 → `Well done! ES-Ops Lab1 clear.`)

## Flag 형식

```
esfg{<base64로 인코딩된 완료 문구>}
```

lab1은 단일 스테이지이므로 flag는 다음 단계 힌트가 아니라 점검 완료를 축하하는 고정 문구입니다.

## 필요 기술스택

- 서비스 버전 핑거프린팅 (HTTP 헤더, `/api/health` 등)
- 공개 CVE 리서치 및 적용 조건 판단 (CVE-2021-43798)
- 경로 순회(Path Traversal) payload 작성, `curl --path-as-is` 등 URL 정규화 우회
- 설정 파일에서 자격증명 파싱, 웹 로그인
- Grafana 대시보드 UI/API 구조에 대한 기본 이해

## 참고

- `grafana.ini`의 관리자 비밀번호 값은 학생에게 직접 공개하지 않아야 CVE 익스플로잇 학습 효과가 유지됩니다.
- 이 컨테이너는 다른 랩 네트워크와 전혀 연결되어 있지 않습니다. lab2/lab3와 자격증명·네트워크를 공유하지 않습니다.
- 참고: [CVE-2021-43798 공식 GitHub Security Advisory](https://github.com/grafana/grafana/security/advisories/GHSA-8vwj-jr6f-8m3g)
