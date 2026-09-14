#!/bin/bash
set -e
mkdir -p /mnt/c/HTB/Nexus/artifacts
cd /mnt/c/HTB/Nexus/artifacts
rm -rf krayin-docker-setup
GIT_SSL_NO_VERIFY=true git -c http.extraHeader="Host: git.nexus.htb" clone http://10.129.12.96/admin/krayin-docker-setup.git 2>&1 || \
git clone http://git.nexus.htb/admin/krayin-docker-setup.git
