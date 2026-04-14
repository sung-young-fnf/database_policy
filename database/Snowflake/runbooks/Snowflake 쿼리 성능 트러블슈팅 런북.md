# Snowflake 쿼리 성능 트러블슈팅 런북

| 필드  | 값   |
|-----|-----|
| 도메인 | 데이터 |
| 플랫폼 | `Snowflake` |
| 서비스 | `Query`, `Warehouse` |
| 유형  | 런북  |
| 대응레벨 | 🟡 단계적 |
| 트리거유형 | 인시던트 |
| 상태  | 초안  |
| 소유자 | @김가람휘 |
| 최종수정 | 2026-04-10 |
| 문서ID | RB-SF-003 |
| 트리거 | 슬로우쿼리 알림, 사용자 성능 불만 접수, 쿼리 타임아웃 |
| 소요시간 | 30분 \~ 1시간 |
| 난이도 | 보통  |
| 키워드 | `슬로우쿼리`, `성능`, `쿼리 최적화`, `Slow Query`, `쿼리 지연`, `타임아웃`, `쿼리 튜닝`, `클러스터링 키`, `파티션 프루닝`, `스필링` |
| 관련문서 | \[\[Snowflake Platform Index\]\], \[\[Snowflake Warehouse Inventory\]\], \[\[Snowflake 웨어하우스 관리 런북\]\] |

Snowflake 쿼리 성능 트러블슈팅(슬로우쿼리 진단, 쿼리 최적화, 쿼리 튜닝) 런북. 쿼리 지연, 타임아웃, 스필링(Spilling) 발생 시 진단 및 대응 절차를 포함한다.

## 진단 흐름

```
┌──────────────────────────┐
│  1. 슬로우쿼리 식별      │
│  (QUERY_HISTORY 조회)     │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  2. 실행 계획 분석       │
│  (EXPLAIN / Query Profile)│
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  3. 원인 분류            │
│  WH 부족? 쿼리 문제?     │
│  데이터 구조 문제?        │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  4. 대응 실행            │
│  WH 스케일업 / 쿼리 최적화│
│  클러스터링 키 설정       │
└──────────────────────────┘
```

## 상세 절차

### Step 1: 슬로우쿼리 식별

```sql
-- 최근 24시간 내 10분 이상 실행된 쿼리
SELECT
  QUERY_ID,
  USER_NAME,
  WAREHOUSE_NAME,
  EXECUTION_STATUS,
  TOTAL_ELAPSED_TIME / 1000 AS ELAPSED_SEC,
  BYTES_SCANNED / 1024 / 1024 / 1024 AS GB_SCANNED,
  ROWS_PRODUCED,
  QUERY_TEXT
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE START_TIME >= DATEADD(HOUR, -24, CURRENT_TIMESTAMP())
  AND TOTAL_ELAPSED_TIME > 600000  -- 10분 이상
ORDER BY TOTAL_ELAPSED_TIME DESC
LIMIT 20;
```

### Step 2: 스필링(Spilling) 확인

```sql
-- 디스크/리모트 스필링 발생 쿼리 (메모리 부족 징후)
SELECT
  QUERY_ID,
  USER_NAME,
  WAREHOUSE_NAME,
  BYTES_SPILLED_TO_LOCAL_STORAGE / 1024 / 1024 AS MB_SPILLED_LOCAL,
  BYTES_SPILLED_TO_REMOTE_STORAGE / 1024 / 1024 AS MB_SPILLED_REMOTE,
  TOTAL_ELAPSED_TIME / 1000 AS ELAPSED_SEC
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE START_TIME >= DATEADD(HOUR, -24, CURRENT_TIMESTAMP())
  AND (BYTES_SPILLED_TO_LOCAL_STORAGE > 0 OR BYTES_SPILLED_TO_REMOTE_STORAGE > 0)
ORDER BY BYTES_SPILLED_TO_REMOTE_STORAGE DESC
LIMIT 10;
```

### Step 3: 큐잉(Queuing) 확인

```sql
-- 큐잉이 발생한 쿼리 (WH 동시성 부족)
SELECT
  QUERY_ID,
  WAREHOUSE_NAME,
  QUEUED_OVERLOAD_TIME / 1000 AS QUEUE_SEC,
  TOTAL_ELAPSED_TIME / 1000 AS ELAPSED_SEC
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE START_TIME >= DATEADD(HOUR, -24, CURRENT_TIMESTAMP())
  AND QUEUED_OVERLOAD_TIME > 0
ORDER BY QUEUED_OVERLOAD_TIME DESC
LIMIT 10;
```

### Step 4: 원인별 대응

| 원인  | 징후  | 대응  |
|-----|-----|-----|
| **WH 사이즈 부족** | 스필링 발생, 쿼리 시간 증가 | WH 스케일업 (\[\[Snowflake 웨어하우스 관리 런북\]\]) |
| **WH 동시성 부족** | 큐잉 발생 | 멀티클러스터 활성화 또는 WH 분리 |
| **풀 테이블 스캔** | 높은 BYTES_SCANNED, 낮은 파티션 프루닝 | WHERE 절 추가, 클러스터링 키 설정 |
| **조인 폭발** | ROWS_PRODUCED >> 예상 | 조인 조건 확인, 중복 데이터 점검 |
| **불필요한 ORDER BY** | 대량 정렬, 스필링 | ORDER BY 제거 또는 LIMIT 추가 |

### Step 5: 클러스터링 키 설정 (대용량 테이블)

```sql
-- 클러스터링 상태 확인
SELECT SYSTEM$CLUSTERING_INFORMATION('PROD_SALES_DB.MART.F_SALES_ORDER', '(ORDER_DATE)');

-- 클러스터링 키 설정
ALTER TABLE PROD_SALES_DB.MART.F_SALES_ORDER
  CLUSTER BY (ORDER_DATE);
```

## 검증 방법

| 확인 항목 | 예상 결과 | 확인 방법 |
|-------|-------|-------|
| 쿼리 실행 시간 | 개선 확인 | 동일 쿼리 재실행 비교 |
| 스필링   | 감소 또는 제거 | QUERY_HISTORY 스필링 컬럼 |
| 큐잉    | 감소 또는 제거 | QUERY_HISTORY 큐잉 컬럼 |

## 에스컬레이션 기준

| 상황  | 조치  | 에스컬레이션 대상 |
|-----|-----|-----------|
| WH 스케일업으로 해결 안 됨 | 쿼리 자체 최적화 필요 | AI 엔지니어링팀 + 데이터팀 |
| 전체 쿼리 성능 저하 (계정 레벨) | Snowflake 서비스 이슈 의심 | Snowflake 지원팀 |
| 비용 급증 동반 | 비용 이상 대응 런북 병행 | AI 엔지니어링팀 + 재경팀 |

> 🟡 **단계적**: 1차로 WH 조정, 미해결 시 쿼리 최적화 및 에스컬레이션.

## 변경 이력

| 버전  | 일자  | 작성자 | 변경내용 |
|-----|-----|-----|------|
| v1.1 | 2026-04-10 | AI(claude-code) | 소유자·담당팀 업데이트 |
| v1.0 | 2026-04-10 | AI(claude-code) | 최초 작성 |