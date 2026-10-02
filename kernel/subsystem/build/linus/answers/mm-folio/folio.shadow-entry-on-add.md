- Scan: `xas_for_each_conflict()`; the order of a value entry comes from
  `xas_get_order()`, sampled for the first entry only.
- Split: `xas_try_split()` under the xa_lock, repeated with orders from
  `xas_try_split_min_order()` until the entry is at the folio's order.
- `__filemap_add_folio()` does not call `xas_split_alloc()` or `xas_split()`;
  nothing is preallocated before the lock on the first pass.
- Split node allocation: `xas_try_split()` tries `GFP_NOWAIT` under the lock;
  on `-ENOMEM` the lock is dropped, `xas_nomem()` allocates with the masked
  `gfp`, and the whole scan restarts at the folio's index and order.
- No "order changed" recheck exists; the restart rescans from scratch.
- Larger value entry in a shmem mapping: unconditional
  `BUG_ON(shmem_mapping(mapping))`, not a `VM_BUG_ON()`.
- Shadows smaller than the folio: overwritten by the multi-index
  `xas_store()` with no split.
- `*shadowp` when the folio covers several shadows: the last one walked;
  the others are dropped unreported.
- `shadowp` may be NULL; `hugetlb_add_to_page_cache()` passes NULL.
- `mapping_set_update()` in `mm/internal.h`: installs
  `workingset_update_node()` only when the mapping is neither DAX nor shmem.
