# HTB Orion

- 플랫폼: Hack The Box — Machines
- 난이도: Unknown · Linux
- 상태: 진행중 (RCE 확인, root/user flag 미획득)
- Write-up: [HTB_Orion_Writeup.md](HTB_Orion_Writeup.md)

## 현재까지 확인된 것

Craft CMS `AssetsController::actionGenerateTransform`의 CVE-2025-32432(인증 없는 RCE, `yii\rbac\PhpManager` 가젯 + nginx access.log 로그 포이즈닝)로 `www-data` 권한 코드 실행을 1회 확인(`http/E13_trigger200_response.html`에 `uid=33(www-data)` 직접 확인). 이후 flag 탐색·권한 상승 재시도 과정에서 트리거가 불안정해져(`Image transform cannot be created` 등 에러 재발) 추가 진행이 막혔다. 자세한 내용과 막힌 지점은 write-up 참고.

## 폴더 구조

- `scans/` — nmap 원본 결과 (E01, E02)
- `http/` — 원본 응답/로그 캡처 (E03~E34)
- `artifacts/` — 대상에서 확보한 leaked 소스(`Component.php`, 취약점 분석용)
- `scripts/` — 익스플로잋 스크립트 원본 (E06~E41)
