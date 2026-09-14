#!/bin/bash
TARGET=10.129.248.191
WORDLIST=/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt
ffuf -w $WORDLIST -H "Host: FUZZ.bedside.htb" -u http://$TARGET/ -fw 21 -o /home/kali/bedside/E04_ffuf_vhost.json -of json
