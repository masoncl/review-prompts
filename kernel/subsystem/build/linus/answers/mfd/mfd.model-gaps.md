- Models take firmware lookups on a child to follow `dev->fwnode`. After
  `device_set_of_node_from_dev()`, `platform_get_irq()` on the child asks the
  parent's node, through `dev_fwnode()`, before the cell's interrupt
  resources; it does not test `dev_of_node_reused()`.
- Models expect `kzalloc()` for a structure in this code.
  `mfd_match_of_node_to_dev()`, `of_syscon_register()` and
  `regmap_add_irq_chip_fwnode()` use `kzalloc_obj()` from
  `include/linux/slab.h`.
- Models expect an explicit `kfree()` on each early exit of
  `of_syscon_register()`. It holds `syscon` under `__free(kfree)` and returns
  it with `return_ptr()`.
- Models name irq_domain_add_linear() for the domain of a regmap interrupt
  chip. No source file in this tree defines it.
- Models do not know `platform_device_set_of_node()` and
  `platform_device_set_fwnode()` in `drivers/base/platform.c`.
