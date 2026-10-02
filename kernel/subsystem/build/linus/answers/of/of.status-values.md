- There is no of_device_is_fail and no of_device_is_reserved in this tree;
  `__of_device_is_fail()` and `__of_device_is_reserved()` are static in
  `drivers/of/base.c`.
- Outside `drivers/of/base.c`: the only exported test for reserved is
  `of_get_next_reserved_child()`; fail and disabled have none, a caller reads
  `status` itself, for example with `of_property_read_string()`.
- `"disabled"`: compared against nowhere in `drivers/of/`; any `status` other
  than `"okay"` or `"ok"` makes the node not available.
- `status` present but empty (non-NULL `value`) or not NUL-terminated:
  `__of_device_is_status()` returns false, so the node is not available, not
  reserved and not fail.
- `of_get_next_cpu_node()` and `for_each_of_cpu_node()`: skip only fail
  nodes; disabled and reserved CPU nodes are returned.
- `of_get_next_reserved_child()` and `for_each_reserved_child_of_node()`:
  return only reserved children; the kerneldoc line about skipping disabled
  nodes describes a different function.
- `of_get_available_child_by_name()`: tests only the first child with that
  name; if it is not available the result is NULL, with no look at later
  children of the same name.
- `of_fwnode_get_next_child_node()` and `of_fwnode_get_named_child_node()` in
  `drivers/of/property.c`: use the available-only iterators, so fwnode child
  walks over OF nodes skip every child that is not available.
- `of_get_next_status_child()`: static worker behind the available and
  reserved child iterators; it takes the status test as a callback.
- `of_fdt_device_is_available()` in `drivers/of/fdt.c` and
  `of_property_status_ok()` in `drivers/of/dynamic.c`: separate parsers that
  know only `"okay"` and `"ok"`; they do not call `__of_device_is_status()`.
