#!/bin/bash
WORDLIST=/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt
ffuf -w $WORDLIST -u http://research.bedside.htb/FUZZ -o /home/kali/bedside/E07_ffuf_research_dir.json -of json
