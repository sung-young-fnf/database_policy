# Database MCP 답변 품질 테스트지

> **목적**: database-mcp에 등록된 KB 문서가 사용자 질의에 대해 정확하게 답변하는지 검증
> **방법**: 각 질문을 대시보드 또는 Claude Code에 입력하고, 기대 답변/탐색 경로와 비교
> **작성일**: 2026-04-13

---

## 채점 기준

| 항목 | 배점 | 설명 |
|------|------|------|
| 정확성 | 40% | 기대 답변의 핵심 내용이 포함되어 있는가 |
| 문서 탐색 | 30% | 올바른 문서를 올바른 순서로 조회했는가 |
| SQL 제공 | 20% | 필요한 SQL이 코드 블록으로 포함되어 있는가 |
| 출처 명시 | 10% | [출처: 문서명 &sect;섹션] 형태로 근거를 명시했는가 |

---

## TC-01. PostgreSQL 서비스 계정 생성 요청

**질문**: PostgreSQL로 신규 서비스 계정 만들어야 하는데, 서비스명은 insa이고 앱에서 쓸 계정이 필요해요

**기대 답변 핵심**:
- 이 요청은 에스컬레이션 대상 (DBA팀 전달)
- 전체 생성 순서 안내: Instance 레벨 → Database 레벨 → 서비스 계정 순서
- `insa_adm` (DB+Schema Owner), `insa_object_owner_role` (NOLOGIN), `insa_sch_dml_role` (NOLOGIN), `insa_oper` (개발자), `insa_svc` (서비스 계정) 안내
- `insa_svc`에는 `dml_role` 부여 (DML 전용)
- DBA팀에 전달할 요청 정보 템플릿 제공

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "계정 생성, PostgreSQL" 키워드 매칭
3. `get_document("PostgreSQL DB 계정 생성 런북")` → 생성 절차 확인
4. `get_document("DB 계정 네이밍 규칙")` → [[]] 참조 따라 네이밍 확인

---

## TC-02. Oracle 23ai 계정 생성 요청

**질문**: Oracle 23ai 환경에서 INSA 서비스 신규로 만들어야 하는데 스키마 계정이랑 개발자 계정 둘 다 필요합니다

**기대 답변 핵심**:
- 에스컬레이션 대상
- 스키마 계정 = 서비스 계정 (앱이 기존 스키마 계정으로 접속)
- 개발자 계정은 `INSA_OPER` (스키마별 별도)
- DDL 부여는 PL/SQL 블록 (ON SCHEMA 방식, 변수 2개만 변경)
- 테이블스페이스 `INSA_TS` 생성 필요
- `OPER_TS` 불필요 (23ai는 ON SCHEMA로 제한)
- PL/SQL 블록 SQL 코드 제공

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "계정 생성, Oracle" 매칭
3. `get_document("Oracle DB 계정 생성 런북")` → 23ai 절차 확인
4. `get_document("DB 계정 네이밍 규칙")` → 네이밍 확인

---

## TC-03. Oracle 19c 레거시 개발자 계정 분리

**질문**: 지금 Oracle 19c 쓰고 있는데 개발자랑 앱이 같은 스키마 계정 쓰고 있어요. 개발자 계정 분리하고 싶습니다

**기대 답변 핵심**:
- 에스컬레이션 대상
- 기존 스키마 계정은 건드리지 않음 (앱 리스크)
- `{서비스명}_OPER` 개발자 계정 신규 생성
- `DDL_DML_ROLE` 생성 (PDB 내 최초 1회, 29개 권한 번들)
- `GRANT DDL_DML_ROLE TO _OPER;` 1줄로 권한 부여
- `OPER_TS` (1MB) 테이블스페이스로 본인 스키마 생성 물리적 차단
- 서비스 TS에만 QUOTA UNLIMITED
- 한계 설명: 기존 스키마 계정 DDL 제거 불가, 계정 분리 요건만 충족

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "계정 생성, Oracle" 매칭
3. `get_document("Oracle DB 계정 생성 런북")` → 19c 레거시 절차 확인
4. `get_document("DB 계정 분리 규칙")` → [[]] 참조로 분리 원칙 확인

---

## TC-04. 계정 이름 규칙 질문

