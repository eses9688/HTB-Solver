# RedLab 테넌트 목록 (완전)

## 📊 **전체 테넌트 (18개)**

| # | Tenant ID | Plan | MRR (KRW) | Status | 비고 |
|---|-----------|------|-----------|--------|------|
| 1 | atlas-3308 | pro | 3,100,000 | active | |
| 2 | bluesky-1102 | standard | 1,200,000 | active | |
| 3 | cedar-6627 | standard | 1,120,000 | **past_due** | ⚠️ 연체 |
| 4 | drift-9051 | growth | 2,210,000 | active | |
| 5 | harbor-8814 | standard | 940,000 | active | |
| 6 | lumen-4471 | growth | 1,980,000 | active | |
| 7 | nimbus-3341 | standard | 890,000 | active | |
| 8 | orbit-2093 | pro | 2,750,000 | active | |
| 9 | pixel-7742 | standard | 870,000 | **trialing** | 🔶 체험판 |
| 10 | quanta-5560 | standard | 1,050,000 | active | |
| 11 | sable-6390 | standard | 1,330,000 | active | |
| **12** | **snojc-cloud-5538** | **enterprise** | **37,600,000** | active | **Stage 0: C** |
| **13** | **snojc-corp-7731** | **enterprise** | **40,200,000** | active | **Stage 0: C** |
| **14** | **snojc-data-2286** | **enterprise** | **39,100,000** | active | **Stage 0: D** |
| **15** | **snojc-labs-4402** | **enterprise** | **38,800,000** | active | **Stage 0: L** |
| **16** | **snojc-systems-6104** | **enterprise** | **42,000,000** | active | **Stage 0: S** |
| **17** | **snojc-tech-9915** | **enterprise** | **41,500,000** | active | **Stage 0: T** |
| 18 | vertex-7788 | pro | 3,400,000 | active | |

---

## 🎯 **Plan 별 분류**

### Enterprise (6개) - Stage 0 정답
```
snojc-systems-6104    42.0M ← 최고
snojc-tech-9915       41.5M
snojc-corp-7731       40.2M
snojc-data-2286       39.1M
snojc-labs-4402       38.8M
snojc-cloud-5538      37.6M ← 최저
합계: 239.2M KRW
```

**특징**:
- MRR 범위: 37.6M ~ 42.0M (매우 좁은 범위)
- 모두 "active" 상태
- STCDLC 정렬: Systems → Tech → Corp → Data → Labs → Cloud

### Pro (3개)
```
vertex-7788          3,400,000 (최고)
atlas-3308           3,100,000
orbit-2093           2,750,000 (최저)
합계: 9,250,000 KRW
```

### Growth (2개)
```
drift-9051          2,210,000
lumen-4471          1,980,000
합계: 4,190,000 KRW
```

### Standard (7개)
```
sable-6390          1,330,000 (최고)
bluesky-1102        1,200,000
cedar-6627          1,120,000 (but past_due)
quanta-5560         1,050,000
harbor-8814           940,000
nimbus-3341           890,000
pixel-7742           870,000 (but trialing)
합계: 7,400,000 KRW
```

---

## 📈 **통계**

| 항목 | 값 |
|------|-----|
| **총 MRR** | 260,142,000 KRW |
| **Plan별 상위** | enterprise (239.2M) |
| **최고 MRR** | snojc-systems-6104 (42M) |
| **최저 MRR** | pixel-7742 (870K) |
| **MRR 비율** | snojc : 기타 = 239.2M : 20.9M (약 11:1) |
| **활성 테넌트** | 16개 |
| **특수 상태** | past_due (1), trialing (1) |

---

## 🔍 **Stage 0 STCDLC 정렬 검증**

| 순서 | 글자 | 테넌트명 | MRR | 상태 |
|------|------|---------|-----|------|
| 1 | **S**ystems | snojc-systems-6104 | 42.0M | ✓ 최고 |
| 2 | **T**ech | snojc-tech-9915 | 41.5M | ✓ 2위 |
| 3 | **C**orp | snojc-corp-7731 | 40.2M | ✓ 3위 |
| 4 | **D**ata | snojc-data-2286 | 39.1M | ✓ 4위 |
| 5 | **L**abs | snojc-labs-4402 | 38.8M | ✓ 5위 |
| 6 | **C**loud | snojc-cloud-5538 | 37.6M | ✓ 6위 |

**검증**: STCDLC = MRR 내림차순 정렬 ✓ 일치

---

## 💡 **관찰 사항**

### snojc 6개 테넌트의 특이성
1. **매우 높은 MRR**: 37.6M ~ 42.0M (기타 최고 3.4M의 약 11배)
2. **좁은 MRR 범위**: 4.4M 폭 (다른 plan들은 넓은 편)
3. **모두 활성**: 모든 snojc는 "active" 상태 (연체 없음)
4. **단일 Department 구조**: "snojc-" 접두사로 명확히 구분

### 기타 테넌트 특이점
- **cedar-6627**: past_due (연체 상태)
- **pixel-7742**: trialing (체험판 상태)
- **나머지 16개**: 모두 active (정상)

---

## 🎓 **Stage 0 풀이 로직**

```
주어진 정보:
- 6개의 숫자: 6104, 9915, 7731, 2286, 4402, 5538

Step 1. /api/billing/tenants 조회
→ 18개 테넌트 데이터 획득

Step 2. 숫자와 일치하는 테넌트 찾기
→ snojc-{name}-{number} 형태 6개 발견

Step 3. STCDLC 패턴 인식
→ Systems, Tech, Corp, Data, Labs, Cloud

Step 4. MRR 패턴 검증
→ STCDLC 순서 = MRR 내림차순 (완벽 일치)

Step 5. Stage 0 정답
→ 6개 snojc 테넌트 = Systems-Tech-Corp-Data-Labs-Cloud
```

