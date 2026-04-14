# Snowflake 데이터 파이프라인 오류 대응 런북

| 필드  | 값   |
|-----|-----|
| 도메인 | 데이터 |
| 플랫폼 | `Snowflake`, `AWS DMS`, `S3`, `MWAA` |
| 서비스 | `DMS`, `S3`, `External Table`, `Stream`, `Airflow` |
| 유형  | 런북  |
| 대응레벨 | 🟡 단계적 |
| 트리거유형 | 인시던트 |
| 상태  | 초안  |
| 소유자 | @김가람휘 |
| 최종수정 | 2026-04-10 |
| 문서ID | RB-SF-005 |
| 트리거 | Airflow DAG 실패 알림, 데이터 정합성 이슈 보고, DMS Task 오류, Snowflake 적재 누락 |
| 소요시간 | 30분 \~ 2시간 (구간별 상이) |
| 난이도 | 보통 \~ 어려움 |
| 키워드 | `파이프라인 오류`, `DMS`, `CDC`, `BULK`, `S3`, `External Table`, `Stream`, `Merge`, `COPY INTO`, `Airflow`, `MWAA`, `DAG 실패`, `데이터 누락`, `적재 오류`, `파이프라인 장애` |
| 관련문서 | \[\[Snowflake Platform Index\]\], \[\[Snowflake Service Dependencies\]\], \[\[Snowflake Warehouse Inventory\]\] |

Snowflake 분석계 데이터 파이프라인 오류 대응 런북. `원천 DB → AWS DMS → S3 → Snowflake` 파이프라인의 각 구간별 장애 진단 및 대응 절차를 정의한다. CDC(500만 행 초과) / BULK(500만 행 이하) 두 가지 방식의 오류를 다룬다.

## 파이프라인 아키텍처

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────────────────┐
│  원천 DB     │      │  AWS DMS     │      │  S3          │      │  Snowflake               │
│  (Oracle 등) │ ───▶ │  CDC / BULK  │ ───▶ │  op-snowflake│ ───▶ │  External Table → Merge  │
│              │      │  Task        │      │  -s3/dms/    │      │  or COPY INTO            │
└──────────────┘      └──────────────┘      └──────────────┘      └──────────────────────────┘
                                                                            │
                                                                   ┌────────┴────────┐
                                                                   │  Airflow (MWAA) │
                                                                   │  DAG 스케줄링    │
                                                                   └─────────────────┘
```

### 방식별 구성 요소

| 방식  | 기준  | DMS Task | S3 경로 | Snowflake 구성 | Airflow DAG |
|-----|-----|----------|-------|--------------|-------------|
| **CDC** | 원천 500만 행 초과 | `*cdc*` Task | `dms/cdc/{schema}/{table}/` | External Table → Stream → Merge Procedure | refresh + merge |
| **BULK** | 원천 500만 행 이하 | `*bulk*` Task | `dms/bulk/{schema}/{table}/` | COPY INTO Procedure (TRUNCATE + LOAD) | copy procedure |

## 오류 진단 흐름

```
DAG 실패 또는 데이터 이상 감지
    │
    ├─ 1. Airflow DAG 확인 ─── DAG 자체 오류?
    │       └─ Yes → [구간 5] Airflow 오류 대응
    │
    ├─ 2. Snowflake 확인 ──── Procedure 실패?
    │       └─ Yes → [구간 4] Snowflake 오류 대응
    │
    ├─ 3. S3 확인 ─────────── 파일 미생성?
    │       └─ Yes → [구간 3] S3 오류 대응
    │
    └─ 4. DMS 확인 ────────── Task 오류?
            └─ Yes → [구간 2] DMS 오류 대응
            └─ No  → [구간 1] 원천 DB 확인
```

## 구간 1: 원천 DB 오류

### 증상

* DMS Task는 정상인데 데이터가 안 옴
* 특정 테이블만 누락

### 진단

```sql
-- Snowflake에서 최근 적재 확인
SELECT COUNT(*) FROM {schema}.{table};

