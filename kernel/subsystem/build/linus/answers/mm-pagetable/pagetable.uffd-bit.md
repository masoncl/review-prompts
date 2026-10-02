- Bit names: `_PAGE_UFFD` and `_PAGE_SWP_UFFD` on x86 and riscv, `PTE_UFFD`
  and `PTE_SWP_UFFD` on arm64. There is no _PAGE_UFFD_WP or
  _PAGE_SWP_UFFD_WP here.
- Accessor pattern, present: `pte_uffd()`, `pte_mkuffd()`,
  `pte_clear_uffd()`; the same three with `pmd_` and with `huge_pte_`.
- Accessor pattern, swap-format: `pte_swp_uffd()`, `pte_swp_mkuffd()`,
  `pte_swp_clear_uffd()`; the same three with `pmd_swp_`.
- No `pte_`, `pmd_` or `huge_pte_` accessor with a uffd_wp suffix exists;
  generic stubs are in `include/asm-generic/pgtable_uffd.h`.
- `pgtable_supports_uffd()`: the runtime test; there is no
  pgtable_supports_uffd_wp().
- `CONFIG_HAVE_ARCH_USERFAULTFD_WP` and `PTE_MARKER_UFFD_WP` keep the old
  spelling.
- `pte_is_uffd_wp_marker()` in `include/linux/leafops.h`: the marker test;
  `pte_swp_uffd_any()` is true for a non-present PTE with the swap bit or the
  marker, and only when `uffd_supports_wp_marker()`.
- Two modes use the bit: write-protect (`VM_UFFD_WP`, `userfaultfd_wp()`) and
  read-write-protect (`VM_UFFD_RWP`, `userfaultfd_rwp()`,
  `CONFIG_USERFAULTFD_RWP`, ioctl `UFFDIO_RWPROTECT`).
- `userfaultfd_register()`: returns `-EINVAL` for
  `UFFDIO_REGISTER_MODE_WP` together with `UFFDIO_REGISTER_MODE_RWP`, so a
  VMA is in at most one of the two modes.
- Mode of an entry: test the VMA and the bit together, with
  `userfaultfd_pte_wp()`, `userfaultfd_pte_rwp()`,
  `userfaultfd_huge_pmd_wp()` or `userfaultfd_huge_pmd_rwp()`;
  `userfaultfd_protected()` is true for either mode.
- `userfaultfd_rwp()`: constant false without
  `CONFIG_ARCH_HAS_PTE_PROTNONE`.
- Armed RWP present entry: the bit plus `PAGE_NONE`. In a
  `vma_is_accessible()` VMA, `handle_pte_fault()` sends a protnone entry to
  `do_uffd_rwp()` only if `userfaultfd_pte_rwp()`; otherwise to
  `do_numa_page()`.
- Protnone plus the bit in a `VM_UFFD_WP` VMA: a NUMA hint on a
  write-protected page, not RWP; see `numa_rebuild_large_mapping()`.
- `PTE_MARKER_UFFD_WP`: installed on a none entry by write-protect only;
  `userfaultfd_wp_use_markers()` is false for RWP, and `change_pte_range()`
  leaves a none PTE alone under `MM_CP_UFFD_RWP`.
