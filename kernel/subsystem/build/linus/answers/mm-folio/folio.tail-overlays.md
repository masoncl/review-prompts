| Fields | Tail page | Exists from order |
|---|---|---|
| `_flags_1`, `_head_1`, `_large_mapcount`, `_nr_pages_mapped`, `_mm_id_mapcount`, `_mm_ids`, `_mapcount_1`, `_refcount_1` | 1 | 1 |
| `_nr_pages` (only under `NR_PAGES_IN_LARGE_FOLIO`) | 1 | 1 |
| `_entire_mapcount`, `_pincount` | 1 with `CONFIG_64BIT`, else 2 | 1 with `CONFIG_64BIT`, else 2 |
| `_deferred_list` | 2 | 2 |
| `_hugetlb_subpool`, `_hugetlb_cgroup`, `_hugetlb_cgroup_rsvd`, `_hugetlb_hwpoison` | 3 | 2, hugetlb only |

- Folio order: the low 8 bits of `_flags_1`, read by `folio_large_order()`.
  There is no _folio_order field.
- `_nr_pages`: there is no _folio_nr_pages. Without `NR_PAGES_IN_LARGE_FOLIO`
  `folio_large_nr_pages()` computes the count from the order.
- `_nr_pages_mapped`, `_mm_id`, `_mm_ids`, `_mm_id_mapcount`: declared
  unconditionally; `CONFIG_PAGE_MAPCOUNT` and `CONFIG_MM_ID` gate their use,
  not their declaration.
- Hugetlb minimum order: `hugetlb_add_hstate()` has
  `BUG_ON(order < order_base_2(__NR_USED_SUBPAGE))`, and `__NR_USED_SUBPAGE`
  is 3, so order 2.
- `folio_entire_mapcount()`, `folio_large_mapcount()`: do not test
  `folio_test_large()`; they assert it with `VM_BUG_ON_FOLIO()` and
  `VM_WARN_ON_FOLIO()`, both debug-only. `folio_mapcount()` tests it.
- `deferred_split_folio()`: returns for `folio_order(folio) <= 1`; it makes no
  `folio_test_large_rmappable()` test.
  `folio_unqueue_deferred_split()` in `mm/internal.h` tests the order and
  `folio_test_large_rmappable()`. There is no folio_undo_large_rmappable().
- At free: the mapcount fields, `_pincount` and `_deferred_list` must hold the
  values `prep_compound_head()` gave them. `free_tail_page_prepare()` in
  `mm/page_alloc.c` checks this only when `is_check_pages_enabled()`.
- **Potentially unsafe usage**: touching `_deferred_list` after testing only
  `folio_test_large()`.
  - Unsafe: when the folio can be order 1, as page-cache folios can; the
    access lands in the `struct page` after the folio.
  - Safe: when the folio is known to be anonymous, as in the
    `folio_test_anon()` branch of `shrink_folio_list()` in `mm/vmscan.c`;
    `THP_ORDERS_ALL_ANON` excludes order 1 and `folio_check_splittable()`
    returns `-EINVAL` for an anonymous split to order 1.
  - Safe: after `folio_order(folio) > 1`, as `migrate_folio_move()` in
    `mm/migrate.c` does.
