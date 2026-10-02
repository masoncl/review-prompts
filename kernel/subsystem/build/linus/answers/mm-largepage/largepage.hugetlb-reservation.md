- Shared `struct resv_map`: lives in `struct hugetlbfs_inode_info`, reached
  with `inode_resv_map()`; nothing in hugetlb uses the mapping's private
  pointer for it.
- Child VMA of a private mapping after fork: `hugetlb_dup_vma_private()`
  clears `vm_private_data`, so it has no reserve map and no flags.
- `HPAGE_RESV_UNMAPPED`: set by `__unmap_hugepage_range()` when it is passed a
  specific folio, as `unmap_ref_private()` does; `hugetlb_no_page()` then
  fails the fault.
- VMA with no reserve map: `__vma_reservation_common()` returns 1 for every
  mode and touches nothing.
- Private mapping: a map entry means the reservation was consumed, and
  `__vma_reservation_common()` inverts the region result (>0 becomes 0, 0
  becomes 1).
- `vma_del_reservation()`: the exception; it returns the raw region result for
  private mappings too.
- Pending add from `vma_needs_reservation()`: completed by any one of
  `vma_commit_reservation()`, `vma_end_reservation()`,
  `vma_add_reservation()` or `vma_del_reservation()`.
- `resv_map_release()`: has `VM_BUG_ON()` on a non-zero `adds_in_progress`.
- `map_chg_state`: a typedef with no enum tag; values `MAP_CHG_REUSE`,
  `MAP_CHG_NEEDED`, `MAP_CHG_ENFORCED`.
- `MAP_CHG_ENFORCED`: set when `cow_from_owner` is true; the reserve map is
  not consulted, and neither commit nor end runs.
- `map_chg != MAP_CHG_REUSE` in `alloc_hugetlb_folio()`: sets
  `HUGETLB_ALLOC_CHARG_CGROUP_RSVD`.
- `hugetlb_reserve_pages()`: returns `chg` (>= 0) on success and a negative
  errno on failure; callers test `< 0`.
