- Type 0 or above maxtype under `NL_VALIDATE_MAXTYPE`: `-EINVAL` with "Unknown
  attribute type", from `__nla_validate_parse()`; "Unsupported attribute" is
  the `NLA_UNSPEC` message from `validate_nla()`.
- `strict_start_type` and a policy hole at or above it: rejected as
  `NLA_UNSPEC` even from a liberal entry point such as
  `nlmsg_parse_deprecated()`.
- Policy array size: must have at least maxtype + 1 entries; `validate_nla()`
  indexes `policy[type]` for any type up to the maxtype the caller passed.
