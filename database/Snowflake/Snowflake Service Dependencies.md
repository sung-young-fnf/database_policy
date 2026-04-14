# Snowflake Service Dependencies

| 필드  | 값   |
|-----|-----|
| 도메인 | 데이터 |
| 플랫폼 | `Snowflake` |
| 유형  | 의존성 |
| 상태  | 초안  |
| 소유자 | @김가람휘 |
| 최종수정 | 2026-04-10 |
| 문서ID | DEP-SF-001 |
| 키워드 | `Snowflake 의존성`, `장애 영향`, `서비스 의존성`, `Snowflake 연동`, `DMS`, `S3`, `Airflow`, `MWAA`, `dbt`, `Power BI`, `Milkyway`, `DCS AI`, `Microsoft SSO` |
| 관련문서 | \[\[Snowflake Platform Index\]\], \[\[Snowflake 데이터 파이프라인 오류 대응 런북\]\], \[\[Service Catalog\]\] |

Snowflake 서비스 의존성 — Snowflake 플랫폼의 상위/하위 기술 의존성과 장애 시 영향도를 정의한다. 파이프라인 구조: `원천 DB → AWS DMS → S3 → Snowflake`.

## 파이프라인 아키텍처

```
┌──────────────┐     ┌──────────────┐     ┌────────────────┐     ┌──────────────────────┐
│  원천 DB     │     │  AWS DMS     │     │  S3            │     │  Snowflake           │
│  Oracle      │ ──▶ │  CDC / BULK  │ ──▶ │  op-snowflake  │ ──▶ │  FNF DB (98 스키마)  │
│  PostgreSQL  │     │  Task        │     │  -s3/dms/      │     │                      │
└──────────────┘     └──────────────┘     └────────────────┘     └──────────┬───────────┘
                                                                            │
                           ┌────────────────────────────────────────────────┤
                           │                    │                           │
                    ┌──────┴──────┐     ┌──────┴──────┐            ┌──────┴──────┐
                    │ Airflow     │     │ dbt         │            │ 소비 계층    │
                    │ (MWAA)      │     │ 변환        │            │ BI/App/API  │
                    └─────────────┘     └─────────────┘            └─────────────┘
```

## 상위 의존성 (Snowflake가 의존)

| 서비스 | 역할  | 장애 시 영향 | 대응  |
|-----|-----|---------|-----|
| **원천 DB** (Oracle, PostgreSQL 등) | 데이터 원천 | 신규 데이터 유입 중단 | VDI 환경에서 원천 DB 상태 확인, Hiware 권한 확인 |
| **AWS DMS** | CDC/BULK 복제 | S3 적재 중단 → Snowflake 데이터 갱신 중단 | DMS Task 상태 확인, Task 재시작 |
| **AWS S3** (`op-snowflake-s3`) | 중간 스토리지 (Parquet) | External Table refresh 실패, COPY INTO 실패 | S3 버킷 상태 확인, 파일 존재 여부 확인 |
| **Microsoft SSO** (Entra ID) | 사용자 인증 | 신규 SSO 로그인 불가 (서비스 계정 정상) | RSA 서비스 계정으로 긴급 접근 |
| **Airflow (MWAA)** | DAG 스케줄링/오케스트레이션 | Procedure 자동 실행 중단 | MWAA UI 확인, DAG 수동 트리거 |

## 하위 의존성 (Snowflake에 의존)

