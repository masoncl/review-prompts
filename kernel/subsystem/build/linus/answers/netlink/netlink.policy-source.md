- `genl_family_rcv_msg_attrs_parse()`: takes the policy and the maximum only
  from `ops->policy` and `ops->maxattr` of the resolved
  `struct genl_split_ops`. The family fallback is applied earlier, in
  `genl_op_from_full()` and `genl_op_from_small()`.
- `struct genl_ops`: `policy` and `maxattr` fall back separately. An op with
  its own `policy` and `maxattr` 0 is parsed with its policy and
  `family->maxattr`.
- Legacy op, no policy anywhere, `cmd >= resv_start_op`:
  `genl_op_fill_in_reject_policy()` installs `genl_policy_reject_all`.
  `maxattr` is not changed.
- Legacy op, no policy anywhere, `cmd < resv_start_op`: no parsing, no
  validation; `info->attrs` is NULL.
- Split entry, no policy: `genl_op_fill_in_reject_policy_split()` installs
  `genl_policy_reject_all` without testing `resv_start_op`.
- Reject-all with `maxattr` 0: strict parsing fails any attribute with
  `-EINVAL` ("Unknown attribute type"). Under `NL_VALIDATE_LIBERAL` the
  attributes are skipped instead.
- `!ops->policy` is the test for "no parsing", not `maxattr == 0`. A policy
  with `maxattr` 0 is validated and still yields a NULL `info->attrs`.
- `info->attrs` is NULL in the reject-all case with `maxattr` 0 too.
  `GENL_REQ_ATTR_CHECK()` in `include/net/genetlink.h` indexes `info->attrs`
  with no NULL test.
