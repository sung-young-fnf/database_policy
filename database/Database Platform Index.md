# Database Platform Index

| 필드 | 값 |
|-----|-----|
| 도메인 | 운영 |
| 플랫폼 | `Database` |
| 유형 | 인덱스 |
| 상태 | 초안 |
| 소유자 | @윤형도 |
| 최종수정 | 2026-04-10 |
| 문서ID | IX-DB-001 |
| 키워드 | `Database`, `DB`, `Oracle`, `PostgreSQL`, `RDS`, `Aurora`, `계정`, `account`, `DDL`, `DML`, `Owner`, `_svc`, `_oper`, `_adm`, `_ops`, `계정 생성`, `계정 분리`, `개발자 계정`, `서비스 계정`, `DB 계정 생성 방법`, `DB 권한`, `DB 점검` |
| 관련문서 | [[Service Catalog]], [[Platform Index]] |

Database(Oracle, PostgreSQL) 플랫폼 관련 모든 문서의 AI 진입점. DB 계정 생성, 계정 분리 규칙, 네이밍, Owner 관리, 개발자 계정, 정책 점검 등 사용자 질문의 키워드를 아래 라우팅 테이블과 매칭하여 적절한 문서로 이동한다.

## 키워드 라우팅

| 사용자 의도 (키워드) | 이동할 문서 | 대응레벨 |
|--------------|--------|------|
| 계정 분리, 서비스 계정, DDL 제거, 권한 범위, 패스워드 | [[DB 계정 분리 규칙]] | - |
| 네이밍, 이름 규칙, _svc, _oper, _adm, _ops | [[DB 계정 네이밍 규칙]] | - |
| Owner, Owner 분리, object_owner_role, NOLOGIN, Role 체인, public schema, RENAME, 이름 변경 | [[PostgreSQL Owner 관리 규칙]] | - |
| Oracle, 계정 생성, 스키마 계정, DDL_DML_ROLE, 19c, 23ai, PL/SQL, 읽기전용 | [[Oracle DB 계정 생성 런북]] | 🔴 에스컬레이션 |
| PostgreSQL, 계정 생성, _adm, _svc, SET ROLE, DEFAULT PRIVILEGES, Aurora, 읽기전용, pg_read_all_data | [[PostgreSQL DB 계정 생성 런북]] | 🔴 에스컬레이션 |
| 개발자 계정, 접근 권한, 다중 스키마, NOINHERIT, developer_, DA#, 도구 계정 | [[DB 개발자 계정 운영 런북]] | 🟡 단계적 |
| 점검, Owner 혼재, 권한 미부여, 스크립트 추출, 정기 점검 | [[DB 계정 정책 점검 런북]] | 🟢 직접처리 |
| 의존성, 장애 영향, 계정 변경 영향 | [[Database Service Dependencies]] | - |

## 문서 목록

### 표준

| 문서 | 서비스 | 설명 |
|-----|-----|-----|
| [[DB 계정 분리 규칙]] | Oracle, PostgreSQL | 3종 계정 분리(서비스/개발자/읽기전용), DDL 제거 사유, 패스워드 정책 |
| [[DB 계정 네이밍 규칙]] | Oracle, PostgreSQL | _svc/_oper/_adm/_ops 패턴, DBMS별 대소문자, 문서ID 채번 |
| [[PostgreSQL Owner 관리 규칙]] | PostgreSQL | Owner 3단 분리, Role 체인, NOLOGIN 원칙, SET ROLE, public schema 금지 |

### 런북

| 문서 | 서비스 | 대응레벨 | 설명 |
|-----|-----|------|-----|
| [[Oracle DB 계정 생성 런북]] | Oracle | 🔴 에스컬레이션 | 23ai(★5안) PL/SQL ON SCHEMA + 19c(★4안) DDL_DML_ROLE |
| [[PostgreSQL DB 계정 생성 런북]] | PostgreSQL | 🔴 에스컬레이션 | Owner 3단 분리, Instance→Database→서비스 계정 순서 |
| [[DB 개발자 계정 운영 런북]] | Oracle, PostgreSQL | 🟡 단계적 | 단일/다중 스키마, NOINHERIT, DA# 도구 계정 |
| [[DB 계정 정책 점검 런북]] | PostgreSQL | 🟢 직접처리 | 스크립트 추출, 권한 미부여, Owner 혼재 점검 SQL |

## 서비스 정보

> 담당자/등급: [[Service Catalog]] 기술 의존성: [[Database Service Dependencies]]

## 에스컬레이션 경로

| 단계 | 담당 | 연락처 |
|-----|-----|-----|
| 1차 접수 | 사무보조 / 챗봇 | 사내 챗봇 |
| 2차 처리 | DBA팀 @최종현 | Teams / 메일 |
| 3차 외부 지원 | AWS 기술지원 | 서비스 요청 |

## 변경 이력

| 버전 | 일자 | 작성자 | 변경내용 |
|-----|-----|-----|------|
| v1.2 | 2026-04-13 | AI(claude-code) | 라우팅 키워드 추가: RENAME/이름 변경(ST-DB-003), 읽기전용/pg_read_all_data(RB-DB-001, RB-DB-002) |
| v1.1 | 2026-04-13 | AI(claude-code) | 키워드 추가: _ops |
| v1.0 | 2026-04-10 | AI(claude-code) | 최초 작성 — 표준 3개 + 런북 4개 + Dependencies 라우팅 |
