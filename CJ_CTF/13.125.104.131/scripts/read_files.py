#!/usr/bin/env python3
"""
/tmp의 파일들을 읽어서 출력
"""

import os
import sys

files = [
    "/tmp/aws_caller_identity.json",
    "/tmp/aws_s3_buckets.txt",
    "/tmp/aws_env_vars.txt",
    "/tmp/aws_dot_aws.txt",
]

for filepath in files:
    print(f"\n{'='*60}")
    print(f"File: {filepath}")
    print(f"{'='*60}")

    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if content:
                print(content)
            else:
                print("[Empty file]")
    except FileNotFoundError:
        print(f"[File not found: {filepath}]")
    except Exception as e:
        print(f"[Error reading file: {e}]")

print("\n" + "="*60)
print("Done")
