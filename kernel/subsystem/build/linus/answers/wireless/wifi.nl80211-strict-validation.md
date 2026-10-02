- Start: `nl80211_policy[0]` is
  `{ .strict_start_type = NL80211_ATTR_HE_OBSS_PD }`; there is no separate
  constant for it.
- `.strict_start_type`: `validate_nla()` in `lib/nlattr.c` adds
  `NL_VALIDATE_STRICT` per attribute, for each one numbered at or above it.
- Unknown attribute numbers and trailing bytes: tested in
  `__nla_validate_parse()` with the op's own flags, so an op with
  `GENL_DONT_VALIDATE_STRICT` still skips attributes above `NL80211_ATTR_MAX`.
- Ops with no `.validate`: parsed with `NL_VALIDATE_STRICT` for every
  attribute, including those numbered below `NL80211_ATTR_HE_OBSS_PD`.
- Commands at or above `.resv_start_op` (`NL80211_CMD_REMOVE_LINK_STA + 1`):
  must leave `.validate` zero; otherwise `genl_validate_ops()` hits a
  `WARN_ON()` and `genl_register_family()` returns `-EINVAL`.
- Nested policies: `validate_nla()` passes its strict flags into
  `nested_policy`, so everything inside a strict attribute is strict.
- Nested `.strict_start_type`: no policy under `net/wireless/` other than
  `nl80211_policy` sets it.
- `NL80211_ATTR_MLO_LINKS`: its nested policy is `nl80211_policy` itself, so
  old attributes inside it are strict too.
- Plain `{ .type = NLA_NESTED }` entry: accepted above the strict start (for
  example `NL80211_ATTR_MBSSID_ELEMS`); the contents are unvalidated until the
  handler parses them.
- Handler parse of a nested set: `nla_parse_nested()` is strict,
  `nla_parse_nested_deprecated()` is liberal.
- `NLA_FLAG`: not in `nla_attr_len[]`; a payload is rejected at any
  validation level.
