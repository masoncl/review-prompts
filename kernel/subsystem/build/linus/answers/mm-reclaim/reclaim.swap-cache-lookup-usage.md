- Before the lookup: stabilise the device with `get_swap_device()`, as
  `do_swap_page()` does.
- Match test: the returned folio may be a large folio whose `folio->swap` is
  lower than the entry; `folio_matches_swap_entry()` rounds the entry down.
- **Potentially unsafe usage**: using the returned folio without lock and
  `folio_matches_swap_entry()`.
  - Unsafe: when mapping it, changing its swap count or reading
    `folio->swap`; the folio may have left the swap cache or serve another
    entry.
  - Safe: reading only `folio_test_uptodate()` as a hint, as `mincore_swap()`
    does.
  - Safe: locking it and calling `folio_free_swap()`, which rechecks the
    folio's own state, as `try_to_unuse()` does.
  - Safe: locking it and comparing `folio_test_swapcache()` and
    `folio->swap.val` with the entry, only after large folios were rejected,
    as `move_swap_pte()` in `mm/userfaultfd.c` does; its caller
    `move_pages_ptes()` returns `-EBUSY` for a large folio.
- Lookup found nothing, swap-in: `do_swap_page()` does not recheck the PTE
  first; `swapin_sync()` or `swapin_readahead()` add a folio through
  `swap_cache_alloc_folio()`.
- Guard on that path: `__swap_cache_add_check()` under the cluster lock
  rejects a slot with count 0 or one already cached.
- Swap-in failed: `do_swap_page()` returns `VM_FAULT_OOM` only if
  `pte_same()` still holds under the PTL.
- Lookup found nothing, entry moved without a folio: under the PTL recheck
  that the PTE is unchanged and that `swap_cache_has_folio()` is still false;
  `move_swap_pte()` returns `-EAGAIN` otherwise.
