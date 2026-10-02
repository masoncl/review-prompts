- Value entries in `i_pages` are of three kinds: workingset shadow, shmem swap
  entry (`swp_to_radix_entry()`), DAX entry.
- Kind of a value entry: not encoded in the entry; decided by the mapping.
  Test `shmem_mapping()` or `dax_mapping()` before decoding, as
  `mincore_page()` in `mm/mincore.c` and `truncate_folio_batch_exceptionals()`
  in `mm/truncate.c` do.
- Swap cache: not looked up through `i_pages` in this tree.
  `swap_cache_get_folio()` and `swap_cache_get_shadow()` in `mm/swap_state.c`
  read the swap table (`mm/swap_table.h`); the initialiser of `swap_space`
  sets only `a_ops`.
- Sibling entries: `xas_load()`, `xa_load()`, `xas_find()` and
  `xas_find_marked()` never return one; `xas_next()` and `xas_prev()` return
  the raw slot and can (see Multi-index entries).
- hugetlb folios: stored as ordinary multi-index entries at base-page indices.
  `hugetlb_add_to_page_cache()` and `filemap_lock_hugetlb_folio()` take an
  index in huge-page units and shift it by `huge_page_order()`.
