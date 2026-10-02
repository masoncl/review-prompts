- The skip is in `change_pte_range()`, before `change_present_ptes()` is
  called; `change_present_ptes()` has no such test.
- Skipped entries are not added to the returned count.
- RWP-armed entries are protnone too, so the scan leaves them alone.
- `MM_CP_UFFD_RWP` skips only protnone entries that already have the uffd bit;
  a NUMA-hint entry is rewritten to add the bit.
- There is no prot_numa_skip() here; the folio filter is
  `folio_can_map_prot_numa()` in `mm/mempolicy.c`, applied only under
  `MM_CP_PROT_NUMA`.
- Top-tier folios: skipped when `NUMA_BALANCING_NORMAL` is clear in
  `sysctl_numa_balancing_mode`.
