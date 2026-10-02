- Not refused: an empty family name, `maxattr` without a policy, unknown bits
  in a group's `flags`, any number of groups. There is no GENL_MAX_MCGRPS
  here.
- `genl_validate_ops()` in `net/netlink/genetlink.c`, `-EINVAL` for: a
  non-zero count with a NULL table; a `struct genl_ops` or
  `struct genl_small_ops` entry with neither `doit` nor `dumpit`; any
  `validate` flag on an op with `cmd >= resv_start_op` (every op when
  `resv_start_op` is 0); the same `cmd` twice across the three tables; the
  split-entry rules under "Operation table forms".
- Family ID range: `GENL_START_ALLOC` to `GENL_MAX_ID`, not `GENL_MIN_ID`.
- Fixed family IDs: `genl_ctrl` is matched by pointer; "pmcraid" and
  "VFS_DQUOT" are matched by `family->name`.
- Fixed group IDs, in `genl_validate_assign_mc_groups()`: four families, not
  three. The family named "NET_DM" gets group 1; `genl_ctrl`, and the
  families whose `id` is `GENL_ID_VFS_DQUOT` or `GENL_ID_PMCRAID`, get
  their family ID as group ID.
- Those four families: `BUG_ON(n_groups != 1)`, so a second group there
  crashes at registration.
- `bind` return value: `genl_bind()` discards it. `genl_bind()` returns only
  0 or the `-EPERM` from the group capability flags; a family cannot refuse
  a join.
