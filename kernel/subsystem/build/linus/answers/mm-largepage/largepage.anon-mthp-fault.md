- Allocation gfp: `vma_thp_gfp_mask(vma)`, which follows the defrag setting
  and `VM_HUGEPAGE` and can include direct reclaim.
- `pte_offset_map()` returning NULL: `alloc_anon_folio()` returns
  `ERR_PTR(-EAGAIN)` and `do_anonymous_page()` returns 0; no order-0 folio is
  allocated.
- `mem_cgroup_charge()` failure: counts
  `MTHP_STAT_ANON_FAULT_FALLBACK_CHARGE` and `MTHP_STAT_ANON_FAULT_FALLBACK`,
  then tries the next lower order.
- `folio_memcg_alloc_deferred()` runs after a successful charge; on failure the
  folio is put and the code jumps to the order-0 `folio_prealloc()`, without
  trying lower orders and without counting a fallback.
- `MTHP_STAT_ANON_FAULT_ALLOC`: counted in `map_anon_folio_pte_pf()` in
  `mm/memory.c`, after the PTEs are set; a folio dropped at the locked recheck
  is not counted.
- `userfaultfd_armed()` in `include/linux/userfaultfd_k.h`: tests
  `__VMA_UFFD_FLAGS`, which here includes `VMA_UFFD_RWP` beside missing, wp
  and minor.
- uffd-wp bit: set with `pte_mkuffd()`; there is no pte_mkuffd_wp() in this
  tree.