**질문**: DB 계정 이름을 어떻게 지어야 하나요? Oracle이랑 PostgreSQL 둘 다 알려주세요

**기대 답변 핵심**:
- Oracle: 대문자, `{스키마명}` (서비스), `{스키마명}_OPER` (23ai 개발자), `{서비스명}_OPER` (19c 개발자)
- PostgreSQL: 소문자, `_adm` / `_oper` / `_ops` / `_svc` 접미사
- DB명에서 `_db` 접미사는 붙이지 않음 (예: `ai_agent_db` → `ai_agent_adm`)
- `object_owner_role`, `dml_role` 네이밍 패턴
- Oracle/PostgreSQL 네이밍 비교표

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "네이밍" 키워드 매칭
3. `get_document("DB 계정 네이밍 규칙")` → 네이밍 규칙 전체 확인

---

## TC-05. 서비스 계정과 개발자 계정 차이

**질문**: 서비스 계정이랑 개발자 계정이 뭐가 달라요? 왜 분리해야 하나요?

**기대 답변 핵심**:
- 서비스 계정: 앱(WAS)이 접속, DML만 (기본)
- 개발자 계정: 개발자가 접속, DDL + DML
- 분리 사유: 보안 진단 지적 (서비스/개발자 미분리, 서비스계정 DDL 보유)
- Oracle: 스키마 계정 = 서비스 계정, `_OPER` = 개발자 계정
- PostgreSQL: `_svc` = 서비스, `_oper` = 개발자

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "계정 분리" 키워드 매칭
3. `get_document("DB 계정 분리 규칙")` → 분리 원칙/사유 확인

---

## TC-06. PostgreSQL Owner가 뭔지 모르겠음

**질문**: PostgreSQL에서 Owner 3단 분리가 뭐예요? 왜 그렇게 해야 하나요?

**기대 답변 핵심**:
- 1단: `_adm` (LOGIN) = DATABASE + Schema Owner
- 2단: `object_owner_role` (NOLOGIN) = Object Owner (DDL+DML)
- 3단: `dml_role` (NOLOGIN) = DML 전용
- DDL은 Object Owner만 실행 가능 (GRANT로 DDL 위임 불가)
- Owner 혼재 방지가 핵심 (모든 오브젝트 Owner를 NOLOGIN Role로 통일)
- `_adm`에 `object_owner_role` 멤버십 미부여 (오브젝트 개별 조작 차단)
- EC-OMS 실 사례 언급 (postgres가 일부 Object Owner로 남아있던 문제)

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "Owner, Owner 분리" 매칭
3. `get_document("PostgreSQL Owner 관리 규칙")` → Owner 3단 분리 전체 확인
4. `get_document("DB 계정 분리 규칙")` → [[]] 참조로 계정 유형 확인

---

## TC-07. 개발자가 여러 스키마 접근 필요

**질문**: 저희 개발자가 insa, asset, crm 스키마 3개를 다 접근해야 하는데 어떻게 해야 돼요? PostgreSQL 입니다

**기대 답변 핵심**:
- 단계적 대응 (🟡)
- 기본 `_oper`는 1개 스키마만 자동 설정 (`ALTER USER SET role TO`)
- 여러 스키마 → `developer_{파트명}` 계정을 **NOINHERIT**으로 생성
- 각 스키마의 `object_owner_role`을 GRANT
- 수동 `SET ROLE`로 스키마 전환 필요
- NOINHERIT 필수 이유: INHERIT이면 SET ROLE 없이 DDL 가능 → Owner 혼재!
- `SET ROLE insa_object_owner_role;` → 작업 → `RESET ROLE;` → 다음 스키마
- SQL 코드 제공

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "개발자, 다중 스키마" 매칭
3. `get_document("DB 개발자 계정 운영 런북")` → 다중 스키마 케이스 확인
4. `get_document("PostgreSQL Owner 관리 규칙")` → [[]] 참조로 NOINHERIT/Owner 원칙

---

## TC-08. DA# 도구 계정 설정

**질문**: PostgreSQL에서 DA# 도구 계정 만들려고 하는데 어떻게 설정하면 돼요?

