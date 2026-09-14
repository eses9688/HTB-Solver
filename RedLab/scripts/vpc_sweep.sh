#!/bin/bash
BASE="http://13.209.81.83:3000/api/reports/import"
for i in $(seq 1 254); do
  ip="10.66.30.$i"
  resp=$(curl -s -m 3 -X POST "$BASE" -H 'Content-Type: application/json' -d "{\"source_url\":\"http://$ip:8000/healthz\"}")
  id=$(echo "$resp" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{try{console.log(JSON.parse(d).id)}catch(e){console.log('ERR')}})" 2>/dev/null)
  if [ "$id" == "ERR" ] || [ -z "$id" ]; then echo "$ip: job-create-failed"; continue; fi
  curl -s -m 3 -X POST "$BASE/$id/transition" -H 'Content-Type: application/json' -d '{"to":"validated"}' >/dev/null
  fres=$(curl -s -m 5 -X POST "$BASE/$id/transition" -H 'Content-Type: application/json' -d '{"to":"fetched"}')
  echo "$ip: $fres"
done
