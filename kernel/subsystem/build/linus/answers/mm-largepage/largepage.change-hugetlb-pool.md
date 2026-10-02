- `add_hugetlb_folio()`: does not change the refcount; the folio must already
  be at 0, which `enqueue_hugetlb_folio()` asserts.
- `account_new_hugetlb_folio()`: increments only `nr_huge_pages` and
  `nr_huge_pages_node[nid]`; the caller enqueues the folio or raises the
  surplus counters in the same hold of `hugetlb_lock`, except for a folio it
  marks `HPG_temporary`, as `alloc_migrate_hugetlb_folio()` does.
- `max_huge_pages`: the helpers do not touch it; callers adjust it, for
  example `dissolve_free_hugetlb_folio()` only when `adjust_surplus` is false.
- **Unsafe usage**: `remove_hugetlb_folio()` then an `add_hugetlb_folio()`
  rollback on an hstate for which `hstate_is_gigantic_no_runtime()` is true;
  the removal is a no-op, so the add-back reinitialises `folio->lru` while
  the folio is still on the free list.
  - Safe: test `hstate_is_gigantic_no_runtime()` in `mm/hugetlb_internal.h`
    first, as `dissolve_free_hugetlb_folio()` does.
  - Safe: `demote_pool_huge_page()` has no test of its own;
    `hugetlb_init_hstates()` leaves `demote_order` 0 for such an hstate, and
    `demote_pool_huge_page()` returns `-EINVAL` when `demote_order` is 0.