**기대 답변 핵심**:
- 단계적 대응 (🟡)
- PostgreSQL: `{서비스명}_adm` 계정 사용 (DB Owner, INHERIT)
- 마스터 계정(postgres/fnfadm)은 Instance 레벨 전용 — DB Owner로 사용 금지
- `_adm`에 `ALTER USER SET role` 설정하지 않음
- `_adm`에 각 스키마의 `object_owner_role` 위임 (단방향만)
- 역방향 GRANT 금지
- Oracle은 스키마 계정 그대로 사용

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "도구, DA#" 매칭
3. `get_document("DB 개발자 계정 운영 런북")` → DA# 도구 계정 섹션 확인
4. `get_document("DB 계정 분리 규칙")` → [[]] 참조로 계정 유형 확인

---

## TC-09. 읽기전용 계정 생성

**질문**: 모니터링 용도로 PostgreSQL 읽기전용 계정 하나 만들어주세요. DB 전체 조회가 필요합니다

**기대 답변 핵심**:
- PG 14+: `GRANT pg_read_all_data TO [계정];` (Database 전체 읽기)
- `pg_read_all_data`는 Database 단위 (Instance 전체 아님)
- DB 2개 이상이면 각 DB에서 각각 부여
- USAGE 없이도 전 스키마 SELECT 가능
- CONNECT 권한은 별도 부여 필요
- DDL, DML 가능 권한 부여 금지
- SQL 코드 제공

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "읽기전용, 모니터링" 매칭
3. `get_document("PostgreSQL DB 계정 생성 런북")` 또는 `get_document("Oracle DB 계정 생성 런북")` → 읽기전용 섹션 확인

---

## TC-10. 패스워드 규칙 확인

**질문**: DB 계정 패스워드 규칙이 어떻게 되나요?

**기대 답변 핵심**:
- 최소 12자리 이상
- 영대문자 2개 + 영소문자 2개 + 숫자 2개 + 특수문자 2개 이상
- 허용 특수문자: `!@#$%^&*()_+-=`

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → 라우팅 확인
3. `get_document("DB 계정 분리 규칙")` → 패스워드 정책 섹션 확인
4. 또는 `search_documents("패스워드")` → 키워드 검색

---

## TC-11. Owner 혼재 점검

**질문**: PostgreSQL에서 Owner가 섞여있는지 확인하고 싶어요. 점검 쿼리 좀 주세요

**기대 답변 핵심**:
- 직접처리 대응 (🟢)
- 간단 점검 SQL 제공 (Owner 불일치 확인 — MISMATCH 표시)
- 전체 현황 추출 SQL 제공 (Database → Schema → Object Owner, PG 11~18 호환)
- Owner 불일치 수정 SQL: `ALTER TABLE ... OWNER TO {object_owner_role};`
- `pg_class` + `pg_proc` UNION ALL 구조

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "점검, Owner 혼재" 매칭
3. `get_document("DB 계정 정책 점검 런북")` → Owner 점검 SQL 확인

---

## TC-12. 기존 계정 권한 역추출

**질문**: 기존 PostgreSQL 계정의 권한을 전부 확인해서 스크립트로 뽑아내고 싶어요

**기대 답변 핵심**:
- 직접처리 대응 (🟢)
- 계정 생성 스크립트 추출 SQL 제공 (target CTE 계정명만 변경)
- 8단계: 일치율 요약, CREATE USER, Role 멤버십, 스키마 권한, 시퀀스, 함수, DEFAULT PRIVILEGES, 개별 오브젝트 GRANT
- 추출된 DDL로 동일 계정 재생성 가능

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "스크립트 추출, 점검" 매칭
3. `get_document("DB 계정 정책 점검 런북")` → 스크립트 추출 SQL 확인

---

## TC-13. 서비스 계정에 DDL 줘도 되는지

**질문**: 앱에서 Flyway로 마이그레이션 할 때 ALTER TABLE을 직접 실행해야 하는데, 서비스 계정에 DDL 권한을 줘도 되나요?

