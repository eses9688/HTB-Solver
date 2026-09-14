# A. 작성 전 증적 감사

**종합 판정: READY**

머신명(Meow), 대상 IP(`10.129.59.55`), 공격 체인(포트 스캔 → telnet 익명/기본 root 접속 → 즉시 root 권한 확인 → 플래그 획득)이 처음부터 끝까지 일관되며, 각 전환 단계에 원본 로그 형태의 직접 증적이 존재한다. 별도의 사용자 권한 획득이나 권한 상승 단계가 없는 구조(telnet 로그인 자체가 root)이므로 해당 절은 "해당 없음"으로 표시한다.

## 1. 차단 항목

없음.

## 2. 경고 항목

1. VPN 트러블슈팅 과정(Machines 풀 → Starting Point 풀 전환)에서 대상 IP가 `10.129.59.45` → `10.129.59.55`로 변경되었다. 초기 IP(`10.129.59.45`)에 대한 스캔 결과는 실제로 도달 불가능했던 상태였으므로 본 문서의 정보 수집·공격 단계에는 포함하지 않고, 12절(트러블슈팅)에서만 다룬다.
2. 본 문서의 nmap/telnet 원본 로그는 최초 플래그 획득 직후 재현을 통해 다시 캡처한 것이다(최초 실행 시 파일로 저장하지 않았음). 재현 시점과 최초 성공 시점의 root flag 값은 동일함을 확인했다.

## 3. 자동 정규화 항목

- 대상 IP `10.129.59.55`는 본문에서 `$TARGET`으로 표기한다.
- 공격자 VPN IP `10.10.14.221`은 본문에서 `$LHOST`로 표기한다.

## 4. 자료 목록

- `scans/E01_nmap_full_tcp.txt` — 전체 TCP 포트 스캔 원본
- `scans/E02_nmap_p23_service.txt` — 23/tcp 서비스 스캔 원본
- `logs/E03_telnet_root_access.log` — telnet 세션 원본 로그(root 로그인, `id`, `hostname`, flag 확인)
- `loot/flags.md` — 획득한 flag (PRIVATE_STUDY)

## 5. 공격 체인 완전성 표

| 단계 | 주장 | 필요 증적 | 확인된 증적 | 상태 |
|------|------|-----------|--------------|------|
| 열거 | 23/tcp(telnet) 외 열린 포트 없음 | 전체 포트 스캔 | E01 | 확인됨 |
| 초기 접근 | telnet에 `root` 계정, 비밀번호 없이 로그인 가능 | 로그인 세션 로그 | E03 | 확인됨 |
| 사용자 권한 | 해당 없음 (로그인 즉시 root) | — | — | 해당 없음 |
| 권한 상승 | 해당 없음 (로그인 즉시 root) | — | — | 해당 없음 |
| root 최종 검증 | 로그인한 계정이 실제 root(uid=0) | `id` 출력 | E03 | 확인됨 |

## 6. 이미지/증적 경로 검사

이미지 증적 없음(전 과정 텍스트 로그로만 증적 확보). 스크린샷을 사용하지 않았으므로 해당 검사 대상 없음.

## 7. 세션 종속 값 및 민감 정보 검사

- `$TARGET`(10.129.59.55), `$LHOST`(10.10.14.221)는 본 세션에 한정된 값으로 표시했다.
- VPN 프로필 파일 경로 및 내용은 본문에 포함하지 않았다.
- HTB 계정 정보, VPN 인증서/키 내용은 기록하지 않았다.

## 8. 취약점 분류 검사

- 분류: **4. 자격 증명 재사용 또는 운영 보안 실패** — 정확히는 "위험한 서비스 구성"(암호화되지 않은 telnet 노출 + 인증 없는/공백 비밀번호 root 계정)에 해당한다. 공개 CVE 아님, 자체 구현 결함 아님.

## 9. 스크립트 존재 여부

본문에서 언급하는 `scripts/`는 없다(별도 익스플로잇 스크립트를 작성하지 않고 표준 도구인 nmap, telnet만 사용했다). 부록 A는 "해당 없음"으로 남긴다.

