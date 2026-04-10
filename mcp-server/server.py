"""범용 stdio MCP 서버 - policy.md를 읽어서 도구로 제공하는 컨테이너"""

import argparse
import re
import sys
from pathlib import Path

import yaml
from mcp.server.fastmcp import FastMCP


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="범용 stdio MCP 서버")
    parser.add_argument("--policy", required=True, help="policy.md 파일 경로")
    return parser.parse_args()


def load_policy(path: str) -> tuple[dict, str]:
    """policy.md를 읽어 YAML 프론트매터(metadata)와 본문(content)을 분리 반환"""
    text = Path(path).read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not match:
        return {}, text
    metadata = yaml.safe_load(match.group(1)) or {}
    content = match.group(2).strip()
    return metadata, content


def extract_sections(content: str) -> dict[str, str]:
    """마크다운 본문을 ## 헤딩 기준으로 섹션 분리"""
    sections: dict[str, str] = {}
    current_name = None
    current_lines: list[str] = []
    for line in content.split("\n"):
        if line.startswith("## "):
            if current_name:
                sections[current_name] = "\n".join(current_lines).strip()
            current_name = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_name:
        sections[current_name] = "\n".join(current_lines).strip()
    return sections


args = parse_args()
policy_path = Path(args.policy).resolve()

if not policy_path.exists():
    print(f"오류: policy 파일을 찾을 수 없습니다: {policy_path}", file=sys.stderr)
    sys.exit(1)

metadata, content = load_policy(str(policy_path))
sections = extract_sections(content)
domain = metadata.get("domain", "unknown")
description = metadata.get("description", "MCP 서버")

mcp = FastMCP(
    name=f"{domain}-mcp",
    instructions=f"{description}. 이 MCP의 policy를 조회하려면 get_policy 도구를 호출하세요.",
)


@mcp.tool()
def get_policy() -> str:
    """이 MCP의 전체 정책(policy.md)을 반환합니다. metadata(domain, description, conflict_priority, related_mcps)와 전체 본문을 포함합니다."""
    meta_str = yaml.dump(metadata, allow_unicode=True, default_flow_style=False)
    return f"=== metadata ===\n{meta_str}\n=== policy 본문 ===\n{content}"


@mcp.tool()
def get_section(section_name: str) -> str:
    """이 MCP 정책에서 특정 섹션만 반환합니다. section_name은 정확한 섹션 제목이어야 합니다. list_sections로 사용 가능한 섹션을 먼저 확인할 수 있습니다."""
    if section_name in sections:
        return f"## {section_name}\n{sections[section_name]}"
    # 부분 매칭
    normalized = section_name.replace(" ", "").lower()
    for name, body in sections.items():
        if name.replace(" ", "").lower() == normalized:
            return f"## {name}\n{body}"
    available = ", ".join(sections.keys())
    return f"섹션 '{section_name}'을 찾을 수 없습니다. 사용 가능한 섹션: {available}"


@mcp.tool()
def list_sections() -> str:
    """이 MCP 정책에서 사용 가능한 섹션 목록을 반환합니다."""
    return "\n".join(f"- {name}" for name in sections.keys())


if __name__ == "__main__":
    mcp.run(transport="stdio")
