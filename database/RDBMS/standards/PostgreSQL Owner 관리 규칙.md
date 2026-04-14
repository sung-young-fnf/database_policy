# PostgreSQL Owner 관리 규칙

| 필드 | 값 |
|-----|-----|
| 도메인 | 보안 |
| 플랫폼 | `AWS` |
| 서비스 | `RDS`, `PostgreSQL` |
| 유형 | 표준 |
| 상태 | 초안 |
| 소유자 | @윤형도 |
| 최종수정 | 2026-04-10 |
| 문서ID | ST-DB-003 |
| 키워드 | `Owner`, `Owner 분리`, `Owner 3단`, `object_owner_role`, `dml_role`, `_adm`, `NOLOGIN`, `SET ROLE`, `Role 체인`, `Schema Owner`, `Object Owner`, `public schema`, `Owner 혼재`, `PostgreSQL 권한`, `DEFAULT PRIVILEGES`, `RENAME` |
| 관련문서 | [[DB 계정 분리 규칙]], [[DB 계정 네이밍 규칙]], [[PostgreSQL DB 계정 생성 런북]], [[DB 계정 정책 점검 런북]] |

PostgreSQL에서 Database/Schema/Object의 소유권(Owner)을 3단 계층으로 분리하는 규칙을 정의한다. Owner 혼재 방지, NOLOGIN Role 원칙, SET ROLE 자동 설정, public schema 금지 등을 포함한다. 이 규칙은 **PostgreSQL 전용**이며, Oracle에는 Schema=User 구조로 Owner 분리 개념이 없다. 계정 유형은 [[DB 계정 분리 규칙]], 네이밍은 [[DB 계정 네이밍 규칙]] 참조.

## Owner 3단 분리

| 단계 | 역할 | LOGIN | 담당 | 권한 범위 |
|------|------|-------|------|----------|
| **1단: `_adm`** | DATABASE Owner + Schema Owner | LOGIN | DBA/파트장급 | 스키마 생성/삭제 전용 |
| **2단: `object_owner_role`** | Object Owner | NOLOGIN | 개발자/도구가 SET ROLE | 테이블 DDL+DML |
| **3단: `dml_role`** | DML 권한 | NOLOGIN | 서비스 계정이 SET ROLE | SELECT/INSERT/UPDATE/DELETE + 시퀀스 + EXECUTE |

## Role 체인 구조

```
fnfadm (rds_superuser) — Instance 레벨 전용
  └── {서비스명}_adm (LOGIN, DB+Schema Owner)
        └── 스키마 생성/삭제 전용, object_owner_role 멤버십 없음
        └── DROP SCHEMA CASCADE로 스키마+오브젝트 일괄 삭제 가능
  └── {서비스명}_object_owner_role (NOLOGIN, Object Owner)
        ├── {서비스명}_oper (개발자) ← SET ROLE 자동
        ├── {서비스명}_{이니셜}_oper (개인) ← 보안 강화 시
        └── {서비스명}_{도구명}_ops (시스템) ← SET ROLE 자동
  └── {스키마명}_dml_role (NOLOGIN, DML)
        └── {서비스명}_svc (앱) ← SET ROLE 자동
```

## 핵심 원칙

| # | 원칙 | 상세 |
|---|------|------|
| 1 | **`_adm`에 `object_owner_role` 멤버십 미부여** | 오브젝트 개별 조작 차단. 필요 시 `DROP SCHEMA CASCADE`로 일괄 삭제 |
| 2 | **DDL 계정은 `SET ROLE object_owner_role`로 실행** | Object Owner 통일 (모든 테이블이 `object_owner_role` 소유) |
| 3 | **서비스 계정은 `dml_role` 부여 (기본)** | 예외 시 `object_owner_role` 부여 가능 — [[DB 계정 분리 규칙]] 참조 |
| 4 | **마스터 계정(postgres/fnfadm) = Instance 레벨 전용** | Database Owner로 사용 금지 |
| 5 | **타 스키마 권한 추가 시 NOLOGIN Role에 GRANT** | login 계정에 직접 GRANT 금지 |
| 6 | **`object_owner_role`에 스키마별 CREATE, USAGE 명시 부여** | 스키마 추가 시마다 실행 필수 |

## 서비스 최소 단위 정책

| 구분 | 설명 |
|------|------|
| **Schema 단위 (기본)** | `_adm`이 DB+Schema Owner, `object_owner_role`이 Object Owner |
| **Database 단위 (레거시/예외)** | 3rd-party 솔루션 등 스키마가 여러 개로 구성된 경우 |

## DEFAULT PRIVILEGES 규칙

`object_owner_role`이 생성한 객체에 대해 `dml_role`에 자동 권한 부여:

```sql
ALTER DEFAULT PRIVILEGES FOR ROLE {서비스명}_object_owner_role IN SCHEMA {스키마명}
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {스키마명}_dml_role;
ALTER DEFAULT PRIVILEGES FOR ROLE {서비스명}_object_owner_role IN SCHEMA {스키마명}
  GRANT USAGE, SELECT ON SEQUENCES TO {스키마명}_dml_role;
ALTER DEFAULT PRIVILEGES FOR ROLE {서비스명}_object_owner_role IN SCHEMA {스키마명}
  GRANT EXECUTE ON FUNCTIONS TO {스키마명}_dml_role;
```

## Role/User RENAME 시 주의

| 저장 방식 | 예시 | RENAME 후 |
|----------|------|----------|
| **OID 기반 (자동 반영)** | `GRANT` 멤버십, `ALTER DEFAULT PRIVILEGES`, `SCHEMA AUTHORIZATION`, `DATABASE OWNER` | 자동 추적됨 |
| **문자열 기반 (수동 갱신 필수)** | `ALTER USER SET role TO`, `ALTER USER SET search_path TO` | 기존 문자열 그대로 → **로그인 실패/권한 오류** |

> RENAME 시 반드시 `ALTER USER xxx SET role TO [새이름];` 재설정 필요

## 금지 사항

| 금지 항목 | 사유 |
|-------|-----|
| public schema 사용 | 보안, 권한 분리 |
| 마스터 계정(postgres/fnfadm)을 Database Owner로 사용 | Instance 레벨 전용 |
| login 계정에 직접 GRANT (타 스키마 권한 추가 시) | NOLOGIN Role에 GRANT 해야 함 |
| `_adm`에 `object_owner_role` 멤버십 부여 | 오브젝트 개별 조작 차단 원칙 |
| SET ROLE 없이 DDL 실행 (INHERIT 계정) | Object Owner 혼재 발생 |

## 관련 문서

* > 관련: [[DB 계정 분리 규칙]] — 계정 3종 분리 (서비스/개발자/읽기전용)
* > 관련: [[DB 계정 네이밍 규칙]] — Role/계정 이름 규칙
* > 구현 런북: [[PostgreSQL DB 계정 생성 런북]] — Owner 3단 분리 생성 절차
* > 구현 런북: [[DB 계정 정책 점검 런북]] — Owner 혼재 점검 SQL
* > 관련: [[DB 개발자 계정 요청 대응 런북]] — SET ROLE 사용법, NOINHERIT

---

## 변경 이력

| 버전 | 일자 | 작성자 | 변경내용 |
|-----|-----|-----|------|
| v1.1 | 2026-04-13 | AI(claude-code) | 키워드 추가: DEFAULT PRIVILEGES/RENAME |
| v1.0 | 2026-04-10 | AI(claude-code) | 최초 작성 — 01-dbuser.md에서 PostgreSQL Owner 정책 추출 |
