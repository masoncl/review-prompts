- `hugetlb_reserve_pages()` when `hugetlb_acct_memory()` fails: puts back only
  `chg - gbl_reserve`, and passes that put's return, negated, to
  `hugetlb_acct_memory()`.
- Same path, the remaining `gbl_reserve` pages: `used_hpages` is lowered
  directly under `spool->lock`, then `unlock_or_release_subpool()`; they do
  not go through `hugepage_subpool_put_pages()`.
- `hugetlb_reserve_pages()` reserve-map unwind: `region_abort()` for shared;
  for private, `kref_put()` of the map and `set_vma_resv_map()` to NULL.
  `hugetlb_reserve_pages()` itself does not call `region_del()`.
- `free_huge_folio()`: does not pass the put's return to
  `hugetlb_acct_memory()`; a put return of 0 makes it do `resv_huge_pages++`.
- **Potentially unsafe usage**: passing the negated return of
  `hugepage_subpool_get_pages()` to `hugetlb_acct_memory()`.
  - Unsafe: when the same pages also go back through
    `hugepage_subpool_put_pages()`; with a minimum size the put can return
    less than the get did, and `return_unused_surplus_pages()` subtracts
    whatever it is given from `resv_huge_pages`.
  - Safe: to reverse an earlier successful `hugetlb_acct_memory()` of that
    same value, with only `chg - gbl_reserve` going through the put, as
    `hugetlb_reserve_pages()` does when `region_add()` fails.
  - Safe: put first, then pass its negated return, as
    `hugetlb_unreserve_pages()` and `hugetlb_vm_op_close()` do;
    `hugepage_new_subpool()` charged `min_hpages` globally, so pages that
    refill `rsv_hpages` stay reserved.
