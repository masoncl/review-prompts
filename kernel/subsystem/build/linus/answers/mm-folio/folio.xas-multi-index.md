- `xas_next()` and `xas_prev()` return the raw slot; siblings are not
  resolved. `xas_load()` and `xas_reload()` resolve a sibling to the
  canonical entry.
- Entry of order below `XA_CHUNK_SHIFT`: `xas_next()` returns the folio at the
  first index and a sibling entry (`xa_is_sibling()`) at every other index.
- Entry of order `XA_CHUNK_SHIFT` or more: `__xas_next()` in `lib/xarray.c`
  returns the content of the slot that covers the new index. The folio
  repeats for every index of the canonical slot; indices in sibling slots
  give a sibling entry.
- `xas_load()` landing inside an entry: `xa_offset` becomes the canonical
  slot, `xa_index` stays as asked. `xas_next()` adds one to each without
  resyncing; `filemap_get_read_batch()` calls `xas_advance()` before the next
  `xas_next()`.
- A sibling entry is not NULL, fails `xa_is_value()` and fails `xas_retry()`.
- **Unsafe usage**: passing the return of `xas_next()` to `folio_try_get()` or
  another folio accessor after testing only NULL, `xas_retry()` and
  `xa_is_value()`.
  - Safe: test `xa_is_sibling()` first and, after taking the folio, call
    `xas_advance(&xas, folio_next_index(folio) - 1)`, as
    `filemap_get_read_batch()` and `filemap_get_folios_contig()` in
    `mm/filemap.c` do.
  - Safe: walk with `xas_for_each()` or `xas_find()`, which skip sibling
    slots and return each entry once; `find_get_entry()` does.
  - Safe: for sibling entries, compare the return with `xas_reload()` and
    `xas_reset()` on mismatch, as `iter_xarray_populate_pages()` in
    `lib/iov_iter.c` does; `xas_reload()` resolves a sibling, so a sibling
    never compares equal and the next `xas_next()` is an `xas_load()`.
- `xas_get_order()`: must not be called while the `xa_state` points at a
  sibling slot, so not right after `xas_next()` returned a sibling entry. It
  probes the slots after `xa_offset` for sibling entries.
- Under RCU only: `filemap_cachestat()` reads the size from
  `xas_get_order()` rather than from an unpinned folio, and uses it only for
  counting. Code that stores or splits on the result holds the xa_lock, as
  `shmem_free_swap()` and `__filemap_add_folio()` do.
- Without `CONFIG_XARRAY_MULTI`: `xa_get_order()` and `xas_get_order()` are
  stubs in `include/linux/xarray.h` that return 0.
