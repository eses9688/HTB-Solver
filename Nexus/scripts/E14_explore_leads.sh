#!/bin/bash
set -e
HOST="billing.nexus.htb"
IP=10.129.12.96
JAR=/mnt/c/HTB/Nexus/loot/E13_cookies.txt

curl -sS -c "$JAR" -b "$JAR" -H "Host: $HOST" "http://$IP/admin/leads/create" -o /mnt/c/HTB/Nexus/http/E14_leads_create.html
echo "saved leads create page"
curl -sS -c "$JAR" -b "$JAR" -H "Host: $HOST" "http://$IP/admin/leads" -o /mnt/c/HTB/Nexus/http/E14_leads_list.html
echo "saved leads list page"
