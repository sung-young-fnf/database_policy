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

SYSTEM_PROMPT = """당신은 레스토랑 MCP 정책 오케스트레이터입니다.

연결된 MCP 도구들이 있습니다. 각 MCP는 get_policy 도구를 제공합니다.
도구를 호출해야만 해당 MCP의 policy.md를 읽을 수 있습니다.

사용자의 질의를 분석하여 다음 절차를 따르세요:

1. MCP 선택: 도구 이름과 설명을 보고, 질의와 관련된 MCP의 get_policy를 호출하세요
2. 정책 분석: 반환된 policy.md를 읽고 관련 정보를 찾으세요
3. 추가 탐색: policy.md 내용이나 related_mcps를 보고 다른 MCP도 참조해야 한다면 추가로 get_policy를 호출하세요 (이미 읽은 MCP는 제외)
4. 충돌 해소: 정책 간 충돌이 있으면 conflict_priority가 낮은 쪽을 우선하세요
5. 답변 생성: 관련 정책을 조합하여 답변을 생성하세요
6. 답변 검증: 답변이 질의에 충분히 답하는지 스스로 검증하세요. 부족하면 추가 MCP를 탐색하세요
7. 반드시 출처를 [출처: MCP명 §섹션명] 형태로 명시하세요

사용자의 질문에 오탈자나 맞춤법 오류가 있더라도 의도를 파악하여 정상적으로 처리하세요.
"""


def _build_allowed_tools(connected_mcps: list[dict]) -> list[str]:
    """연결된 MCP만 도구 사용 허용"""
    tools = []
    for mcp in connected_mcps:
        name = mcp["name"]
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
