- `NLA_POLICY_RANGE()`, `NLA_POLICY_MIN()`, `NLA_POLICY_MAX()`: also accept
  `NLA_MSECS`; see `NLA_ENSURE_INT_OR_BINARY_TYPE()`.
- `NLA_POLICY_FULL_RANGE()`: accepts `NLA_MSECS`, `NLA_UINT`, `NLA_BE16` and
  `NLA_BE32` as well as the fixed unsigned types and `NLA_BINARY`.
- `NLA_POLICY_MASK()`: accepts `NLA_BE16`, `NLA_BE32` and `NLA_UINT`; refuses
  `NLA_MSECS` and `NLA_BINARY`; see `__NLA_IS_UINT_TYPE()`.
- There is no NLA_POLICY_MAX_BE() here; big-endian attributes use the
  ordinary range and mask macros, and the value is compared after `ntohs()`
  or `ntohl()`.
- `NLA_POLICY_VALIDATE_FN()`: build error for `NLA_BITFIELD32`, `NLA_REJECT`,
  `NLA_NESTED` and `NLA_NESTED_ARRAY`; its optional third argument sets `len`.
- `NLA_POLICY_EXACT_LEN()`, `NLA_POLICY_EXACT_LEN_WARN()`,
  `NLA_POLICY_MIN_LEN()`, `NLA_POLICY_MAX_LEN()`: take no type argument and
  always produce `NLA_BINARY`.
- `NLA_POLICY_EXACT_LEN_WARN()`: a payload that is too long passes with a
  warning unless `NL_VALIDATE_STRICT_ATTRS` is set; a payload that is too
  short fails in both modes.
- `NLA_POLICY_ETH_ADDR`, `NLA_POLICY_ETH_ADDR_COMPAT`: object-like macros, no
  parentheses; they are the exact and the warn form for `ETH_ALEN`.
- The macros make no build-time check of the bounds; `__NLA_ENSURE()` tests
  the type only.
- Bound above 32767 on an unsigned type: truncated into the `s16`; if it
  lands negative, `nla_get_range_unsigned()` hits `WARN_ON_ONCE()` at run
  time, and the range it returns is wrong either way.
- `NLA_REJECT` has no initialiser macro; entries are written
  `{ .type = NLA_REJECT }`, optionally with `.reject_message`.
