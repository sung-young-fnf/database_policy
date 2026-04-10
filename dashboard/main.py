"""대시보드 FastAPI 서버 - 메인 MCP

MCP 연결/해제 시 main-policy.md와 .mcp.json을 동기화한다.
"""

import json
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from policy_parser import (
    load_main_policy,
    save_main_policy,
    get_connected_mcps,
    add_mcp,
    remove_mcp,
)
from orchestrator import process_query

MAIN_POLICY_PATH = str(Path(__file__).parent / "main-policy.md")
MCP_JSON_PATH = str(Path(__file__).parent.parent / ".mcp.json")
MCP_SERVER_SCRIPT = str(Path(__file__).parent.parent / "mcp-server" / "server.py")
POLICIES_DIR = str(Path(__file__).parent.parent / "policies")
DATABASE_DIR = str(Path(__file__).parent.parent / "database")
STATIC_DIR = str(Path(__file__).parent / "static")

app = FastAPI(title="MCP 정책 오케스트레이터 - 대시보드")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 요청/응답 모델 ---

class QueryRequest(BaseModel):
    query: str

class MCPRegisterRequest(BaseModel):
    name: str
    description: str
    policy_path: str  # policies/ 하위 경로 (예: kitchen/policy.md)

class MainPolicyUpdateRequest(BaseModel):
    content: str


# --- .mcp.json 관리 ---

def _load_mcp_json() -> dict:
    path = Path(MCP_JSON_PATH)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"mcpServers": {}}


def _save_mcp_json(data: dict) -> None:
    Path(MCP_JSON_PATH).write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _sync_mcp_json_add(name: str, policy_path: str) -> None:
    """MCP 연결 시 .mcp.json에 서버 추가"""
    data = _load_mcp_json()
    full_policy_path = str(Path(POLICIES_DIR).parent / policy_path)
    data["mcpServers"][name] = {
        "command": "python",
        "args": [MCP_SERVER_SCRIPT, "--policy", full_policy_path],
    }
    _save_mcp_json(data)


def _sync_mcp_json_remove(name: str) -> None:
    """MCP 해제 시 .mcp.json에서 서버 제거"""
    data = _load_mcp_json()
    data["mcpServers"].pop(name, None)
    _save_mcp_json(data)


def _is_mcp_in_json(name: str) -> bool:
    """MCP가 .mcp.json에 등록되어 있는지 확인"""
    data = _load_mcp_json()
    return name in data.get("mcpServers", {})


# --- 정책 로드 ---

def _load_policy() -> dict[str, Any]:
    return load_main_policy(MAIN_POLICY_PATH)


# --- API 엔드포인트 ---

@app.post("/api/query")
async def api_query(req: QueryRequest):
    """사용자 질의 처리 — Claude CLI 에이전트 루프 실행"""
    if not req.query.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_QUERY", "message": "질의가 비어 있습니다"}},
        )

    policy = _load_policy()
    mcps = get_connected_mcps(policy)

    # 연결된(활성화된) MCP만 필터
    active_mcps = [m for m in mcps if _is_mcp_in_json(m["name"])]

    result = await process_query(query=req.query, connected_mcps=active_mcps)
    return result


@app.get("/api/mcps")
async def api_list_mcps():
    """등록된 MCP 목록 + 연결 상태 조회"""
    policy = _load_policy()
    mcps = get_connected_mcps(policy)

    result = []
    for mcp in mcps:
        connected = _is_mcp_in_json(mcp["name"])
        result.append({
            "name": mcp["name"],
            "description": mcp["description"],
            "policy_path": mcp.get("policy_path", ""),
            "connected": connected,
        })
    return result


@app.post("/api/mcps")
async def api_register_mcp(req: MCPRegisterRequest):
    """MCP 등록 + 연결"""
    policy = _load_policy()

    # main-policy.md에 추가
    try:
        add_mcp(policy, req.name, f"stdio://{req.name}", req.description)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_QUERY", "message": str(e)}},
        )

    # policy_path를 메타데이터에 저장
    for mcp in policy["connected_mcps"]:
        if mcp["name"] == req.name:
            mcp["policy_path"] = req.policy_path
            break

    save_main_policy(MAIN_POLICY_PATH, policy)

    # .mcp.json에도 추가 (연결)
    _sync_mcp_json_add(req.name, req.policy_path)

    return {"name": req.name, "description": req.description, "connected": True}


