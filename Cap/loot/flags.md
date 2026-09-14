# Cap — 플래그 (PRIVATE_STUDY)

민감 정보 — 이 파일은 로컬 개인 학습 용도로만 사용하며 공개 저장소에 올리지 않는다.

- **user flag**: `ea2a0b3322200cb4eda1fd5809e2f43d`
  - 계정: `nathan` (uid=1001)
  - 경로: `/home/nathan/user.txt`
  - 증적: E10 (`logs/E10_ssh_nathan_login.log`)
- **root flag**: `cf0898973b65f62ce18e511fb228163e`
  - 경로: `/root/root.txt`
  - 증적: E12 (`logs/E12_privesc_root.log`)

## 사용된 자격 증명

- FTP/SSH 공용: `nathan` / `Buck3tH4TF0RM3!` — 웹앱 IDOR로 획득한 과거 pcap(`http/E09_0.pcap`)에서 평문 FTP 인증으로 노출됨.
