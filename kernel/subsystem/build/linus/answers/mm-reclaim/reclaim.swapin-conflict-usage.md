- Return value: `ERR_PTR(-EBUSY)`, and only when the order that failed was
  the lowest one set in `orders`.
- Callers that never see `-EBUSY`: every caller with `BIT(0)` in `orders`,
  because at order 0 `__swap_cache_add_check()` returns before the range
  loop. These are `swap_cache_read_folio()`, `zswap_writeback_entry()` and
  `do_swap_page()` through `swapin_sync()`, large orders included.
- Caller that can see `-EBUSY`: `shmem_swap_alloc_folio()` in `mm/shmem.c`,
  which passes a single `BIT(order)` to `swapin_sync()`.
- `shmem_swap_alloc_folio()`: on any error at a nonzero order it retries
  once at order 0 with the same `entry`; an error at order 0 is returned
  unchanged. It does not call `folio_put()` and does not adjust `entry`;
  `__swap_cache_alloc()` frees its own folio on failure.
- **Unsafe usage**: retrying after `-EBUSY` with the same `orders`;
  `__swap_cache_add_check()` returns `-EBUSY` again for as long as the
  slot state lasts.
  - Safe: retry once with a lower order and treat an order 0 error as
    final, as `shmem_swap_alloc_folio()` does.
  - Safe: pass `BIT(0)` together with the large orders, so the fallback
    happens inside `swap_cache_alloc_folio()`, as `do_swap_page()` does.
- **Unsafe usage**: passing an entry rounded down to the folio size as the
  target, in place of the entry of the slot wanted;
  `__swap_cache_add_check()` tests the target slot itself for `-EEXIST` and
  `-ENOENT`, and an order 0 retry reads the slot it is given.
  - Safe: pass the entry of the faulting slot; `__swap_cache_alloc()`
    rounds it down. `shmem_swapin_folio()` adds the index offset to the
    stored entry before the call.
- Folio after a retry: may be smaller than the entry in the mapping.
  `shmem_swapin_folio()` tests `order > folio_order(folio)` and calls
  `shmem_split_large_entry()` before it inserts the folio.
- Folio from `swapin_sync()`: may be an existing swap cache folio, returned
  unlocked; the caller locks it and checks `folio_matches_swap_entry()`.
- `-EEXIST` to `shmem_get_folio_gfp()`: never comes from `swapin_sync()`,
  which loops on it. `shmem_swapin_folio()` sets it itself, for example when
  `shmem_confirm_swap()` or `folio_matches_swap_entry()` fails; another
  error of `swapin_sync()` is passed up while `shmem_confirm_swap()` still
  finds the entry.
