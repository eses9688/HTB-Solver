#!/bin/bash
WORDLIST=/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt
ffuf -w $WORDLIST -u http://bedside.htb/FUZZ -recursion -recursion-depth 1 -o /home/kali/bedside/E05_ffuf_dir.json -of json
