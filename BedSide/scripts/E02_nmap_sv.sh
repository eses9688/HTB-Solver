#!/bin/bash
TARGET=10.129.248.191
sudo nmap -sC -sV -p22,80,3000 -oA /home/kali/bedside/E02_nmap_sv $TARGET
