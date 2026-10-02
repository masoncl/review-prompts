- Reference from `of_node_get()` in `mfd_match_of_node_to_dev()`: dropped
  when `platform_device_release()` calls `fwnode_handle_put()` on
  `dev.fwnode`, while `dev.fwnode` is still the OF node.
- Software node: removed with `device_remove_software_node()` when
  `cell->swnode` is set.
- IRQ mappings made by `irq_create_mapping()` in `mfd_add_device()`: not
  disposed. `drivers/mfd/mfd-core.c` does not call `irq_dispose_mapping()`,
  and neither do `platform_device_del()` and `platform_device_release()`.
