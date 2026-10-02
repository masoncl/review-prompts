- `filemap_free_folio()`: static in `mm/filemap.c`, takes `(mapping, folio)`;
  code outside that file cannot call it.

| Function | Who drops the cache's `folio_nr_pages()` references |
|---|---|
| `filemap_remove_folio()` | itself, via `filemap_free_folio()` |
| `delete_from_page_cache_batch()` | itself, `filemap_free_folio()` per folio |
| `__filemap_remove_folio()` | its caller |
| `folio_unmap_invalidate()` | itself, open-coded `free_folio` then `folio_put_refs()` |
| `__remove_mapping()` | nobody puts; refcount was frozen at `1 + folio_nr_pages()` and is 0 on return |
| `remove_mapping()` | `folio_ref_unfreeze(folio, 1)`, leaving the caller's reference |

- `__remove_mapping()`: calls `a_ops->free_folio` itself; its reclaim caller
  in `mm/vmscan.c` frees the folio.
- `filemap_remove_folio()` and `delete_from_page_cache_batch()`: take
  `mapping->host->i_lock`, then `xa_lock_irq()`.
- `i_lock`: needed for `inode_lru_list_add()`, which asserts it and runs
  when `mapping_shrinkable()`; there is no inode_add_lru() here.
- `__filemap_remove_folio()`: the folio lock is the only lock tested by a
  `VM_BUG_ON_FOLIO()` (in `page_cache_delete()`); the caller must also hold
  the `i_pages` lock for `xas_store()`.
- Shadow: only `__remove_mapping()` passes one to
  `__filemap_remove_folio()`, and only when `reclaimed`,
  `folio_is_file_lru()`, not `mapping_exiting()` and not `dax_mapping()`;
  every other caller passes NULL, and `delete_from_page_cache_batch()`
  stores NULL.
- `delete_from_page_cache_batch()`: does no unmap, invalidate or dirty
  cancel; `truncate_inode_pages_range()` runs `truncate_cleanup_folio()` on
  each folio first.
- Still-mapped folio in `filemap_unaccount_folio()`: `VM_BUG_ON_FOLIO()`
  under `CONFIG_DEBUG_VM`; otherwise alert and taint, and the mapcount is
  reset only for a small folio in a `mapping_exiting()` mapping.
