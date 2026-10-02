- `user_alloc_needs_zeroing()`: true when `cpu_dcache_is_aliasing()` or
  `cpu_icache_is_aliasing()`, even with init-on-alloc enabled; otherwise
  true only when `init_on_alloc` is off.
- Generic `vma_alloc_zeroed_movable_folio()` in `include/linux/highmem.h`:
  allocates without `__GFP_ZERO` and calls `clear_user_highpage()` only when
  `user_alloc_needs_zeroing()` is true.
- Architecture overrides of `vma_alloc_zeroed_movable_folio()` pass
  `__GFP_ZERO` instead; search `arch/` for the name.
- `__GFP_ZERO` for user-mapped memory also appears in generic code, for
  example `alloc_huge_zero_folio()` in `mm/huge_memory.c`.
- `folio_zero_user()`: clears up to three contiguous ranges through
  `clear_contig_highpages()`; the last range is the faulting page plus up to
  `FOLIO_ZERO_LOCALITY_RADIUS` pages on each side.
- `folio_zero_user()`: `clear_contig_highpages()` calls `might_sleep()`, so it
  needs a context that may sleep.
- `folio_zero_user()` rescheduling: on a preemptible model one range is one
  unit with no `cond_resched()` inside it.
- **Unsafe usage**: skipping the zeroing because
  `user_alloc_needs_zeroing()` is false, for a folio that did not just come
  from the page allocator; the function tests only the `init_on_alloc` key
  and cache aliasing.
  - Safe: a folio fresh from `vma_alloc_folio()`, as in `alloc_anon_folio()`
    and `vma_alloc_anon_folio_pmd()`.
  - Safe: zero unconditionally for a folio from a pool, as
    `hugetlb_no_page()`, `hugetlbfs_fallocate()` and `memfd_alloc_folio()` do
    with `folio_zero_user()`.
