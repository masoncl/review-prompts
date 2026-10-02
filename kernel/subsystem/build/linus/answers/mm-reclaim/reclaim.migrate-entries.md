- Names in this tree: `softleaf_is_migration()`,
  `softleaf_entry_wait_on_locked()` in `mm/filemap.c`, `pte_swp_uffd()`,
  `pte_mkuffd()`. There is no is_migration_entry(),
  migration_entry_wait_on_locked() or pte_swp_uffd_wp().
- `remove_migration_ptes()` takes `enum ttu_flags`: `TTU_RMAP_LOCKED` and
  `TTU_USE_SHARED_ZEROPAGE`. There is no RMP_LOCKED or
  RMP_USE_SHARED_ZEROPAGE.
- PTEs that get no migration entry in `try_to_migrate_one()`:
  - a hwpoisoned subpage gets `make_hwpoison_entry()`;
  - a `pte_unused()` PTE in a VMA without userfaultfd is left cleared.
- `remove_migration_ptes()` restores neither of those two.
- uffd bit in `remove_migration_pte()`: `pte_mkuffd()` only when the entry is
  not writable.
- `userfaultfd_rwp()` VMA with the uffd bit: the new PTE is changed to
  `PAGE_NONE`.
- Dirty: restored only if the entry is dirty and `folio_test_dirty()` is
  still true.
- Soft-dirty: set from the entry, otherwise cleared on the new PTE.
- mlock: rebuilt by `mlock_vma_folio()` in the rmap add helpers, only when
  the call maps the whole folio. A PTE-mapped large folio does not get it.
- Device-private destination: `remove_migration_pte()` installs a
  device-private entry, not a present PTE.
- `TTU_USE_SHARED_ZEROPAGE`: allowed only when `src == dst`.
