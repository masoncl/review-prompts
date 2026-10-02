- Return value: 0 on success. MIGRATEPAGE_SUCCESS is not defined.
- File-backed hugetlb folio that was mapped: the callback runs with
  `i_mmap_rwsem` held for write by `unmap_and_move_hugetlb_folio()`.
- Hugetlb path: does not test or wait for writeback before the callback.
- `dst->migrate_info`: zero at the call from `migrate_folio_move()`. It
  overlays `dst->private`.
- `dst` references: after success `migrate_folio_move()` calls
  `folio_put(dst)`. The callback must have given `dst` the references its
  new owner holds, as `__folio_migrate_mapping()` does with
  `folio_ref_add()`.
- `dst` and the LRU: `migrate_folio_move()` calls `folio_add_lru(dst)` after
  success; the callback does not.
- `-EAGAIN`, outside hugetlb: the callback is called again on the next pass
  with both folios still locked and `src` still unmapped.
