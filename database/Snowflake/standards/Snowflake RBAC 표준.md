# Snowflake RBAC 표준

| 필드  | 값   |
|-----|-----|
| 도메인 | 데이터 |
| 플랫폼 | `Snowflake` |
| 유형  | 표준  |
| 상태  | 초안  |
| 소유자 | @김가람휘 |
| 최종수정 | 2026-04-10 |
| 문서ID | ST-SF-002 |
| 키워드 | `RBAC`, `Role-Based Access Control`, `롤`, `권한`, `접근 제어`, `최소 권한`, `롤 계층`, `PM`, `PU`, `S_R`, `S_RW`, `Snowflake 권한 관리`, `스키마 롤` |
| 관련문서 | \[\[Snowflake Platform Index\]\], \[\[Snowflake 네이밍 규칙\]\], \[\[Snowflake 사용자 계정 관리 런북\]\] |

Snowflake RBAC 표준 — 4단계 롤 체계(PM/PU/S_R/S_RW), 스키마 단위 권한 관리, 신규 스키마 생성 시 롤 자동 생성 절차를 정의한다.

## 설계 원칙

| 원칙  | 설명  |
|-----|-----|
| 최소 권한 (Least Privilege) | 업무에 필요한 최소한의 권한만 부여 |
| 롤 기반 접근 (RBAC) | 사용자에게 직접 권한 부여 금지, 반드시 롤을 통해 부여 |
| 스키마 단위 권한 | 스키마마다 `S_R_` / `S_RW_` 롤 쌍을 생성하여 관리 |
| 롤 계층 활용 | `S_R_` → `S_RW_` → `PM_` / `PU_` → `SYSADMIN` 상속 구조 |

## 롤 계층 구조

```
ACCOUNTADMIN (비상 시에만 사용)
  └── SYSADMIN (DB/스키마/WH 생성)
  │     ├── S_RW_{schema} ← 스키마별 읽기/쓰기 (OWNERSHIP 포함)
  │     │     └── S_R_{schema} ← 스키마별 읽기 전용
  │     │
  │     └── (WH 소유: DEV_WH, OP_WH, AI_WH)
  │
  └── SECURITYADMIN (롤/사용자 관리)
        ├── PM_{domain} ← 프로젝트 관리자 (S_RW_ 포함)
        │     └── S_RW_{schema} (해당 도메인 스키마)
        │
        └── PU_{team} ← 일반 사용자 (S_R_ 포함)
              └── S_R_{schema} (해당 팀 필요 스키마)

공통 읽기 롤 자동 부여:
  PU_ALL ← 모든 S_R_{schema} (프로세스부문-데이터팀)
  PU_BIP ← 모든 S_R_{schema} (경영개선팀)
  PU_HR  ← 모든 S_R_{schema} (HR팀)
```

## 4단계 롤 체계

### 1. S_R_{schema} — 스키마 읽기 전용

스키마의 모든 오브젝트에 대한 **읽기** 권한.

**부여 권한**:

* `USAGE` on DATABASE FNF, SCHEMA, WAREHOUSE DEV_WH
* `SELECT` on ALL/FUTURE TABLES, VIEWS, MATERIALIZED VIEWS, EXTERNAL TABLES
* `USAGE` on ALL/FUTURE PROCEDURES
* `READ`, `USAGE` on ALL/FUTURE STAGES

**자동 상위 부여**: `PU_ALL`, `PU_BIP`, `PU_HR`

### 2. S_RW_{schema} — 스키마 읽기/쓰기

스키마의 모든 오브젝트에 대한 **읽기 + 쓰기 + 생성** 권한. `S_R_{schema}`를 상속합니다.

**추가 부여 권한** (S_R_ 상속 외):

* `SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES` on ALL/FUTURE TABLES
* `CREATE VIEW, CREATE TABLE, CREATE MATERIALIZED VIEW, CREATE SEQUENCE, CREATE FUNCTION, CREATE PROCEDURE, CREATE TASK, CREATE EXTERNAL TABLE, CREATE TEMPORARY TABLE, CREATE FILE FORMAT` on SCHEMA
* `OWNERSHIP` on ALL TABLES, PROCEDURES (COPY CURRENT GRANTS)

**자동 상위 부여**: `SYSADMIN`

### 3. PM_{domain} — 프로젝트 관리자

프로젝트/도메인 단위의 **관리자** 롤. 해당 도메인 `S_RW_` 롤을 포함합니다.

