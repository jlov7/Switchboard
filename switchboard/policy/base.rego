package switchboard.authz

default allow = false
default requires_approval = false
default reason = "allowed"
default risk_level = "medium"

# --- Helper predicates --------------------------------------------------------
segregation_of_duties_violation {
    approver := input.context.metadata.approver
    approver != ""
    is_string(approver)
    is_string(input.context.principal_id)
    lower(approver) == lower(input.context.principal_id)
}

pii_gate {
    input.context.pii == true
}

severity_gate {
    input.context.severity == "p0"
}

p0_sensitive_block {
    severity_gate
    count(input.context.sensitivity_tags) > 0
}

prod_scope_violation {
    input.context.resource_scope == "prod"
    not user_in_ops_role
}

rate_limit_exceeded {
    input.activity.window_count > input.policy.rate_limit
}

user_in_ops_role {
    role := input.context.metadata.role
    is_string(role)
    lower(role) == "ops"
}

user_in_ops_role {
    roles := input.context.metadata.roles
    some idx
    role := roles[idx]
    is_string(role)
    lower(role) == "ops"
}

# --- Policy rules -------------------------------------------------------------
deny[msg] {
    segregation_of_duties_violation
    msg := "Segregation of duties: requester cannot approve"
}

deny[msg] {
    p0_sensitive_block
    msg := "p0 action with sensitive tags denied"
}

deny[msg] {
    prod_scope_violation
    msg := "role=ops required for prod scope"
}

deny[msg] {
    rate_limit_exceeded
    msg := "action rate limit exceeded"
}

requires_approval {
    pii_gate
}

requires_approval {
    severity_gate
}

allow {
    not some_deny
}

some_deny {
    deny[_]
}

policy_ids = ids {
    ids := [id | policy_id(id)]
}

policy_id("policy:segregation-of-duties") {
    segregation_of_duties_violation
}

policy_id("policy:p0-sensitive-block") {
    p0_sensitive_block
}

policy_id("policy:prod-role") {
    prod_scope_violation
}

policy_id("policy:rate-limit") {
    rate_limit_exceeded
}

policy_id("policy:pii-approval") {
    requires_approval
}

reason = msg {
    messages := [m | deny[m]]
    count(messages) > 0
    msg := concat("; ", messages)
}

risk_level = "critical" {
    p0_sensitive_block
}

risk_level = "critical" {
    severity_gate
    pii_gate
}

risk_level = "high" {
    severity_gate
    not p0_sensitive_block
    not pii_gate
}
