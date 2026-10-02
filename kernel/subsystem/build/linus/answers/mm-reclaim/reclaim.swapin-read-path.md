- Names: there is no alloc_swap_folio(), swapin_folio(),
  swapcache_prepare() or __read_swap_cache_async() here. `swapin_sync()` in
  `mm/swap_state.c` is the synchronous path.
- Choice in `do_swap_page()`: `SWP_SYNCHRONOUS_IO` in `si->flags` alone;
  `__swap_count()` is not tested.
- `swapin_sync()`: gets `thp_swapin_suitable_orders(vmf) | BIT(0)` as
  `orders` from `do_swap_page()`; allocation, memcg charge and swap cache
  insertion all happen in `swap_cache_alloc_folio()`.
- Every path puts the folio in the swap cache before the read. The comment
  "skipping swap cache" at the `shmem_swap_alloc_folio()` call does not
  describe `swapin_sync()`.
- `thp_swapin_suitable_orders()`: filters on `userfaultfd_armed()`,
  `zswap_never_enabled()`, THP settings, alignment and `can_swapin_thp()`
  only. Zero flag, cached slots and counts are left to
  `__swap_cache_add_check()`.
- `swap_vma_readahead()` and `swap_cluster_readahead()`: call
  `swap_cache_read_folio()` per entry, then fetch the target with
  `swap_cache_read_folio_sync()`. `read_swap_cache_async()` is not on this
  path; `mm/madvise.c` uses it.
- Failure value: `swapin_sync()` returns an `ERR_PTR()` and, with
  `CONFIG_SWAP`, never NULL; `swapin_readahead()` returns NULL and never an
  `ERR_PTR()`. `do_swap_page()` tests `IS_ERR_OR_NULL()`.
- `swap_read_folio()`: after the zero-flag and `zswap_load()` checks it
  queues the folio in the caller's `struct swap_io_ctx` with
  `swap_add_folio()`. There is no swap_read_folio_fs(),
  swap_read_folio_bdev_sync() or swap_read_folio_bdev_async();
  `swap_read_submit()` calls `submit_read` of `struct swap_ops`.
