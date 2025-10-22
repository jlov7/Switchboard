package switchboard.authz

default allow = false
default requires_approval = false
default reason = "policy evaluation failed"

allow {
  not deny_action
}

deny_action[msg] {
  input.context.resource_scope == "prod"
  not user_in_ops_role
  msg := "role=ops required for prod scope"
}

requires_approval {
  input.context.pii == true
}

requires_approval {
  input.context.severity == "p0"
}

deny_action[msg] {
  input.context.severity == "p0"
  count(input.context.sensitivity_tags) > 0
  msg := "p0 action with sensitive tags denied"
}

deny_action[msg] {
  exceeding_rate_limit
  msg := "action rate limit exceeded"
}

exceeding_rate_limit {
  input.activity.window_count > input.policy.rate_limit
}

user_in_ops_role {
  input.context.metadata.role == "ops"
}
