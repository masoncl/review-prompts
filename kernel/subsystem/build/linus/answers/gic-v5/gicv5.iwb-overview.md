- Domain creation: `gicv5_iwb_init_bases()` calls
  `gicv5_iwb_create_device_domain()`, which calls
  `msi_create_device_irq_domain()` with `MSI_DEFAULT_DOMAIN`; the driver does
  not call `irq_domain_create_hierarchy()` or
  `msi_create_parent_irq_domain()`.
- ITS device: allocated at probe, not at the first interrupt request;
  `msi_create_device_irq_domain()` runs the new domain's `msi_prepare`, which
  `its_v5_init_dev_msi_info()` set to `its_v5_pmsi_prepare()` in
  `drivers/irqchip/irq-gic-its-msi-parent.c`.
- ITS device size: the wire count rounded up by `roundup_pow_of_two()` in
  `its_v5_pmsi_prepare()`, stored as `num_events`.
- Device ID: read in `its_v5_pmsi_prepare()`; on DT it is the argument cell
  of `msi-parent`, through `of_pmsi_get_msi_info()`; on ACPI it comes from
  `iort_pmsi_get_msi_info()`.
- Wire number and MSI index: not the same thing;
  `msi_device_domain_alloc_wired()` allocates the index with `MSI_ANY_INDEX`.
- Wire number path: `msi_device_domain_alloc_wired()` puts the wire in the
  low 32 bits of `desc->data.icookie.value` (type in the high 32);
  `gicv5_iwb_domain_set_desc()` copies it to `alloc_info->hwirq`.
- `MSI_ALLOC_FLAGS_FIXED_MSG_DATA`: makes `gicv5_its_alloc_eventid()` in
  `drivers/irqchip/irq-gic-v5-its.c` take `info->hwirq` as the event ID
  instead of searching `event_map`; without the flag the wire and the event
  ID need not match.
- `iwb_msi_template` chip: `.irq_mask` and `.irq_unmask` are
  `irq_chip_mask_parent()` and `irq_chip_unmask_parent()`; the callbacks that
  write IWB registers are `gicv5_iwb_irq_enable()`,
  `gicv5_iwb_irq_disable()` and `gicv5_iwb_set_type()`.
- `gicv5_iwb_write_msi_msg()`: empty, but it cannot be removed;
  `msi_lib_init_dev_msi_info()` in `drivers/irqchip/irq-msi-lib.c` fails
  domain creation when `irq_write_msi_msg` is NULL.
- `MSI_FLAG_USE_DEV_FWNODE`: the domain's fwnode is the bridge device's own
  fwnode, so a consumer's DT or ACPI specifier that names the bridge finds
  this domain.
