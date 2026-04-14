# Snowflake Platform Index

| 필드  | 값   |
|-----|-----|
| 도메인 | 데이터 |
| 플랫폼 | `Snowflake` |
| 유형  | 인덱스 |
| 상태  | 초안  |
| 소유자 | @김가람휘 |
| 최종수정 | 2026-04-10 |
| 문서ID | IX-SF-001 |
| 키워드 | `Snowflake`, `스노우플레이크`, `데이터 웨어하우스`, `DWH`, `데이터 레이크`, `데이터 공유`, `Snowflake 플랫폼 인덱스`, `Snowflake 진입점`, `Snowflake 문서 위치`, `Snowflake 어디`, `웨어하우스`, `쿼리`, `크레딧`, `비용`, `SSO`, `PAT`, `RSA`, `Snowsight` |
| 관련문서 | \[\[Service Catalog\]\], \[\[Platform Index\]\] |

Snowflake 플랫폼 인덱스 — Snowflake 관련 문서가 어디 있는지 안내하는 AI 진입점(Snowflake 진입점). 데이터 웨어하우스 운영, 사용자/권한 관리, 비용 관리, 쿼리 최적화 등 Snowflake 플랫폼 운영 문서의 위치를 제공한다.

## 키워드 라우팅

| 키워드 | 타겟  | 설명  |
|-----|-----|-----|
| 계정 목록, 리전, 에디션 | \[\[Snowflake Account Inventory\]\] | Snowflake 계정 자산 목록 |
| 웨어하우스, WH, 사이즈, 오토서스펜드 | \[\[Snowflake Warehouse Inventory\]\] | 웨어하우스별 설정 및 담당팀 |
| 사용자, 계정 생성, 계정 신청, 권한, SSO, PAT, RSA | \[\[Snowflake 사용자 계정 관리 런북\]\] | 계정 신청·접속 방법·인증 방식 |
| 웨어하우스 생성, WH 변경, 사이즈 조정 | \[\[Snowflake 웨어하우스 관리 런북\]\] | WH 생성·변경·삭제 절차 |
| 쿼리 성능, 슬로우쿼리, 최적화 | \[\[Snowflake 쿼리 성능 트러블슈팅 런북\]\] | 슬로우쿼리 진단 및 최적화 |
| 비용, 크레딧, 과금, 비용 이상 | \[\[Snowflake 비용 이상 대응 런북\]\] | 크레딧 급증 알림 대응 |
| 네이밍, 이름 규칙 | \[\[Snowflake 네이밍 규칙\]\] | DB·스키마·테이블·WH 네이밍 |
| RBAC, 롤 구조, 권한 표준 | \[\[Snowflake RBAC 표준\]\] | 롤 계층 및 최소권한 원칙 |
| 의존성, 장애 영향 | \[\[Snowflake Service Dependencies\]\] | 상위/하위 서비스 의존성 |

## 관리 개요

| 항목  | 내용  |
|-----|-----|
| 플랫폼 | Snowflake Data Cloud |
| 에디션 | Enterprise |
| 리전  | AWS ap-northeast-2 (Seoul) |
| 인증  | Microsoft SSO (기본), PAT (로컬 자동화), RSA (서비스/배치) |
| ID/PW | **미지원** — 기존 계정도 2026년 상반기 내 SSO 전환 예정 |
| 관리팀 | AI 엔지니어링팀 (@김가람휘) |
| 계정 신청 | JIRA 서비스데스크 |

## 인증 방식 요약

| 인증 방식 | 사용 대상 | 용도  |
|-------|-------|-----|
| **SSO** (Microsoft) | User  | 일반 사용자 접속 (Snowsight, 도구 연결) |
| **PAT** (Personal Access Token) | User  | 로컬 개발 자동화 |
| **RSA** (키페어) | Service | 서비스 / 배치 시스템 |

> 개인키(.p8), PAT 토큰 등 **인증 정보는 외부 공유 및 Git 저장소 업로드를 금지**합니다.

## 상위 참조

> 서비스 담당자/벤더: \[\[Service Catalog\]\] 플랫폼 라우팅: \[\[Platform Index\]\]

## 변경 이력

| 버전  | 일자  | 작성자 | 변경내용 |
|-----|-----|-----|------|
| v1.1 | 2026-04-10 | AI(claude-code) | Notion Snowflake 가이드 기반 업데이트 — 담당자, 인증 방식, 관리 개요 반영 |
| v1.0 | 2026-04-10 | AI(claude-code) | 최초 작성 |