- Split lock storage: `ALLOC_SPLIT_PTLOCKS` decides whether `ptl` in
  `struct ptdesc` is the lock itself or a pointer to it.
- `softleaf_t`: the decoded form of a non-present leaf. It is a typedef alias
  of `swp_entry_t` in `include/linux/mm_types.h`, so the two mix without a
  compiler error.
- `enum softleaf_type`: the kinds of non-present leaf; the one easy to forget
  is `SOFTLEAF_DEVICE_EXCLUSIVE`.
- `PT_kernel` in `pt_flags`: marks a table that maps the kernel; every caller
  of `ptdesc_set_kernel()` is in `include/asm-generic/pgalloc.h`.
- Deposited PTE tables for a huge PMD, except on powerpc hash: hang off
  `pmd_huge_pte` in the PMD table's `struct ptdesc` under
  `CONFIG_SPLIT_PMD_PTLOCKS`, otherwise off `pmd_huge_pte` in
  `struct mm_struct`; use the `pmd_huge_pte()` macro.
- Present leaf and `struct folio`: a present leaf need not map an accounted
  folio. `vm_normal_page()` in `mm/memory.c` returns NULL for special entries
  (`VM_PFNMAP`, `VM_MIXEDMAP`, the shared zero folios) when the VMA has no
  `find_normal_page`, and `zap_present_ptes()` then clears the entry with no
  rmap or refcount work.
- PTE table lifetime: an empty PTE table can be freed while its VMA stays
  mapped. `zap_pte_range()` does it under `CONFIG_PT_RECLAIM` when
  `reclaim_pt` is set in `struct zap_details`.
- `struct unmap_desc` in `mm/vma.h`: describes one teardown; `unmap_vmas()`
  and `free_pgtables()` take it in place of separate range arguments. It
  keeps the VMA range apart from the floor and ceiling within which tables
  may be freed.
- hugetlb shared PMD table: the number of extra sharers is `pt_share_count`
  in the table's `struct ptdesc`, present only under
  `CONFIG_HUGETLB_PMD_PAGE_TABLE_SHARING`.
- hugetlb unsharing and `struct mmu_gather`: `huge_pmd_unshare()` takes the
  gather and records the unshare in it; `huge_pmd_unshare_flush()` completes
  the sequence. See `tlb_unshare_pmd_ptdesc()` in
  `include/asm-generic/tlb.h`.
- `struct lazy_mmu_state`: per-task nesting state for batched entry updates,
  embedded in `struct task_struct` under `CONFIG_ARCH_HAS_LAZY_MMU_MODE`.
- Lazy MMU in `mm/`: code brackets updates with `lazy_mmu_mode_enable()` and
  `lazy_mmu_mode_disable()` from `include/linux/pgtable.h`; nothing under
  `mm/` calls `arch_enter_lazy_mmu_mode()` directly.
