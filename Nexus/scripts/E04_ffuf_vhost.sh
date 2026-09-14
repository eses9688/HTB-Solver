#!/bin/bash
set -e
TARGET=10.129.12.96
WORDLIST=/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt
if [ ! -f "$WORDLIST" ]; then
  WORDLIST=/usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt
fi
ffuf -u "http://$TARGET/" \
  -c -w "$WORDLIST" \
  -H "Host: FUZZ.nexus.htb" \
  -fs 154 \
  -o /mnt/c/HTB/Nexus/scans/E04_ffuf_vhost.json -of json
