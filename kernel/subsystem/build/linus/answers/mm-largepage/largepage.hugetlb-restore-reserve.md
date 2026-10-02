- Flag set at allocation: in `hugetlb_alloc_folio()`, under
  `HUGETLB_ALLOC_USE_GLOBAL_RESERVATIONS`; `alloc_hugetlb_folio()` passes that
  flag when `gbl_chg == 0`.
- Flag set at unmap: `__unmap_hugepage_range()` sets it when the folio is anon
  and no longer mapped, `__vma_private_lock()` is true and
  `h->surplus_huge_pages` is 0.
- Same unmap path: it then calls `vma_needs_reservation()` and clears the flag
  again if that fails.
- Flag cleared on instantiation: inside `hugetlb_add_new_anon_rmap()` in
  `mm/rmap.c`, and in `hugetlb_add_to_page_cache()` on success only.
- `free_huge_folio()` with the flag set: does `resv_huge_pages++` and skips
  `hugepage_subpool_put_pages()`.
- `restore_reserve_on_error()` with the flag set: `vma_add_reservation()` if
  the map shows no reservation, `vma_end_reservation()` if it shows one; it
  clears the flag if `vma_needs_reservation()` fails.
- `restore_reserve_on_error()` with the flag clear: `vma_del_reservation()` if
  the map shows a reservation, `vma_end_reservation()` if not.
- Flag clear and a map call fails: it sets the flag when
  `vma_del_reservation()` fails, and for a private mapping when
  `vma_needs_reservation()` fails.
- Failure inside `hugetlb_alloc_folio()` after the flag is set (memcg charge):
  it calls `free_huge_folio()` itself, and `alloc_hugetlb_folio()` ends the
  pending add; `restore_reserve_on_error()` is not needed there.
- **Potentially unsafe usage**: calling `restore_reserve_on_error()` without
  the hugetlb fault mutex for that index.
  - Unsafe: when the VMA has a reserve map; another `alloc_hugetlb_folio()`
    at the same index can change the entry between the allocation and the
    restore.
  - Safe: under the mutex, which `hugetlb_fault()` takes before it
    allocates, as `hugetlb_no_page()`, `hugetlb_wp()`,
    `hugetlb_mfill_atomic_pte()` and `hugetlbfs_fallocate()` do.
  - Safe: on the child VMA of a private mapping in
    `copy_hugetlb_page_range()`; `hugetlb_dup_vma_private()` left it no
    reserve map, so every reserve-map call returns 1 and changes nothing.
