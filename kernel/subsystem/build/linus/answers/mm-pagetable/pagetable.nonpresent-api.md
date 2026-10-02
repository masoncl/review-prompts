- Old swap-entry predicates: defined nowhere in this tree (for example
  is_swap_pte(), is_migration_entry(), is_pfn_swap_entry(), non_swap_entry(),
  pte_to_swp_entry(), is_pte_marker()); of that family only
  `is_hwpoison_entry()` remains in `include/linux/swapops.h`.
- Kind predicates on a present or empty entry: all false, so no
  `pte_present()` test is needed before a kind test; `check_pte()` in
  `mm/page_vma_mapped.c` decodes a possibly-present PTE under
  `PVMW_MIGRATION` and relies on this.
- `softleaf_is_none()`: true for both present and empty; it cannot tell them
  apart.
- `softleaf_type()`: returns `SOFTLEAF_NONE` after `VM_WARN_ON_ONCE()` for a
  type number it does not know; `softleaf_is_none()` is false for that same
  entry.
- `softleaf_from_pmd()`: real only under `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`,
  otherwise it returns the none value for every PMD; there is no
  CONFIG_ARCH_ENABLE_THP_MIGRATION here.
- `pmd_is_device_private_entry()`: a `false` stub unless both
  `CONFIG_ZONE_DEVICE` and `CONFIG_ARCH_HAS_PMD_SOFTLEAVES` are set.
- Predicates easy to miss: `softleaf_is_migration_young()`,
  `softleaf_is_migration_dirty()`, `pte_is_uffd_marker()` (uffd-wp or poison
  marker), `softleaf_is_valid_pmd_entry()`.
- Encoders: `softleaf_to_pte()` and `softleaf_to_pmd()` wrap
  `swp_entry_to_pte()` and `swp_entry_to_pmd()`; both spellings are in use.