## 10. 추가로 필요한 증적

없음. 초기 접근부터 root 검증까지 직접 증적이 모두 확보되었다.

---

# B. 최종 Write-up

```yaml
---
title: "HTB Meow Write-up"
machine: "Meow"
platform: "Hack The Box"
os: "Linux"
difficulty: "Very Easy"
date_started: "2026-08-14"
date_completed: "2026-08-14"
writeup_mode: "PRIVATE_STUDY"
status: "Completed"
tags:
  - htb
  - cybersecurity
  - writeup
---
```

# HTB Meow Write-up

## 0. 문서 범위 및 주의사항

이 문서는 사용자가 명시적으로 지정한 HTB Starting Point 머신 `Meow`(대상: `$TARGET`)에 대한 개인 학습용 풀이 기록이다. 해당 랩 환경 외의 시스템은 다루지 않는다. `writeup_mode: PRIVATE_STUDY`이므로 본 머신에 한정된 root flag 값을 loot 파일에 별도 보관한다.

## 1. 개요

Meow는 HTB Starting Point Tier 0의 Very Easy Linux 머신이다. 전체 포트 스캔 결과 telnet(23/tcp) 서비스 하나만 노출되어 있으며, 해당 telnet 데몬은 `root` 계정에 비밀번호 없이 로그인을 허용하는 구성 결함을 가지고 있다. 별도의 익스플로잇 없이 서비스 자체의 잘못된 구성만으로 즉시 root 권한을 획득할 수 있다.

## 2. 공격 흐름

```mermaid
flowchart LR
    A[전체 TCP 포트 스캔] --> B[23/tcp telnet 확인]
    B --> C[telnet 접속]
    C --> D["root 계정, 비밀번호 없이 로그인"]
    D --> E["id로 uid=0 확인"]
    E --> F["/root/flag.txt 획득"]
```

한 줄 공격 체인: 전체 포트 스캔 → telnet(23) 확인 → `root` 계정 무인증 로그인 → root flag 획득.

## 3. 실습 환경

- `$TARGET` = `10.129.59.55`
- `$DOMAIN` = 해당 없음
- `$LHOST` = `10.10.14.221` (HTB Starting Point VPN, `tun0`)
- 사용 도구: `nmap` 7.99, `telnet`(GNU inetutils), `expect`(세션 자동화 및 로그 캡처용)
- 실행 환경: Windows 11 + WSL2 Kali Linux, HTB Starting Point OpenVPN(UDP, US StartingPoint 2)

## 4. 공격 표면 요약

- 노출 서비스: 23/tcp telnet(Linux telnetd) 단 하나.
- 인증되지 않은 원격 서비스이며 암호화되지 않은 평문 프로토콜이다.

## 5. 정보 수집

### 목표

대상에 노출된 전체 서비스 목록을 확인한다.

### 관찰 및 가설

새로 spawn/reset된 Starting Point 머신이므로 열린 포트가 제한적일 것으로 예상했다.

### 검증 명령 또는 요청

```bash
nmap -sT -p- --min-rate 3000 -Pn $TARGET
```

### 핵심 결과

```text
PORT   STATE SERVICE
23/tcp open  telnet
```

전체 65535개 TCP 포트 중 23/tcp만 open, 나머지는 전부 closed로 확인되었다.

### 성공 판정

전체 포트 범위를 스캔했고 결과가 명확히 재현 가능하므로 유효한 정보 수집으로 판정한다.

### 취약점 원인과 공격 조건

해당 없음(정보 수집 단계).

### 해석과 다음 결정

단일 서비스(telnet)만 공격 표면에 해당하므로 해당 서비스의 배너와 인증 방식을 확인한다.

### 증적

E01 — `scans/E01_nmap_full_tcp.txt`

---

### 목표

23/tcp 서비스의 세부 정보(버전, 배너)를 확인한다.

### 검증 명령 또는 요청

```bash
nmap -sT -sV -sC -p 23 -Pn $TARGET
```

### 핵심 결과

```text
PORT   STATE SERVICE VERSION
23/tcp open  telnet  Linux telnetd
```

### 성공 판정

