- `softleaf_t`: defined in `include/linux/mm_types.h` as a typedef of
  `swp_entry_t`; no conversion exists or is needed, there is no
  softleaf_to_swp_entry().
- pte_to_swp_entry(): not in this tree; `softleaf_from_pte()` is the generic
  decoder, and `include/linux/swapops.h` keeps the encoders `swp_entry()`,
  `swp_entry_to_pte()` and the `swp_type()`, `swp_offset()` accessors.
- Old predicates: non_swap_entry(), is_swap_pte(), is_swap_pmd(),
  is_migration_entry(), is_pfn_swap_entry() and is_pte_marker_entry() are
  absent; `is_hwpoison_entry()` remains in `include/linux/swapops.h`.
- `softleaf_from_pte()`: clears the swap-PTE flag bits with
  `pte_swp_clear_flags()`, so exclusive, soft-dirty and uffd state must be
  read from the PTE with `pte_swp_exclusive()`, `pte_swp_soft_dirty()` and
  `pte_swp_uffd()`, as `copy_nonpresent_pte()` in `mm/memory.c` does.
- `softleaf_from_pmd()`: returns the none entry unless
  `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`; only migration and device-private entries
  are valid at PMD level, see `softleaf_is_valid_pmd_entry()`.
