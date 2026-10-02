- Rule: a function with a `prev`, `previous` or `from` parameter puts that
  node, except `__of_find_all_nodes()`; search `include/linux/of.h` and
  `include/linux/of_graph.h` for "next" and for `from`.
- Consumers whose name or parameter does not show it:
  `of_get_next_parent()` (parameter `node`), `of_find_all_nodes()`,
  `of_phandle_iterator_next()` (puts `it->node`),
  `__of_find_node_by_full_path()` (parameter `node`).
- Steppers also covered by the rule: `of_get_next_reserved_child()`,
  `of_get_next_child_with_prefix()`, `of_get_next_cpu_node()`,
  `of_graph_get_next_endpoint()`, `of_graph_get_next_port()`,
  `of_graph_get_next_port_endpoint()`.
- NULL parent: `of_get_next_child()`, `of_get_next_child_with_prefix()`,
  `of_get_next_available_child()`, `of_get_next_reserved_child()`,
  `of_graph_get_next_port()`, `of_graph_get_next_port_endpoint()` and
  `of_graph_get_next_endpoint()` return NULL before the put, so `prev` keeps
  its reference.
- `of_irq_find_parent()`: leaves the argument's count alone; it takes its own
  reference first and puts that one while walking up.
- Get-before-consume in a driver: `gsc_hwmon_get_devtree_pdata()` in
  `drivers/hwmon/gsc-hwmon.c` calls `of_node_get()` on the borrowed
  `of_node` on the line before `of_find_compatible_node()`.
