- No node accepted and no compatible node disabled: `pr_warn()` with
  "Failed to locate of_node", the child is registered with
  `dev.of_node == NULL`, and `mfd_add_device()` returns 0.
- `disabled` in `mfd_add_device()`: set by any compatible node that fails
  `of_device_is_available()`, before the claimed test and the `of_reg` test
  run.
- Cell dropped without a message: whenever no node is accepted and at
  least one compatible node is disabled, even if that node has a different
  `reg` or the cell's own node is absent or already claimed.
- Disabled sibling plus an accepted node: the child is registered
  normally; `disabled` is only read after the loop ends without a match.
- Dropped cell: `mfd_add_device()` returns 0 through `fail_alias`, adds
  nothing to `mfd_of_node_list`, and `mfd_add_devices()` goes on to the
  next cell.
