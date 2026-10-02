- PCI interrupts: mapped straight after allocation. `MSI_COMMON_FLAGS` in
  `drivers/pci/msi/irqdomain.c` includes `MSI_FLAG_ACTIVATE_EARLY`, so
  `msi_init_virq()` calls `irq_domain_activate_irq()` inside
  `__msi_domain_alloc_irqs()`. No other file sets that flag.
- `reserve` argument: ignored by `gicv5_its_irq_domain_activate()`; the
  event is always mapped.
- Entry written: an ITT entry (`GICV5_ITTL2E_LPI_ID`, `GICV5_ITTL2E_VALID`),
  not a device table entry.
- Invalidation: `gicv5_its_itt_cache_inv()`; there is no
  gicv5_its_invalidate_ite() in this tree.
- `gicv5_its_map_event()`: `-EEXIST` is its only error. The return value of
  `gicv5_its_itt_cache_inv()` is discarded by map and by unmap, so a timed
  out invalidation still returns 0.
- `-EEXIST` trigger: `irq_domain_activate_irq()` skips an interrupt that is
  already activated, so the error means the entry was left valid by an
  earlier user of that event ID.
