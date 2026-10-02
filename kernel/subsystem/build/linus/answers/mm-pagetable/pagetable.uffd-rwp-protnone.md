- Two mechanisms: NUMA hinting (`MM_CP_PROT_NUMA`) and userfaultfd RWP
  (`VM_UFFD_RWP`, `MM_CP_UFFD_RWP`, `mrwprotect_range()` in
  `mm/userfaultfd.c`). `change_protection()` uses `PAGE_NONE` for both.
- `CONFIG_USERFAULTFD_RWP` off: `VM_UFFD_RWP` is `VM_NONE`. Without
  `CONFIG_ARCH_HAS_PTE_PROTNONE`, `userfaultfd_rwp()` returns false.
- RWP entry: `pte_protnone()` plus `pte_uffd()` in a VMA with `VM_UFFD_RWP`;
  test with `userfaultfd_pte_rwp()` or `userfaultfd_huge_pmd_rwp()`.
- Any other protnone entry in an accessible VMA is a NUMA hint, including
  protnone plus uffd bit in a `VM_UFFD_WP` VMA: the scan keeps the bit.
- `handle_pte_fault()`: `do_uffd_rwp()` for RWP, else `do_numa_page()`. The PMD
  twin is `do_huge_pmd_uffd_rwp()`.
- `userfaultfd_pte_wp()` tests `userfaultfd_wp()`, so it is false in RWP VMAs.
- Non-present entries carry only the bit (`pte_swp_uffd()`); the protection is
  derived again when the entry becomes present.
- NUMA state is not kept across a rebuild: `__split_huge_pmd_locked()` and
  `remove_migration_pte()` build from `vma->vm_page_prot`.
- `change_present_ptes()`: reapplies `PAGE_NONE` after `pte_modify()` when the
  entry has the bit in an RWP VMA, so mprotect cannot disarm it.
- **Potentially unsafe usage**: building a present entry from
  `vma->vm_page_prot` and carrying the uffd bit over with `pte_mkuffd()`.
  - Unsafe: in a VMA where `userfaultfd_rwp()` is true, when the old entry
    can be RWP-armed (non-present with the bit, or protnone with the bit),
    without `pte_modify(pte, PAGE_NONE)`; the next access does not trap.
  - Safe: `pte_mkuffd()` then `pte_modify(pte, PAGE_NONE)`, as `do_swap_page()`
    and `__split_huge_pmd_locked()` do. Search `mm/` for `PAGE_NONE` for the
    rest.
  - Safe: `wp_page_copy()`, where the old entry is present and, in an
    accessible VMA, never protnone: `handle_pte_fault()` sends every protnone
    entry of an accessible VMA elsewhere before `do_wp_page()`, and
    `do_swap_page()` skips `do_wp_page()` for a restored RWP entry.
- **Unsafe usage**: clearing the uffd bit of an RWP entry and leaving
  `PAGE_NONE`; the entry then faults as a NUMA hint.
  - Safe: `pte_modify()` to the `vm_page_prot` of the VMA, then
    `pte_clear_uffd()`, as `__copy_present_ptes()` and `move_ptes()` in
    `mm/mremap.c` do.
- **Unsafe usage**: a NUMA rebuild that rewrites every protnone entry it finds.
  - Safe: skip entries with `userfaultfd_rwp(vma) && pte_uffd()`, as
    `numa_rebuild_large_mapping()` does.
