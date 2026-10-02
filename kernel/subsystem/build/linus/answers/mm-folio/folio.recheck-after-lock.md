- Folio held by the lookup's reference: cannot be reclaimed, migrated or split
  by the paths that call `folio_ref_freeze()`, which fails on the extra
  reference; for example `__remove_mapping()` in `mm/vmscan.c`,
  `__folio_migrate_mapping()` in `mm/migrate.c`,
  `__folio_freeze_and_split_unmapped()` in `mm/huge_memory.c`.
- `filemap_remove_folio()` and `folio_unmap_invalidate()`: remove the folio
  whatever its refcount, so the lookup's reference does not stop truncation
  or invalidation.
- Index after locking: asserted, not rechecked;
  `VM_BUG_ON_FOLIO(!folio_contains())` in `filemap_fault()`,
  `find_lock_entries()` and `truncate_inode_pages_range()` is compiled out
  without `CONFIG_DEBUG_VM`.
- `page_cache_delete()`: clears `folio->mapping` and leaves `folio->index`
  set, so the index alone never shows a truncated folio.
- `find_lock_entries()`: uses `folio_trylock()` only and skips a folio it
  cannot lock; after the lock it tests `folio->mapping` and writeback.
- `filemap_fault()` with a locked folio that is not uptodate and without
  `invalidate_lock`: unlocks, puts and redoes the lookup under
  `invalidate_lock` before it reads the folio.
- `folio_matches_swap_entry()` in `mm/swap.h`: the swap-cache recheck;
  `do_swap_page()` calls it right after `folio_lock_or_retry()`.
- **Potentially unsafe usage**: `folio_lock()` on a folio from an unlocked
  lookup, then use without testing `folio->mapping`.
  - Unsafe: when the code then dereferences `folio->mapping` or treats the
    folio as the file's data at that index; `page_cache_delete()` may have
    set `folio->mapping` to NULL.
  - Safe: when the work under the lock reads the mapping itself and accepts
    NULL, as `folio_mark_dirty()` does through `folio_mapping()`; see
    `folio_mark_dirty_lock()`.