| PM 롤 | 설명  | 포함 S_RW 롤 (예시) |
|------|-----|----------------|
| `PM_DM` | 데이터관리 PM (8명) | 관리 대상 스키마 S_RW |
| `PM_AI` | AI 프로젝트 PM (2명) | `S_RW_AI` 등    |
| `PM_CHN` | 중국 법인 PM (6명) | `S_RW_CHN`, `S_RW_CN_*` 등 |
| `PM_SAP` | SAP 연동 PM (5명) | `S_RW_SAP_*` 등 |
| `PM_DBT` | dbt 파이프라인 PM (3명) | 파이프라인 관련 S_RW  |
| `PM_DE` | 데이터파이프라인 구축용 (1명) | 파이프라인 관련 S_RW  |
| `PM_FNCO` | FNCO 법인 PM (4명) | `S_RW_FNCO*` 등 |
| `PM_MOB` | 모바일 Sales PM (1명) | `S_RW_MOB*` 등  |

### 4. PU_{team} — 일반 사용자

부서/팀 단위의 **읽기 + 제한적 쓰기** 롤. 필요한 `S_R_` 롤을 포함합니다.

| PU 롤 | 설명  | 사용자 수 |
|------|-----|-------|
| `PU_ALL` | 프로세스부문-데이터팀 — **모든 S_R 자동 부여** | 20명   |
| `PU_BIP` | 경영개선팀 — **모든 S_R 자동 부여** | 3명    |
| `PU_HR` | HR팀 — **모든 S_R 자동 부여** + HR 전용 | 8명    |
| `PU_CHN` | 중국 법인 | 13명   |
| `PU_DX` | 디스커버리 사업부 | 10명   |
| `PU_MLB` | MLB 사업부 | 6명    |
| `PU_FNCO` | FNCO 법인 | 6명    |
| `PU_PI` | 상품기획 | 10명   |
| `PU_SQL` | SQL 교육용 | 32명   |
| `PU_PBI` | Power BI 연동 | 5명    |

## 신규 스키마 생성 시 롤 생성 절차

신규 스키마를 만들면 반드시 `S_R_` / `S_RW_` 롤 쌍을 생성해야 합니다. Snowflake Notebook에서 아래 코드를 실행합니다.

> 코드 위치: Snowflake Notebook (Snowpark Python)

