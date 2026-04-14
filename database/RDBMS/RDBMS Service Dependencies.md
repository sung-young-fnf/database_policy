# RDBMS Service Dependencies

| 필드 | 값 |
|-----|-----|
| 도메인 | 운영 |
| 플랫폼 | `Database` |
| 유형 | 인덱스 |
| 상태 | 초안 |
| 소유자 | @윤형도 |
| 최종수정 | 2026-04-10 |
| 문서ID | IX-DB-002 |
| 키워드 | `의존성`, `영향도`, `Database`, `Oracle`, `PostgreSQL`, `RDS`, `장애 영향`, `서비스 관계`, `계정 분리`, `Owner`, `dependency`, `object_owner_role`, `dml_role`, `DDL_DML_ROLE` |
| 관련문서 | [[Service Catalog]], [[RDBMS Platform Index]] |

Database 플랫폼 내 서비스 간 기술 의존성을 정의한다. DB 계정 변경/장애 시 영향 범위 파악, 계정 분리 작업의 영향도 분석에 활용한다.

## 서비스 간 의존성

| 소비 서비스 | 의존 서비스 | 의존 내용 |
|--------|--------|-------|
| 애플리케이션 (WAS) | 서비스 계정 (`_svc` / 스키마 계정) | DB 접속, DML 실행 |
| 개발자 (IDE/CLI) | 개발자 계정 (`_oper` / `_OPER`) | DDL+DML 실행 |
| DA#/접근제어 도구 | 도구 계정 (`_adm` / `_ops`) | DB 관리, 스키마 설계 |
| 마이그레이션 도구 (Flyway/Prisma) | 시스템 DDL 계정 (`_ops`) | 스키마 마이그레이션 |
| 모니터링 (aidba) | 읽기전용 계정 | SELECT, 시스템 뷰 조회 |
| GHA 파이프라인 | 서비스 계정 / Task Role | 배포 시 DB 접속 |
| PostgreSQL 서비스 계정 | `dml_role` (NOLOGIN) | SET ROLE로 DML 권한 획득 |
| PostgreSQL 개발자/도구 | `object_owner_role` (NOLOGIN) | SET ROLE로 DDL 권한 획득 |

## 장애 영향도

| 장애 서비스 | 영향 받는 서비스 | 영향 내용 | 심각도 |
|--------|-----------|-------|-----|
| 서비스 계정 권한 변경 | 애플리케이션 전체 | DML 실패 → 서비스 장애 | 높음 |
| `object_owner_role` 변경/삭제 | 개발자, 도구, 마이그레이션 | DDL 불가 → 배포/개발 중단 | 높음 |
| `dml_role` 변경/삭제 | 서비스 계정 (`_svc`) | DML 불가 → 서비스 장애 | 높음 |
| `_adm` 계정 변경 | DA#, 접근제어 도구 | DB 관리 불가 | 중간 |
| Owner 혼재 발생 | 해당 Object의 ALTER/DROP | DDL 불가 → 스키마 변경 차단 | 중간 |
| PostgreSQL Role RENAME | SET ROLE 설정된 계정 | 로그인 실패/권한 오류 (문자열 기반) | 높음 |
| DDL_DML_ROLE 변경 (Oracle 19c) | 모든 `_OPER` 계정 | DDL 권한 일괄 변경 | 높음 |

## 서비스별 관련 문서

### Oracle

* > 런북: [[Oracle DB 계정 생성 런북]] — 계정 생성/변경 절차
* > 표준: [[DB 계정 분리 규칙]] — 19c/23ai 계정 분리 방식
* > 표준: [[DB 계정 네이밍 규칙]] — Oracle 대문자 네이밍

### PostgreSQL

* > 런북: [[PostgreSQL DB 계정 생성 런북]] — Owner 3단 분리 생성 절차
* > 런북: [[DB 계정 정책 점검 런북]] — Owner 혼재/권한 점검
* > 표준: [[PostgreSQL Owner 관리 규칙]] — Role 체인, NOLOGIN 원칙

### 공통

* > 런북: [[DB 개발자 계정 운영 런북]] — 개발자/도구 계정 사용법
* > 표준: [[DB 계정 분리 규칙]] — 3종 계정 분리 정책

## 관련 조직

| 부서 | 역할 | 담당 서비스 |
|-----|-----|--------|
| DBA팀 (EA팀) | DB 계정 생성/변경, Owner 관리, 정기 점검 | Oracle, PostgreSQL 전체 |
| 서비스팀 (개발팀) | 계정 요청, 접속 테스트, GHA 파이프라인 수정 | 담당 서비스 |

## 관련 문서

* > 관련: [[RDBMS Platform Index]]
* > 관련: [[Service Catalog]]

---

## 변경 이력

| 버전 | 일자 | 작성자 | 변경내용 |
|-----|-----|-----|------|
| v1.3 | 2026-04-14 | AI(claude-code) | 문서명 변경: Database Service Dependencies → RDBMS Service Dependencies |
| v1.2 | 2026-04-13 | AI(claude-code) | 키워드 추가: dependency/object_owner_role/ dml_role/DDL_DML_ROLE |
| v1.1 | 2026-04-13 | AI(claude-code) | 플랫폼 필드 수정 (IX-DB-001과 통일) |
| v1.0 | 2026-04-10 | AI(claude-code) | 최초 작성 |
