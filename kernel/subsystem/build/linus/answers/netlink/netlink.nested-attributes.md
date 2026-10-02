- Handler's `nla_parse_nested()` policy: may be `NULL` when the outer policy
  entry already validated the nest with the same maxtype, as
  `nl80211_parse_mbssid_config()` in `net/wireless/nl80211.c` does.
- Nest validation flags: the nest is validated with the flags of the outer
  parse, made strict for a type at or above `strict_start_type`, but
  `nla_parse_nested()` in the handler is always `NL_VALIDATE_STRICT`.
- Outer parse liberal, handler uses `nla_parse_nested()`: the handler can
  reject a nest the outer parse accepted, for a missing `NLA_F_NESTED`, an
  unknown type, trailing bytes or an over-long integer.
- `{ .type = NLA_NESTED }` with no `nested_policy`: nothing inside the nest
  is validated; the contents reach the handler unchecked.
- `NLA_NESTED_ARRAY`: `nla_validate_array()` skips zero-length elements and
  never tests `NLA_F_NESTED` on an element; the handler's `nla_parse_nested()`
  on each element does.
