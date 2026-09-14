#!/bin/bash
TARGET=10.129.248.191
sudo nmap -p- --min-rate 3000 -T4 -Pn -oA /home/kali/bedside/E01_nmap_full_tcp $TARGET
