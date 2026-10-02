- Non-scoped, leave early and hand the reference out:
  `of_get_child_by_name()` (`break`, then returns the child) and
  `of_graph_get_endpoint_by_regs()` (`return node` inside
  `for_each_endpoint_of_node()`).
- Scoped, leave early with no put: `of_platform_populate()` and
  `of_platform_bus_probe()` in `drivers/of/platform.c` use
  `for_each_child_of_node_scoped()` with a bare `break`.
- Scoped, hand the loop's own reference out: `return_ptr()` in
  `of_graph_get_port_by_id()`; no `of_node_get()` is needed for that.
- Scoped, keep the node while the loop goes on: store `of_node_get()` of it;
  the loop's reference is put at the next step.
