# ES Lab

Naver Cloud VM 위에 직접 설계·구축한 3단계 자체 제작 취약점 실습 랩. HTB처럼 남이 만든 문제를 푸는 대신, 시나리오 설계부터 Docker 기반 취약 서비스 구현, flag 삽입, 검증까지 전 과정을 직접 진행했다.

각 랩 폴더의 `README.md`는 시나리오·공격 체인·배포 방법을 담은 설계 문서(Instructor 전용, 답안 포함), `WRITEUP.md`는 실제 공격자 관점에서 처음부터 끝까지 검증한 공식 풀이 기록이다.

## 랩 목록

| 랩 | 난이도 | 스테이지 | 취약점 | 상태 | 문서 |
|---|---|---|---|---|---|
| Lab1 — ES-Ops Grafana | Easy | 1 | CVE-2021-43798 (Grafana 경로 순회 → 자격증명 평문 노출) | Verified | [README](lab1/README.md) · [WRITEUP](lab1/WRITEUP.md) |
| Lab2 — ES Customer Portal | Medium | 2 | IDOR → SSRF(블랙리스트 우회, 오픈 리다이렉트 체이닝) → 내부 IMDS 탈취 | Verified | [README](lab2/README.md) · [WRITEUP](lab2/WRITEUP.md) |
| Lab3 — ES DevOps Platform | Hard | 4 | JWT `alg:none` 위조 → 2차 SSRF 피벗 → 내부 RCE → `sudo` tar wildcard injection으로 root | Verified | [README](lab3/README.md) · [WRITEUP](lab3/WRITEUP.md) |

## 설계 원칙

- 스테이지가 올라갈수록 컨테이너 수·네트워크 분리·인증 계층이 늘어나도록 구성(Lab1: 단일 컨테이너 → Lab3: 3-컨테이너, 2차 SSRF 피벗 요구).
- 모든 취약점은 실제 CVE 또는 널리 알려진 설정 결함 패턴(IDOR, SSRF 필터 우회, JWT 위조, sudo wildcard injection)에 기반.
- flag는 base64(또는 이중 base64)로 인코딩된 고정 문구, 컨테이너 재생성 시에도 동일하게 재현되도록 고정 구성.
- 각 랩은 네트워크·자격증명·컨테이너 이름이 서로 완전히 분리되어 있어 독립적으로 실행/초기화 가능.

## 배포

랩별 폴더에서 `docker compose up -d`(Lab2/3은 `--build` 필요). 평소에는 컨테이너를 내려 포트를 비워둔다.
