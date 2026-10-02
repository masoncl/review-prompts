- `device_set_node()`: assigns `dev->fwnode` and `dev->of_node`, takes no
  reference.
- `device_add()` and `device_release()` in `drivers/base/core.c`: neither
  gets nor puts `dev->of_node`; whoever creates the device owns the reference
  and must drop it itself.
- Core helpers that do take and drop it: `device_add_of_node()` and
  `device_remove_of_node()`, `device_set_of_node_from_dev()`,
  `platform_device_set_of_node()`, `platform_device_set_fwnode()`,
  `platform_device_set_of_node_from_dev()`.
- `of_device_alloc()`: calls `platform_device_set_of_node()`, which takes the
  reference with `fwnode_handle_get()`.
- `platform_device_release()`: drops the node with `fwnode_handle_put()` on
  `dev.fwnode`; it does not call `of_node_put()` on `dev.of_node`.
- Platform device whose `dev.of_node` is assigned by hand with
  `of_node_get()` while `dev.fwnode` is left unset: the release does not drop
  that reference; use `platform_device_set_of_node()`.
- `platform_device_register_full()`: takes `fwnode_handle_get()` on
  `pdevinfo->fwnode` itself.
- `device_set_of_node_from_dev()`: marks reuse with
  `dev_set_of_node_reused()`, a bit `DEV_FLAG_OF_NODE_REUSED`; `struct device`
  has no `of_node_reused` field, only `struct platform_device_info` has.
- `device_add_of_node()`: returns `-EBUSY` and takes nothing if the device
  already has an `of_node`.
- `__of_find_node_by_path()` and `__of_find_node_by_full_path()` in
  `drivers/of/base.c`: return a counted node.
- `__of_find_all_nodes()`: borrowed; `of_find_all_nodes()` is the counted
  form.
- `dev_of_node()` and `to_of_node()`: borrowed, plain accessors.
- Bus code that sets the node with `device_set_node()` and wants it counted
  takes the reference itself, for example `of_register_spi_device()` with
  `of_node_get()`.
