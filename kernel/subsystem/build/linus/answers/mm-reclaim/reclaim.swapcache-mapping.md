- Shmem folio in the swap cache: `folio->mapping` is NULL, set by
  `shmem_delete_from_page_cache()`, outside the window described under
  "Swapbacked, swapcache and mapping".
- Folio created by `swap_cache_alloc_folio()`: `folio->mapping` is NULL and
  `folio_test_anon()` is false until `do_swap_page()` maps it, so
  `folio->mapping` cannot tell an anon swap-cache folio from a shmem one.
- `folio->swap`: shares storage with `folio->private`, not with
  `folio->index`.
- `swap_space`: its initialiser sets only `a_ops`, so `host` is NULL;
  `swap_aops` has `dirty_folio` and, under `CONFIG_MIGRATION`,
  `migrate_folio`.
- Writeback: not reachable through the result; `pageout()` in `mm/vmscan.c`
  calls `swap_writeout()` directly.
- **Potentially unsafe usage**: using `host` or `i_pages` of the mapping that
  `folio_mapping()` returned, for a folio that can be in the swap cache.
  - Unsafe: dereferencing `host` or taking the `i_pages` lock; `host` of
    `swap_space` is NULL.
  - Safe: test `folio_test_swapcache()` first and take the cluster lock with
    `swap_cluster_get_and_lock_irq()` instead, as `__remove_mapping()` in
    `mm/vmscan.c` does.
  - Safe: pass `host` only to `mapping_can_writeback()` before any
    dereference, as `folio_clear_dirty_for_io()` does; `inode_to_bdi()`
    returns `noop_backing_dev_info` for a NULL inode.
