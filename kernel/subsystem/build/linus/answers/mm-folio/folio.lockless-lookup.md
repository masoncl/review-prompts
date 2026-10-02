- `xas_reload()` after `folio_try_get()`: proves that the folio still covers
  the index only because a split keeps the folio frozen until its slots are
  rewritten. `__folio_freeze_and_split_unmapped()` in `mm/huge_memory.c`
  unfreezes the original folio after all new folios are stored;
  `__folio_migrate_mapping()` in `mm/migrate.c` stores the new folio before
  `folio_ref_unfreeze()`.
- **Unsafe usage**: unfreezing a folio whose `i_pages` slots still point to it
  but which no longer covers those indices.
  - Safe: rewrite every slot first, then `folio_ref_unfreeze()`, as
    `__folio_freeze_and_split_unmapped()` does; `filemap_get_entry()` relies
    on it, since a stale slot would pass its `xas_reload()` comparison.
- After locking: `__filemap_get_folio_mpol()` rechecks only
  `folio->mapping != mapping` and retries. `folio_contains()` is asserted with
  `VM_BUG_ON_FOLIO()`, not rechecked; callers need no index recheck of their
  own.
