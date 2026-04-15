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

Database 플랫폼 관련 모든 문서의 최상위 AI 진입점. 이 문서에서 개별 런북/표준으로 직접 이동하지 않는다. 아래 기준으로 **하위 Platform Index를 선택**하여 탐색을 이어간다.

## 탐색 가이드

### RDBMS → [[RDBMS Platform Index]]

| 분류 | 고유 키워드 |
|------|-----------|
| 플랫폼 | Oracle, PostgreSQL, PG, RDS, Aurora, 19c, 23ai |
| 고유 패턴 | `_svc`, `_oper`, `_adm`, `_ops`, `object_owner_role`, `dml_role`, `DDL_DML_ROLE` |
| 고유 개념 | 계정 분리(3종), DB 패스워드 정책, Owner 혼재, DB 정책 점검 |

### Snowflake → [[Snowflake Platform Index]]

| 분류 | 고유 키워드 |
|------|-----------|
| 플랫폼 | Snowflake, 스노우플레이크, DWH, Snowsight |
| 고유 패턴 | SSO, PAT, RSA, RBAC, `PM_`, `PU_`, `S_R_`, `S_RW_` |
| 고유 개념 | 웨어하우스, WH, 크레딧, Resource Monitor |

### 플랫폼 특정이 필요한 공용 키워드

다음 키워드는 양쪽 플랫폼 모두에서 사용된다. 위 고유 키워드로 판단이 안 되면 사용자에게 **Oracle/PostgreSQL인지 Snowflake인지 확인**한다.

`계정 생성`, `계정 삭제`, `네이밍 규칙`, `개발자 계정`, `서비스 계정`, `읽기전용`, `DDL`, `DML`, `Owner`, `롤`, `권한`, `비용`

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
| v1.1 | 2026-04-15 | AI(claude-code) | 탐색 가이드 추가, 공용 키워드 분리 — 고유 키워드만 라우팅에 사용, 공용 키워드는 플랫폼 확인 재질문 |
| v1.0 | 2026-04-15 | AI(claude-code) | 최초 작성 — database-index.md 대체, RDBMS/Snowflake 라우팅 |
