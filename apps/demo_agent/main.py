from __future__ import annotations

import asyncio
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, StateGraph

from switchboard.core.models import (
    ActionArguments,
    ActionContext,
    ActionRequest,
    ActionSeverity,
    ApprovalStatus,
)

API_URL = "http://localhost:8000"


class AgentState(TypedDict, total=False):
    actions: list[ActionRequest]
    pointer: int
    results: list[dict[str, Any]]


def build_actions() -> list[ActionRequest]:
    return [
        ActionRequest(
            context=ActionContext(
                agent_id="demo-agent",
                principal_id="user-123",
                tenant_id="demo",
                severity=ActionSeverity.P1,
                metadata={"role": "ops"},
            ),
            tool_name="jira",
            tool_action="create_issue",
            arguments=ActionArguments(
                data={"project": "SW", "summary": "Demo change request", "issue_key": "SW-123"}
            ),
        ),
        ActionRequest(
            context=ActionContext(
                agent_id="demo-agent",
                principal_id="user-123",
                tenant_id="demo",
                severity=ActionSeverity.P1,
                pii=True,
                sensitivity_tags=["financial"],
                metadata={"role": "ops"},
            ),
            tool_name="jira",
            tool_action="update_issue",
            arguments=ActionArguments(
                data={"issue_key": "SW-123", "fields": {"description": "PII update"}}
            ),
        ),
        ActionRequest(
            context=ActionContext(
                agent_id="demo-agent",
                principal_id="user-123",
                tenant_id="demo",
                severity=ActionSeverity.P0,
                resource_scope="prod",
                metadata={"role": "analyst"},
            ),
            tool_name="github",
            tool_action="comment_issue",
            arguments=ActionArguments(data={"repository": "example/repo", "issue": 42}),
        ),
    ]


async def planner(_: AgentState) -> AgentState:
    return AgentState(actions=build_actions(), pointer=0, results=[])


async def executor(state: AgentState) -> AgentState:
    pointer = state.get("pointer", 0)
    actions = state["actions"]
    if pointer >= len(actions):
        return state
    action = actions[pointer]
    async with httpx.AsyncClient(base_url=API_URL, timeout=10.0) as client:
        response = await client.post("/route", json={"request": action.model_dump()})
        if response.status_code == 202:
            payload = response.json()
            approval_id = payload["approval_id"]
            await client.post(
                "/approve",
                json={
                    "approval_id": approval_id,
                    "status": ApprovalStatus.APPROVED.value,
                    "decided_by": "demo-approver",
                },
            )
            result_detail = {"action": "approved", "approval_id": approval_id}
        elif response.status_code == 403:
            result_detail = {"action": "blocked", "detail": response.json()}
        else:
            result_detail = response.json()

    state.setdefault("results", []).append(result_detail)
    state["pointer"] = pointer + 1
    return state


async def should_continue(state: AgentState) -> str:
    if state.get("pointer", 0) >= len(state["actions"]):
        return END
    return "execute"


async def main() -> None:
    graph: Any = StateGraph(AgentState)
    graph.add_node("plan", planner)
    graph.add_node("execute", executor)
    graph.add_edge("plan", "execute")
    graph.add_conditional_edges("execute", should_continue, {END: END, "execute": "execute"})
    graph.set_entry_point("plan")

    compiled = graph.compile()
    initial_state: AgentState = {}
    result = await compiled.ainvoke(initial_state)
    for idx, entry in enumerate(result["results"], 1):
        print(f"[{idx}] -> {entry}")


if __name__ == "__main__":
    asyncio.run(main())
