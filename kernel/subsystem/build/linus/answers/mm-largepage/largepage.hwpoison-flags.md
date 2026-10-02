- `PG_has_hwpoisoned`: stored only in the flags of the second page of the
  folio (`FOLIO_SECOND_PAGE` in `include/linux/page-flags.h`), never the head.
- `PG_has_hwpoisoned` is an alias of `PG_active`, so the bit left on a page
  that becomes an order-0 folio would read as `PG_active`.
- Hugetlb per-page record: `struct raw_hwp_page` list in
  `mm/memory-failure.c`; with `HPG_raw_hwp_unreliable` set the list is gone.
- Hugetlb free: `__update_and_free_hugetlb_folio()` calls
  `folio_clear_hugetlb_hwpoison()`, which moves `PG_hwpoison` from the head to
  the listed pages.
- Split: there is no __split_huge_page() here; `__split_folio_to_order()` in
  `mm/huge_memory.c` handles the flag, with `page_range_has_hwpoisoned()`.
- Split sequence in `__split_folio_to_order()`:
  - clears the flag on the original folio, always;
  - if it was set and `new_order` is above 0, sets it again on each resulting
    folio whose range holds a `PG_hwpoison` page;
  - sets it on a new folio only after `prep_compound_page()`.
- One page that may be in a hugetlb folio: `PageHWPoison()` on a tail is false.

| Helper | Result for a hugetlb tail | Context |
|---|---|---|
| `is_page_hwpoison()` | true if the head has `PG_hwpoison` | any |
| `is_raw_hwpoison_page_in_hugepage()` | true for the listed page; for all if unreliable | takes `mf_mutex`, may sleep |

- **Potentially unsafe usage**: `folio_test_hwpoison()` alone to decide
  whether a folio holds poison.
  - Unsafe: on a large folio that is not hugetlb; it reads the head page only
    and misses a poisoned tail page.
  - Safe: on a hugetlb folio, where `hugetlb_update_hwpoison()` sets the flag
    on the head, as `hugetlbfs_read_iter()` does.
  - Safe: `folio_contain_hwpoisoned_page()` on any folio, as
    `shrink_folio_list()` and `do_migrate_range()` do.
- **Unsafe usage**: `folio_test_has_hwpoisoned()` on a folio that may be
  order 0; `const_folio_flags()` reads the next `struct page`.
  - Safe: after `folio_test_large()`, as `shmem_file_read_iter()` does.
  - Safe: after `is_pmd_order()`, as `do_set_pmd()` does.
