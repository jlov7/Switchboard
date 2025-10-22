from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server")

app = FastAPI(title="Switchboard MCP Server", version="0.1.0")


class ActionPayload(BaseModel):
    request_id: str
    tool: str
    action: str
    arguments: dict[str, Any]
    context: dict[str, Any]


class Tool:
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    def execute(self, action: str, arguments: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class JiraTool(Tool):
    def execute(self, action: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if action not in {"create_issue", "update_issue"}:
            raise ValueError(f"Unsupported Jira action: {action}")
        logger.info(
            "jira_action",
            extra={"action": action, "project": arguments.get("project"), "summary": arguments},
        )
        return {"issue_key": arguments.get("issue_key", "SW-123")}


class GitHubTool(Tool):
    def execute(self, action: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if action not in {"comment_issue", "create_pr"}:
            raise ValueError(f"Unsupported GitHub action: {action}")
        logger.info(
            "github_action",
            extra={"action": action, "repository": arguments.get("repository"), "body": arguments},
        )
        return {"status": "queued"}


TOOLS: dict[str, Tool] = {
    "jira": JiraTool("jira"),
    "github": GitHubTool("github"),
}


@app.post("/actions")
async def execute_action(payload: ActionPayload) -> dict[str, Any]:
    tool = TOOLS.get(payload.tool)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{payload.tool}' not found")
    try:
        data = tool.execute(payload.action, payload.arguments)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "detail": "action executed", "data": data}
