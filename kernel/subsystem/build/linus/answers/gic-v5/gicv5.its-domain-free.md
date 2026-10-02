- Last two calls: `gicv5_its_syncr()` then `gicv5_irs_syncr()`.
  `gicv5_its_device_cache_inv()` is not called from free.
- Order before the syncs: `bitmap_release_region()`, then
  `irq_domain_reset_irq_data()`, then `irq_domain_free_irqs_parent()`. The
  event ID and the LPI are back in their allocators before either sync
  starts.
- LPI release: done by the parent. `irq_domain_free_irqs_parent()` reaches
  `gicv5_irq_lpi_domain_free()`, which calls `release_lpi()`; there is no
  gicv5_free_lpi() in this tree.
- Reuse before the syncs finish: prevented by `domain->root->mutex`.
  `irq_domain_free_irqs()` holds it across `.free`, and
  `__irq_domain_alloc_irqs()` takes the same mutex; the root of every ITS
  and per-device domain is the LPI domain.
- Per interrupt: `.free` runs with `nr_irqs == 1` (see "Event ID
  allocation"), so both syncs are issued once per freed interrupt.
- Guarantee to the caller: none is reported. Both functions return void and
  wait with `gicv5_wait_for_op()`; a timeout is only logged, and free
  completes anyway.
- Hardware meaning of the syncs: no comment or document in this tree states
  it.
- Context: `gicv5_wait_for_op()` uses `readl_poll_timeout()`, which may
  sleep, so free must run in sleepable context.
- LPI state: not cleaned at free. `gicv5_irq_lpi_domain_alloc()` calls
  `gicv5_lpi_config_reset()` when the LPI is handed out again.
- `struct gicv5_its_dev`: not released by free, even when `event_map`
  becomes empty; `gicv5_its_msi_teardown()` does that.
- **Unsafe usage**: freeing an interrupt whose event is still mapped.
  - Unsafe: `gicv5_its_irq_domain_free()` never writes the ITT, so the entry
    stays valid and names an LPI that `release_lpi()` has returned; the next
    `gicv5_its_map_event()` for that event ID returns `-EEXIST`.
  - Safe: through `__msi_domain_free_irqs()` in `kernel/irq/msi.c`, which
    calls `irq_domain_deactivate_irq()` on every activated interrupt before
    `irq_domain_free_irqs()`.
  - Safe: on the alloc error paths, where the interrupt was never activated,
    for example `out_free_irqs` in `irq_domain_alloc_irqs_locked()`.
