- `swap_writeout()` order: `folio_free_swap()`, `arch_prepare_to_swap()`,
  zero-filled test, `zswap_store()`, `mem_cgroup_zswap_writeback_enabled()`,
  then `__swap_writepage()`.
- Zero-filled mark: set by `swap_zeromap_folio_set()` in the cluster's swap
  table or `ci->zero_bitmap`; there is no si->zeromap.
- `swap_read_folio()`, after its zero-mark and `zswap_load()` tests, and
  `__swap_writepage()` have no per-device branch; both end in
  `swap_add_folio()`.
- Every device queues, block devices too: `swap_add_folio()` adds the folio
  to `ctx->sio`.
- `swap_add_folio()` sends the batch itself in three cases: the new folio
  cannot merge, the batch reached `SWAP_CLUSTER_MAX` folios, or it is a write
  to an `SWP_SYNCHRONOUS_IO` device.
- A read queued into an empty context is never sent by `swap_read_folio()`
  alone, on any device.
- There is no swap_read_unplug() or swap_write_unplug(); the flush calls are
  `swap_read_submit()` and `swap_write_submit()` in `mm/page_io.c`.
- Both submit calls return at once when `ctx->sio` is NULL.
- Until submit, a queued read folio stays locked and a queued write folio
  stays under writeback; `swap_read_end()` and `swap_write_end()` release them.
- `mempool_alloc(sio_pool, GFP_NOIO)` in `swap_add_folio()` can sleep.
- **Unsafe usage**: passing a NULL `struct swap_io_ctx` pointer;
  `swap_add_folio()` dereferences it.
  - Safe: a zeroed `struct swap_io_ctx ctx = {};` on the stack, as
    `swapin_sync()` does.
- **Potentially unsafe usage**: returning without the submit call.
  - Unsafe: after any call that may have queued a folio, such as
    `swap_read_folio()`, `read_swap_cache_async()`, `swap_writeout()` or
    `shmem_writeout()`.
  - Safe: before anything was queued, as the early error exits of
    `zswap_writeback_entry()` do.
  - Safe: one submit on the common exit, as `shrink_folio_list()` does.
- **Unsafe usage**: waiting on a folio that sits in the caller's own context.
  - Safe: submit before the folio goes to code that locks it, as
    `swapin_sync()` does before it returns the folio to `do_swap_page()`.
- **Unsafe usage**: queuing reads and writes in one context; `swap_add_folio()`
  picks the submit direction from the folio being added.
  - Safe: a context used for one direction only, as `shrink_folio_list()`
    does for writes.
- `may_enter_fs()` in `mm/vmscan.c`: a swap-cache folio needs only `__GFP_IO`
  unless `si->ops->flags` has `SWAP_OPS_F_REQUIRE_NOFS`; there is no
  SWP_FS_OPS or folio_swap_flags().