서비스가 Linux 표준 telnetd로 확인되어, 다음 단계로 직접 접속을 시도할 근거가 마련되었다.

### 해석과 다음 결정

telnet은 기본적으로 인증 절차(로그인 프롬프트)를 거치므로, 우선 흔한 기본/무결 자격 증명(`root`, 빈 비밀번호)으로 접속을 시도한다.

### 증적

E02 — `scans/E02_nmap_p23_service.txt`

## 6. 초기 접근

### 목표

telnet 서비스에 유효한 자격 증명으로 로그인 가능한지 확인한다.

### 관찰 및 가설

Very Easy 난이도 머신에서 인증 없는 telnet 노출은 흔히 관리자 계정의 잘못된 초기 구성(빈 비밀번호)과 결합된다는 가설을 세웠다.

### 검증 명령 또는 요청

```bash
telnet $TARGET
```

로그인 프롬프트에서 `root` 입력, 비밀번호 프롬프트 없이 바로 셸 진입 여부를 확인했다.

### 핵심 결과

```text
Meow login: root
...
root@Meow:~# id
uid=0(root) gid=0(root) groups=0(root)
root@Meow:~# hostname
Meow
```

### 성공 판정

비밀번호 입력 절차 없이 `root` 셸(`root@Meow:~#`)에 직접 진입했고, `id` 출력이 `uid=0(root)`임을 직접 확인했다. 연결 성립 자체가 아니라 실제 셸 권한을 근거로 성공을 판정했다.

### 취약점 원인과 공격 조건

- 원인: telnetd가 `root` 계정에 비밀번호 인증 없이 로그인을 허용하도록 구성됨.
- 공격 조건: 대상 네트워크(HTB VPN)에 도달 가능하고 23/tcp에 접근할 수 있으면 별도 조건 없이 성립한다.
- 분류: 위험한 서비스 구성 / 자격 증명 부재(운영 보안 실패). 공개 CVE 아님.

### 해석과 다음 결정

로그인 즉시 root 권한이므로 별도의 사용자 권한 획득이나 권한 상승 단계가 필요하지 않다. 바로 목표 파일(`/root/flag.txt`)을 확인한다.

### 증적

E03 — `logs/E03_telnet_root_access.log`

## 7. 사용자 권한 획득

해당 없음 — telnet 로그인이 곧바로 root 권한을 부여한다.

## 8. 권한 상승 열거

해당 없음.

## 9. 권한 상승

해당 없음.

## 10. 권한 및 신뢰 경계 전환

해당 없음. 단일 telnet 세션 내에서 초기 접근과 root 검증이 동시에 이루어졌다.

## 11. 취약점 요약

| 항목 | 내용 |
|------|------|
| 분류 | 위험한 서비스 구성 (telnet + 무인증 root) |
| CVE | 해당 없음 |
| CWE 후보 | CWE-306 (Missing Authentication for Critical Function) — `[추론]`, 공식 매핑 미확인 |
| 공격 조건 | 대상 23/tcp 도달 가능, `root` 계정에 비밀번호 없음 |
| 영향 | 원격 미인증 root 셸 획득 |
| 증적 | E01, E02, E03 |

## 12. 실패한 접근과 트러블슈팅

같은 세션에서 처음 시도한 대상 `10.129.59.45`는 "Machines" VPN 풀(AU Machines 2)에 연결한 상태에서 전 포트가 filtered로 나타났고, ICMP도 VPN 게이트웨이(`10.10.14.1`)로부터 즉시 "Destination Host Unreachable"을 받았다. 머신을 리셋해 IP가 `10.129.59.55`로 바뀐 뒤에도 동일 증상이 재현되어, 단순 부팅 지연이 아님을 확인했다.

HTB 웹 대시보드에서 VPN 연결 패널을 확인한 결과 Meow는 "Starting Point" 풀(서버: US StartingPoint 2) 소속이었으나, 실제 연결된 세션은 "Machines" 풀(AU Machines 2)이었다. 두 풀의 사설 IP 대역이 겹쳐 보여 혼동했으나 실제로는 서로 다른 VPN 게이트웨이였다. Starting Point용 `.ovpn` 프로필을 새로 받아 재연결한 후(`$LHOST` = `10.10.14.221`) 정상적으로 ICMP 응답 및 23/tcp 접근이 확인되었다.

