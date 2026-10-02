- Models take `of_device_alloc()` to store the node with `of_node_get()`.
  `platform_device_set_of_node()`, which it calls, sets both `dev.fwnode` and
  `dev.of_node`.
- Models take `of_node_reused` to be a member of `struct device`. The bit is
  read with `dev_of_node_reused()`, which `__create_dev_flag_accessors()`
  generates in `include/linux/device.h`.
- Models take `RESERVEDMEM_OF_DECLARE()` to register an init function. Its
  third argument is a `struct reserved_mem_ops *`; see
  `include/linux/of_reserved_mem.h`.
- Models take `node_init` in `struct reserved_mem_ops` to be optional like the
  other callbacks. `__reserved_mem_init_node()` in
  `drivers/of/of_reserved_mem.c` calls it without a NULL test.
- Models name of_node_alloc() as a way to create a dynamic node.
  `of_changeset_create_node()` in `drivers/of/dynamic.c` creates one, through
  `__of_node_dup()`.
- Models do not know `kzalloc_obj()`, `kzalloc_objs()` and `kmalloc_obj()`,
  which `drivers/of/` uses for struct allocations. The GFP argument is
  optional and defaults to `GFP_KERNEL`; see `include/linux/slab.h`.
- Models take a missing `#address-cells` or `#size-cells` to fall back
  silently to the parent or the default. `of_bus_n_addr_cells()` and
  `of_bus_n_size_cells()` in `drivers/of/base.c` `WARN_ONCE()` for a level
  that lacks the property, except with `CONFIG_SPARC` or when the tree has a
  node compatible with "coreboot".
- Models take `of_root` to be NULL when the bootloader passed no blob.
  `of_have_populated_dt()` tells that case by testing `of_root` for a
  "compatible" property; see `include/linux/of.h`.
- Models take `early_init_dt_scan()` and `early_init_dt_verify()` to take one
  pointer. Both take `(void *dt_virt, phys_addr_t dt_phys)`; the physical
  address is kept in `initial_boot_params_pa`.
- Models do not know `of_imap_parser_init()` and `for_each_of_imap_item()` in
  `include/linux/of_irq.h`, which walk `interrupt-map`. Leaving the loop early
  owes `of_node_put()` on `item.parent_args.np`.
- Models do not know the root-node helpers `of_machine_get_match()`,
  `of_machine_get_match_data()`, `of_machine_device_match()`,
  `of_machine_read_compatible()` and `of_machine_read_model()`; see
  `include/linux/of.h`.
- Models look for `of_get_cpu_node()` and `of_cpu_device_node_get()` in
  `drivers/of/base.c` and for `of_modalias()` in `drivers/of/device.c`. They
  are in `drivers/of/cpu.c` and `drivers/of/module.c`.
- Models look for `struct of_device_id` in `include/linux/mod_devicetable.h`.
  It is defined in `include/linux/device-id/of.h`, which that header includes.
