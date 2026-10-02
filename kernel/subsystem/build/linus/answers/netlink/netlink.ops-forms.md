- Mixing: `genl_validate_ops()` has no test on which tables are present. Any
  combination of `ops`, `small_ops` and `split_ops` passes, provided no
  `cmd` appears in more than one.
- Lookup order in `genl_get_cmd()`: `ops`, then `small_ops`, then
  `split_ops`.
- Conversion: there is no genl_cmd_small_to_split() here.
  `genl_op_from_small()` fills a `struct genl_ops`, then
  `genl_cmd_full_to_split()` converts it.
- `pre_doit` and `post_doit`: `struct genl_split_ops` carries its own. The
  hooks in `struct genl_family` are copied in only by
  `genl_cmd_full_to_split()`, so they never run for a split entry.
- `GENL_CMD_CAP_DO` and `GENL_CMD_CAP_DUMP`: the core adds them to legacy
  ops from the handlers present; a split entry must set exactly one itself.
- Handler pointers of a split entry: not checked. An entry with
  `GENL_CMD_CAP_DO` and a NULL `doit` registers, and
  `genl_family_rcv_msg_doit()` calls `ops->doit` with no test.
- `start` or `done` without `dumpit`: no test for it.
- Order of split entries: `cmd` must not decrease from one entry to the
  next; two entries with one `cmd` must be the `GENL_CMD_CAP_DO` entry
  followed by the `GENL_CMD_CAP_DUMP` entry.
- Two split entries with one `cmd`: `internal_flags` must be equal, as well
  as `flags` outside `GENL_CMD_CAP_DO` and `GENL_CMD_CAP_DUMP`.
