from __future__ import annotations

import os
from typing import Any, cast

import httpx
import streamlit as st

API_URL = os.getenv("SWITCHBOARD_API_URL", "http://localhost:8000")

st.set_page_config(page_title="Switchboard Approvals", layout="wide")

st.title("Switchboard Approvals Queue")
st.caption(
    "Designed for screen readers and keyboard navigation. Use the tab key to move between controls."
)


@st.cache_data(ttl=5.0)
def load_pending() -> list[dict[str, Any]]:
    with httpx.Client(base_url=API_URL, timeout=10.0) as client:
        response = client.get("/approvals/pending")
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            return []
        return cast(list[dict[str, Any]], data)


def act_on_request(approval_id: str, action: str) -> None:
    with httpx.Client(base_url=API_URL, timeout=10.0) as client:
        response = client.post(
            "/approve",
            json={
                "approval_id": approval_id,
                "status": action,
                "decided_by": "ui-operator",
            },
        )
        if response.status_code >= 400:
            st.error(f"Failed to {action} approval {approval_id}: {response.text}")
        else:
            st.success(f"{action.capitalize()} request {approval_id}")


if st.button("Refresh queue", use_container_width=True):
    cast(Any, load_pending).clear()

pending = load_pending()
if not pending:
    st.info("No pending approvals.")
else:
    for item in pending:
        approval_id = item["approval_id"]
        with st.container(border=True):
            st.subheader(f"Approval {approval_id}")
            st.markdown(f"**Adapter**: `{item['adapter']}`")
            st.json(item["request"], expanded=False)
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    f"Approve {approval_id}",
                    key=f"approve-{approval_id}",
                    use_container_width=True,
                ):
                    act_on_request(approval_id, "approved")
                    cast(Any, load_pending).clear()
                    st.rerun()
            with col2:
                if st.button(
                    f"Deny {approval_id}",
                    key=f"deny-{approval_id}",
                    use_container_width=True,
                ):
                    act_on_request(approval_id, "denied")
                    cast(Any, load_pending).clear()
                    st.rerun()
