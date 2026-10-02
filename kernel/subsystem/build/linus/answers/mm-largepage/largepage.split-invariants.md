- Anon folio, in order:
  1. folio lock (caller)
  2. `folio_get_anon_vma()`, `anon_vma_lock_write()`
  3. precheck, `unmap_folio()`
  4. `local_irq_disable()`
  5. order above 1 only: `rcu_read_lock()`, `list_lru_lock()` on
     `deferred_split_lru`
  6. `folio_ref_freeze()`, dequeue, `list_lru_unlock()`
  7. swap cache only: `swap_cluster_get_and_lock()`
  8. `folio_lruvec_lock()`
- File folio, in order:
  1. folio lock (caller)
  2. `filemap_release_folio()`; `xas_split_alloc()` for a uniform split
  3. `i_mmap_lock_read()`
  4. precheck, `unmap_folio()`
  5. `local_irq_disable()`, `xas_lock()`
  6. `folio_ref_freeze()`, with no deferred-split lock
  7. `folio_lruvec_lock()`
- New pieces: unfrozen one by one to `folio_cache_ref_count() + 1`, under
  whichever of `xas_lock()`, the swap cluster lock and the lruvec lock are
  held.
- Original folio: unfrozen last, under the same locks.
- Release order: `lruvec_unlock()`, `swap_cluster_unlock()`, `xas_unlock()`,
  `local_irq_enable()`, `remap_page()`, `i_mmap_unlock_read()`, unlock and
  put the other pieces, `anon_vma_unlock_write()`.
- `i_mmap_rwsem`: dropped before any piece is unlocked; nothing after that
  touches the mapping or the inode.
- Kept piece: the one containing `lock_at`; see "Split entry points" for
  which page each entry point passes.
- Caller's reference: each piece is unfrozen with one reference above the
  cache count; the unlock loop puts it for every piece but `lock_at`'s.
