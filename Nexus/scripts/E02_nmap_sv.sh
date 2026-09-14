#!/bin/bash
set -e
export TARGET=10.129.12.96
mkdir -p /mnt/c/HTB/Nexus/scans
nmap -sC -sV -p22,80 -oA /mnt/c/HTB/Nexus/scans/E02_nmap_sv "$TARGET"