-- 원천 DB row 수와 비교 (VDI 환경에서 DBeaver로 확인)
```

### 대응

| 증상  | 원인  | 해결  |
|-----|-----|-----|
| 원천 테이블 조회 안됨 | Hiware 권한 만료 | JIRA로 DB 권한 재신청 |
| 원천 데이터가 0건 | 원천 시스템 이슈 | 해당 시스템 담당자에게 확인 |
| CDC 변경분 미감지 | Oracle ASM 로그 접근 권한 없음 | IT/EA 최종현 대리에게 권한 부여 요청 |

> Hiware 권한 신청: https://fnf.atlassian.net/servicedesk/customer/portal/36/create/10145

## 구간 2: AWS DMS 오류

### 증상

* DMS Task 상태가 Error 또는 Stopped
* S3에 파일이 생성되지 않음

### 진단


1. AWS 콘솔 → DMS → Database migration tasks
2. 원천 DB의 Endpoint 확인: [DMS Endpoints](https://ap-northeast-2.console.aws.amazon.com/dms/v2/home?region=ap-northeast-2#endpointList)
3. 해당 Endpoint의 Task 검색 (`*cdc*` 또는 `*bulk*`)
4. Task의 Table statistics 탭에서 오류 테이블 확인

### 대응

| 증상  | 원인  | 해결  |
|-----|-----|-----|
| Task 상태 `Error` | 원천 DB 연결 실패 | Endpoint 연결 테스트, 원천 DB 상태 확인 |
| Task 상태 `Stopped` | 수동 중지 또는 에러 후 중단 | Task 재시작 (Resume/Restart) |
| 특정 테이블만 오류 | DDL 변경, 권한 문제 | Table statistics에서 오류 메시지 확인 후 조치 |
| CDC Task 지연 | 대량 변경 발생 | Task 모니터링, 필요시 replication instance 스케일업 |
| CDC 엔드포인트 없음 | Oracle ASM 권한 미부여 | IT/EA 최종현 대리에게 권한 부여 요청 후 엔드포인트 생성 |

### DMS Task 테이블 추가 시 참고 (JSON)

```json
{
    "rule-type": "selection",
    "rule-id": "221245816",
    "rule-name": "221245816",
    "object-locator": {
        "schema-name": "FNF",
        "table-name": "VIEW_HR_PERSON"
    },
    "rule-action": "include",
    "filters": []
}
```

> 개인정보 컬럼 제거가 필요한 경우 `rule-action: "remove-column"` transformation 규칙 추가

## 구간 3: S3 적재 오류

### 증상

* DMS는 정상인데 Snowflake에서 데이터가 안 보임
* External Table refresh 시 빈 결과

### 진단

```bash
# S3 파일 존재 확인
aws s3 ls s3://op-snowflake-s3/dms/cdc/{schema}/{table}/ --recursive | tail -10
aws s3 ls s3://op-snowflake-s3/dms/bulk/{schema}/{table}/ --recursive | tail -10
```

### 대응

| 증상  | 원인  | 해결  |
|-----|-----|-----|
| S3 경로에 파일 없음 | DMS가 다른 경로에 적재 | DMS Task의 Target 설정 확인 |
| 파일은 있으나 0 byte | DMS 적재 실패 | DMS Task 재시작 |
| 파일 형식 오류 | Parquet 포맷 불일치 | FILE_FORMAT 설정 확인 (`FNF_OBJ.FILE_FMT_PARQUET`) |

## 구간 4: Snowflake 오류

### 4-1. CDC 방식 오류

**External Table Refresh 실패**:

```sql
-- External Table 수동 refresh
ALTER EXTERNAL TABLE {schema}.{table}_EXT REFRESH;

-- refresh 결과 확인
SELECT COUNT(*) FROM {schema}.{table}_EXT;
```

**Stream 오류**:

```sql
-- Stream 상태 확인
SHOW STREAMS LIKE '%{table}%' IN SCHEMA {schema};

-- Stream에 미처리 데이터 확인
SELECT SYSTEM$STREAM_HAS_DATA('{schema}.{table}_EXT_STREAM');

-- Stream이 stale 상태인 경우 재생성
CREATE OR REPLACE STREAM {schema}.{table}_EXT_STREAM
  ON EXTERNAL TABLE {schema}.{table}_EXT INSERT_ONLY = TRUE;
```

**Merge Procedure 실패**:

```sql
-- Procedure 수동 실행
CALL {schema}.SP_MERGE_INTO_{table}();

-- 최근 실행 이력 확인
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE QUERY_TEXT ILIKE '%SP_MERGE_INTO_{table}%'
ORDER BY START_TIME DESC
LIMIT 5;
```

| 증상  | 원인  | 해결  |
|-----|-----|-----|
| External Table refresh 실패 | S3 파일 없음 또는 경로 불일치 | S3 경로 확인, stage 경로 검증 |
| Stream stale | 14일 이상 refresh 안됨 | Stream 재생성 |
| Merge 실패 — 컬럼 불일치 | 원천 DDL 변경 (컬럼 추가/삭제) | External Table + Table DDL 동기화 |
| Merge 실패 — PK 중복 | CDC 이벤트 순서 꼬임 | `ROW_NUMBER() OVER(PARTITION BY ... ORDER BY TRANSACTION_ID DESC)` 확인 |
| 데이터 타입 오류 | Oracle DATE → Snowflake 매핑 불일치 | `TIMESTAMP_NTZ(9)` 매핑 확인 |

### 4-2. BULK 방식 오류

**COPY INTO 실패**:

```sql
-- Procedure 수동 실행
CALL {schema}.SP_COPY_INTO_{table}();

