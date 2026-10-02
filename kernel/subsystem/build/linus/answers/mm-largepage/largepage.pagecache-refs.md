- `filemap_free_folio()`: one unconditional
  `folio_put_refs(folio, folio_nr_pages(folio))`; no separate `folio_put()`
  path for a small folio, and no count argument.
- hugetlb folios: get `folio_nr_pages()` references too.
  `hugetlb_add_to_page_cache()` calls `__filemap_add_folio()`; `huge` there
  only skips the statistics.
- shmem folios: `__filemap_add_folio()` asserts `!folio_test_swapbacked()`.
  `shmem_add_to_page_cache()` takes the references and
  `shmem_delete_from_page_cache()` drops them at swap-out, in
  `shmem_writeout()`.
- There is no delete_from_page_cache() here. `filemap_free_folio()` is static
  in `mm/filemap.c`; its callers are `filemap_remove_folio()` and
  `delete_from_page_cache_batch()`.
- `filemap_remove_folio()`: removes and drops the references in one call.
  Nothing has to follow it.
- `__filemap_remove_folio()` called directly: drops no page cache reference.
  The caller does, for example `folio_unmap_invalidate()` in `mm/truncate.c`.
- `__remove_mapping()` in `mm/vmscan.c`: consumes the references in the freeze
  and returns the folio at refcount 0. `remove_mapping()` restores the caller's
  reference with `folio_ref_unfreeze(folio, 1)`.
- Folio still mapped at removal: `filemap_unaccount_folio()` has
  `VM_BUG_ON_FOLIO(folio_mapped(folio), folio)`. `truncate_cleanup_folio()` and
  `folio_unmap_invalidate()` call `unmap_mapping_folio()` first.
- **Unsafe usage**: one `folio_put()` for the page cache after removing a folio
  that may be large.
  - Safe: `folio_put_refs(folio, folio_nr_pages(folio))` after
    `__filemap_remove_folio()`, as `folio_unmap_invalidate()` does. It matches
    `folio_ref_add(folio, nr)` in `__filemap_add_folio()`.
  - Safe: no put at all after `__remove_mapping()` succeeded, as
    `remove_mapping()` does; the freeze took the references.