**기대 답변 핵심**:
- 기본 정책: 서비스 계정에는 `dml_role` 부여 (DML 전용)
- **예외 허용**: 앱이 스키마 마이그레이션을 직접 수행하는 경우 `object_owner_role` 부여 가능
- 또는 `_ops` 도구 계정을 별도 생성하여 Flyway 전용으로 사용 (권장)
- `_ops` = 시스템/도구 (DA#, Flyway, Prisma 등)
- SQL: `GRANT {서비스명}_object_owner_role TO {서비스명}_svc;`

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "서비스 계정, DDL" 매칭
3. `get_document("DB 계정 분리 규칙")` → 서비스 계정 예외 정책 확인
4. `get_document("DB 개발자 계정 운영 런북")` → [[]] 참조로 _ops 계정 안내

---

## TC-14. _svc, _oper, _ops, _adm 차이

**질문**: PostgreSQL에서 _svc, _oper, _ops, _adm이 각각 뭔가요? 헷갈려요

**기대 답변 핵심**:
- `_adm`: DBA/파트장급, DATABASE + Schema Owner, 스키마 생성/삭제 전용
- `_oper`: 개발자 (사람), `object_owner_role` 부여, SET ROLE 자동
- `_ops`: 시스템/도구 (DA#, Flyway, Prisma), `object_owner_role` 부여
- `_svc`: 서비스 계정 (앱, WAS, 배치), `dml_role` 부여 (기본)
- `_oper`와 `_ops` 차이: 사람 vs 시스템 (감사 추적 분리)

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "계정 유형" 매칭
3. `get_document("DB 계정 네이밍 규칙")` → 접미사별 역할 확인
4. `get_document("DB 계정 분리 규칙")` → [[]] 참조로 계정 유형 정의

---

## TC-15. 계정 변경 시 영향도 확인

**질문**: DB 계정 분리 작업을 하면 다른 서비스에 영향이 있을까요?

**기대 답변 핵심**:
- 계정 변경 시 관련 서비스 영향도 설명
- PostgreSQL: Owner 변경 시 기존 GRANT/DEFAULT PRIVILEGES에 영향
- Oracle: 스키마 계정을 서비스 계정으로 유지하므로 앱 설정 변경 불필요
- 서비스 간 의존성 관계 안내

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → 라우팅 확인
3. `get_document("Database Service Dependencies")` → 의존성/영향도 확인
4. `get_document("DB 계정 분리 규칙")` → [[]] 참조로 분리 원칙

---

## TC-16. 권한 미부여 테이블 찾기

**질문**: 특정 계정한테 SELECT 권한이 안 준 테이블이 있는지 확인하고 싶어요

**기대 답변 핵심**:
- 직접처리 대응 (🟢)
- `has_table_privilege` 기반 미부여 테이블 추출 SQL 제공
- 계정명 부분만 변경하면 사용 가능
- 출력: schemaname, tablename, tableowner

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "권한, 미부여" 매칭
3. `get_document("DB 계정 정책 점검 런북")` → 미부여 확인 SQL 제공

---

## TC-17. PostgreSQL에서 스키마 추가 시 해야 할 것

**질문**: 기존 PostgreSQL 서비스에 스키마를 하나 더 추가해야 하는데, 권한 설정을 어떻게 해야 하나요?

**기대 답변 핵심**:
- `_adm`으로 `CREATE SCHEMA [스키마명] AUTHORIZATION [서비스명]_adm;`
- `GRANT CREATE, USAGE ON SCHEMA [스키마명] TO [서비스명]_object_owner_role;`
- 새 `dml_role` 필요 시: `CREATE ROLE [스키마명]_dml_role NOLOGIN;`
- DEFAULT PRIVILEGES 설정
- 기존 `_oper`, `_svc` 계정에 추가 스키마 권한 부여 필요

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "스키마 추가" 매칭
3. `get_document("PostgreSQL DB 계정 생성 런북")` → 스키마 생성 절차
4. `get_document("PostgreSQL Owner 관리 규칙")` → [[]] 참조로 Owner 규칙 확인

---

## TC-18. Role RENAME 주의사항

**질문**: PostgreSQL에서 Role 이름을 바꿔야 하는데 주의할 점이 있나요?

**기대 답변 핵심**:
- OID 기반 (자동 반영): GRANT 멤버십, ALTER DEFAULT PRIVILEGES, SCHEMA AUTHORIZATION, DATABASE OWNER
- 문자열 기반 (수동 갱신 필수): `ALTER USER SET role TO`, `ALTER USER SET search_path TO`
- RENAME 후 `ALTER USER xxx SET role TO [새이름];` 재설정 필수
- 안 하면 로그인 실패/권한 오류 발생

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `search_documents("RENAME")` → 키워드 검색
3. `get_document("PostgreSQL Owner 관리 규칙")` 또는 관련 문서 → RENAME 주의사항

---

## TC-19. EAS 서비스 전체 구축 (복합 질문)

**질문**: EAS 서비스를 PostgreSQL로 신규 구축하려고 합니다. 스키마는 smartbill, patuah, eas 3개이고, 개발자가 3개 스키마를 모두 접근해야 합니다. 서비스 계정도 스키마별로 필요합니다.

**기대 답변 핵심**:
- 에스컬레이션 대상 (DBA팀 전달)
- `eas_adm` (DB Owner)
- NOLOGIN Role 6개: 스키마별 `object_owner_role` + `dml_role`
- 개발자 계정 3개: 스키마별 `_oper` (SET ROLE 자동)
- 서비스 계정 3개: 스키마별 `_svc` (DML 전용)
- 다중 스키마 계정 1개: `developer_eas` (NOINHERIT)
- Instance → Database 레벨 분리된 전체 SQL
- DEFAULT PRIVILEGES 설정

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "계정 생성, PostgreSQL" 매칭
3. `get_document("PostgreSQL DB 계정 생성 런북")` → 생성 절차
4. `get_document("DB 개발자 계정 운영 런북")` → [[]] 참조로 다중 스키마 개발자
5. `get_document("DB 계정 네이밍 규칙")` → [[]] 참조로 네이밍 확인
6. `get_document("PostgreSQL Owner 관리 규칙")` → [[]] 참조로 Owner 규칙

---

## TC-20. 오타/비공식 표현 처리

**질문**: postgrse 서비스계정 만드는법 알려줘

**기대 답변 핵심**:
- "postgrse"를 PostgreSQL로 인식하여 정상 답변
- PostgreSQL 서비스 계정(`_svc`) 생성 절차 안내
- 오타에도 불구하고 정확한 문서 탐색

**기대 탐색 경로**:
1. `list_documents` → 문서 목록 확인
2. `get_document("Database Platform Index")` → "PostgreSQL, 서비스계정" 매칭
3. `get_document("PostgreSQL DB 계정 생성 런북")` → 서비스 계정 절차

---

## 문서 커버리지 매트릭스

각 테스트 케이스가 어떤 문서를 검증하는지 매핑:

| 문서 | TC |
|------|----|
| Database Platform Index (IX-DB-001) | 모든 TC (진입점) |
| Database Service Dependencies (IX-DB-002) | TC-15 |
| DB 계정 분리 규칙 (ST-DB-001) | TC-05, TC-10, TC-13, TC-14, TC-15 |
| DB 계정 네이밍 규칙 (ST-DB-002) | TC-01, TC-02, TC-04, TC-14, TC-19 |
| PostgreSQL Owner 관리 규칙 (ST-DB-003) | TC-06, TC-07, TC-17, TC-18 |
| Oracle DB 계정 생성 런북 (RB-DB-001) | TC-02, TC-03, TC-09 |
| PostgreSQL DB 계정 생성 런북 (RB-DB-002) | TC-01, TC-09, TC-17, TC-19, TC-20 |
| DB 개발자 계정 운영 런북 (RB-DB-003) | TC-07, TC-08, TC-13, TC-19 |
| DB 계정 정책 점검 런북 (RB-DB-004) | TC-11, TC-12, TC-16 |

---

## 테스트 결과 기록표

| TC | 정확성 (40) | 탐색 (30) | SQL (20) | 출처 (10) | 합계 | 비고 |
|----|------------|----------|---------|----------|------|------|
| TC-01 | | | | | | |
| TC-02 | | | | | | |
| TC-03 | | | | | | |
| TC-04 | | | | | | |
| TC-05 | | | | | | |
| TC-06 | | | | | | |
| TC-07 | | | | | | |
| TC-08 | | | | | | |
| TC-09 | | | | | | |
| TC-10 | | | | | | |
| TC-11 | | | | | | |
| TC-12 | | | | | | |
| TC-13 | | | | | | |
| TC-14 | | | | | | |
| TC-15 | | | | | | |
| TC-16 | | | | | | |
| TC-17 | | | | | | |
| TC-18 | | | | | | |
| TC-19 | | | | | | |
| TC-20 | | | | | | |
| **평균** | | | | | | |