-- COPY 이력 확인
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY
WHERE TABLE_NAME = '{TABLE}'
ORDER BY LAST_LOAD_TIME DESC
LIMIT 10;
```

| 증상  | 원인  | 해결  |
|-----|-----|-----|
| COPY INTO 0건 | S3에 파일 없음 | DMS BULK Task 실행 상태 확인 |
| TRUNCATE 후 COPY 실패 | 파일 포맷 불일치 | `MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE` 확인 |
| 컬럼 매핑 오류 | 원천 컬럼명 대소문자 불일치 | 원천 DDL 대소문자 재확인 |

## 구간 5: Airflow (MWAA) 오류

### 증상

* DAG 실패 알림
* DAG가 스케줄대로 실행되지 않음

### 진단


1. MWAA UI에서 DAG 상태 확인
2. 실패한 Task의 로그 확인
3. 소스 코드 확인: [Bitbucket - data-de-pipeline](https://bitbucket.org/fnf-dt/data-de-pipeline/src/master/)

### 대응

| 증상  | 원인  | 해결  |
|-----|-----|-----|
| DAG import 오류 | Python 문법 오류 | Bitbucket에서 코드 확인 및 수정 |
| Task 실행 실패 | Snowflake 연결 오류 | Airflow Connection 설정 확인 |
| DAG 미표시 | DAG 파일 미배포 | Bitbucket → MWAA S3 동기화 확인 |
| DAG 실행은 됐으나 데이터 없음 | Procedure 내부 오류 | Snowflake에서 직접 Procedure 실행하여 오류 확인 |

### 주요 DAG / 설정 파일

| 파일  | 역할  |
|-----|-----|
| `dags/constants/dms_arn_info.py` | DMS Task ARN 정보 |
| `dags/constants/dms_tbl_info.py` | DMS 테이블 매핑 정보 |
| `cdc_oracle_info.py` | Oracle CDC 설정 |
| `cdc_postgres_info.py` | PostgreSQL CDC 설정 |
| `dms_bulk_*` | BULK DAG |
| `dms_cdc_*` | CDC DAG |

## 데이터 정합성 검증

오류 복구 후 반드시 데이터 정합성을 확인합니다.

```sql
-- Snowflake 테이블 row 수 확인
SELECT COUNT(*) FROM {schema}.{table};

-- 최근 적재 시간 확인 (BULK 방식)
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY
WHERE TABLE_NAME = '{TABLE}'
ORDER BY LAST_LOAD_TIME DESC
LIMIT 1;

-- CDC Stream 미처리 데이터 확인
SELECT SYSTEM$STREAM_HAS_DATA('{schema}.{table}_EXT_STREAM');
```

> 원천 DB(VDI DBeaver)와 Snowflake의 row 수, 데이터 값을 비교하여 정합성 확인

## 에스컬레이션 기준

| 상황  | 조치  | 에스컬레이션 대상 |
|-----|-----|-----------|
| DMS Task 복구 불가 | AWS DMS 서비스 이슈 의심 | AI 엔지니어링팀 + AWS Support |
| 원천 DB 권한 문제 | Hiware/DB 접근 권한 신청 | IT/EA팀 (최종현 대리) |
| CDC 엔드포인트 생성 필요 | Oracle ASM 권한 + 엔드포인트 생성 | IT/EA팀 (최종현 대리) |
| 대량 데이터 정합성 불일치 | 전체 재적재 필요 | AI 엔지니어링팀 (팀즈 공지 후 진행) |
| Airflow DAG 전체 장애 | MWAA 인프라 이슈 | AI 엔지니어링팀 + AWS Support |

> 🟡 **단계적**: 구간별로 진단 후, 1차 대응 시도. 미해결 시 에스컬레이션.

> ⚠️ 데이터 재적재 시 다른 DAG(모바일 등)에 영향이 있을 수 있으므로 **반드시 팀즈로 사전 공지** 후 진행.

## 변경 이력

| 버전  | 일자  | 작성자 | 변경내용 |
|-----|-----|-----|------|
| v1.0 | 2026-04-10 | AI(claude-code) | 최초 작성 — Notion DMS 인수인계 문서 기반, 원천DB→DMS→S3→Snowflake 파이프라인 구간별 오류 대응 |