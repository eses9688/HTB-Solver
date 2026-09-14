# HTB Nimbus

- 플랫폼: Hack The Box — Machines
- 난이도: Unknown · Linux
- 상태: 진행중 (root/user flag 미획득)
- Write-up: [HTB_Nimbus_Writeup.md](HTB_Nimbus_Writeup.md)

## 폴더 구조

- `scans/` — nmap 원본 결과 (E01, E02)
- `http/` — `/jobs/preview` SSRF 탐색·필터 우회·LocalStack S3/SQS 관련 원본 요청/응답 (E03~E37)
- `scripts/` — SSRF 우회, 내부망 스캔, SQS/CodeBuild/Lambda 피벗 시도 스크립트 (E13~E50)
- `notes/` — 비어 있음 (증적 인덱스 미작성)
- `logs/` — 비어 있음
- `artifacts/` — 비어 있음
- `loot/` — 비어 있음 (flag/자격 증명 미확보)
- `attachments/` — 비어 있음 (스크린샷 없음)

## 진행 요약

`/jobs/preview`의 URL 미리보기 기능(SSRF)이 쿼리스트링에 `?x=.yaml`을 붙이는 방식으로 확장자·내부 IP 필터를 우회당해, 도커 내부망의 LocalStack S3 API(172.18.0.2:4566)까지 도달했다. 이를 통해 `nimbus-dev-artifacts` 버킷의 `worker.py` 소스를 확보해, SQS 메시지의 `script` 필드가 그대로 `python3 -c`로 실행되는 RCE 구조를 확인했다. 그러나 SSRF 경유로 SQS `SendMessage`를 실제로 호출하는 방법을 찾지 못했고(모든 위조 시도가 S3 응답으로 귀결), 이후 사용된 AWS 임시 자격 증명은 출처 증적이 없어 CodeBuild/Lambda 피벗 시도의 유효성도 확인할 수 없다. 자세한 내용과 막힌 지점은 Write-up의 "다음 시도할 것 / 막힌 지점" 절을 참고.
