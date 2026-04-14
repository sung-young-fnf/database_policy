# RDBMS vs Snowflake 라우팅 테스트 질문지

> 목적: 사용자 질문 시 AI가 RDBMS 문서와 Snowflake 문서를 올바르게 구분하는지 확인
> 확인 방법: 대시보드에서 tool_tracker 로그의 get_document 호출 경로 확인

## 테스트 방법

1. 대시보드에서 각 질문을 입력
2. 답변 아래 STEP 경로에서 어떤 문서를 읽었는지 확인
3. 기대 문서와 실제 문서가 일치하는지 체크

---

## A. RDBMS로 가야 하는 질문 (Snowflake 안 봐야 함)

| # | 질문 | 기대 문서 | Snowflake 봤는지 |
|---|------|----------|----------------|
| A1 | PostgreSQL 서비스 계정 만들어줘 | RB-DB-002 | |
| A2 | Oracle 19c에 개발자 계정 추가하고 싶어 | RB-DB-003 → RB-DB-001 | |
| A3 | DB 패스워드 규칙이 어떻게 돼? | ST-DB-001 | |
| A4 | _oper 계정이 뭐야? | ST-DB-002 또는 ST-DB-001 | |
| A5 | Owner 혼재가 발견됐는데 어떻게 정리해? | RB-DB-004 | |
| A6 | PostgreSQL Role RENAME하면 문제 생겨? | ST-DB-003 | |
| A7 | DA# 도구로 DB 접속하려면 어떤 계정 써야 해? | RB-DB-003 | |

## B. Snowflake로 가야 하는 질문 (RDBMS 안 봐야 함)

| # | 질문 | 기대 문서 | RDBMS 봤는지 |
|---|------|----------|-------------|
| B1 | Snowflake 사용자 계정 만들어줘 | SF 사용자 계정 관리 런북 | |
| B2 | 웨어하우스 사이즈 변경하고 싶어 | SF 웨어하우스 관리 런북 | |
| B3 | Snowflake 쿼리가 너무 느린데 어떻게 해? | SF 쿼리 성능 트러블슈팅 런북 | |
| B4 | 이번 달 Snowflake 비용이 갑자기 올랐어 | SF 비용 이상 대응 런북 | |
| B5 | Snowflake RBAC 롤 구조 알려줘 | SF RBAC 표준 | |
| B6 | Snowflake 네이밍 규칙이 뭐야? | SF 네이밍 규칙 | |
| B7 | Snowsight 접속이 안 돼 | SF 사용자 계정 관리 런북 | |

## C. 햇갈리는 질문 (키워드가 겹침)

| # | 질문 | 정답 | 햇갈리는 이유 |
|---|------|------|-------------|
| C1 | 계정 생성해줘 | 추가 질문 필요 | "계정"이 RDBMS/Snowflake 둘 다 해당 |
| C2 | 권한 부여 방법 알려줘 | 추가 질문 필요 | RDBMS GRANT vs Snowflake RBAC |
| C3 | 네이밍 규칙이 뭐야? | 추가 질문 필요 | 양쪽 다 네이밍 규칙 문서 있음 |
| C4 | 읽기전용 계정 만들어줘 | 추가 질문 필요 | RDBMS readonly vs Snowflake READER |
| C5 | 스키마 생성 방법 알려줘 | 추가 질문 필요 | PostgreSQL schema vs Snowflake schema |
| C6 | 개발자한테 DB 접근 권한 주려면? | 추가 질문 필요 | RDBMS _oper vs Snowflake 사용자 계정 |
| C7 | 서비스 의존성 확인하고 싶어 | 추가 질문 필요 | RDBMS Dependencies vs SF Dependencies |
| C8 | 계정 점검 방법 알려줘 | 추가 질문 필요 | RDBMS 점검 런북 vs Snowflake 없음(→RDBMS) |

## D. 판정 기준

- **PASS**: 기대 문서만 읽고 답변
- **WARN**: 기대 문서를 읽었지만 다른 쪽 문서도 같이 읽음 (불필요한 로딩)
- **FAIL**: 엉뚱한 문서를 읽고 답변
- **GOOD**: C 그룹에서 "어떤 DB인가요?" 같은 추가 질문을 함