| 서비스 | 사용 WH | 인증 방식 | 장애 시 영향 | 대응  |
|-----|-------|-------|---------|-----|
| **Airflow** (MWAA) | AIRFLOW_WH | RSA (AIRFLOW 계정) | ETL 파이프라인 전체 중단 | WH 상태 확인, DAG 재실행 |
| **dbt** | DEV_WH | RSA (DBT 계정) | 데이터 변환 중단 | dbt run 재실행 |
| **Power BI** | OP_WH | RSA (POWERBI 계정) | 대시보드 갱신 중단 | 캐시 데이터 임시 운영 |
| **Milkyway** (자체 분석 플랫폼) | DEV_WH | RSA (MILKYWAY 계정) | 분석 플랫폼 데이터 중단 | WH 상태 확인 |
| **DCS AI** | AI_WH | RSA (DCS_AI\* 계정) | AI 서비스 데이터 중단 | AI_WH 상태 확인 |
| **Excel 연동** | DEV_WH | RSA (MLB_EXCEL 등) | 엑셀 데이터 갱신 중단 | 수동 갱신 안내 |
| **외부 업체** (Dalpha 등) | OP_WH | RSA (EXT_DALPHA 등) | 외부 연동 중단 | 업체 연락 + 계정 상태 확인 |
| **FNF Data API** | OP_WH | RSA (FNF_DATA_API) | API 응답 실패 | WH 스케일업, 캐시 활용 |

## 데이터 파이프라인 장애 영향 시나리오

| 장애 유형 | 영향 범위 | 심각도 | 대응 런북 |
|-------|-------|-----|-------|
| Snowflake 서비스 전체 장애 | BI, ETL, API, 분석 플랫폼 전체 중단 | 🔴 Critical | Snowflake 상태 페이지 확인 |
| DMS Task 오류 | 해당 원천 DB 데이터 갱신 중단 | 🟡 Medium | \[\[Snowflake 데이터 파이프라인 오류 대응 런북\]\] 구간 2 |
| S3 접근 불가 | 전체 파이프라인 적재 실패 | 🔴 Critical | S3 버킷 정책/IAM 확인 |
| Airflow DAG 전체 장애 | 모든 스케줄 작업 중단 | 🔴 Critical | MWAA 콘솔 확인, Snowflake에서 수동 Procedure 실행 |
| 특정 WH Suspend/용량 부족 | 해당 WH 사용 서비스만 영향 | 🟡 Medium | \[\[Snowflake 웨어하우스 관리 런북\]\] |
| Microsoft SSO 장애 | 사용자 로그인 불가 (서비스 계정 정상) | 🟡 Medium | RSA 서비스 계정으로 긴급 대응 |
| 원천 DB 장애/권한 만료 | 해당 스키마 데이터 갱신 중단 | 🟡 Medium | VDI에서 확인, Hiware 권한 재신청 |

## 주요 참조 링크

| 리소스 | URL |
|-----|-----|
| DMS Endpoints | https://ap-northeast-2.console.aws.amazon.com/dms/v2/home?region=ap-northeast-2#endpointList |
| Bitbucket (DAG 코드) | https://bitbucket.org/fnf-dt/data-de-pipeline/src/master/ |
| Hiware 권한 신청 (JIRA) | https://fnf.atlassian.net/servicedesk/customer/portal/36/create/10145 |
| Snowflake 계정 신청 (JIRA) | https://fnf.atlassian.net/servicedesk/customer/portal/50/group/158/create/1189 |
| Data part Assets (엑셀) | [SharePoint - Data part Assets.xlsx](https://fnf365.sharepoint.com/:x:/r/sites/PRCSMLBProcessTeam/_layouts/15/Doc.aspx?sourcedoc=%7BB42AE906-2757-4A86-B94A-9EB4DCBF6DAF%7D&file=Data%20part%20Assets.xlsx&action=default&mobileredirect=true) |

## 변경 이력

| 버전  | 일자  | 작성자 | 변경내용 |
|-----|-----|-----|------|
| v1.2 | 2026-04-10 | AI(claude-code) | Notion DMS 인수인계 기반 전면 개편 — 실제 파이프라인 아키텍처, 연동 서비스(Airflow/dbt/PowerBI/Milkyway/DCS AI), 주요 참조 링크 반영 |
| v1.1 | 2026-04-10 | AI(claude-code) | Notion 가이드 기반 Microsoft SSO, 인증 방식별 의존성 반영 |
| v1.0 | 2026-04-10 | AI(claude-code) | 최초 작성 |