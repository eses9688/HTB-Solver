# HTB-Solver

Hack The Box 머신/챌린지 및 승인된 침투테스트 실습에 대한 개인 풀이 저장소.
각 대상을 독립된 폴더로 관리하며, 정찰부터 권한 상승까지의 과정을 증적(evidence) 단위로 남긴다.

## 이 저장소가 하는 것

- 대상별 write-up과 원본 증적(스캔 로그, HTTP 요청/응답, 익스플로잋 스크립트, 획득한 flag)을 한 곳에 정리
- 모든 신규 산출물에 `E01`, `E02`... 순번을 부여해 `notes/evidence-index.md`에서 추적 가능하게 함
- 다단계 피벗이 있는 체인 작업은 상위 폴더에 대상 간 관계를 기록

## 폴더 구조

```
HTB-Solver/
├── AGENTS.md                  # 단일 머신 write-up 컨벤션 (기본 하네스)
├── PROCESS.md                 # 다단계 체인(CJ_CTF) 전용 컨벤션 — AGENTS.md 확장/이탈 사항
├── Meow/                      # HTB Machine — Very Easy — Completed
├── Cap/                       # HTB Machine — Easy — Completed
├── Abducted/                  # HTB Machine — Completed
├── Nexus/                     # HTB Machine — Completed
├── BedSide/                   # HTB Machine — 진행중
├── Nimbus/                    # HTB Machine — 진행중
├── Orion/                     # HTB Machine — 진행중
├── RedLab/                    # 챌린지 — 진행중
├── CJ_CTF/                    # 다단계 피벗 체인 (43.200.51.235 → 3.37.135.243 → 13.125.104.131 → AWS) + 13.209.81.83
└── ES_Lab/                    # 자체 제작 3단계 랩 (Grafana CVE / SSRF-IMDS / JWT+RCE+sudo) — Verified
```

각 폴더의 완료 여부는 해당 폴더의 `README.md`를 참고 — root/user flag를 확보하지 못한 대상은 상태를 `진행중`으로 명시한다.

각 대상 폴더는 아래 하위 구조를 따른다 (해당 사항이 있을 때만 생성):

| 폴더 | 내용 |
|---|---|
| `notes/` | 분석 노트, `evidence-index.md` |
| `logs/` | 세션/커맨드 원본 로그 |
| `scans/` | nmap 등 스캔 원본 결과 |
| `http/` | 웹 요청/응답, 캡처 |
| `scripts/` | 익스플로잋/자동화 스크립트 |
| `loot/` | 획득한 자격 증명, flag |
| `attachments/` | 스크린샷 등 첨부 증적 |
| `HTB_<이름>_Writeup.md` | 최종 write-up |

## 표기 규칙

증적에는 확인 수준을 태그로 남긴다.

- `[자체 확인]` — 직접 실행/응답으로 확보
- `[팀원 힌트]` — 전달받았으나 자체 미검증
- `[재현 필요]` — 시도했으나 미완료
- `[반증됨]` — 가설상 성립해 보였으나 실제 검증으로 부정됨

상세 컨벤션은 [`AGENTS.md`](AGENTS.md)(단일 머신 기본), 다단계 체인은 [`PROCESS.md`](PROCESS.md)를 참고.

## 주의

이 저장소는 승인된 실습/과제 환경만을 대상으로 하며 `PRIVATE_STUDY` 목적의 private 저장소다.
포함된 자격 증명·키 값은 실제 유효한 것은 마스킹 처리했고, 대상 IP·flag·테스트 계정 정보는 실습 목적상 그대로 남겨두었다.
