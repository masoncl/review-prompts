- Macros that declare the loop variable themselves, as `struct device_node *`
  with `__free(device_node)`: `for_each_child_of_node_scoped()`,
  `for_each_available_child_of_node_scoped()`,
  `for_each_compatible_node_scoped()`,
  `for_each_child_of_node_with_prefix()`, `for_each_of_graph_port()`,
  `for_each_of_graph_port_endpoint()`. No other node iterator in
  `include/linux/of.h` or `include/linux/of_graph.h` does.
- `for_each_child_of_node_with_prefix()`, `for_each_of_graph_port()`,
  `for_each_of_graph_port_endpoint()`: no "_scoped" in the name, yet they
  declare the variable; a variable of that name declared by the caller is
  shadowed and never set.
- There is no for_each_endpoint_of_node_scoped in this tree;
  `for_each_endpoint_of_node()` uses a caller-declared variable and the caller
  puts it on early exit.
- `for_each_reserved_child_of_node()` and `for_each_node_with_property()`:
  counted, caller-declared, same rule as `for_each_child_of_node()`.
- `of_property_for_each_u32()`: takes three arguments and declares its own
  cursor `_it` in the `for`; only the `u32` is the caller's.
- `of_property_for_each_string()`: declares nothing; the caller supplies
  both the `struct property *` and the `const char *`.
- `for_each_of_allnodes()`, `for_each_of_allnodes_from()`: usable only by
  built-in code; `__of_find_all_nodes()` is not exported, `of_mutex` is
  declared only in `drivers/of/of_private.h`, and `devtree_lock` only there
  and in `arch/sparc/include/asm/prom.h`.
- `for_each_of_allnodes()` and `for_each_of_allnodes_from()`: take no
  reference; in-tree callers hold `devtree_lock` (for example the `of_find_`
  functions in `drivers/of/base.c`), hold `of_mutex` (`of_core_init()`), or
  run from `__init` code.
