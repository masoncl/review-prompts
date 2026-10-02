- Order: `kho_restore_page()` makes no order check of any kind; only
  `info.magic` is tested.
- Caller-side check: `kho_test_restore_data()` in `lib/test_kho.c` compares
  `folio_order()` of the result with the order it recorded itself.
- Reading before restore: preserved data is readable through `phys_to_virt()`
  before any restore call, as `memfd_luo_retrieve()` does with
  `struct memfd_luo_ser`.
- `kho_alloc_preserve()` memory: `kho_restore_folio()` also fits, since
  `kho_restore_free()` calls it and then `folio_put()`.
- **Unsafe usage**: `kho_restore_folio()` on a range from
  `kho_preserve_pages()`; it restores only the first block, as a compound page
  of that block's stored order, with no `MAX_PAGE_ORDER` check.
  - Safe: `kho_restore_pages()` with the preserved count, as
    `kho_restore_vmalloc()` does for blocks from `kho_preserve_vmalloc()`;
    `kho_restore_page()` picks `kho_init_pages()` from `is_folio`.
- **Unsafe usage**: `kho_restore_pages()` on a folio from
  `kho_preserve_folio()`; `kho_init_pages()` gives every page refcount 1 and
  sets up no compound page.
  - Safe: `kho_restore_folio()`, as `memfd_luo_retrieve_folios()` does;
    `kho_init_folio()` sets tail counts to 0 and calls `prep_compound_page()`.
