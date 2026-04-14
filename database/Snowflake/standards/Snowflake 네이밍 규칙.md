# Snowflake 네이밍 규칙

| 필드  | 값   |
|-----|-----|
| 도메인 | 데이터 |
| 플랫폼 | `Snowflake` |
| 유형  | 표준  |
| 상태  | 초안  |
| 소유자 | @김가람휘 |
| 최종수정 | 2026-04-10 |
| 문서ID | ST-SF-001 |
| 키워드 | `Snowflake 네이밍`, `이름 규칙`, `네이밍 컨벤션`, `데이터베이스 이름`, `스키마 이름`, `테이블 이름`, `웨어하우스 이름`, `뷰 이름`, `Naming Convention`, `롤 이름`, `사용자 이름` |
| 관련문서 | \[\[Snowflake Platform Index\]\], \[\[Snowflake RBAC 표준\]\] |

Snowflake 네이밍 규칙 — 데이터베이스, 스키마, 테이블, 뷰, 웨어하우스, 롤, 사용자 등 Snowflake 오브젝트의 네이밍 표준을 정의한다. 실제 운영 환경 기준.

## 공통 규칙

| 항목  | 규칙  |
|-----|-----|
| 대소문자 | **대문자 (UPPER_CASE)** |
| 구분자 | 언더스코어 (`_`) |
| 한글  | 사용 금지 |
| 예약어 | Snowflake 예약어 사용 금지 |

## 데이터베이스

**패턴**: `{DOMAIN}` 또는 `{DOMAIN}_{ENV}`

| 데이터베이스 | Owner | 설명  |
|--------|-------|-----|
| `FNF`  | SYSADMIN | 메인 통합 DW (스키마 98개) |
| `ANL_API_DEV` | ACCOUNTADMIN | 분석계 통합 API 개발 DB |
| `ANL_API_PRD` | ACCOUNTADMIN | 분석계 통합 API 운영 DB |

> 대부분의 데이터는 `FNF` 데이터베이스에 스키마 단위로 관리됩니다.

## 스키마

**패턴**: 소스 시스템 또는 업무 도메인 기반

스키마는 데이터 원천/용도별로 구분되며, FNF 데이터베이스 내에 약 98개 스키마가 운영 중입니다.

| 분류  | 스키마 예시 | 설명  |
|-----|--------|-----|
| **ERP/기간계** | `AX`, `ERP`, `NERP`, `GERP`, `MERP`, `SERP`, `SAP_CO`, `SAP_FNF`, `SAP_IF` | ERP/SAP 원천 데이터 |
| **이커머스** | `EC`, `ECOM`, `EC_AD`, `NMALL` | 이커머스·광고 데이터 |
| **CRM** | `CRM_FNF`, `CRM_MEMBER`, `CRM_SALESFORCEPROD` | CRM·멤버십 데이터 |
| **중국** | `CHN`, `CHN_MKT`, `CN_AX`, `CN_BOS`, `CN_OA`, `CN_OMS`, `CN_SAP`, `CN_LIANBAI` | 중국 법인 데이터 |
| **S3 외부 스테이지** | `STRG_AD`, `STRG_BIZ`, `STRG_ECOM`, `STRG_EDI`, `STRG_FNCO`, `STRG_GA`, `STRG_GLB`, `STRG_SAP`, `STRG_SCL` 등 | S3 연동 외부 데이터 (접두사 `STRG_`) |
| **조직/부서** | `ORG_BIP`, `ORG_HR_INT`, `ORG_ICFPA`, `ORG_PF`, `ORG_TD` | 부서별 분석 스키마 (접두사 `ORG_`) |
| **분석/BI** | `PRCS`, `DASHFF`, `BI`, `MKT`, `MKTS`, `TG_MKT`, `EXCEL`, `GA`, `GTM` | 분석·마케팅·대시보드 |
| **모바일** | `MOB`, `MOB_ARCHIVE`, `MOB_DEV` | 모바일 세일즈 데이터 |
| **AI/ML** | `AI`, `AIC`, `DCS_AI`, `ML_DIST`, `KG` | AI·ML·지식그래프 |
| **FNCO** | `FNCO`, `FNCO_ANL`, `FNCO_PRDT_MDM`, `MILKYWAY_FNCO` | F&CO 법인 데이터 |
| **기타** | `FNF`, `FNF_ADM`, `FNF_API`, `FNF_LOG`, `FNF_OBJ`, `DEV`, `COMM`, `FIN`,  `PRCS_ARCHIVE` 등 | 공통·관리·개발 |

### 스키마 접두사 규칙

