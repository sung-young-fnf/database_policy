# DB 계정 관리 MCP 오케스트레이터

DB 계정 분리 정책(Oracle/PostgreSQL)을 MCP로 제공하여, 사용자의 자연어 질의에 AI가 문서를 자율 탐색하여 답변하는 시스템.

## 핵심 컨셉

- **폴더 기반 MCP**: database 폴더 내 9개 .md 문서를 개별 문서로 제공
- AI가 `list_documents` → `get_document` → `search_documents` 순서로 **필요한 문서를 스스로 탐색**
- 문서 내 `[[]]` 참조를 따라 **연쇄 탐색** (표준 → 런북, 런북 → 점검 등)
- **답변만 목적** — AI가 직접 DB 조작(action)을 하지 않음. 절차/규칙을 안내
- **Claude Max 구독으로 동작** — API Key 불필요 (Claude CLI subprocess 방식)

## 프로젝트 구조

```
policy_agent/
├── dashboard/
│   ├── main.py              # 대시보드 FastAPI 서버 (포트 8001)
│   ├── orchestrator.py      # Claude CLI subprocess + hook 로그 수집
│   ├── policy_parser.py     # YAML 프론트매터 파싱
│   ├── main-policy.md       # 메인 정책 (database-mcp 연결)
│   └── static/
│       ├── index.html       # 프론트엔드 UI
│       └── kb.html          # KB 문서 미리보기 (Outline 스타일)
├── mcp-server/
│   ├── server.py            # 범용 stdio MCP 서버 (policy.md 기반, 레거시)
│   └── folder_server.py     # 폴더 기반 stdio MCP 서버 (database용)
├── database/                # DB 계정 관리 KB 문서 (9개)
│   ├── Database Platform Index.md        ← IX-DB-001 (AI 진입점)
│   ├── Database Service Dependencies.md  ← IX-DB-002
│   ├── standards/
│   │   ├── DB 계정 분리 규칙.md           ← ST-DB-001
│   │   ├── DB 계정 네이밍 규칙.md         ← ST-DB-002
│   │   └── PostgreSQL Owner 관리 규칙.md  ← ST-DB-003
│   └── runbooks/
│       ├── Oracle DB 계정 생성 런북.md     ← RB-DB-001
│       ├── PostgreSQL DB 계정 생성 런북.md ← RB-DB-002
│       ├── DB 개발자 계정 요청 대응 런북.md     ← RB-DB-003
│       └── DB 계정 정책 점검 런북.md       ← RB-DB-004
├── hooks/
│   └── tool_tracker.py      # Hook: MCP 도구 호출 추적
├── .mcp.json                # Claude Code MCP 서버 등록
├── requirements.txt
└── CLAUDE.md                # 문서 작성 가이드
```

## 문서 구조

### 표준 (Standards) — "무엇을/왜"

| 문서 | 문서ID | 내용 |
|------|--------|------|
| DB 계정 분리 규칙 | ST-DB-001 | 3종 계정 분리, DDL 제거 사유, 패스워드 정책 |
| DB 계정 네이밍 규칙 | ST-DB-002 | _svc/_oper/_adm/_ops 패턴, DBMS별 대소문자 |
| PostgreSQL Owner 관리 규칙 | ST-DB-003 | Owner 3단 분리, Role 체인, NOLOGIN 원칙 |

### 런북 (Runbooks) — "어떻게"

| 문서 | 문서ID | 대응레벨 | 내용 |
|------|--------|---------|------|
| Oracle DB 계정 생성 런북 | RB-DB-001 | 🔴 | 23ai PL/SQL ON SCHEMA + 19c DDL_DML_ROLE |
| PostgreSQL DB 계정 생성 런북 | RB-DB-002 | 🔴 | Owner 3단 분리 생성 절차 |
| DB 개발자 계정 요청 대응 런북 | RB-DB-003 | 🟡 | 단일/다중 스키마, NOINHERIT, DA# |
| DB 계정 정책 점검 런북 | RB-DB-004 | 🟢 | 스크립트 추출, Owner 혼재 점검 SQL |

## 설치

```bash
pip install -r requirements.txt
```

## 실행

### 1. 대시보드 서버 시작

```bash
cd dashboard
python main.py
```

브라우저에서 `http://localhost:8001` 접속

### 2. Claude Code에서 MCP 도구 사용

`.mcp.json`에 database-mcp가 등록되어 있어, Claude Code를 이 프로젝트에서 열면 자동으로 연결됩니다.

```
database-mcp → list_documents, get_document, search_documents
```

## MCP 서버

### 폴더 기반 서버 (database용)

`mcp-server/folder_server.py` — 폴더 내 .md 파일들을 개별 문서로 제공

```bash
python mcp-server/folder_server.py \
  --folder database \
  --name database-mcp \
  --description "DB 계정 생성 및 관리 정책"
```

| 도구 | 설명 |
|------|------|
| `list_documents` | 문서 목록 반환 |
| `get_document` | 특정 문서 전체 내용 반환 (부분 매칭 지원) |
| `search_documents` | 키워드로 문서 검색 (매칭된 줄 반환) |

## AI 답변 흐름

```
사용자: "PostgreSQL 서비스 계정 만들어줘"
    ↓
AI: list_documents → 9개 문서 목록 확인
    ↓
AI: get_document("Database Platform Index") → 키워드 라우팅 확인
    ↓
AI: get_document("PostgreSQL DB 계정 생성 런북") → 생성 절차 확인
    ↓
AI: [[DB 계정 네이밍 규칙]] 참조 발견 → get_document("DB 계정 네이밍 규칙")
    ↓
AI: 절차 + 네이밍 + SQL을 종합하여 답변
```

## 기술 스택

| 영역 | 기술 |
|------|------|
| 대시보드 | Python FastAPI + HTML/JS |
| MCP 서버 | Python MCP SDK (stdio) |
| Claude 연동 | Claude CLI subprocess (Claude Max) |
| 도구 호출 추적 | Claude Code Hook |
| KB 문서 | 마크다운 (Outline KB 형식) |
