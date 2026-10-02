- `fallback_migrate_folio()`: a dirty folio returns `-EBUSY`. Nothing is
  written out; there is no writeout() here.
- `fallback_migrate_folio()` when `filemap_release_folio()` fails: `-EAGAIN`
  in `MIGRATE_SYNC`, `-EBUSY` in the other modes.
- `filemap_migrate_folio()`: `__migrate_folio()` plus moving the private
  pointer. It is not the fallback.
- `mapping_inaccessible()`: checked in `move_to_new_folio()` before the
  callback and before the fallback; returns `-EOPNOTSUPP`.
- Opting out: providing no callback does not stop migration, since the
  fallback migrates clean folios. A callback that always fails does; for
  example `secretmem_migrate_folio()` in `mm/secretmem.c`.
- Without `CONFIG_MIGRATION`: `filemap_migrate_folio`,
  `buffer_migrate_folio` and `buffer_migrate_folio_norefs` are defined as
  NULL. `migrate_folio()` has no such stub; `shmem_aops` and `swap_aops`
  wrap it in `#ifdef CONFIG_MIGRATION`.
