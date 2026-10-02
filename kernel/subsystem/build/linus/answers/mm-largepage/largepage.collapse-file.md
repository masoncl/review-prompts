- Old folios before commit: stay in their page cache slots, locked, isolated
  from the LRU, each with two references beyond the page cache's: the pin and
  the one from `folio_isolate_lru()`. `collapse_file()` does not call
  `folio_ref_freeze()`.
- Refcount test: `folio_ref_count()` must equal `2 + folio_nr_pages()`, checked
  once under `xas_lock_irq()`; a new mapping needs the folio lock after that,
  for example `folio_trylock()` in `next_uptodate_folio()`.
- `try_to_unmap()` result: not checked. A folio that is still mapped fails the
  refcount test with `SCAN_PAGE_COUNT`.
- xa_lock in the first loop: held for `folio_trylock()`, dropped for
  isolating, releasing and unmapping each folio, retaken for the refcount
  test.
- Non-shmem folio: must be clean before `folio_isolate_lru()` and again after
  `try_to_unmap()`, which moves PTE dirty bits to the folio.
- `nr_none`: counts shmem holes only. A hole in a regular file is filled by
  `page_cache_sync_readahead()` or the collapse fails.
- New folio before commit: locked, with `mapping` and `index` set, not in the
  xarray, not uptodate.
- Slots changed before commit: only shmem holes, set to `XA_RETRY_ENTRY`.
- Point of no return: after the hole recheck and the `userfaultfd_missing()`
  walk, with the xa_lock held; one multi-index `xas_store()` replaces all old
  entries.
- `folio_mark_dirty()` on the new folio: shmem only.
- Rolled back: retry entries back to NULL, `mapping->nrpages` and
  `shmem_uncharge()` for `nr_none`, old folios unlocked and put back on the
  LRU, new folio `mapping` cleared and freed. The xarray needs no other repair.
- Not rolled back: PTEs removed by `try_to_unmap()`, private data dropped by
  `filemap_release_folio()`, folios brought in by swap-in or readahead.
- filemap_nr_thps_inc() and filemap_nr_thps_dec(): not in this tree.
- Page tables, first: `try_to_unmap()` per old folio in the first loop, flushed
  by `try_to_unmap_flush()` before the copy.
- Page tables, second: `retract_page_tables()` after the store and before
  `folio_unlock()` of the new folio. It relies on that lock to keep faults from
  refilling the table.
- `file_backed_vma_is_retractable()`: skips a VMA with `anon_vma`, with
  `userfaultfd_protected()`, or with `VMA_MAYBE_GUARD_BIT`;
  `retract_page_tables()` calls it again under the PTE lock.
- MADV_COLLAPSE: `collapse_file()` turns success into
  `SCAN_PTE_MAPPED_HUGEPAGE`; `collapse_single_pmd()` then takes
  `mmap_read_lock()` and calls `try_collapse_pte_mapped_thp()` with
  `install_pmd` true.
- Daemon finding a PMD-order folio already in the cache:
  `collapse_scan_file()` returns `SCAN_PTE_MAPPED_HUGEPAGE` and
  `collapse_single_pmd()` calls `try_collapse_pte_mapped_thp()` with
  `install_pmd` false, which retracts the table in that mm only.