```python
from snowflake.snowpark import Session

def create_roles_for_schema(session, schema):
    result_log = []
    sql_statements = [
        'USE ROLE SECURITYADMIN',
        f"CREATE ROLE IF NOT EXISTS S_R_{schema}",
        f"CREATE ROLE IF NOT EXISTS S_RW_{schema}",
        f"GRANT ROLE S_R_{schema} TO ROLE S_RW_{schema}",
        "USE ROLE SYSADMIN",
        f"GRANT USAGE ON WAREHOUSE DEV_WH TO ROLE S_R_{schema}",
        f"GRANT USAGE ON DATABASE FNF TO ROLE S_R_{schema}",
        f"GRANT USAGE ON SCHEMA {schema} TO ROLE S_R_{schema}",
        "USE ROLE SECURITYADMIN",
        # S_R: 읽기 권한
        f"GRANT SELECT ON ALL TABLES IN SCHEMA FNF.{schema} TO ROLE S_R_{schema}",
        f"GRANT SELECT ON FUTURE TABLES IN SCHEMA FNF.{schema} TO ROLE S_R_{schema}",
        f"GRANT SELECT ON ALL VIEWS IN SCHEMA FNF.{schema} TO ROLE S_R_{schema}",
        f"GRANT SELECT ON FUTURE VIEWS IN SCHEMA FNF.{schema} TO ROLE S_R_{schema}",
        f"GRANT SELECT ON ALL MATERIALIZED VIEWS IN SCHEMA FNF.{schema} TO ROLE S_R_{schema}",
        f"GRANT SELECT ON FUTURE MATERIALIZED VIEWS IN SCHEMA FNF.{schema} TO ROLE S_R_{schema}",
        f"GRANT SELECT ON ALL EXTERNAL TABLES IN SCHEMA FNF.{schema} TO ROLE S_R_{schema}",
        f"GRANT SELECT ON FUTURE EXTERNAL TABLES IN SCHEMA FNF.{schema} TO ROLE S_R_{schema}",
        f"GRANT USAGE ON ALL PROCEDURES IN SCHEMA FNF.{schema} TO ROLE S_R_{schema}",
        f"GRANT USAGE ON FUTURE PROCEDURES IN SCHEMA FNF.{schema} TO ROLE S_R_{schema}",
        # S_RW: 쓰기 권한
        f"GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES ON ALL TABLES IN SCHEMA FNF.{schema} TO ROLE S_RW_{schema}",
        f"GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES ON FUTURE TABLES IN SCHEMA FNF.{schema} TO ROLE S_RW_{schema}",
        # S_R: 스테이지 읽기
        f"GRANT READ ON ALL STAGES IN SCHEMA FNF.{schema} TO ROLE S_R_{schema}",
        f"GRANT USAGE ON ALL STAGES IN SCHEMA FNF.{schema} TO ROLE S_R_{schema}",
        f"GRANT READ ON FUTURE STAGES IN SCHEMA FNF.{schema} TO ROLE S_R_{schema}",
        f"GRANT USAGE ON FUTURE STAGES IN SCHEMA FNF.{schema} TO ROLE S_R_{schema}",
        # S_RW: 오브젝트 생성 권한
        f"GRANT CREATE VIEW, CREATE TABLE, CREATE MATERIALIZED VIEW, CREATE SEQUENCE, CREATE FUNCTION, CREATE PROCEDURE, CREATE TASK, CREATE EXTERNAL TABLE, CREATE TEMPORARY TABLE, CREATE FILE FORMAT ON SCHEMA FNF.{schema} TO ROLE S_RW_{schema}",
        # 공통 읽기 롤에 자동 부여
        f"GRANT ROLE S_R_{schema} TO ROLE PU_ALL",
        f"GRANT ROLE S_R_{schema} TO ROLE PU_BIP",
        f"GRANT ROLE S_R_{schema} TO ROLE PU_HR",
        # OWNERSHIP 이전
        "USE ROLE ACCOUNTADMIN",
        f"GRANT OWNERSHIP ON ALL TABLES IN SCHEMA FNF.{schema} TO ROLE S_RW_{schema} COPY CURRENT GRANTS",
        f"GRANT OWNERSHIP ON ALL PROCEDURES IN SCHEMA FNF.{schema} TO ROLE S_RW_{schema} COPY CURRENT GRANTS",
        f"GRANT ROLE S_RW_{schema} TO ROLE SYSADMIN"
    ]

    for stmt in sql_statements:
        try:
            session.sql(stmt).collect()
        except Exception as e:
            result_log.append(f"❌ Error: {e} - SQL: {stmt}")
            break
    else:
        result_log.append(f"✅ {schema} ROLE 생성 완료")
    
    return result_log


def main(session: Session):
    # 여기에 새로 생성한 스키마 입력
    schema_query = "SELECT SCHEMA_NAME FROM FNF.INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{NEW_SCHEMA}'"
    schema_df = session.sql(schema_query).to_pandas()

    log = []
    for schema in schema_df['SCHEMA_NAME']:
        log += create_roles_for_schema(session, schema)

    return log
```

> 작성자: Vivian (김가람휘)

## 금지 사항

| 항목  | 설명  |
|-----|-----|
| ACCOUNTADMIN 일상 사용 | 비상 시에만 사용, 일상 작업은 SYSADMIN 이하 롤 사용 |
| 사용자 직접 권한 부여 | 반드시 롤을 통해 부여 (`GRANT ... TO USER` 금지) |
| PUBLIC 롤 권한 추가 | PUBLIC 롤에 추가 권한 부여 금지 |
| S_R/S_RW 없이 스키마 운영 | 신규 스키마 생성 시 반드시 롤 쌍 생성 |

## 권한 신청 절차

권한 변경은 JIRA 서비스데스크를 통해 신청합니다.

* **신청 URL**: https://fnf.atlassian.net/servicedesk/customer/portal/50/group/158/create/1189
* **담당자**: AI 엔지니어링팀 김가람휘
* **상세 절차**: \[\[Snowflake 사용자 계정 관리 런북\]\] 참조

## 현황 요약

| 항목  | 수량  |
|-----|-----|
| 총 롤 수 | 약 310개 |
| PM 롤 | 약 34개 |
| PU 롤 | 약 68개 |
| S_R 롤 | 약 100개 |
| S_RW 롤 | 약 100개 |
| 내장 롤 | 6개 (ACCOUNTADMIN, SYSADMIN, SECURITYADMIN, USERADMIN, ORGADMIN, PUBLIC) |

## 변경 이력

| 버전  | 일자  | 작성자 | 변경내용 |
|-----|-----|-----|------|
| v1.2 | 2026-04-10 | AI(claude-code) | Snowflake MCP 실제 데이터 + 신규 스키마 롤 생성 코드 기반 전면 개편 — PM/PU/S_R/S_RW 4단계 체계, 실제 롤 310개 반영 |
| v1.1 | 2026-04-10 | AI(claude-code) | Notion 가이드 기반 JIRA 신청 경로, 담당자 반영 |
| v1.0 | 2026-04-10 | AI(claude-code) | 최초 작성 |