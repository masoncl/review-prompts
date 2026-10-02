- Test to choose between page-cache and swap-cache operations:
  `folio_test_swapcache()` in `include/linux/page-flags.h`, as
  `folio_mapping()` does.
- Shmem folio in both caches at once: happens with the folio locked, for
  example in `shmem_writeout()` between `folio_alloc_swap()` and
  `shmem_delete_from_page_cache()`, and in `shmem_swapin_folio()` between
  `shmem_add_to_page_cache()` and `swap_cache_del_folio()`.
- In that window: `folio_test_swapcache()` is true while `folio->mapping` is
  the shmem mapping, so the test selects the right operations only under the
  folio lock.
