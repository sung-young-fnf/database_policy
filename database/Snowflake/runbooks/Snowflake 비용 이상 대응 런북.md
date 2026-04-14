# Snowflake 비용 이상 대응 런북

| 필드  | 값   |
|-----|-----|
| 도메인 | 데이터 |
| 플랫폼 | `Snowflake` |
| 서비스 | `Billing`, `Warehouse` |
| 유형  | 런북  |
| 대응레벨 | 🔴 에스컬레이션 |
| 트리거유형 | 인시던트 |
| 상태  | 초안  |
| 소유자 | @김가람휘 |
| 최종수정 | 2026-04-10 |
| 문서ID | RB-SF-004 |
| 트리거 | 크레딧 사용량 알림, 일일 크레딧 소모 임계치 초과, 월간 예산 초과 경고 |
| 소요시간 | 30분 \~ 2시간 |
| 난이도 | 어려움 |
| 키워드 | `비용`, `크레딧`, `과금`, `비용 이상`, `비용 급증`, `크레딧 소모`, `예산 초과`, `Cost`, `Credit`, `Resource Monitor`, `비용 관리` |
| 관련문서 | \[\[Snowflake Platform Index\]\], \[\[Snowflake Warehouse Inventory\]\], \[\[Snowflake 웨어하우스 관리 런북\]\] |

Snowflake 비용 이상 대응(크레딧 급증, 예산 초과) 런북. Resource Monitor 알림, 일일/월간 크레딧 소모 이상 탐지 시 긴급 대응 절차를 포함한다. 원인 분석, 웨어하우스 서스펜드, 비용 최적화 조치를 다룬다.

## 대응 흐름

```
┌──────────────────────────┐
│  1. 알림 수신            │
│  Resource Monitor / 모니터│
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  2. 즉시 대응            │
│  이상 WH 식별 및 서스펜드 │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  3. 원인 분석            │
│  WH별 크레딧 소모 조회   │
└──────────┬───────────────┘
           ▼
┌──────────────────────────┐
│  4. 재발 방지            │
│  Resource Monitor / 정책  │
└──────────────────────────┘
```

## 상세 절차

### Step 1: 크레딧 소모 현황 파악

```sql
-- 최근 7일 웨어하우스별 크레딧 소모
SELECT
  WAREHOUSE_NAME,
  SUM(CREDITS_USED) AS TOTAL_CREDITS,
  SUM(CREDITS_USED_COMPUTE) AS COMPUTE_CREDITS,
  SUM(CREDITS_USED_CLOUD_SERVICES) AS CLOUD_CREDITS
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE START_TIME >= DATEADD(DAY, -7, CURRENT_TIMESTAMP())
GROUP BY WAREHOUSE_NAME
ORDER BY TOTAL_CREDITS DESC;
```

### Step 2: 일별 추이 확인

```sql
-- 일별 크레딧 소모 추이 (이상 탐지)
SELECT
  DATE_TRUNC('DAY', START_TIME) AS USAGE_DATE,
  WAREHOUSE_NAME,
  SUM(CREDITS_USED) AS DAILY_CREDITS
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE START_TIME >= DATEADD(DAY, -30, CURRENT_TIMESTAMP())
GROUP BY USAGE_DATE, WAREHOUSE_NAME
ORDER BY USAGE_DATE DESC, DAILY_CREDITS DESC;
```

### Step 3: 이상 웨어하우스 즉시 서스펜드

```sql
-- 이상 소모 WH 즉시 서스펜드
ALTER WAREHOUSE PROD_ETL_WH SUSPEND;

-- 실행 중인 쿼리 강제 취소 (필요 시)
SELECT SYSTEM$CANCEL_ALL_QUERIES('PROD_ETL_WH');
```

### Step 4: 원인 쿼리 식별

```sql
-- 해당 WH에서 크레딧을 많이 소모한 쿼리
SELECT
  QUERY_ID,
  USER_NAME,
  TOTAL_ELAPSED_TIME / 1000 AS ELAPSED_SEC,
  CREDITS_USED_CLOUD_SERVICES,
  QUERY_TEXT
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE WAREHOUSE_NAME = 'PROD_ETL_WH'
  AND START_TIME >= DATEADD(DAY, -1, CURRENT_TIMESTAMP())
ORDER BY TOTAL_ELAPSED_TIME DESC
LIMIT 20;
```

### Step 5: Resource Monitor 설정/강화

```sql
-- Resource Monitor 생성 (월간 100 크레딧 제한)
USE ROLE ACCOUNTADMIN;

CREATE RESOURCE MONITOR MONTHLY_BUDGET
  WITH CREDIT_QUOTA = 100
  FREQUENCY = MONTHLY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS
    ON 75 PERCENT DO NOTIFY          -- 75% 도달 시 알림
    ON 90 PERCENT DO NOTIFY          -- 90% 도달 시 알림
    ON 100 PERCENT DO SUSPEND        -- 100% 도달 시 WH 서스펜드
    ON 110 PERCENT DO SUSPEND_IMMEDIATE;  -- 110% 도달 시 즉시 서스펜드

-- WH에 Resource Monitor 연결
ALTER WAREHOUSE PROD_ETL_WH SET RESOURCE_MONITOR = MONTHLY_BUDGET;
```

## 비용 최적화 체크리스트

| 항목  | 확인 사항 | 조치  |
|-----|-------|-----|
| Auto-Suspend | 모든 WH에 설정되어 있는가? | 60\~300초 권장 |
| WH 사이즈 | 용도 대비 과대하지 않은가? | 스케일다운 검토 |
| 미사용 WH | 30일 이상 미사용 WH가 있는가? | 삭제 검토 |
| Resource Monitor | 모든 WH에 연결되어 있는가? | 모니터 생성 및 연결 |
| 쿼리 최적화 | 비효율 쿼리가 반복 실행되는가? | 쿼리 튜닝 |

## 에스컬레이션 기준

| 상황  | 조치  | 에스컬레이션 대상 |
|-----|-----|-----------|
| 월간 예산 100% 초과 | 즉시 보고, 원인 분석 | AI 엔지니어링팀 + 재경팀 |
| 단일 쿼리 10+ 크레딧 소모 | 쿼리 취소 및 사용자 연락 | AI 엔지니어링팀 + 해당 서비스팀 |
| 비인가 사용자 대량 쿼리 | 계정 비활성화, 감사 | AI 엔지니어링팀 + 보안팀 |
| Snowflake 자체 과금 이슈 | Snowflake 지원 티켓 | Snowflake 지원팀 |

> 🔴 **에스컬레이션**: 비용 이상은 재무 영향이 있으므로 즉시 보고 및 대응합니다.

## 변경 이력

| 버전  | 일자  | 작성자 | 변경내용 |
|-----|-----|-----|------|
| v1.1 | 2026-04-10 | AI(claude-code) | 소유자·담당팀 업데이트 |
| v1.0 | 2026-04-10 | AI(claude-code) | 최초 작성 |