#!/bin/bash
BASE="http://13.209.81.83:3000/api/reports/import"
TRANS="http://13.209.81.83:3000/api/reports/import"
hosts=(db postgres postgresql mysql redis cache worker import-worker importworker importer queue rabbitmq admin gateway proxy api frontend nginx vault secrets minio s3 elasticsearch mongo mongodb signer)
ports=(8000 80 8080 5000 6379 5432 27017 9200 5672)

declare -A jobmap
for h in "${hosts[@]}"; do
  for p in "${ports[@]}"; do
    url="http://$h:$p/"
    resp=$(curl -s -m 4 -X POST "$BASE" -H 'Content-Type: application/json' -d "{\"source_url\":\"$url\"}")
    id=$(echo "$resp" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{try{console.log(JSON.parse(d).id)}catch(e){console.log('ERR')}})" 2>/dev/null)
    echo "$url -> job $id"
    if [ "$id" != "ERR" ] && [ -n "$id" ]; then
      jobmap["$url"]="$id"
    fi
  done
done
echo "---transitioning---"
for url in "${!jobmap[@]}"; do
  id="${jobmap[$url]}"
  curl -s -m 4 -X POST "$TRANS/$id/transition" -H 'Content-Type: application/json' -d '{"to":"validated"}' > /dev/null
  fres=$(curl -s -m 6 -X POST "$TRANS/$id/transition" -H 'Content-Type: application/json' -d '{"to":"fetched"}')
  echo "$url (job $id): $fres"
done
