- **Potentially unsafe usage**: `of_node_put()` on a `__free(device_node)`
  variable.
  - Unsafe: when the variable still holds the put pointer at any scope exit;
    the `DEFINE_FREE` body in `include/linux/of.h` puts it a second time.
  - Safe: when the variable is overwritten with a counted pointer or NULL
    before any exit, as `__of_translate_address()` in `drivers/of/address.c`
    does with `dev`.
- **Potentially unsafe usage**: passing a `__free(device_node)` variable as
  the consumed argument of `of_get_next_parent()` or an `of_find_` function.
  - Unsafe: when the result goes to another variable; the callee has put the
    node and the cleanup puts it again.
  - Safe: when the result is assigned back to the same variable, as
    `of_link_to_phandle()` in `drivers/of/property.c` does with
    `of_get_next_parent()`.
- **Unsafe usage**: storing an `ERR_PTR()` value in a
  `__free(device_node)` variable; the `DEFINE_FREE` body tests only for NULL
  and calls `of_node_put()` on it.
  - Safe: NULL, as `opp_np` in `_bandwidth_supported()` in
    `drivers/opp/of.c` holds until a lookup is assigned.
- `of_graph_get_port_by_id()`: its `__free(device_node)` variable `node` is
  never handed out; `return_ptr()` is applied to the loop variable of
  `for_each_child_of_node_scoped()`.
- Storing instead of returning: `*host = no_free_ptr(dev)` in
  `__of_translate_address()`.
