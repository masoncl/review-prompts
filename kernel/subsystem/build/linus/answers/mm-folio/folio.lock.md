- Top comment of `mm/filemap.c`: names the folio lock once, as `->lock_page`,
  in the chain `->mmap_lock` → `->invalidate_lock` → `->lock_page`; it gives
  no position relative to `i_mmap_rwsem` or the `i_pages` lock.
- Header comment of `mm/rmap.c`: holds the full chain, with `folio_lock`
  above `mapping->i_mmap_rwsem` and the `i_pages` lock near the bottom.
- `invalidate_lock` between `mmap_lock` and the folio lock: `filemap_fault()`
  takes it only when the lookup finds no folio or one not uptodate, and on a
  retry; an uptodate cached folio is locked without it.
- Order checking: none at run time; `folio_lock()`, `folio_trylock()`,
  `__folio_lock()` and `folio_unlock()` make no lockdep call.
- Folio data: buffered writes are serialized by the lock, since
  `generic_perform_write()` copies between `write_begin` and `write_end`;
  stores through a user mapping and DMA are not.
- `generic_perform_write()`: does not fault the source in before
  `write_begin`; it copies with `copy_folio_from_iter_atomic()` (page faults
  disabled) and calls `fault_in_iov_iter_readable()` only after `write_end`
  returned 0.
