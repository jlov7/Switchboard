package switchboard.authz

default allow = false
default requires_approval = false

deny[msg] {
    input.context.resource_scope == "prod"
    not user_in_ops_role
    msg := "role=ops required for prod scope"
}

deny[msg] {
    input.context.severity == "p0"
    count(input.context.sensitivity_tags) > 0
    msg := "p0 action with sensitive tags denied"
}

deny[msg] {
    input.activity.window_count > input.policy.rate_limit
    msg := "action rate limit exceeded"
}

requires_approval {
    input.context.pii == true
}

requires_approval {
    input.context.severity == "p0"
}

allow {
    not some_deny
}

some_deny {
    deny[_]
}

user_in_ops_role {
    input.context.metadata.role == "ops"
}
