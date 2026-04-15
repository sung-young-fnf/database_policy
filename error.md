# RDBMS KB 문서 검토 결과

| 필드 | 값 |
|-----|-----|
| 검토일 | 2026-04-15 |
| 검토자 | AI(claude-code) |
| 대상 | database/RDBMS 폴더 내 9개 문서 + 원본 01~03-dbuser 대조 |
| 분류 | SQL 오류, 정책 모순, 누락, 개선 제안 |

---

## 판정 기준

| 판정 | 의미 |
|------|------|
| **오류** | KB 문서 자체의 잘못. 수정 필요 |
| **원본 동일 오류** | KB와 원본 모두 같은 문제 보유. 원본부터 수정 필요 |
| **오류 아님** | 원본 확인 결과 오류가 아닌 것으로 판명 |
| **누락** | KB에 있어야 할 내용이 빠짐 |
| **개선 제안** | 기능적 문제는 없으나 개선하면 좋은 항목 |

---

## 요약

| 심각도 | 번호 | 판정 | 문서 | 내용 |
|-------|------|------|------|------|
| **높음** | 1 | **원본 동일 오류** | RB-DB-001 | `'+DATA'` ASM 경로 → RDS에서 실행 불가 |
| **높음** | 2 | **원본 동일 오류** | RB-DB-004 | ACL 파싱 로직 버그 (role 이름 혼동 + 첫 매칭만 반환) |
| **높음** | 3 | **오류** | RB-DB-003 | `_adm`이 `object_owner_role` 객체 관리 가능하다는 서술 — 01-dbuser 정책상 멤버십 미부여이므로 불가 |
| **중간** | 4 | **누락** | ST-DB-002 | `developer_` 패턴이 네이밍 규칙에 미정의 |
| **중간** | 5 | **오류 아님** | RB-DB-003 | ~~예시 DB명 `easdb` 불일치~~ → `_db` 선택적이므로 유효 |
| **낮음** | 6 | **개선 제안** | RB-DB-004 | Step 2 계정명 하드코딩 (CTE 통일 권장) |
| **낮음** | 7 | **개선 제안** | RB-DB-002 | 읽기전용 계정에 login 직접 GRANT (원칙 #5 예외 미명시) |
| **낮음** | 8 | **개선 제안** | RB-DB-002 | `_oper` search_path 미설정 |
| **낮음** | 9 | **오류** | IX-DB-001 | 키워드 trailing comma |
| --- | --- | --- | --- | **아래는 원본 대조 시 추가 발견** |
| **참고** | 10 | **원본 불일치** | 02-dbuser 원본 | Role 네이밍 패턴이 01-dbuser와 다름 (`_role_owner` vs `_object_owner_role`) |
| **참고** | 11 | **원본 불일치** | 02-dbuser 원본 | Schema Owner 설정이 01-dbuser와 다름 (NOLOGIN Role vs `_adm`) |

---

## SQL 오류

### 1. [높음] RB-DB-001 Step 1: ASM 경로 — RDS 환경에서 실행 불가

**판정**: **원본 동일 오류** — 01-dbuser.md 23ai 섹션에 동일한 `'+DATA'` 경로 사용

**위치**: `Oracle DB 계정 생성 런북.md` Step 1 (23ai 스키마 계정 생성)

**현재 SQL**:
```sql
CREATE TABLESPACE [스키마명]_TS
  DATAFILE '+DATA' SIZE 1G
  AUTOEXTEND ON MAXSIZE 100G;
```

**문제**:
- `'+DATA'`는 on-premise ASM(Automatic Storage Management) 전용 경로
- 메타블록 플랫폼이 `AWS RDS`인데 RDS에서는 datafile 경로를 지정할 수 없어 에러 발생
- 같은 문서 Step 4(19c)는 `DATAFILE SIZE 1M`으로 경로 없이 작성 → 같은 문서 내 일관성 없음

**원본 확인**:
- 01-dbuser.md line 110: `DATAFILE '+DATA' SIZE 1G` (23ai 템플릿) — **동일 오류**
- 01-dbuser.md line 352: `DATAFILE SIZE 1M` (19c 템플릿) — 경로 없음 (정상)
- 23ai 전체 예시(line 194)도 `'+DATA'` 사용 → 원본 전체적으로 23ai에 ASM 경로 하드코딩

**수정안** (원본 + KB 모두):
```sql
CREATE TABLESPACE [스키마명]_TS
  DATAFILE SIZE 1G
  AUTOEXTEND ON MAXSIZE 100G;
```

---

### 2. [높음] RB-DB-004 Step 1: DEFAULT PRIVILEGES ACL 파싱 버그

**판정**: **원본 동일 오류** — 03-dbuser_policy_check.md에 완전 동일한 SQL

**위치**: `DB 계정 정책 점검 런북.md` Step 1 섹션 7번 (DEFAULT PRIVILEGES)

**현재 SQL**:
```sql
CASE
    WHEN acl::text LIKE '%r%' THEN 'SELECT'
    WHEN acl::text LIKE '%a%' THEN 'INSERT'
    WHEN acl::text LIKE '%w%' THEN 'UPDATE'
    WHEN acl::text LIKE '%d%' THEN 'DELETE'
    WHEN acl::text LIKE '%D%' THEN 'TRUNCATE'
    WHEN acl::text LIKE '%x%' THEN 'REFERENCES'
    WHEN acl::text LIKE '%t%' THEN 'TRIGGER'
    ELSE 'ALL'
END
```

**문제 (2가지)**:

**(a) role 이름과 권한 문자 혼동**:
- PostgreSQL ACL 문자열 형식: `prcs_user=arwd/owner`
- `LIKE '%r%'`는 권한 부분의 `r`(SELECT)뿐만 아니라 role 이름 `prcs_user`의 `r`도 매칭
- 이름에 `r`, `a`, `w`, `d` 등이 포함된 계정은 항상 잘못된 결과 출력

**(b) CASE는 첫 매칭만 반환**:
- `arwd`(SELECT+INSERT+UPDATE+DELETE)가 모두 있어도 CASE는 첫 번째 매칭 `SELECT`만 반환
- 나머지 INSERT, UPDATE, DELETE 3개 권한 누락

**원본 확인**: 03-dbuser_policy_check.md line 147~168에 완전 동일한 SQL. 원본의 버그를 KB가 그대로 가져옴.

**수정 방향**:
- 권한 부분만 추출: `split_part(split_part(acl::text, '=', 2), '/', 1)`
- 개별 권한 문자를 unnest하여 각각 매핑:

```sql
-- 수정안 (섹션 7 교체)
SELECT 7,
    'ALTER DEFAULT PRIVILEGES FOR ROLE ' || pg_get_userbyid(d.defaclrole) ||
    CASE WHEN n.nspname IS NOT NULL THEN ' IN SCHEMA ' || n.nspname ELSE '' END ||
    ' GRANT ' ||
    CASE ch
        WHEN 'r' THEN 'SELECT'
        WHEN 'a' THEN 'INSERT'
        WHEN 'w' THEN 'UPDATE'
        WHEN 'd' THEN 'DELETE'
        WHEN 'D' THEN 'TRUNCATE'
        WHEN 'x' THEN 'REFERENCES'
        WHEN 't' THEN 'TRIGGER'
        WHEN 'X' THEN 'EXECUTE'
        WHEN 'U' THEN 'USAGE'
        ELSE ch
    END ||
    ' ON ' ||
    CASE d.defaclobjtype
        WHEN 'r' THEN 'TABLES'
        WHEN 'S' THEN 'SEQUENCES'
        WHEN 'f' THEN 'FUNCTIONS'
    END ||
    ' TO ' || t.rname || ';'
FROM target t
JOIN pg_default_acl d ON true
LEFT JOIN pg_namespace n ON d.defaclnamespace = n.oid
CROSS JOIN LATERAL unnest(d.defaclacl) AS acl
CROSS JOIN LATERAL unnest(
    string_to_array(
        split_part(split_part(acl::text, '=', 2), '/', 1),
        NULL
    )
) WITH ORDINALITY AS chars(ch, ord)
WHERE split_part(acl::text, '=', 1) = t.rname
  AND ch ~ '[rawdDxtXU]'
```

> `string_to_array(..., NULL)`은 PostgreSQL에서 문자열을 개별 문자로 분리.
> 각 권한 문자마다 별도 행이 생성되어 모든 권한이 정확히 추출됨.

---

## 정책/내용 오류

### 3. [높음] RB-DB-003: `_adm`이 `object_owner_role` 객체 관리 가능하다는 서술 — 정책상 불가

**판정**: **오류** — RB-DB-003이 02-dbuser 예시를 잘못 따름. 01-dbuser 정책은 멤버십 미부여

**위치**: `DB 개발자 계정 요청 대응 런북.md` 케이스 3 PostgreSQL (line 177, 185~188)

**RB-DB-003 서술**:
> `_adm` 계정 사용. INHERIT이므로 SET ROLE 없이 `object_owner_role` 소유 객체 관리 가능.

**정책 원본 (01-dbuser.md)**:
> `_adm`은 스키마 생성/삭제 전용, `object_owner_role`에 멤버십 부여하지 않음 (오브젝트 개별 조작 차단)

**KB 정책 (ST-DB-003)**: `_adm`에 `object_owner_role` 멤버십 미부여 — **01-dbuser와 일치, 정상**

**오류 원인**:
- 02-dbuser_developer_guide.md EAS 예시(line 334)에서 `GRANT smartbill_sch_role_owner TO eas_adm;`으로 부여
- 이 예시 자체가 01-dbuser 정책을 위반한 것
- RB-DB-003이 02-dbuser 예시 기준으로 서술하여 정책과 불일치 발생

**실제 동작**:
- `_adm`에 `object_owner_role` 멤버십이 없으면 INHERIT이어도 해당 Role의 권한 상속 불가
- `_adm`은 Schema Owner이므로 `DROP SCHEMA CASCADE`는 가능하지만, 개별 `ALTER TABLE`/`DROP TABLE`은 불가
- DA#이 개별 객체 관리가 필요하면 `_ops` 계정 사용 — RB-DB-002 Step 4 참조

**수정 필요 사항**:

| 문서 | 수정 내용 |
|------|----------|
| RB-DB-003 케이스 3 | "`_adm`이 INHERIT으로 객체 관리 가능" 삭제. `_adm`은 Schema 레벨 관리 전용으로 정정. 개별 객체 관리 필요 시 `_ops` 사용 안내 |
| RB-DB-003 역할 요약표 | "Database 전체 DDL (INHERIT)" → "Database/Schema 레벨 DDL (CREATE/DROP SCHEMA)" |
| 02-dbuser 원본 | EAS 예시의 `GRANT sch_role_owner TO eas_adm;` — 01-dbuser 정책 위반. 원본 수정 권장 |

---

### 4. [중간] ST-DB-002: `developer_` 네이밍 패턴 누락

**판정**: **누락** — 원본 02-dbuser_developer_guide.md에 `developer_` 패턴이 정의/사용되나 KB 네이밍 표준에 미반영

**위치**:
- `DB 계정 네이밍 규칙.md` PostgreSQL 전용 네이밍 (line 30~39)
- `DB 개발자 계정 요청 대응 런북.md` 케이스 2 PostgreSQL (line 128)

**현재 상태**:
- RB-DB-003에서 다중 스키마 전용 `developer_` 패턴 사용:
  ```sql
  CREATE USER developer_eas WITH PASSWORD '[패스워드]' NOINHERIT;
  ```
- ST-DB-002에는 `developer_` 패턴이 정의되어 있지 않음
- ST-DB-002의 PostgreSQL 개발자 계정 패턴: `{서비스명}_oper` (공유), `{서비스명}_{이니셜}_oper` (개인)

**원본 확인**: 02-dbuser_developer_guide.md section 2.3에서 `developer_` 패턴을 정의하고 EAS 예시에서 사용. 실제 운영에서 쓰이는 패턴이므로 네이밍 표준에 반영 필요.

**수정안**: ST-DB-002 "PostgreSQL 전용 네이밍" 테이블에 추가:

| 유형 | 패턴 | LOGIN | 예시 |
|------|------|-------|------|
| `developer_` | `developer_{서비스명}` 또는 `developer_{이니셜}` | LOGIN, **NOINHERIT** | `developer_eas`, `developer_sykim` |

---

### 5. [오류 아님] ~~RB-DB-003: 예시 DB명 `easdb` 네이밍 불일치~~

**판정**: **오류 아님**

**이전 지적**: `easdb`가 ST-DB-002의 `{서비스명}_db` 패턴과 불일치한다는 지적

**원본 확인 결과**:
- 01-dbuser.md line 89: `Database명 | {서비스명}_db (소문자, **_db 선택적**)` — `_db` 접미사는 **선택 사항**
- ST-DB-002 line 38에서도 `{서비스명}_db (_db 선택적)`으로 명시
- 02-dbuser_developer_guide.md line 323: `CREATE DATABASE easdb` — 원본에서도 `easdb` 사용

따라서 `easdb`(접미사 없음)도 정책상 유효. 다만 KB 내 다른 예시(`insa_db`, `ai_agent_db`)와의 **일관성**을 위해 `eas_db`로 통일하는 것을 권장하는 수준.

---

## 개선 제안

### 6. [낮음] RB-DB-004 Step 2: 계정명 하드코딩

**판정**: **개선 제안** — 원본(03-dbuser_policy_check.md)도 동일한 하드코딩 스타일

**위치**: `DB 계정 정책 점검 런북.md` Step 2

**현재 SQL**:
```sql
AND NOT has_table_privilege('prcs_user', schemaname || '.' || tablename, 'SELECT')
```

**사유**:
- Step 1은 CTE(`WITH target AS (SELECT 'prcs_user'::text AS rname)`)로 한 곳만 변경하면 되지만 Step 2는 하드코딩
- 사용자가 계정명 변경을 빠뜨릴 위험
- 원본(03-dbuser_policy_check.md)도 동일 구조이므로 오류가 아닌 개선 제안

**수정안**: Step 1과 동일하게 CTE 패턴으로 통일:
```sql
WITH target AS (
    SELECT 'prcs_user'::text AS rname
)
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables, target t
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  AND NOT has_table_privilege(t.rname, schemaname || '.' || tablename, 'SELECT')
ORDER BY schemaname, tablename;
```

---

### 7. [낮음] RB-DB-002 Step 7: 읽기전용 계정에 login 직접 GRANT

**판정**: **개선 제안** — 원칙 예외 명시 필요

**위치**: `PostgreSQL DB 계정 생성 런북.md` Step 7 PG14 미만 (line 190-191)

**현재 SQL**:
```sql
ALTER DEFAULT PRIVILEGES FOR ROLE [서비스명]_object_owner_role IN SCHEMA [스키마명]
  GRANT SELECT ON TABLES TO [읽기전용계정명];
```

**사유**:
- ST-DB-003 원칙 #5: "타 스키마 권한 추가 시 NOLOGIN Role에 GRANT"
- 읽기전용 계정(login)에 직접 GRANT하여 형식적으로 원칙 위반
- PG 14+의 `pg_read_all_data`는 내장 NOLOGIN Role이라 문제없지만, PG 14 미만 경로는 원칙에 어긋남
- 원본 01-dbuser.md에도 동일한 패턴 사용 — 읽기전용 계정은 Role 체인 밖의 일회성 계정이므로 원칙 #5의 적용 범위 밖으로 볼 수 있음

**수정 방향**:
- ST-DB-003에 "읽기전용 계정은 원칙 #5의 예외 — Role 체인 구조와 무관한 단독 계정"임을 명시
- 또는 `_readonly_role` NOLOGIN을 만들어 통일

---

### 8. [낮음] RB-DB-002: `_oper`에 search_path 미설정

**판정**: **개선 제안** — 원본에서 주석 처리(선택 사항)

**위치**: `PostgreSQL DB 계정 생성 런북.md` Step 2~3

**현재 상태**:
- `_svc`에는 설정됨: `ALTER USER [서비스명]_svc SET search_path TO [스키마명];`
- `_oper`에는 미설정

**원본 확인**:
- 01-dbuser.md line 511: `-- ALTER USER [서비스명]_oper SET search_path TO [스키마명];` — **주석 처리** (선택 사항)
- 02-dbuser_developer_guide.md EAS 예시 line 366: `ALTER USER smartbill_oper SET search_path TO smartbill_sch;` — **설정함**
- 원본 간에도 일관되지 않음 (01은 주석, 02는 설정)

**영향**: 개발자가 항상 `스키마명.테이블명`으로 prefix를 붙여야 하는 불편

**수정안**: Step 2에 주석 포함 추가 (선택적임을 표시):
```sql
-- (선택) 개발자 편의를 위한 search_path 설정
-- ALTER USER [서비스명]_oper SET search_path TO [스키마명];
```

---

### 9. [낮음] IX-DB-001: 키워드 trailing comma

**판정**: **오류** — 단순 서식 오류

**위치**: `RDBMS Platform Index.md` 메타블록 키워드 (line 12)

**현재**:
```
| 키워드 | ... `DB 점검`,   |
```

마지막에 쉼표와 공백이 남아 있음. 삭제 필요.

---

## 원본 불일치 (참고)

> 아래는 KB 문서의 오류가 아니라 **원본(01~03-dbuser) 간의 불일치**. KB는 올바른 쪽(01-dbuser.md)을 선택했으나, 원본 02-dbuser_developer_guide.md를 직접 참조하는 사람에게 혼동을 줄 수 있음.

### 10. [참고] 원본 02의 Role 네이밍 패턴 불일치

**해당 원본**: 02-dbuser_developer_guide.md

| 항목 | 01-dbuser.md (정책) & KB | 02-dbuser_developer_guide.md (개발자 가이드) |
|------|--------------------------|---------------------------------------------|
| Object Owner Role | `{서비스명}_object_owner_role` | `{스키마명}_role_owner` (예: `smartbill_sch_role_owner`) |
| DML Role | `{스키마명}_dml_role` | `{스키마명}_role_dml` (예: `smartbill_sch_role_dml`) |

**상세**:
- 01-dbuser.md line 43: `{서비스명}_object_owner_role`
- 02-dbuser_developer_guide.md line 40: `{스키마명}_role_owner`
- 02-dbuser_developer_guide.md EAS 예시: `smartbill_sch_role_owner`, `smartbill_sch_role_dml`

KB는 01-dbuser.md 기준으로 통일 (`_object_owner_role`, `_dml_role`). 이것은 올바른 선택이나, **02-dbuser_developer_guide.md 원본을 01 기준으로 네이밍 통일하는 것을 권장**.

---

### 11. [참고] 원본 02의 Schema Owner 설정 불일치

**해당 원본**: 02-dbuser_developer_guide.md EAS 예시

| 항목 | 01-dbuser.md (정책) & KB | 02-dbuser_developer_guide.md EAS 예시 |
|------|--------------------------|---------------------------------------|
| Schema Owner | `_adm` (LOGIN) | `_role_owner` (NOLOGIN) |
| `CREATE SCHEMA` | `AUTHORIZATION [서비스명]_adm` | `AUTHORIZATION smartbill_sch_role_owner` |

**상세**:
- 01-dbuser.md line 504: `CREATE SCHEMA [스키마명] AUTHORIZATION [서비스명]_adm;` — `_adm`이 Schema Owner
- 02-dbuser_developer_guide.md line 353: `CREATE SCHEMA smartbill_sch AUTHORIZATION smartbill_sch_role_owner;` — NOLOGIN Role이 Schema Owner
- 01-dbuser.md의 3단 분리: `_adm` = DB+Schema Owner, `object_owner_role` = Object Owner만

KB는 01-dbuser.md 기준을 따름 (정상). 02의 EAS 예시는 3단 분리 이전 버전으로 추정되며, 원본 업데이트 권장.

---

## 변경 이력

| 버전 | 일자 | 작성자 | 변경내용 |
|-----|-----|-----|------|
| v2.0 | 2026-04-15 | AI(claude-code) | 원본(01~03-dbuser) 대조 결과 반영 — 판정 컬럼 추가, #5 오류아님 판정, #10~11 원본 불일치 추가 |
| v1.0 | 2026-04-15 | AI(claude-code) | 최초 작성 — 9개 문서 전수 검토 |
