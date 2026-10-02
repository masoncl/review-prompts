- `dax_make_entry()`: takes `unsigned long pfn`; there is no pfn_t type in
  this tree.
- `dax_is_conflict()`: compares with `XA_RETRY_ENTRY`; there is no
  DAX_CONFLICT name here, and `fs/dax.c` never stores the value in `i_pages`.
- Zero entry: the pfn bits hold the pfn of the zero page (`zero_pfn()` in
  `dax_load_hole()`) or of the huge zero folio (`dax_pmd_load_hole()`), not 0.
- Zero and empty entries: test the flags before `dax_to_folio()`;
  `dax_associate_entry()`, `dax_disassociate_entry()` and `dax_busy_page()`
  return early for both, and `dax_entry_size()` returns 0.
- `DAX_EMPTY` entry: can be found unlocked; `dax_unlock_entry()` stores it
  back when a fault ends without `dax_insert_entry()`, for example the
  `pmd_trans_huge()` path of `dax_iomap_pte_fault()`.
- `PAGECACHE_TAG_TOWRITE`: set on a DAX mapping in two places,
  `tag_pages_for_writeback()` and `dax_insert_entry()` for an `IOMAP_WRITE`
  fault on an `IOMAP_F_SHARED` iomap.
