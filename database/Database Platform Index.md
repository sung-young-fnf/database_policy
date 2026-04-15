# Database Platform Index

| 필드 | 값 |
|-----|-----|
| 도메인 | 운영 |
| 플랫폼 | `Database` |
| 유형 | 인덱스 |
| 상태 | 초안 |
| 소유자 | @윤형도 |
| 최종수정 | 2026-04-15 |
| 문서ID | IX-DB-000 |
| 키워드 | `Database`, `데이터베이스`, `DB`, `RDBMS`, `Oracle`, `PostgreSQL`, `Snowflake`, `DWH`, `계정`, `권한`, `스키마` |
| 관련문서 | [[Service Catalog]], [[Platform Index]] |

Database 플랫폼 관련 모든 문서의 최상위 AI 진입점. 사용자 질문의 키워드를 분석하여 RDBMS(Oracle/PostgreSQL) 또는 Snowflake 하위 플랫폼으로 라우팅한다.

## 키워드 라우팅

| 사용자 의도 (키워드) | 이동할 문서 | 설명 |
|--------------|--------|------|
| Oracle, PostgreSQL, PG, RDS, Aurora, DB 계정, _svc, _oper, _adm, Owner, DDL, DML, 계정 분리, 개발자 계정, 서비스 계정, 패스워드, 읽기전용 | [[RDBMS Platform Index]] | Oracle/PostgreSQL 계정 생성, 권한 분리, Owner 관리, 정책 점검 |
| Snowflake, 스노우플레이크, DWH, 웨어하우스, 크레딧, 비용, SSO, PAT, RSA, Snowsight, RBAC, 데이터 공유 | [[Snowflake Platform Index]] | Snowflake 사용자/권한, 웨어하우스, 비용, 쿼리 성능 |

## 하위 플랫폼

| 플랫폼 | Platform Index | 담당자 | 설명 |
|--------|---------------|--------|------|
| **RDBMS** | [[RDBMS Platform Index]] | @윤형도 | Oracle, PostgreSQL 계정 생성/관리/점검 |
| **Snowflake** | [[Snowflake Platform Index]] | @김가람휘 | 데이터 웨어하우스 운영, 사용자/권한, 비용 관리 |

## 에스컬레이션 경로

| 단계 | 담당 | 연락처 |
|-----|-----|-----|
| 1차 접수 | 사무보조 / 챗봇 | 사내 챗봇 |
| 2차 처리 (RDBMS) | DBA팀 @최종현 | Teams / 메일 |
| 2차 처리 (Snowflake) | 데이터팀 @김가람휘 | Teams / 메일 |
| 3차 외부 지원 | AWS 기술지원 / Snowflake Support | 서비스 요청 |

## 변경 이력

| 버전 | 일자 | 작성자 | 변경내용 |
|-----|-----|-----|------|
| v1.0 | 2026-04-15 | AI(claude-code) | 최초 작성 — database-index.md 대체, RDBMS/Snowflake 라우팅 |
