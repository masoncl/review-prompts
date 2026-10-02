- `gicv5_irq_lpi_domain_alloc()`: loops over `nr_irqs` and calls `alloc_lpi()`
  itself; it does not reject `nr_irqs != 1` and does not take an LPI from
  `arg`.
- `alloc_lpi()` failure at index `i`: nothing is in flight; the function only
  frees interrupts 0 to `i - 1`.
- `gicv5_irs_iste_alloc()` failure: `release_lpi()` for the in-flight LPI,
  then the same free of 0 to `i - 1`.
- Interrupts already set up: undone by `gicv5_irq_lpi_domain_free()` with
  count `i`; the LPI domain has no parent, so
  `irq_domain_free_irqs_parent()` plays no part.
- Not undone: an L2 IST that `gicv5_irs_iste_alloc()` installed stays; the
  priority and handling mode written to hardware stay.
- `gicv5_irq_ipi_domain_alloc()` and `gicv5_its_irq_domain_alloc()`: neither
  frees an LPI; each makes one parent call for the whole range and the loop
  after it cannot fail. The ITS error path releases the EventID range only.
- **Unsafe usage**: returning an error from a domain `alloc` callback while
  earlier interrupts of the range still hold resources.
  - Unsafe: `irq_domain_alloc_irqs_locked()` does not call the `free` callback
    when `alloc` fails; it frees only `irq_data` and descriptors, so the LPIs
    stay allocated in `lpi_ida`.
  - Safe: free 0 to `i - 1` before returning, as
    `gicv5_irq_lpi_domain_alloc()` does.
  - Safe: do every step that can fail before the per-interrupt loop, as
    `gicv5_its_irq_domain_alloc()` does.
- **Unsafe usage**: passing the in-flight interrupt, or all `nr_irqs`, to
  `gicv5_irq_lpi_domain_free()` from the error path.
  - Unsafe: `gicv5_irq_lpi_domain_free()` calls `release_lpi()` on `d->hwirq`,
    which is not set until `irq_domain_set_info()` has run for that interrupt.
  - Safe: `release_lpi()` on the local value for the in-flight interrupt, then
    `gicv5_irq_lpi_domain_free()` with count `i`, as
    `gicv5_irq_lpi_domain_alloc()` does.
