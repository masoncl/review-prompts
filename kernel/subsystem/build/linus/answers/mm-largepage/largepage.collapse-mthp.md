- mTHP collapse is in this tree; see `mthp_collapse()` in `mm/khugepaged.c`.
  There is no collapse_scan_bitmap() and no mthp_bitmap; the bitmap is
  `mthp_present_ptes` in `struct collapse_control`.
- `collapse_possible_orders()`: `THP_ORDERS_ALL_ANON` only for `TVA_KHUGEPAGED`
  on an anonymous VMA; MADV_COLLAPSE and file VMAs get PMD order only.
- `mthp_collapse()`: no stack. It walks an offset from 0 to `HPAGE_PMD_NR`; at
  each offset it tries the enabled orders downward, not below
  `KHUGEPAGED_MIN_MTHP_ORDER`, then advances by the size last tried and
  restarts at `max_order_from_offset()`.
- Attempt condition per order: occupied bits in the range >=
  `(1 << order) - collapse_max_ptes_none()`.
- `collapse_max_ptes_none()` below PMD order: `(1 << order) - 1` when the sysfs
  value equals `KHUGEPAGED_MAX_PTES_LIMIT`; 0 for every other value, with a
  `pr_warn_once()` if it was nonzero. There is no shift scaling.
- `collapse_max_ptes_none()` with a uffd-armed `vma`: 0. `mthp_collapse()`
  passes a NULL `vma`, so that rule applies in
  `__collapse_huge_page_isolate()`, and in `collapse_scan_pmd()` only when PMD
  order is the only enabled order.
- `collapse_scan_pmd()`: applies `collapse_max_ptes_swap()` and
  `collapse_max_ptes_shared()` for `HPAGE_PMD_ORDER` to the whole PMD. If
  either is exceeded the scan fails and no smaller order is tried.
- Swap PTEs: not set in `mthp_present_ptes`; `unmapped` is added to the occupied
  count only for the PMD-order attempt.
- Below PMD order, swap PTE inside the range: `__collapse_huge_page_swapin()`
  fails at the first one with `SCAN_EXCEED_SWAP_PTE` and swaps nothing in.
- Below PMD order, shared folio inside the range:
  `__collapse_huge_page_isolate()` fails with `SCAN_EXCEED_SHARED_PTE`.
- Below PMD order, folio in the range with `folio_order()` >= target order:
  `__collapse_huge_page_isolate()` returns `SCAN_PTE_MAPPED_HUGEPAGE`;
  `mthp_collapse()` skips to the next offset without trying a lower order.
- Result handling in `mthp_collapse()`: the `switch` lists which results try
  the next lower order; any result not listed, for example `SCAN_VMA_CHECK` or
  `SCAN_COPY_MC`, stops work on the whole PMD.
- `mthp_collapse()` return: `SCAN_SUCCEED` if any range collapsed.
- Counters: `count_collapse_event()` bumps the mTHP counter of the order it is
  given, `MTHP_STAT_COLLAPSE_EXCEED_NONE`, `MTHP_STAT_COLLAPSE_EXCEED_SWAP` or
  `MTHP_STAT_COLLAPSE_EXCEED_SHARED`, and the vm event only for PMD order.
  Below PMD order `__collapse_huge_page_swapin()` bumps
  `MTHP_STAT_COLLAPSE_EXCEED_SWAP` with `count_mthp_stat()` directly.
