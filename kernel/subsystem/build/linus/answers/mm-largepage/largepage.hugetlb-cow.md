- Reuse test in a VMA without `VM_MAYSHARE`:
  `folio_mapcount(old_folio) == 1 && folio_test_anon(old_folio)`
  and nothing else.
- `PageAnonExclusive()`: not part of the test; it is set after the decision.
- Reuse: the PTE becomes writable through `set_huge_ptep_maybe_writable()`,
  only with `VM_WRITE` and not on `FAULT_FLAG_UNSHARE`.
- There is no page_move_anon_rmap() here; `folio_move_anon_rmap()` does that.
- There is no outside_reserve here; the flag is `cow_from_owner`, true when
  the VMA has `HPAGE_RESV_OWNER` and `folio_test_anon(old_folio)`.
- `unmap_ref_private()`: skips `VM_MAYSHARE` VMAs and VMAs with
  `HPAGE_RESV_OWNER`.
- Recheck after `unmap_ref_private()`: no new folio exists on this path; on a
  mismatch `hugetlb_wp()` returns 0 with the page table lock held.
