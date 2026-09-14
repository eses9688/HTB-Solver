# 📖 OpenAPI 설명 텍스트 직접 추출 가이드

## 방법 1️⃣: curl + node.js (가장 간단)

```bash
curl -s http://13.209.81.83:3000/api/openapi.json | node -e "
let d='';
process.stdin.on('data', c => d += c);
process.stdin.on('end', () => {
  const api = JSON.parse(d);
  const desc = api.paths['/billing/tenants'].get.description;
  console.log(desc);
});
"
```

**작동 방식**:
1. `curl -s http://...` : API 스키마 요청
2. `node -e` : JavaScript 한 줄 코드 실행
3. `JSON.parse(d)` : 응답을 JSON으로 파싱
4. `api.paths['/billing/tenants'].get.description` : 특정 경로의 설명 추출
5. `console.log(desc)` : 출력

---

## 방법 2️⃣: curl + grep (텍스트 검색)

```bash
curl -s http://13.209.81.83:3000/api/openapi.json | grep -o '"description":"[^"]*' | head -5
```

**한계**: JSON 형식이 깨질 수 있음 (복잡한 설명에는 부적합)

---

## 방법 3️⃣: 브라우저에서 직접 보기

```
1. http://13.209.81.83:3000/api/openapi.json 접속
2. Ctrl+F 로 "tenant_ids" 검색
3. 주변 텍스트에서 "description" 필드 확인
```

**장점**: 전체 구조를 시각적으로 이해 가능

---

## 방법 4️⃣: curl + Python (설치된 경우)

```bash
curl -s http://13.209.81.83:3000/api/openapi.json | python3 -c "
import json, sys
api = json.load(sys.stdin)
desc = api['paths']['/billing/tenants']['get']['description']
print(desc)
"
```

**요구사항**: Python3 설치 필요

---

## 방법 5️⃣: PowerShell (Windows)

```powershell
$response = Invoke-WebRequest -Uri "http://13.209.81.83:3000/api/openapi.json" -UseBasicParsing
$json = ConvertFrom-Json $response.Content
$json.paths."/billing/tenants".get.description
```

---

## 방법 6️⃣: curl로 저장 후 편집기에서 검색

```bash
# 1단계: 파일로 저장
curl -s http://13.209.81.83:3000/api/openapi.json -o openapi.json

# 2단계: 텍스트 편집기에서 열기
cat openapi.json | grep -A 5 'tenant_ids'

# 또는 Ctrl+F로 "description" 찾기
```

---

## 🎯 추천 방법

**🥇 1순위**: 방법 1 (curl + node.js)
```bash
curl -s http://13.209.81.83:3000/api/openapi.json | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const api=JSON.parse(d);console.log(api.paths['/billing/tenants'].get.description);})"
```

**왜?**
- 한 줄 명령어
- node.js는 거의 모든 개발 환경에 설치됨
- 정확한 JSON 파싱
- 복잡한 설명도 안전하게 처리

---

## 📝 전체 과정 시나리오

```bash
# 1. 대상 서버에 접속
curl -v http://13.209.81.83:3000/

# 2. 숨겨진 OpenAPI 스키마 발견 (미인증 접근 가능)
curl http://13.209.81.83:3000/api/openapi.json

# 3. 스키마에서 힌트 찾기
curl -s http://13.209.81.83:3000/api/openapi.json | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const api=JSON.parse(d);Object.entries(api.paths).forEach(([p,ops])=>{Object.entries(ops).forEach(([m,o])=>{if(o.description) console.log(m.toUpperCase()+' '+p+': '+o.description.substring(0,80))})});})"

# 4. 특정 엔드포인트 깊이 분석
curl -s http://13.209.81.83:3000/api/openapi.json | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const api=JSON.parse(d);const endpoint=api.paths['/billing/tenants'].get;console.log(JSON.stringify(endpoint, null, 2));})"
```

---

## 🔑 핵심 포인트

| 단계 | 명령어 | 출력 |
|---|---|---|
| 1. API 스키마 요청 | `curl http://.../api/openapi.json` | JSON (전체) |
| 2. JSON 파싱 | `\| node -e "JSON.parse(...)"` | JavaScript 객체 |
| 3. 경로 선택 | `.paths['/billing/tenants']` | 엔드포인트 정보 |
| 4. 메서드 선택 | `.get` | GET 메서드 정보 |
| 5. 설명 추출 | `.description` | 텍스트 출력 |

---

## 🚀 한 줄 요약

```bash
curl -s http://13.209.81.83:3000/api/openapi.json | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).paths['/billing/tenants'].get.description));"
```

이것만 실행하면 우리가 발견한 Stage 0/2/3 힌트를 바로 볼 수 있습니다!

