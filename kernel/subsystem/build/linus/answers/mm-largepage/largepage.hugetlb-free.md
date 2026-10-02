- Surplus test in `free_huge_folio()`: only that
  `h->surplus_huge_pages_node[nid]` is non-zero for the folio's node; it does
  not test whether this folio was allocated as surplus.
- Reservation: restored by `h->resv_huge_pages++` in `free_huge_folio()`
  under `hugetlb_lock`, not by a call to `hugetlb_acct_memory()`.
- Subpool pointer: in `folio->_hugetlb_subpool`; only the `HPG_*` flags are
  in `folio->private`.
- `HPG_raw_hwp_unreliable`: `__update_and_free_hugetlb_folio()` returns
  without freeing such a folio, after the counters have dropped it, so it
  reaches neither the pool nor the allocator.
- Waiting for the deferred free: `wait_for_freed_hugetlb_folios()`, as
  `test_pages_isolated()` does, or `flush_free_hpage_work()` inside
  `mm/hugetlb.c`.
