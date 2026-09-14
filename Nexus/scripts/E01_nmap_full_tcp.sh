#!/bin/bash
set -e
export TARGET=10.129.12.96
export LHOST=$(ip -4 -o addr show tun0 | awk '{print $4}' | cut -d/ -f1)
echo "TARGET=$TARGET LHOST=$LHOST"
mkdir -p /mnt/c/HTB/Nexus/scans /mnt/c/HTB/Nexus/logs
nmap -p- --min-rate 3000 -T4 -Pn -oA /mnt/c/HTB/Nexus/scans/E01_nmap_full_tcp "$TARGET"
