- Head vmemmap page after optimisation: a newly allocated copy, mapped
  read-write; it holds the first `HUGETLB_VMEMMAP_RESERVE_PAGES` struct pages.
- Every other vmemmap page of the folio: mapped `PAGE_KERNEL_RO` onto one
  shared page per zone and order, `vmemmap_tails[]` in `struct zone`.
- Shared tail page: filled by `init_compound_tail()` with a NULL head, so it
  carries node, zone and the tail marker, and no state of any one folio.
- `compound_head()` on such a tail: still finds the right head, because
  `compound_info` holds a mask when `compound_info_has_mask()` is true.
- Not in this tree: fake head pages, a static key for the optimisation, and
  RCU synchronisation in optimise or in the refcount helpers.
- Fields hugetlb keeps in tail pages, such as `_hugetlb_subpool`: stay
  writable; `hugetlb_vmemmap_init()` checks `__NR_USED_SUBPAGE` against
  `HUGETLB_VMEMMAP_RESERVE_PAGES` at build time.
- `hugetlb_vmemmap_optimize_folio()`: returns void and can leave the folio
  unoptimised; test `folio_test_hugetlb_vmemmap_optimized()` per folio.
- `vmemmap_optimize_enabled`: a runtime sysctl, so one pool can hold
  optimised and unoptimised folios.
- `hugetlb_vmemmap_restore_folio()`: expects the hugetlb type set and
  refcount 0, and returns 0 for a folio that is not optimised.
- Restore allocation: `GFP_KERNEL | __GFP_RETRY_MAYFAIL` on the folio's node,
  in `alloc_vmemmap_page_list()`; `__GFP_THISNODE` is not set.
- **Potentially unsafe usage**: reading a tail struct page of an optimised
  hugetlb folio.
  - Unsafe: for per-page state such as `PG_hwpoison`, refcount or
    `private`; past the first `HUGETLB_VMEMMAP_RESERVE_PAGES` struct pages
    the read returns the shared page's value.
  - Safe: for node, zone or the head lookup, which `init_compound_tail()`
    sets; `hugetlb_bootmem_init_migratetype()` passes such tail pages on.
  - Safe: for a poisoned subpage, ask `is_raw_hwpoison_page_in_hugepage()`,
    which reads the list that `hugetlb_update_hwpoison()` fills, as
    `adjust_range_hwpoison()` in `fs/hugetlbfs/inode.c` does.
