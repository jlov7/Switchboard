from __future__ import annotations

import os
from typing import Any, cast

import httpx
import streamlit as st

from switchboard.audit.receipt import build_receipt, receipt_to_json
from switchboard.audit.service import AuditVerificationResult
from switchboard.core.models import AuditRecord

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


def verify_audit(record: dict[str, Any]) -> dict[str, Any] | None:
    if not record:
        st.warning("Audit record data is unavailable for verification.")
        return None
    with httpx.Client(base_url=API_URL, timeout=10.0) as client:
        response = client.post(
            "/audit/verify",
            json={"record": record, "verify_rekor": True},
        )
        if response.status_code >= 400:
            st.error(f"Verification failed: {response.text}")
            return None
        payload = cast(dict[str, Any], response.json())
        verification = AuditVerificationResult(**payload)
        audit_record = AuditRecord.model_validate(record)
        receipt = build_receipt(audit_record, verification)
        return {"result": payload, "receipt": receipt}


if st.button("Refresh queue", use_container_width=True):
    cast(Any, load_pending).clear()
    for key in list(st.session_state.keys()):
        if str(key).startswith("verify-result-"):
            st.session_state.pop(key, None)

pending = load_pending()
if not pending:
    st.info("No pending approvals.")
else:
    for item in pending:
        approval_id = item["approval_id"]
        policy = item["policy"]
        audit = item.get("audit", {})
        policy_ids = policy.get("policy_ids", [])
        reason = policy.get("reason", "")
        risk_level = policy.get("risk_level", "unknown")
        risk_color = {
            "critical": "red",
            "high": "orange",
            "medium": "blue",
            "low": "green",
        }.get(str(risk_level).lower(), "gray")
        verify_key = f"verify-result-{approval_id}"
        with st.container(border=True):
            st.subheader(f"Approval {approval_id}")
            st.markdown(f"**Adapter**: `{item['adapter']}`")
            st.markdown(f"**Policy decision**: `{reason}`")
            st.markdown(f"**Risk level**: :{risk_color}[{str(risk_level).upper()}]")
            if policy_ids:
                st.markdown(
                    "**Policy IDs**: "
                    + ", ".join(f"`{pid}`" for pid in policy_ids)
                )
            st.json(item["request"], expanded=False)
            if audit.get("event_id"):
                verify_cmd = f"./scripts/verify_audit.sh {audit['event_id']}"
                st.markdown("**Verify audit signature:**")
                st.code(verify_cmd, language="bash")
                if audit.get("verification_url") and audit["verification_url"] not in {None, "offline"}:
                    st.markdown(
                        f"Verification reference: `{audit['verification_url']}`"
                    )
                if st.button(
                    f"Run live verification {audit['event_id']}",
                    key=f"verify-{approval_id}",
                    use_container_width=True,
                ):
                    verification = verify_audit(audit.get("record", {}))
                    if verification is not None:
                        st.session_state[verify_key] = verification
                        st.rerun()
                if verify_key in st.session_state:
                    verify_entry = st.session_state[verify_key]
                    result_payload = verify_entry["result"]
                    receipt_payload = verify_entry["receipt"]
                    if result_payload.get("verified"):
                        st.success("Latest verification succeeded.")
                    else:
                        st.error("Verification failed.")
                    st.json(result_payload, expanded=False)
                    st.download_button(
                        "Download receipt (JSON)",
                        data=receipt_to_json(receipt_payload),
                        file_name=f"audit-receipt-{audit['event_id']}.json",
                        mime="application/json",
                        use_container_width=True,
                    )
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    f"Approve {approval_id}",
                    key=f"approve-{approval_id}",
                    use_container_width=True,
                ):
                    st.session_state.pop(verify_key, None)
                    act_on_request(approval_id, "approved")
                    cast(Any, load_pending).clear()
                    st.rerun()
            with col2:
                if st.button(
                    f"Deny {approval_id}",
                    key=f"deny-{approval_id}",
                    use_container_width=True,
                ):
                    st.session_state.pop(verify_key, None)
                    act_on_request(approval_id, "denied")
                    cast(Any, load_pending).clear()
                    st.rerun()
