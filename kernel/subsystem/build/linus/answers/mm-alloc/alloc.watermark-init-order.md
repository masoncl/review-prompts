- `CONFIG_DEFERRED_STRUCT_PAGE_INIT`: `page_alloc_init_late()` blocks until
  deferred init has finished, and `kernel_init_freeable()` calls it before
  `do_basic_setup()`, so `init_per_zone_wmark_min()` sees final zone sizes.
- Before `init_per_zone_wmark_min()` has run, `__zone_watermark_ok()` given a
  mark from an accessor returns true whenever the free count minus the
  unusable pages is above `lowmem_reserve[highest_zoneidx]`, plus the
  free-list scan for an order above zero.
- `lowmem_reserve[]` can be non-zero before `init_per_zone_wmark_min()`:
  `adjust_managed_page_count()` calls `setup_per_zone_lowmem_reserve()`, for
  example from `init_cma_reserved_pageblock()`.
- `cond_accept_memory()`: treats `promo_wmark_pages()` of 0 as "not
  initialised" and accepts one block with `try_to_accept_memory_one()`.
- **Unsafe usage**: computing a deficit from a watermark accessor in code
  that can run before `init_per_zone_wmark_min()`, without a test for 0; the
  deficit is never positive and the work is never done.
  - Safe: test the mark for 0 and take a fixed step, as
    `cond_accept_memory()` does.
  - Safe: test for 0 and do nothing, as `boost_watermark()` does.
  - Safe: a plain pass or fail test, as `zone_watermark_fast()` in
    `get_page_from_freelist()`; with a mark of 0 it passes while the usable
    free pages exceed `lowmem_reserve[highest_zoneidx]`.
