- There is no nlmsg_validate() here; the only message-level validate helper
  is `nlmsg_validate_deprecated()`, which is liberal.
- `genlmsg_parse()` is `NL_VALIDATE_STRICT` and `genlmsg_parse_deprecated()`
  is `NL_VALIDATE_LIBERAL`; both are in `include/net/genetlink.h`.
- `nla_parse_nested()`: `NL_VALIDATE_STRICT` plus its own `NLA_F_NESTED` test
  on the container.
- `NULL` policy under a strict entry point: only the maxtype and trailing
  checks run; `__nla_validate_parse()` does not call `validate_nla()`.
- `strict_start_type`: there is no macro for it; entry 0 is written by hand,
  for example `[NDA_UNSPEC] = { .strict_start_type = NDA_NH_ID }` in
  `net/core/neighbour.c`.
- `strict_start_type` at the same level: adds the per-attribute checks only;
  trailing bytes and types above maxtype stay as the entry point chose.
- `strict_start_type` and a nested attribute at or above it that has a
  `nested_policy`: `validate_nla()` passes the upgraded flags into the nest,
  so the nest's contents get all five checks.
- Per-operation flags go in the `validate` field of the op, not in `flags`.
- `validate` flag on a command at or above `resv_start_op`:
  `genl_validate_ops()` fires `WARN_ON()` as well as returning the `-EINVAL`
  given under "Family registration".