- `[확인됨]` 원인: 잘못된 VPN 풀(Machines)에 연결된 상태로 Starting Point 대상에 접근을 시도함.
- `[확인됨]` 해결: Starting Point 전용 VPN 프로필로 재연결.

## 13. 실습 중 생성한 흔적과 정리

- 대상 시스템에는 파일을 업로드하거나 계정/스케줄 작업을 생성하지 않았다. `cat`, `id`, `hostname` 조회만 수행했다.
- 로컬(Kali WSL)에 임시로 생성한 `/mnt/c/HTB/Meow/` 하위 로그·스캔 파일은 본 문서의 정식 증적으로 보존한다(삭제 대상 아님).
- VPN 프로필 파일(`machines_au-2.ovpn`, `starting_point_us-2.ovpn`)은 로컬 `~/HTB/vpn/`에 남아 있으며 이 문서에는 내용을 포함하지 않았다. `[권장 정리]` 학습 종료 후 불필요한 VPN 프로필은 사용자가 직접 정리 여부를 판단한다.

## 14. 탐지 및 대응

- 근본 원인: telnet 서비스에서 `root` 계정이 비밀번호 없이 인증을 통과하도록 구성됨.
- 단기 완화: `root`의 원격 로그인을 비활성화하거나 강력한 비밀번호를 설정한다.
- 근본 수정: 평문 프로토콜인 telnet 서비스를 비활성화하고 SSH 등 암호화된 관리 채널로 대체한다. 관리자 계정의 원격 직접 로그인을 금지하고 개별 계정 + `sudo`로 전환한다.
- 탐지 가능한 흔적: telnetd 접속 로그(`utmp`/`wtmp`, `auth.log` 등)에 남는 `root` 원격 로그인 이벤트. 네트워크 IDS에서 평문 telnet 트래픽 자체를 이상 징후로 탐지할 수 있다.

## 15. 핵심 학습 포인트

1. 전체 포트 스캔(`-p-`)을 먼저 수행해 기본 상위 포트 스캔에서 누락될 수 있는 서비스를 확인하는 습관이 중요하다.
2. telnet처럼 오래된 프로토콜이 열려 있으면 우선적으로 무인증/기본 자격 증명 로그인을 시도해볼 가치가 있다.
3. HTB에서 "Machines"와 "Starting Point"는 서로 다른 VPN 풀이며, IP 대역이 겹쳐 보여도 실제로는 별개의 게이트웨이로 라우팅된다는 점을 확인했다.
4. VPN 게이트웨이가 즉시 "Destination Host Unreachable"을 반환하면 로컬 라우팅보다 VPN 풀/서버 매칭 여부를 먼저 의심해야 한다.
5. `sudo` 비밀번호가 필요한 자동화는 비대화형 셸에서 멈추므로, 그런 명령은 사용자가 직접 실행 가능한 대화형 세션(tmux 등)으로 안내하는 편이 안전하고 확실하다.

## 16. 참고 자료

이번 문제 해결에는 외부 CVE/보안 공지 검증이 필요하지 않았다(공개 CVE 아님). HTB 자체 트러블슈팅 문서(Connection Troubleshooting, help.hackthebox.com)를 참고해 VPN 관련 증상(다중/orphan TUN 인터페이스, 재연결 시 새 DHCP 리스 등)을 대조했으나, 최종 원인은 문서에 명시된 시나리오가 아니라 잘못된 VPN 풀 연결로 확인되었다.

## 부록 A. 사용한 스크립트

해당 없음. 표준 도구(nmap, telnet, expect)만 사용했으며 별도 익스플로잇/자동화 스크립트를 작성하지 않았다.

## 부록 B. 원본 스캔 및 응답

- `scans/E01_nmap_full_tcp.txt`
- `scans/E02_nmap_p23_service.txt`
- `logs/E03_telnet_root_access.log`

## 부록 C. 증적 목록

`notes/evidence-index.md` 참고.
