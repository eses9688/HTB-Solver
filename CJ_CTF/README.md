# CJ 체인 (다단계 피벗)

- 플랫폼: 승인된 다단계 침투테스트 체인 (CJ 체인)
- 구성: 4개 IP를 순차 피벗하는 체인(Stage 1~4) + 별도 병렬 타깃(13.209.81.83)
- 컨벤션: 단일 대상 기본값은 [`AGENTS.md`](../AGENTS.md), 체인 전용 확장은 [`PROCESS.md`](../PROCESS.md) 참고

## Stage 현황

| Stage | 대상 | 상태 | Write-up |
|---|---|---|---|
| 1 | 43.200.51.235 | 진행중 (Stage 1 자체 침투는 완료, 2차 SQLi는 [팀원 힌트·재현 필요]) | [43.200.51.235/Stage1-Writeup.md](43.200.51.235/Stage1-Writeup.md) |
| 2 | 3.37.135.243 | Completed | [3.37.135.243/WRITEUP_STAGE2.md](3.37.135.243/WRITEUP_STAGE2.md) |
| 3 | 13.125.104.131 | Completed (root 권한 확보) | [13.125.104.131/WRITEUP_STAGE3_KO.md](13.125.104.131/WRITEUP_STAGE3_KO.md) |
| 4 | AWS (DynamoDB PII) | 진행중 (Stage 3 산출 자격 증명 전달 지연으로 실행 차단, 분석은 완료) | [AWS/README.md](AWS/README.md) |

## 폴더 구조

```
CJ_CTF/
├── 43.200.51.235/    # Stage 1 — FTP → 자격증명 → Grafana → SSRF → Path Traversal → GitHub PAT
├── 3.37.135.243/     # Stage 2 — CVE-2024-53677(Struts) 임의 파일 쓰기 → root
├── 13.125.104.131/   # Stage 3 — CVE-2025-49113(Roundcube 역직렬화) → root
└── AWS/              # Stage 4 — SigV4 서명 → S3 → DynamoDB PII 분석
```

> 별도 타깃이었던 `13.209.81.83`(SNOJC Reports — SSRF/IMDS 챌린지)는 같은 문제를 처음부터 다시 푼 [`RedLab/`](../RedLab/README.md)과 동일 대상으로 확인되어 그쪽으로 병합했다. 이 세션 고유 증적은 [`RedLab/session2_cjctf_merge/`](../RedLab/session2_cjctf_merge/)에 보존.

각 대상 폴더는 자체 `scans/`, `http/`, `logs/`, `scripts/`, `loot/`, `notes/` 하위 구조와 write-up을 가진다. 세부 컨벤션은 [`PROCESS.md`](../PROCESS.md) 참고.
