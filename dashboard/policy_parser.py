"""main-policy.md 파싱 및 관리"""

import re
from pathlib import Path
from typing import Any

import yaml


def load_main_policy(path: str) -> dict[str, Any]:
    """main-policy.md를 읽어 YAML 프론트매터를 파싱하여 반환"""
    text = Path(path).read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not match:
        raise ValueError("main-policy.md 파싱 실패: YAML 프론트매터를 찾을 수 없습니다")

    metadata = yaml.safe_load(match.group(1)) or {}
    metadata["_body"] = match.group(2).strip()
    return metadata


def save_main_policy(path: str, metadata: dict[str, Any]) -> None:
    """main-policy.md에 메타데이터를 YAML 프론트매터로 저장"""
    body = metadata.pop("_body", "")
    frontmatter = yaml.dump(metadata, allow_unicode=True, default_flow_style=False, sort_keys=False)
    content = f"---\n{frontmatter}---\n\n{body}\n"
    Path(path).write_text(content, encoding="utf-8")
    metadata["_body"] = body


def get_connected_mcps(metadata: dict[str, Any]) -> list[dict[str, str]]:
    """connected_mcps 목록 반환"""
    return metadata.get("connected_mcps", [])


def add_mcp(metadata: dict[str, Any], name: str, url: str, description: str) -> None:
    """MCP 등록"""
    mcps = metadata.setdefault("connected_mcps", [])
    for mcp in mcps:
        if mcp["name"] == name:
            raise ValueError(f"MCP '{name}'이 이미 등록되어 있습니다")
    mcps.append({"name": name, "url": url, "description": description})


def remove_mcp(metadata: dict[str, Any], name: str) -> None:
    """MCP 삭제"""
    mcps = metadata.get("connected_mcps", [])
    original_len = len(mcps)
    metadata["connected_mcps"] = [m for m in mcps if m["name"] != name]
    if len(metadata["connected_mcps"]) == original_len:
        raise ValueError(f"MCP '{name}'을 찾을 수 없습니다")
