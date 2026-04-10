"""폴더 기반 stdio MCP 서버 - 폴더 내 .md 파일들을 개별 문서로 제공"""

import argparse
import re
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="폴더 기반 stdio MCP 서버")
    parser.add_argument("--folder", required=True, help="문서 폴더 경로")
    parser.add_argument("--name", default="folder-mcp", help="MCP 서버 이름")
    parser.add_argument("--description", default="폴더 기반 문서 MCP", help="MCP 설명")
    return parser.parse_args()


def load_documents(folder: Path) -> dict[str, str]:
    """폴더 내 모든 .md 파일을 재귀적으로 읽어 {파일명(확장자 제외): 본문} 딕셔너리 반환"""
    docs: dict[str, str] = {}
    for md_file in sorted(folder.rglob("*.md")):
        name = md_file.stem  # 확장자 제외한 파일명
        text = md_file.read_text(encoding="utf-8")
        # YAML 프론트매터 제거
        match = re.match(r"^---\s*\n.*?\n---\s*\n(.*)", text, re.DOTALL)
        content = match.group(1).strip() if match else text.strip()
        docs[name] = content
    return docs


args = parse_args()
folder_path = Path(args.folder).resolve()

if not folder_path.exists() or not folder_path.is_dir():
    print(f"오류: 폴더를 찾을 수 없습니다: {folder_path}", file=sys.stderr)
    sys.exit(1)

documents = load_documents(folder_path)

mcp = FastMCP(
    name=args.name,
    instructions=f"{args.description}. list_documents로 문서 목록을 확인하고, get_document로 필요한 문서를 읽고, search_documents로 키워드 검색하세요.",
)


@mcp.tool()
def list_documents() -> str:
    """이 MCP에서 사용 가능한 문서 목록을 반환합니다. 문서명으로 get_document를 호출하여 내용을 조회할 수 있습니다."""
    return "\n".join(f"- {name}" for name in documents.keys())


@mcp.tool()
def get_document(document_name: str) -> str:
    """특정 문서의 전체 내용을 반환합니다. document_name은 list_documents에서 확인한 문서명을 사용하세요. 부분 매칭도 지원합니다."""
    if document_name in documents:
        return documents[document_name]
    # 부분 매칭
    normalized = document_name.replace(" ", "").lower()
    for name, content in documents.items():
        if name.replace(" ", "").lower() == normalized:
            return content
    # 포함 매칭
    for name, content in documents.items():
        if normalized in name.replace(" ", "").lower():
            return f"[매칭된 문서: {name}]\n\n{content}"
    available = ", ".join(documents.keys())
    return f"문서 '{document_name}'을 찾을 수 없습니다. 사용 가능한 문서: {available}"


@mcp.tool()
def search_documents(keyword: str) -> str:
    """키워드로 문서를 검색합니다. 문서 내용에 키워드가 포함된 모든 문서의 이름과 매칭된 줄을 반환합니다."""
    results: list[str] = []
    keyword_lower = keyword.lower()
    for name, content in documents.items():
        matched_lines: list[str] = []
        for line in content.split("\n"):
            if keyword_lower in line.lower():
                matched_lines.append(line.strip())
        if matched_lines:
            preview = "\n".join(matched_lines[:5])
            if len(matched_lines) > 5:
                preview += f"\n... 외 {len(matched_lines) - 5}줄"
            results.append(f"📄 {name} ({len(matched_lines)}건 매칭)\n{preview}")
    if not results:
        return f"'{keyword}'를 포함하는 문서를 찾을 수 없습니다."
    return "\n\n".join(results)


if __name__ == "__main__":
    mcp.run(transport="stdio")
