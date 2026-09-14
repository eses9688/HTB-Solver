#!/usr/bin/env python3
"""Comprehensive endpoint enumeration for research.bedside.htb"""
import requests
import sys

s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0'

base = 'http://research.bedside.htb'

# Common Flask/Django/app endpoints
paths = [
    '/',
    '/admin', '/admin/', '/admin/dashboard', '/admin/login',
    '/api', '/api/', '/api/upload', '/api/process', '/api/files',
    '/upload', '/process', '/view', '/render', '/convert',
    '/uploads', '/uploads/', '/uploads/list',
    '/dashboard', '/status', '/health', '/ping',
    '/v1', '/v1/files', '/v1/process',
    '/static', '/media', '/downloads',
    '/ajax', '/ajax/upload', '/ajax/process',
]

print("[*] Enumerating endpoints...")
for path in paths:
    r = s.get(base + path, timeout=3)
    if r.status_code != 404:
        print(f"{path:40} {r.status_code:3} {len(r.content):10} bytes")

# Try POST methods
print("\n[*] Trying POST on interesting paths...")
for path in ['/api/upload', '/api/process', '/process', '/convert', '/upload']:
    r = s.post(base + path, timeout=3)
    if r.status_code != 404:
        print(f"POST {path:35} {r.status_code:3}")

# Check for API endpoints with JSON
print("\n[*] Checking for JSON APIs...")
json_data = {'action': 'list', 'format': 'json'}
r = s.post(base + '/api', json=json_data, timeout=3)
if r.status_code < 400:
    print(f"POST /api with JSON: {r.status_code}")
    print(f"  Response: {r.text[:200]}")
