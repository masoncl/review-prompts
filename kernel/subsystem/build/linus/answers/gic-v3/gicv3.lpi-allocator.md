- `alloc_lpi_range()`: all or nothing. It takes `nr_lpis` from the first
  range with `span >= nr_lpis`, and returns `-ENOSPC` when no single range is
  large enough; it never returns part of a request.
- `its_lpi_alloc()`: halves `nr_irqs` and retries by itself. On failure it
  returns NULL with `*base` and `*nr_ids` set to 0, not an error code.
- Shortfall in `its_create_device()`: the device keeps the smaller
  `nr_lpis`; `its_alloc_device_irq()` later returns `-ENOSPC` when
  `lpi_map` has no free region.
- Shortfall in `its_vpe_irq_domain_alloc()`: `nr_ids < nr_irqs` frees the
  range again and returns `-ENOMEM`.
- `free_lpi_range()`: allocates its node before taking the lock and returns
  `-ENOMEM` without touching the list; `its_lpi_free()` only does
  `WARN_ON()`, so those LPIs are not returned.
- **Unsafe usage**: calling `free_lpi_range()` for LPIs that are already in
  `lpi_range_list`. Nothing checks for overlap; `merge_lpi_ranges()` merges
  only on exact adjacency, so `alloc_lpi_range()` can then hand out the same
  LPI twice.
  - Safe: one `its_lpi_free()` with the `base` and `nr_ids` that
    `its_lpi_alloc()` returned, as `its_msi_teardown()` does after it finds
    `lpi_map` empty.
