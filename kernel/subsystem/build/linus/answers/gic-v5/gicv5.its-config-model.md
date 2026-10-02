- One device or event mapping change is two calls: `its_write_table_entry()`
  (store plus clean or barrier), then `gicv5_its_itt_cache_inv()` or
  `gicv5_its_device_cache_inv()` (register writes plus the poll).
- `gicv5_its_dcache_clean()`: outside `its_write_table_entry()` it is called
  only on whole tables.
- `gicv5_its_cache_sync()`: called only from the two invalidate helpers.
- Device mapping: `gicv5_its_device_register()`, reached from
  `gicv5_its_msi_prepare()` through `gicv5_its_alloc_device()`.
- Event mapping: `gicv5_its_map_event()`, reached from
  `gicv5_its_irq_domain_activate()`.
- `gicv5_its_irq_domain_alloc()`: writes no ITS table entry; it reserves
  EventIDs in `event_map` and allocates the LPI through the parent domain.
