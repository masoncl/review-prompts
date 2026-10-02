- `dev_alloc_lock` in `struct gicv5_its_chip_data`: the only lock the
  driver defines; there is no per-device lock, no bitmap lock and no lock
  around the invalidate registers.
- `dev_alloc_lock`: taken only in `gicv5_its_msi_prepare()` and
  `gicv5_its_msi_teardown()`.
- `gicv5_its_device_cache_inv()`: every path holds `dev_alloc_lock`; it is
  reached only through `gicv5_its_device_register()` and
  `gicv5_its_device_unregister()`.
- `gicv5_its_itt_cache_inv()`: reached only from `gicv5_its_map_event()`
  and `gicv5_its_unmap_event()`; the driver takes no lock on this path.
- Activate/deactivate callers: hold the per-device `mutex` of
  `struct msi_device_data` (`msi_init_virq()`, `__msi_domain_free_irqs()`)
  or the per-interrupt `desc->lock` (for example `irq_activate()` from
  `__setup_irq()`, `irq_shutdown_and_deactivate()`).
- `irq_domain_activate_irq()` and `irq_domain_deactivate_irq()`: do not
  take `domain->root->mutex`.
- `GICV5_ITS_DIDR`, `GICV5_ITS_EIDR`, `GICV5_ITS_STATUSR`: one set per ITS;
  no lock in this tree is per ITS on the event path, and none is held on
  every path to both `gicv5_its_itt_cache_inv()` and
  `gicv5_its_device_cache_inv()`.
- `event_map` allocation and release: in `gicv5_its_irq_domain_alloc()` and
  `gicv5_its_irq_domain_free()`, with no driver lock.
- `gicv5_its_irq_domain_alloc()` and `gicv5_its_irq_domain_free()`: run
  under `domain->root->mutex`, taken in `__irq_domain_alloc_irqs()` and
  `irq_domain_free_irqs()` in `kernel/irq/irqdomain.c`.
- `domain->root` for the ITS domain: `gicv5_global_data.lpi_domain`, so one
  mutex covers every ITS and every device.
- `gicv5_its_msi_teardown()`: tests `bitmap_empty()` and calls
  `bitmap_free()` under `dev_alloc_lock`, not under `domain->root->mutex`;
  it is reached from `msi_remove_device_irq_domain()`, which holds the
  per-device MSI mutex.
- **Unsafe usage**: calling `gicv5_its_device_register()`,
  `gicv5_its_device_unregister()` or `gicv5_its_devtab_get_dte_ref()` with
  `alloc` true, without `dev_alloc_lock`.
  - Unsafe: `gicv5_its_alloc_l2_devtab()` tests `GICV5_DTL1E_VALID` and then
    allocates, and `gicv5_its_alloc_device()` does `xa_load()` then
    `xa_store()`; both are check-then-act with no lock of their own.
  - Safe: under `guard(mutex)(&its->dev_alloc_lock)`, as
    `gicv5_its_msi_prepare()` does.
