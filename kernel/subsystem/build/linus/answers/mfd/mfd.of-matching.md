- `mfd_match_of_node_to_dev()`: takes `(pdev, np, cell)` and tests one
  candidate node; it does not read the parent.
- `mfd_add_device()`: holds the loop over the children of
  `parent->of_node` and the `of_device_is_compatible()` and
  `of_device_is_available()` tests, in that order, before each call.
- Loop iterator: `for_each_child_of_node_scoped()`; the `continue` and
  `goto` exits need no `of_node_put()`, and adding one is a double put.
- Accepted node: set with `device_set_node(&pdev->dev,
  of_fwnode_handle(np))`, which writes both `dev.fwnode` and `dev.of_node`.
- References: one `of_node_get()` per accepted node; the entry's `np` and
  the child's `dev.fwnode` share it.
