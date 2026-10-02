- `struct page` has no field named compound_head; `_compound_head()` reads
  `page->compound_info` (`include/linux/mm_types.h`); `compound_head()` is
  the macro that casts its result.
- Tail encoding depends on `compound_info_has_mask()` in
  `include/linux/page-flags.h`: true only with
  `CONFIG_HUGETLB_PAGE_OPTIMIZE_VMEMMAP` and a power-of-2
  `sizeof(struct page)`.
  - False: a tail's `compound_info` is the head pointer with bit 0 set.
  - True: a tail's `compound_info` is a mask with bit 0 set; the head is the
    tail's own address ANDed with that mask.
- Fake heads: there is no page_fixed_fake_head() and no fake-head test in this
  tree; `_compound_head()` makes no vmemmap-optimisation check beyond the
  mask.
- Page pointer in mask mode: must be the address of the entry in the memmap,
  because the head is computed from that address; a copied tail
  `struct page` gives a wrong head.
- `snapshot_page()` in `mm/util.c`: decodes a copied `struct page` using the
  address of the original.
- **Unsafe usage**: decoding a tail's `compound_info` by hand as "head
  pointer plus 1".
  - Safe: call `compound_head()` or `page_folio()`.
  - Safe: branch on `compound_info_has_mask()` first, as `snapshot_page()`
    does.
- `page_folio()` argument: evaluated once; `_Generic` evaluates only the
  selected association.
- State tested before the reference must be tested again after it:
  `page_idle_get_folio()` in `mm/page_idle.c` tests `folio_test_lru()` on
  both sides of `folio_try_get()`.
- **Potentially unsafe usage**: reading fields of `page_folio(page)` with no
  reference.
  - Unsafe: when the caller acts on the value as if it were stable; the
    folio can be split or freed, and the value is then stale or garbage.
  - Safe: when the value is only a hint and is validated, as
    `scan_movable_pages()` in `mm/memory_hotplug.c` does; it range-checks
    `folio_nr_pages()` against `MAX_FOLIO_NR_PAGES` before skipping ahead.
