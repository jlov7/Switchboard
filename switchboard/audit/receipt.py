from __future__ import annotations

import json
from typing import Any

from switchboard.audit.service import AuditVerificationResult
from switchboard.core.models import AuditRecord


def build_receipt(
    record: AuditRecord,
    result: AuditVerificationResult,
    include_rekor_reference: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "audit_event": str(record.event_id),
        "verified": result.verified,
        "signature_valid": result.signature_valid,
        "rekor_included": result.rekor_included,
        "failure_reason": result.failure_reason,
    }
    if include_rekor_reference:
        payload["verification_reference"] = record.verification_url
    return payload


def receipt_to_json(receipt: dict[str, Any]) -> str:
    return json.dumps(receipt, separators=(",", ":"), sort_keys=True)
