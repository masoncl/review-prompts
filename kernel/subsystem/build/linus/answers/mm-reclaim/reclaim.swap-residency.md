- folio_swapped(): not in this tree; the test is `folio_maybe_swapped()`,
  static in `mm/swapfile.c`.
- `mem_cgroup_swap_full()`: not tested by `folio_free_swap()`; a caller that
  wants it tests it first, as `should_try_to_free_swap()` in `mm/memory.c`
  does; `__try_to_reclaim_swap()` tests it, when called with `TTRS_FULL`,
  before its own `swap_cache_del_folio()`.
- `pm_suspended_storage()`: when true, `folio_swapcache_freeable()` refuses.
- Folio lock: required but only asserted, with `VM_BUG_ON_FOLIO()`.
- False "unused": not possible while the caller holds the folio lock, because
  a count leaves 0 only through `folio_dup_swap()`.
- Return `true`: also means the folio was marked dirty.
- Return `false`: the folio may not be in the swap cache at all.
