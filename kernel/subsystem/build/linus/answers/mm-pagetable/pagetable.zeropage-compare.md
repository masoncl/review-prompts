- `try_to_map_unused_to_zeropage()` in `mm/migrate.c`: compares with
  `pages_identical(page, ZERO_PAGE(0))`; it does not call `memchr_inv()`.
- Its refusals: `PageCompound()`, `PageHWPoison()`, `folio_test_mlocked()`,
  `VM_LOCKED`, `mm_forbids_zeropage()`. It has no userfaultfd test and no MTE
  test of its own.
- It keeps the uffd bit (`pte_mkuffd()`) and reapplies `PAGE_NONE` for RWP.
- Stability there: the entry is not present and the page is locked;
  `VM_BUG_ON_PAGE()` asserts both.
- It runs after every successful split of an anon folio that is not
  device-private (`TTU_USE_SHARED_ZEROPAGE`), not only for underused folios.
- arm64 `memcmp_pages()` in `arch/arm64/kernel/mte.c`: equal data with either
  page `page_mte_tagged()` compares as different, unless both are the same
  page.
- Another caller: `orig_page_is_identical()` in `kernel/events/uprobes.c`;
  `__uprobe_write()` compares after `ptep_clear_flush()` and a refcount test.
- **Unsafe usage**: deciding to replace a page in a user mapping with a byte
  compare that is not `memcmp_pages()`; on arm64 the tags are lost.
  - Safe: `pages_identical()`, as `try_to_merge_one_page()` does; a checksum
    such as `calc_checksum()` only as a filter before it.
