from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

import httpx
import yaml

from switchboard.core.models import ActionRequest, PolicyDecision
from switchboard.policy.opa_client import OPAClient, OPAError


@dataclass
class RateLimitConfig:
    window_seconds: int
    limit: int


class LocalPolicyEngine:
    def __init__(self, rate_limits: dict[str, RateLimitConfig], approval_tags: set[str]) -> None:
        self.rate_limits = rate_limits
        self.approval_tags = approval_tags
        self.activity_window: dict[tuple[str, str, str], deque[float]] = defaultdict(deque)

    @staticmethod
    def _extract_roles(metadata: dict[str, Any]) -> set[str]:
        roles: set[str] = set()
        direct = metadata.get("role")
        if isinstance(direct, str):
            roles.add(direct.strip().lower())
        multi = metadata.get("roles")
        if isinstance(multi, (list, tuple, set)):
            for value in multi:
                if isinstance(value, str):
                    roles.add(value.strip().lower())
        return {role for role in roles if role}

    def evaluate(self, request: ActionRequest) -> PolicyDecision:
        policy_ids: list[str] = []
        requires_approval = False
        allowed = True
        reasons: list[str] = []
        risk_level = "medium"

        context = request.context
        metadata = context.metadata or {}
        roles = self._extract_roles(metadata)
        now = time.time()
        key = (context.tenant_id, request.tool_name, context.severity.value)
        rate_config = self.rate_limits.get(context.severity.value, self.rate_limits["default"])

        window = self.activity_window[key]
        while window and now - window[0] > rate_config.window_seconds:
            window.popleft()

        if context.severity.value == "p0":
            risk_level = "high"

        approver = metadata.get("approver")
        principal = context.principal_id
        if (
            isinstance(approver, str)
            and isinstance(principal, str)
            and approver.strip()
            and approver.casefold() == principal.casefold()
        ):
            allowed = False
            reasons.append("Segregation of duties: requester cannot approve")
            if "policy:segregation-of-duties" not in policy_ids:
                policy_ids.append("policy:segregation-of-duties")

        if context.severity.value == "p0" and context.sensitivity_tags:
            allowed = False
            reasons.append("p0 action with sensitive tags denied")
            if "policy:p0-sensitive-block" not in policy_ids:
                policy_ids.append("policy:p0-sensitive-block")
            risk_level = "critical"

        if context.resource_scope == "prod" and "ops" not in roles:
            allowed = False
            reasons.append("role=ops required for prod scope")
            if "policy:prod-role" not in policy_ids:
                policy_ids.append("policy:prod-role")

        if context.severity.value == "p0":
            requires_approval = True
            if risk_level != "critical":
                risk_level = "high"
            if "policy:pii-approval" not in policy_ids:
                policy_ids.append("policy:pii-approval")

        if context.pii or any(tag in self.approval_tags for tag in context.sensitivity_tags):
            requires_approval = True
            if "policy:pii-approval" not in policy_ids:
                policy_ids.append("policy:pii-approval")
            if context.severity.value == "p0":
                risk_level = "critical"

        if len(window) >= rate_config.limit:
            allowed = False
            reasons.append("rate limit exceeded")
            if "policy:rate-limit" not in policy_ids:
                policy_ids.append("policy:rate-limit")

        if allowed:
            window.append(now)

        reason = "allowed"
        if reasons:
            reason = "; ".join(dict.fromkeys(reasons))

        return PolicyDecision(
            allowed=allowed,
            requires_approval=requires_approval,
            reason=reason,
            policy_ids=policy_ids,
            risk_level=risk_level,
        )


class PolicyEngine:
    def __init__(self, config_path: str | None = None) -> None:
        env_config = os.getenv("SWITCHBOARD_POLICY_CONFIG")
        config_path_value: str = (
            config_path
            if config_path is not None
            else env_config or "switchboard/policy/config.yaml"
        )
        with open(config_path_value, encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)

        rate_limits = {
            "default": RateLimitConfig(
                window_seconds=raw["rate_limits"]["default"]["window_seconds"],
                limit=raw["rate_limits"]["default"]["limit"],
            )
        }
        for key, value in raw["rate_limits"].items():
            if key == "default":
                continue
            rate_limits[key] = RateLimitConfig(
                window_seconds=value["window_seconds"],
                limit=value["limit"],
            )

        approval_tags = set(raw.get("sensitivity", {}).get("requires_approval_tags", []))
        self.local_engine = LocalPolicyEngine(rate_limits=rate_limits, approval_tags=approval_tags)
        opa_url = os.getenv("OPA_URL", "http://localhost:8181/v1/data/switchboard/authz")
        self.opa_client: OPAClient | None = None
        if os.getenv("SWITCHBOARD_USE_OPA", "true").lower() != "false":
            self.opa_client = OPAClient(opa_url)

    async def evaluate(self, request: ActionRequest) -> PolicyDecision:
        if self.opa_client:
            try:
                return await self.opa_client.evaluate(request)
            except (OPAError, httpx.HTTPError):
                # Fall back to local engine if OPA unavailable
                pass
        return self.local_engine.evaluate(request)
