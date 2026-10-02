- Swap-in error: there is no separate swap-error marker;
  `make_poisoned_swp_entry()` builds a `PTE_MARKER_POISONED` marker, so the
  fault returns `VM_FAULT_HWPOISON`.
- `pte_marker_handle_uffd_wp()`: when the VMA is not `userfaultfd_wp()` it
  calls `pte_marker_clear()`, which clears the PTE only if it still equals
  `vmf->orig_pte`, and returns 0; otherwise `do_pte_missing()`.
- uffd-wp markers are write-protect only: `copy_pte_marker()` and
  `pte_marker_handle_uffd_wp()` test `userfaultfd_wp()`, not
  `userfaultfd_protected()`; a VMA with only `VM_UFFD_RWP` gets no uffd-wp
  marker copied and clears one on fault.
- hugetlb fault: `hugetlb_fault()` tests the marker itself and does not call
  `handle_pte_marker()`; poison gives `VM_FAULT_HWPOISON_LARGE`, guard gives
  `WARN_ON_ONCE()` plus `VM_FAULT_SIGSEGV`, anything else goes to
  `hugetlb_no_page()`.
- Zap without `ZAP_FLAG_DROP_MARKER`:

| Marker | Survives |
|---|---|
| uffd-wp, anonymous VMA | no, always dropped |
| uffd-wp, other VMA | yes |
| guard | yes |
| poison | only when `should_zap_cows()` is false |

- `cond_install_uffd_wp_ptes()` in `mm/memory.c`: installs the uffd-wp marker
  after a clear, only in a non-anonymous `userfaultfd_wp()` VMA and only when
  the old entry carried the uffd bit or was a uffd-wp marker; there is no
  pte_install_uffd_wp_if_needed() here.
- `vma_needs_copy()`: true when `dst_vma` has any `VM_COPY_ON_FORK` flag
  (`VM_PFNMAP`, `VM_MIXEDMAP`, `VM_UFFD_WP`, `VM_UFFD_RWP`, `VM_MAYBE_GUARD`)
  or `src_vma->anon_vma` is set; otherwise no entry, marker or not, is copied.