| 접두사 | 의미  | 예시  |
|-----|-----|-----|
| `STRG_` | S3 외부 스테이지 연동 | `STRG_AD`, `STRG_ECOM` |
| `ORG_` | 조직/부서별 분석 스키마 | `ORG_BIP`, `ORG_PF` |
| `CN_` | 중국 법인 원천 데이터 | `CN_AX`, `CN_SAP` |
| `CHN_` | 중국 DW 분석 데이터 | `CHN`, `CHN_MKT` |
| `MOB_` | 모바일 세일즈 | `MOB`, `MOB_DEV` |
| (없음) | 소스 시스템 또는 도메인 | `AX`, `ERP`, `MKT` |

## 웨어하우스

**패턴**: `{PURPOSE}_WH`

| 웨어하우스 | Owner | 설명  |
|-------|-------|-----|
| `DEV_WH` | SYSADMIN | 데이터엔지니어링팀 개발용 (기본 WH) |
| `OP_WH` | SYSADMIN | 운영 쿼리 (멀티클러스터 3) |
| `AI_WH` | SYSADMIN | AI/ML 워크로드 |
| `AIRFLOW_WH` | ACCOUNTADMIN | Airflow ETL 파이프라인 |

## 롤

### 롤 유형별 네이밍

| 접두사 | 유형  | 패턴  | 설명  |
|-----|-----|-----|-----|
| `PM_` | Project Manager | `PM_{도메인/프로젝트}` | 프로젝트 관리자 — 데이터 쓰기 + 관리 권한 |
| `PU_` | Power User | `PU_{도메인/팀}` | 일반 사용자 — 부서/업무별 읽기 + 제한적 쓰기 |
| `S_R_` | Schema Read | `S_R_{스키마명}` | 스키마 읽기 전용 |
| `S_RW_` | Schema Read-Write | `S_RW_{스키마명}` | 스키마 읽기/쓰기 |

### 롤 예시

**PM (Project Manager) 롤**:

| 롤   | 설명  |
|-----|-----|
| `PM_DM` | 데이터관리 PM |
| `PM_AI` | AI 프로젝트 PM |
| `PM_CHN` | 중국 법인 PM |
| `PM_SAP` | SAP 연동 PM |
| `PM_DBT` | dbt 파이프라인 PM |
| `PM_DE` | 데이터파이프라인 구축용 |
| `PM_FNCO` | FNCO 법인 PM |

**PU (Project User) 롤**:

| 롤   | 설명  |
|-----|-----|
| `PU_ALL` | 프로세스부문-데이터팀 (전체 읽기) |
| `PU_BIP` | 경영개선팀 |
| `PU_HR` | HR팀 |
| `PU_DX` | 디스커버리 사업부 |
| `PU_MLB` | MLB 사업부 |
| `PU_FNCO` | FNCO 법인 |
| `PU_CHN` | 중국 법인 |
| `PU_SQL` | SQL 교육용 |
| `PU_PBI` | Power BI 연동 |

**S_R / S_RW (스키마 롤)**: 스키마명과 1:1 매핑

| 스키마 | 읽기 롤 | 쓰기 롤 |
|-----|------|------|
| `AX` | `S_R_AX` | `S_RW_AX` |
| `CHN` | `S_R_CHN` | `S_RW_CHN` |
| `PRCS` | `S_R_PRCS` | `S_RW_PRCS` |
| `FNCO` | `S_R_FNCO` | `S_RW_FNCO` |

## 사용자

**패턴**: 개인 사용자는 `{회사이메일ID}`, 서비스 계정은 `SVC_{서비스명}`

| 유형  | 패턴  | 예시  |
|-----|-----|-----|
| 개인 (SSO) | `{ID}` (대문자) | `KIMKRH`, `KGI083`, `SY0513` |
| 서비스 (RSA) | `SVC_{서비스명}` | `SVC_AGENT_MCP`, `SVC_ANL_DATA_API`, `SVC_DCS_AI_MLS` |
| 시스템 | `{시스템명}` | `AIRFLOW`, `DBT`, `POWERBI`, `MILKYWAY` |
| 중국 법인 | `CN_{역할}` or `{이름}` | `CN_MILKYWAY`, `CN_POWERBI`, `AMYLIU` |
| 엑셀 연동 | `{브랜드}_EXCEL` | `MLB_EXCEL`, `DISCOVERY_EXCEL`, `DV_EXCEL` |
| 외부 연동 | `EXT_{업체}` | `EXT_DALPHA`, `EXT_CN_DXC_USER01` |

> 신규 사용자는 Microsoft SSO 방식으로만 발급됩니다. ID/PW 방식은 미지원.

## 변경 이력

| 버전  | 일자  | 작성자 | 변경내용 |
|-----|-----|-----|------|
| v1.2 | 2026-04-10 | AI(claude-code) | Snowflake MCP 실제 데이터 기반 전면 개편 — DB 6개, 스키마 98개, 롤 310개, 사용자 234개 실제 패턴 반영 |
| v1.1 | 2026-04-10 | AI(claude-code) | Notion 가이드 기반 SSO/RSA 인증 정보 반영 |
| v1.0 | 2026-04-10 | AI(claude-code) | 최초 작성 |