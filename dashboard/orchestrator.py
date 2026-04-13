"""Claude 오케스트레이터 - Claude CLI subprocess + hook 로그 수집"""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any

LOG_DIR = Path(__file__).parent / "logs"
LOG_FILE = LOG_DIR / "tool_calls.jsonl"
PROJECT_DIR = Path(__file__).parent.parent

SYSTEM_PROMPT = """당신은 DB 계정 관리 정책 오케스트레이터입니다.

연결된 MCP 도구들이 있습니다. 각 MCP는 list_documents, get_document, search_documents 도구를 제공합니다.

사용자의 질의를 분석하여 다음 절차를 따르세요:

1. 문서 목록 확인: list_documents로 사용 가능한 문서 목록을 확인하세요
2. 진입점 조회: get_document("Database Platform Index")로 키워드 라우팅 테이블을 확인하세요
3. 문서 조회: 사용자 질문의 키워드와 매칭되는 문서를 get_document로 조회하세요
4. 연쇄 탐색: 문서 내 [[문서명]] 참조가 있으면 해당 문서도 get_document로 추가 조회하세요
5. 키워드 검색: 필요 시 search_documents로 키워드 검색하여 관련 문서를 추가 탐색하세요
6. 답변 생성: 조회한 문서들을 종합하여 답변을 생성하세요
7. 대응레벨 확인: 문서의 대응레벨을 확인하고:
   - 🟢 직접처리: 절차를 직접 안내
   - 🟡 단계적: 1차 안내 후 에스컬레이션 조건 안내
   - 🔴 에스컬레이션: 필요 정보 수집 후 DBA팀 전달 안내
8. Oracle과 PostgreSQL을 구분하여 답변하세요
9. SQL 코드는 코드 블록으로 제공하세요
10. 반드시 출처를 [출처: 문서명 §섹션명] 형태로 명시하세요
11. 문서를 찾지 못하면 "해당 문서가 없습니다. DBA팀(@윤형도)에 문의하세요."로 안내하세요

사용자의 질문에 오탈자나 맞춤법 오류가 있더라도 의도를 파악하여 정상적으로 처리하세요.
"""


def _build_allowed_tools(connected_mcps: list[dict]) -> list[str]:
    """연결된 MCP만 도구 사용 허용"""
    tools = []
    for mcp in connected_mcps:
        name = mcp["name"]
        # 폴더 기반 MCP (folder_server.py)
        tools.append(f"mcp__{name}__list_documents")
        tools.append(f"mcp__{name}__get_document")
        tools.append(f"mcp__{name}__search_documents")
        # 레거시 MCP (server.py)
        tools.append(f"mcp__{name}__get_policy")
        tools.append(f"mcp__{name}__get_section")
        tools.append(f"mcp__{name}__list_sections")
    return tools


def _parse_hook_logs(start_time: float) -> list[dict]:
    """hook이 기록한 로그에서 start_time 이후 항목을 읽어 reasoning_steps로 변환"""
    steps = []
    if not LOG_FILE.exists():
        return steps

    step_number = 0
    seen = set()
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                # start_time 이후 로그만 수집
                if entry.get("timestamp", 0) < start_time:
                    continue
                # PreToolUse만 STEP으로 표시 (PostToolUse는 중복 방지)
                if entry.get("event") != "PreToolUse":
                    continue

                mcp_name = entry.get("mcp_name", "unknown")
                action = entry.get("action", "unknown")
                key = f"{mcp_name}_{action}"
                if key in seen:
                    continue
                seen.add(key)

                step_number += 1
                if action == "get_policy":
                    desc = f"{mcp_name} 정책 조회"
                elif action == "get_section":
                    section = entry.get("tool_input", {}).get("section_name", "")
                    desc = f"{mcp_name} §{section} 조회"
                elif action == "list_sections":
                    desc = f"{mcp_name} 섹션 목록 조회"
                else:
                    desc = f"{mcp_name} → {action}"

                steps.append({
                    "step_number": step_number,
                    "description": desc,
                    "detail": f"도구: {entry.get('tool_name', '')}",
                    "status": "completed",
                })
            except json.JSONDecodeError:
                continue

    return steps


async def process_query(
    query: str,
    connected_mcps: list[dict],
) -> dict[str, Any]:
    """사용자 질의를 Claude CLI subprocess로 처리"""
    start_time = time.time()
    session_id = str(uuid.uuid4())[:8]

    LOG_DIR.mkdir(exist_ok=True)

    # 허용할 MCP 도구 목록
    allowed_tools = _build_allowed_tools(connected_mcps)

    # 프롬프트 구성
    full_prompt = f"{SYSTEM_PROMPT}\n\n사용자 질의: {query}"

    # claude CLI 명령 구성
    cmd = [
        "claude",
        "-p", full_prompt,
        "--output-format", "json",
        "--max-turns", "15",
    ]

    # 허용할 도구 추가
    for tool in allowed_tools:
        cmd.extend(["--allowedTools", tool])

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_DIR),
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=120,  # 2분 타임아웃
        )

        output = stdout.decode("utf-8", errors="replace").strip()

        # JSON 파싱 시도
        try:
            result_json = json.loads(output)
            # claude CLI --output-format json은 {"type":"result","result":"..."} 형식
            if isinstance(result_json, dict) and "result" in result_json:
                answer = result_json["result"]
            elif isinstance(result_json, dict) and "content" in result_json:
                answer = result_json["content"]
            else:
                answer = output
        except json.JSONDecodeError:
            answer = output

    except asyncio.TimeoutError:
        answer = "오류: Claude CLI 응답 시간이 초과되었습니다 (120초)."
    except FileNotFoundError:
        answer = "오류: claude CLI를 찾을 수 없습니다. Claude Code가 설치되어 있는지 확인하세요."
    except Exception as e:
        answer = f"오류: {str(e)}"

    # hook 로그에서 추론 과정 수집
    reasoning_steps = _parse_hook_logs(start_time)

    # 로그가 없으면 기본 STEP 추가
    if not reasoning_steps:
        reasoning_steps.append({
            "step_number": 1,
            "description": "Claude CLI 실행",
            "detail": f"질의 처리 완료 (허용 MCP: {', '.join(m['name'] for m in connected_mcps)})",
            "status": "completed",
        })

    duration_ms = int((time.time() - start_time) * 1000)

    # 답변에서 출처 추출 (간단한 파싱)
    sources = _extract_sources(answer)

    return {
        "answer": answer,
        "sources": sources,
        "reasoning_steps": reasoning_steps,
        "duration_ms": duration_ms,
        "session_id": session_id,
    }


def _extract_sources(answer: str) -> list[dict]:
    """답변 텍스트에서 [출처: MCP명 §섹션명] 패턴을 추출"""
    import re
    sources = []
    pattern = r'\[출처:\s*([^\]§]+?)(?:\s*§\s*([^\]]+))?\]'
    for match in re.finditer(pattern, answer):
        mcp_name = match.group(1).strip()
        section = match.group(2).strip() if match.group(2) else "전체"
        sources.append({
            "mcp_name": mcp_name,
            "section": section,
            "excerpt": "",
        })
    return sources
