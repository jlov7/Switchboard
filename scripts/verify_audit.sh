#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/verify_audit.sh AUDIT_EVENT_ID [options]

Required:
  AUDIT_EVENT_ID         UUID of the audit event to verify.

Options:
  --bundle PATH          Load verification payload from a JSON bundle (defaults to local audit log).
  --rekor-url URL        Override the Rekor transparency log endpoint.
  --log PATH             Path to the structured audit log (default: data/audit-log.jsonl).
  --no-rekor             Skip Rekor inclusion verification (signature check only).
  --json                 Emit machine-readable JSON instead of text output.

The script prints a short receipt and exits non-zero if verification fails.
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

AUDIT_ID="$1"
shift

LOG_FILE="data/audit-log.jsonl"
BUNDLE_PATH=""
VERIFY_REKOR=1
OUTPUT_JSON=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bundle)
      BUNDLE_PATH="$2"
      shift 2
      ;;
    --rekor-url)
      export REKOR_URL="$2"
      shift 2
      ;;
    --log)
      LOG_FILE="$2"
      shift 2
      ;;
    --no-rekor)
      VERIFY_REKOR=0
      shift
      ;;
    --json)
      OUTPUT_JSON=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

python - <<'PYTHON' "${AUDIT_ID}" "${LOG_FILE}" "${BUNDLE_PATH}" "${VERIFY_REKOR}" "${OUTPUT_JSON}"
import asyncio
import json
import sys
from pathlib import Path

from switchboard.audit.receipt import build_receipt, receipt_to_json
from switchboard.audit.service import AuditService
from switchboard.core.models import AuditRecord

audit_id = sys.argv[1]
log_path = Path(sys.argv[2])
bundle_path = Path(sys.argv[3]) if sys.argv[3] else None
verify_rekor = bool(int(sys.argv[4]))
output_json = bool(int(sys.argv[5]))


def load_entry() -> dict[str, object]:
    if bundle_path:
        if not bundle_path.exists():
            raise SystemExit(f"Bundle not found: {bundle_path}")
        return json.loads(bundle_path.read_text(encoding='utf-8'))

    if not log_path.exists():
        raise SystemExit(f"No audit log found at {log_path}")

    with log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            record = entry.get("record", {})
            if str(record.get("event_id")) == audit_id:
                return entry

    raise SystemExit(f"Audit event {audit_id} not found in {log_path}")


def to_audit_record(entry: dict[str, object]) -> AuditRecord:
    record = entry.get("record", {})
    if not isinstance(record, dict):
        raise SystemExit("Malformed bundle: record missing")
    record["signature"] = entry.get("signature")
    record["signature_algorithm"] = entry.get("algorithm")
    record["verification_url"] = entry.get("verification_reference")
    return AuditRecord.model_validate(record)


async def run() -> int:
    entry = load_entry()
    audit_record = to_audit_record(entry)
    service = AuditService()
    result = await service.verify(audit_record, verify_rekor=verify_rekor)
    receipt = build_receipt(audit_record, result)

    if not verify_rekor:
        receipt["rekor_included"] = None

    if output_json:
        print(receipt_to_json(receipt))
    else:
        status_lines = [
            f"audit_event: {receipt['audit_event']}",
            f"signature_valid: {receipt['signature_valid']}",
            f"verified: {receipt['verified']}",
        ]
        if verify_rekor:
            status_lines.insert(2, f"rekor_included: {receipt['rekor_included']}")
        else:
            status_lines.insert(2, "rekor_included: skipped (user disabled)")
        if receipt.get("verification_reference"):
            status_lines.insert(3, f"verification_reference: {receipt['verification_reference']}")
        if receipt.get("failure_reason"):
            status_lines.append(f"failure_reason: {receipt['failure_reason']}")
        print("\n".join(status_lines))

    return 0 if receipt["verified"] else 1


raise SystemExit(asyncio.run(run()))
PYTHON
