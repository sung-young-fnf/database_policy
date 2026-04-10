"""Hook: MCP 도구 호출 추적 → 로그 파일에 기록

Claude CLI가 MCP 도구를 호출할 때마다 이 스크립트가 실행되어
추론 과정을 로그 파일에 JSON Lines 형식으로 기록한다.
대시보드가 이 로그를 읽어 UI에 STEP으로 표시한다.
"""

import json
import sys
import time
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent / "dashboard" / "logs" / "tool_calls.jsonl"
LOG_FILE.parent.mkdir(exist_ok=True)


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return

    tool_name = input_data.get("tool_name", "")
    hook_event = input_data.get("hook_event_name", "")

    # MCP 도구 호출만 필터
    if not tool_name.startswith("mcp__"):
        return

    # MCP 이름과 도구명 추출 (mcp__kitchen-mcp__get_policy → kitchen-mcp, get_policy)
    parts = tool_name.split("__")
    mcp_name = parts[1] if len(parts) >= 3 else "unknown"
    action = parts[2] if len(parts) >= 3 else "unknown"

    log_entry = {
        "timestamp": time.time(),
        "event": hook_event,
        "mcp_name": mcp_name,
        "action": action,
        "tool_name": tool_name,
        "tool_input": input_data.get("tool_input", {}),
        "session_id": input_data.get("session_id", ""),
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
