- `truncate_inode_partial_folio()` split failure: a dirty folio stays and
  the function returns false; a clean folio is removed whole by
  `truncate_inode_folio()`.
- After false: `truncate_inode_pages_range()` narrows `start` or `end` so
  pass 2 skips that folio.
- Split helper: `folio_split()` to `mapping_min_folio_order()`, in
  `folio_split_or_unmap()`; on failure a non-shmem folio is unmapped with
  `try_to_unmap()`.
- Zeroing of the in-range part: skipped when `mapping_inaccessible()`.
- There is no invalidate_complete_folio2() here; `folio_unmap_invalidate()`
  in `mm/truncate.c` does that job, and returns 1 on removal.
- `invalidate_inode_pages2_range()` return: 0, `-EBUSY`, or the error from
  `a_ops->launder_folio`; the last failing folio's code wins.
- `invalidate_inode_pages2_range()` leaves a folio when: laundering fails,
  `filemap_release_folio()` fails, or the folio is dirty at the recheck
  under `i_lock` and the xa_lock.
- Mapped folios: being mapped is never a reason for
  `folio_unmap_invalidate()` to leave a folio; it unmaps, then
  `BUG_ON(folio_mapped(folio))`.
- Folio whose `folio->mapping` changed before the lock: skipped by
  `invalidate_inode_pages2_range()` without setting an error.
- Large folio overlapping the range: `invalidate_inode_pages2_range()`
  invalidates it whole; it does not zero or split.
- `mapping_evict_folio()`: makes no `folio_mapped()` or
  `mapping_unevictable()` test; a mapped folio fails the refcount test
  `folio_ref_count() > folio_nr_pages() + folio_has_private() + 1`.
- `mapping_evict_folio()` return: pages removed, from `remove_mapping()`,
  which can still fail on its own refcount freeze and dirty recheck.
- `mapping_try_invalidate()` return: pages evicted plus one per value entry,
  not a folio count.
- Value entries in a shmem mapping: left alone by
  `truncate_inode_pages_range()` and `invalidate_inode_pages2_range()`;
  `truncate_folio_batch_exceptionals()` and `clear_shadow_entries()` return
  early.
- DAX entries: truncate hits `WARN_ON_ONCE()` and
  `dax_delete_mapping_entry()`; invalidate uses
  `dax_invalidate_mapping_entry_sync()` and sets `-EBUSY` on failure.