@app.delete("/api/mcps/{name}")
async def api_delete_mcp(name: str):
    """MCP 등록 해제 (main-policy.md + .mcp.json 모두 제거)"""
    policy = _load_policy()
    try:
        remove_mcp(policy, name)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "SECTION_NOT_FOUND", "message": str(e)}},
        )
    save_main_policy(MAIN_POLICY_PATH, policy)
    _sync_mcp_json_remove(name)
    return {"success": True}


@app.post("/api/mcps/{name}/connect")
async def api_connect_mcp(name: str):
    """MCP 연결 (활성화) — .mcp.json에 추가"""
    policy = _load_policy()
    mcps = get_connected_mcps(policy)
    mcp = next((m for m in mcps if m["name"] == name), None)
    if not mcp:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "SECTION_NOT_FOUND", "message": f"MCP '{name}'을 찾을 수 없습니다"}},
        )

    policy_path = mcp.get("policy_path", f"policies/{name.replace('-mcp', '')}/policy.md")
    _sync_mcp_json_add(name, policy_path)
    return {"name": name, "connected": True}


@app.post("/api/mcps/{name}/disconnect")
async def api_disconnect_mcp(name: str):
    """MCP 연결 해제 (비활성화) — .mcp.json에서 제거, main-policy.md는 유지"""
    if not _is_mcp_in_json(name):
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "SECTION_NOT_FOUND", "message": f"MCP '{name}'이 연결되어 있지 않습니다"}},
        )

    _sync_mcp_json_remove(name)
    return {"name": name, "connected": False}


@app.get("/api/main-policy")
async def api_get_main_policy():
    """main-policy.md 조회"""
    content = Path(MAIN_POLICY_PATH).read_text(encoding="utf-8")
    return {"content": content}


@app.put("/api/main-policy")
async def api_update_main_policy(req: MainPolicyUpdateRequest):
    """main-policy.md 수정"""
    Path(MAIN_POLICY_PATH).write_text(req.content, encoding="utf-8")
    return {"success": True}


# --- KB 문서 미리보기 API ---

@app.get("/api/kb/tree")
async def api_kb_tree():
    """database 폴더의 문서 트리 구조 반환"""
    db_path = Path(DATABASE_DIR)
    if not db_path.exists():
        return {"tree": []}

    tree: list[dict] = []
    for md_file in sorted(db_path.rglob("*.md")):
        rel = md_file.relative_to(db_path)
        parts = list(rel.parts)
        tree.append({
            "path": str(rel),
            "name": md_file.stem,
            "folder": str(rel.parent) if len(parts) > 1 else "",
        })
    return {"tree": tree}


@app.get("/api/kb/document")
async def api_kb_document(path: str):
    """특정 문서의 마크다운 원문 반환"""
    doc_path = (Path(DATABASE_DIR) / path).resolve()
    db_resolved = Path(DATABASE_DIR).resolve()

    if not str(doc_path).startswith(str(db_resolved)):
        raise HTTPException(status_code=400, detail="잘못된 경로입니다")
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail=f"문서를 찾을 수 없습니다: {path}")

    content = doc_path.read_text(encoding="utf-8")
    return {"path": path, "name": doc_path.stem, "content": content}


@app.get("/kb")
async def kb_viewer():
    """KB 문서 미리보기 페이지"""
    kb_path = Path(STATIC_DIR) / "kb.html"
    if kb_path.exists():
        return FileResponse(str(kb_path))
    raise HTTPException(status_code=404, detail="kb.html이 없습니다")


# --- 정적 파일 서빙 ---

@app.get("/")
async def root():
    index_path = Path(STATIC_DIR) / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "MCP 정책 오케스트레이터 대시보드", "docs": "/docs"}


if Path(STATIC_DIR).exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    print("[대시보드] 서버 시작: http://localhost:8001")
    print("[대시보드] main-policy: {MAIN_POLICY_PATH}")
    print("[대시보드] .mcp.json: {MCP_JSON_PATH}")
    print("[대시보드] API 문서: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)
