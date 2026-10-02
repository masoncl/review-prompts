- There is no gicv5_alloc_lpi() or gicv5_free_lpi() in this tree; the ITS
  domain neither allocates nor frees an LPI itself.
- Parent LPIs: one call
  `irq_domain_alloc_irqs_parent(domain, virq, nr_irqs, NULL)` for the whole
  range. `gicv5_irq_lpi_domain_alloc()` in `drivers/irqchip/irq-gic-v5.c`
  takes each LPI with the static `alloc_lpi()` and calls
  `gicv5_irs_iste_alloc()`; it ignores `arg`.
- LPI number: unknown to the ITS at alloc time; it is first read from
  `d->parent_data->hwirq` in `gicv5_its_irq_domain_activate()`.
- Steps that can fail, in order: `gicv5_its_alloc_eventid()`,
  `iommu_dma_prepare_msi()`, `irq_domain_alloc_irqs_parent()`.
- `iommu_dma_prepare_msi()` or parent failure: both jump to `out_eventid`,
  which calls `gicv5_its_free_eventid()` and nothing else.
- Partial parent failure: `gicv5_irq_lpi_domain_alloc()` releases the LPIs
  it already took through `gicv5_irq_lpi_domain_free()` before returning;
  the ITS has no per-interrupt unwind loop.
- After the parent call nothing can fail: `irq_domain_set_info()` returns
  void.
- Per-interrupt flags: `irqd_set_single_target()` and
  `irqd_set_affinity_on_activate()`; resend-when-in-progress is not set.
- `struct gicv5_its_dev`: not freed on any failure of
  `gicv5_its_irq_domain_alloc()`; once prepare has succeeded, only
  `gicv5_its_msi_teardown()` frees it.
