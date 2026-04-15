# DB 계정 네이밍 규칙

| 필드 | 값 |
|-----|-----|
| 도메인 | 데이터베이스 |
| 플랫폼 | `RDBMS` |
| 서비스 | `RDS`, `Oracle`, `PostgreSQL` |
| 유형 | 표준 |
| 상태 | 초안 |
| 소유자 | @윤형도 |
| 최종수정 | 2026-04-10 |
| 문서ID | ST-DB-002 |
| 키워드 | `네이밍`, `naming`, `명명 규칙`, `_svc`, `_oper`, `_adm`, `_ops`, `object_owner_role`, `dml_role`, `DDL_DML_ROLE`, `OPER_TS`, `계정 이름`, `DB 네이밍` |
| 관련문서 | [[DB 계정 분리 규칙]], [[PostgreSQL Owner 관리 규칙]], [[Oracle DB 계정 생성 런북]], [[PostgreSQL DB 계정 생성 런북]] |

DB 계정 및 Role의 네이밍 규칙을 정의한다. Oracle(대문자)과 PostgreSQL(소문자)의 DBMS별 패턴, 접미사별 용도를 명시한다. 계정 유형(서비스/개발자/읽기전용)의 정의는 [[DB 계정 분리 규칙]] 참조.

## 계정 유형 및 네이밍 패턴

| 항목 | Oracle 23ai+ | Oracle 19c- | PostgreSQL |
|------|---------------------|---------------------|------------|
| 스키마 계정 (= 서비스) | `{스키마명}` (대문자) | `{스키마명}` (대문자) | N/A |
| 서비스 계정 (앱용) | = 스키마 계정 | = 스키마 계정 | `{서비스명}_svc` (소문자) |
| 개발자 계정 | `{스키마명}_OPER` (스키마별) | `{서비스명}_OPER` (DB 전체 1개) | `{서비스명}_oper` (공유) 또는 `{서비스명}_{이니셜}_oper` (개인) |
| 시스템 DDL 계정 (도구) | N/A | N/A | `{서비스명}_{도구명}_ops` (소문자) |
| 읽기전용 계정 | 솔루션별 별도 네이밍 | 솔루션별 별도 네이밍 | 솔루션별 별도 네이밍 |

## PostgreSQL 전용 네이밍

| 유형 | 패턴 | LOGIN | 예시 |
|------|------|-------|------|
| `_adm` | `{서비스명}_adm` | LOGIN | `insa_adm`, `ai_agent_adm` |
| `object_owner_role` | `{서비스명}_object_owner_role` | NOLOGIN | `insa_object_owner_role` |
| `dml_role` | `{스키마명}_dml_role` | NOLOGIN | `insa_sch_dml_role`, `ai_agent_dml_role` |
| `_oper` | `{서비스명}_oper` | LOGIN | `insa_oper`, `ai_agent_oper` |
| `developer_` | `developer_{서비스명}` 또는 `developer_{이니셜}` | LOGIN, **NOINHERIT** | `developer_eas`, `developer_sykim` |
| `_ops` | `{서비스명}_{도구명}_ops` | LOGIN | `ai_agent_prisma_ops` |
| `_svc` | `{서비스명}_svc` | LOGIN | `insa_svc`, `ai_agent_svc` |
| Database명 | `{서비스명}_db` (`_db` 선택적) | - | `insa_db`, `ai_agent_db` |
| Schema명 | `{서비스명}` 또는 `{서비스명}_sch` | - | `insa_sch`, `ai_agent` |

> `_adm`/`_oper`/`_ops`/`_svc` 네이밍 시 DB명의 `_db` 접미사를 **붙이지 않음**
> - 예: DB명 `ai_agent_db` → `ai_agent_adm` (O), `ai_agent_db_adm` (X)

> PostgreSQL Role/Owner 계층에 대한 상세 규칙은 [[PostgreSQL Owner 관리 규칙]] 참조.

## Oracle 전용 네이밍

### 23ai+ 

| 유형 | 패턴 | 예시 |
|------|------|------|
| 스키마 계정 (= 서비스) | `{스키마명}` (대문자) | `INSA`, `ERP` |
| 개발자 계정 | `{스키마명}_OPER` (스키마별) | `INSA_OPER`, `ERP_OPER` |
| 테이블스페이스 | `{스키마명}_TS` | `INSA_TS` |
| Schema명 | `{서비스명}` (대문자) | `INSA` |

### 19c- 

| 유형 | 패턴 | 예시 |
|------|------|------|
| 스키마 계정 (= 서비스) | `{스키마명}` (대문자) | `INSA`, `FEC` |
| 개발자 계정 | `{서비스명}_OPER` (DB 전체 1개) | `HR_OPER`, `EAS_OPER` |
| DDL Role | `DDL_DML_ROLE` (PDB 내 1개) | `DDL_DML_ROLE` |
| 개발자 테이블스페이스 | `OPER_TS` (1MB, 생성 방지용) | `OPER_TS` |

## DDL 권한 부여 방식

| DBMS | 방식 | 설명 |
|------|------|------|
| Oracle 23ai+ | PL/SQL 블록 (ON SCHEMA) | 변수 2개(`v_schema`, `v_grantee`) 변경으로 27개 권한 일괄 부여 |
| Oracle 19c- | `DDL_DML_ROLE` (Global ANY) | Role 1개에 28개 권한 번들, `GRANT DDL_DML_ROLE TO _OPER;` 1줄 |
| PostgreSQL | `object_owner_role` (NOLOGIN) | `SET ROLE`로 DDL 실행 → Object Owner 통일 |

## 문서ID 채번 규칙

| 유형 | 코드 | 예시 |
|------|------|------|
| 표준 | `ST-DB` | ST-DB-001 |
| 런북 | `RB-DB` | RB-DB-001 |
| 인덱스 | `IX-DB` | IX-DB-001 |

## 금지 사항

| 금지 항목 | 사유 |
|-------|-----|
| DB명의 `_db` 접미사를 계정명에 포함 | `ai_agent_db_adm` (X) → `ai_agent_adm` (O) |
| Oracle 개발자 계정에 소문자 사용 | Oracle은 대문자 표준 |
| PostgreSQL 계정에 대문자 사용 | PostgreSQL은 소문자 표준 |
| 한글 계정명 | 시스템 호환성 |

## 관련 문서

* > 관련: [[DB 계정 분리 규칙]] — 계정 유형(서비스/개발자/읽기전용) 정의
* > 관련: [[PostgreSQL Owner 관리 규칙]] — PG Role 네이밍과 Owner 계층
* > 구현 런북: [[Oracle DB 계정 생성 런북]] — Oracle 네이밍 적용 절차
* > 구현 런북: [[PostgreSQL DB 계정 생성 런북]] — PostgreSQL 네이밍 적용 절차
* > 관련: [[DB 개발자 계정 요청 대응 런북]] — 개발자/도구 계정 네이밍 적용
* > 관련: [[DB 계정 정책 점검 런북]] — 네이밍 규칙 준수 점검

---

## 변경 이력

| 버전 | 일자 | 작성자 | 변경내용 |
|-----|-----|-----|------|
| v1.1 | 2026-04-13 | AI(claude-code) | 관련 문서에 [[DB 계정 정책 점검 런북]] 참조 추가 |
| v1.0 | 2026-04-10 | AI(claude-code) | 최초 작성 |
