- Test used by `pmd_trans_huge_lock()`: `pmd_is_huge()` in
  `include/linux/huge_mm.h`; there is no is_swap_pmd() and no pmd_devmap()
  in this tree.
- `pmd_is_huge()` accepts: a present PMD with `pmd_trans_huge()`, and every
  PMD that is neither present nor none.
- Checked twice: `pmd_trans_huge_lock()` tests unlocked, then
  `__pmd_trans_huge_lock()` tests again under `pmd_lock()`.
- Non-present helpers: there is no is_pmd_migration_entry() or
  pmd_to_swp_entry(); use `pmd_is_migration_entry()`,
  `pmd_is_device_private_entry()` and `softleaf_from_pmd()` from
  `include/linux/leafops.h`.
- Non-present does not mean no folio: get it with `pmd_to_softleaf_folio()`,
  never `pmd_folio()`; a device-private folio still has rmap and a
  reference, see `zap_huge_pmd_folio()`.
- Present kinds: see `insert_pmd()` in `mm/huge_memory.c`; a raw PFN and the
  huge zero folio get `pmd_mkspecial()`, any other folio is refcounted and
  rmapped.
- `vm_normal_folio_pmd()`: returns NULL for the special kinds.
- Code that gets it right: `madvise_free_huge_pmd()` and
  `madvise_cold_or_pageout_pte_range()` test `is_huge_zero_pmd()`, then
  `pmd_present()`, then call `pmd_folio()`.
- `zap_huge_pmd()` and `change_huge_pmd()`: also right, but they call
  `__pmd_trans_huge_lock()` directly.
