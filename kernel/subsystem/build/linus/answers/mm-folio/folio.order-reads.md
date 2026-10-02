- `_nr_pages` in `struct folio`: present only when `NR_PAGES_IN_LARGE_FOLIO`
  is defined, which `include/linux/mm_types.h` does for `CONFIG_MEMCG` or
  `CONFIG_SLAB_OBJ_EXT`; it does not depend on `CONFIG_64BIT`. Without it
  `folio_large_nr_pages()` computes `1L << folio_large_order()`.
- `folio_nr_pages()` with no reference, under `NR_PAGES_IN_LARGE_FOLIO`: can
  return 0 or a value that is not `1 << order`, because `_nr_pages` is stored
  apart from the order bits. `__free_pages_prepare()` zeroes both before it
  clears `PG_head`, and `prep_compound_page()` sets `PG_head` before
  `folio_set_order()` runs.
- `folio_order()` and `folio_nr_pages()` on a pointer that has become a tail:
  `const_folio_flags()` hits `VM_BUG_ON_PGFLAGS()`, compiled in only under
  `CONFIG_DEBUG_VM_PGFLAGS`.
- `compound_order()` and `compound_nr()`: raw `test_bit()` of `PG_head`, no
  assertion.
- There is no MAX_ORDER here; the buddy limit is `MAX_PAGE_ORDER`.
- Two bounds, with different effect:

| Bound | Defined in | Covers gigantic folios | Used by |
|---|---|---|---|
| `MAX_PAGE_ORDER` | `include/linux/mmzone.h` | no; walker advances one page | `isolate_migratepages_block()` |
| `MAX_FOLIO_ORDER`, `MAX_FOLIO_NR_PAGES` | `include/linux/mmzone.h` | yes | `page_is_unmovable()`, `scan_movable_pages()` |

- Walker that carries a `struct page *` along with the PFN: bound the step to
  the range end before stepping, as `isolate_freepages_block()` does.
- Walker that calls `pfn_to_page()` again each iteration behind a
  `pfn < end` test: may overshoot and clamp after the loop, as
  `isolate_migratepages_block()` does.
- With a reference held: read `folio_nr_pages()` before an operation that
  changes it; `split_huge_pages_all()` reads it before `split_folio()`.
- **Unsafe usage**: stepping by `folio_nr_pages()` or `1UL << order` read
  from an unreferenced folio with no check on the value.
  - Safe: `compound_order()` on the scanned page, bounded by
    `MAX_PAGE_ORDER`, as `isolate_migratepages_block()` does for THP.
  - Safe: `compound_order()` on the `page_folio()` head, bounded by
    `MAX_FOLIO_ORDER`, with the step aligned to the folio end, as
    `page_is_unmovable()` in `mm/page_isolation.c` does.
  - Safe: `folio_nr_pages()` rejected when below 1, above
    `MAX_FOLIO_NR_PAGES` or not a power of two, as `scan_movable_pages()`
    in `mm/memory_hotplug.c` does.
  - Safe: after `folio_try_get()` and the `page_folio()` recheck, as
    `do_migrate_range()` does.
