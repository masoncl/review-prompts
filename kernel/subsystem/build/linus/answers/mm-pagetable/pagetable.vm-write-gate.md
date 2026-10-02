- `FAULT_FLAG_WRITE` does not imply `VM_WRITE`: `FOLL_FORCE` write faults reach
  `wp_page_reuse()` and `wp_page_copy()` in a VMA without it. `maybe_mkwrite()`
  then leaves the entry dirty and read-only.
- The page table lock does not hold `vm_flags` stable. `mprotect_fixup()`
  rewrites them under the mmap write lock and `vma_start_write()`, then calls
  `change_protection()`.
- Rmap walks take neither lock for the VMAs they visit; their callbacks in
  `mm/rmap.c`, `mm/migrate.c` and `mm/ksm.c` do not test `VM_WRITE`.
- `remove_migration_pte()`: calls `pte_mkwrite()` when
  `softleaf_is_migration_write()`; it does not call `maybe_mkwrite()`. There is
  no is_writable_migration_entry() here.
- `__split_huge_pmd_locked()`: takes `write` from `pmd_write()`,
  `softleaf_is_migration_write()` or `softleaf_is_device_private_write()`,
  with no `VM_WRITE` test.
- Saved write state is downgraded in `change_softleaf_pte()` in
  `mm/mprotect.c`, `change_non_present_huge_pmd()` in `mm/huge_memory.c` and,
  for hugetlb, `hugetlb_change_protection()` in `mm/hugetlb.c`.
- The downgrade is unconditional: every `change_protection()` pass, NUMA scan
  and userfaultfd included, turns writable migration entries read-only.
- `can_change_pte_writable()` result: valid only under the same page table
  lock hold. `do_numa_page()` drops it once it unlocks (`ignore_writable`).
- **Potentially unsafe usage**: `pte_mkwrite()` on a new entry in place of
  `maybe_mkwrite()`.
  - Unsafe: when the write bit comes neither from saved state nor from
    `vma->vm_page_prot`, and nothing on the path has tested `VM_WRITE` under
    the mmap lock or VMA lock; the entry is then writable in a VMA without
    `VM_WRITE`.
  - Safe: after an explicit test, as `map_anon_folio_pte_nopf()` does.
  - Safe: `move_present_ptes()`, since `validate_move_areas()` rejects VMAs
    without `VM_WRITE`.
  - Safe: when the entry built from `vma->vm_page_prot` is already
    `pte_write()`, as in `do_numa_page()`; `vma_set_page_prot()` derives
    `vm_page_prot` from the VMA flags.
  - Safe: from saved state under the page table lock, as
    `remove_migration_pte()` does; `change_softleaf_pte()` downgrades that
    state under the same lock when the protection changes.
- **Unsafe usage**: a new kind of saved write state that
  `change_softleaf_pte()` does not downgrade; `remove_migration_pte()` and
  `__split_huge_pmd_locked()` set the write bit from saved state with no
  `VM_WRITE` test.
  - Safe: a kind that `change_softleaf_pte()` rewrites to its read form, as
    it does for `softleaf_is_migration_write()` and
    `softleaf_is_device_private_write()` entries;
    `change_non_present_huge_pmd()` does the same for PMDs.
