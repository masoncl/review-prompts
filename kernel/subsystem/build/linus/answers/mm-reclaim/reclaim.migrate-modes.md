- `enum migrate_mode`: three values. There is no MIGRATE_SYNC_NO_COPY.

| Blocking point | `MIGRATE_ASYNC` | `MIGRATE_SYNC_LIGHT` | `MIGRATE_SYNC` |
|---|---|---|---|
| source folio lock | trylock | sleeps only if folio is uptodate | sleeps |
| folio under writeback | `-EBUSY` | `-EBUSY` | waits |
| buffer lock | trylock | sleeps only if buffer is uptodate | sleeps |
| hugetlb source lock | trylock | trylock | sleeps from the fourth pass |
| lock for `try_split_folio()` | trylock | sleeps | sleeps |

- `PF_MEMALLOC` task: `migrate_folio_unmap()` never sleeps on the source
  folio lock, in any mode.
- `MIGRATE_ASYNC` still sleeps on the rmap rwsem: `try_to_migrate()` does not
  set `try_lock` in its `struct rmap_walk_control`.
- Sync modes, non-hugetlb folios: `migrate_pages_sync()` runs the batch as
  `MIGRATE_ASYNC` first (`NR_MAX_MIGRATE_ASYNC_RETRY` passes), then retries
  failures one folio at a time in the caller's mode. A callback sees
  `MIGRATE_ASYNC` first.
- Pieces of a split large folio: migrated with `MIGRATE_ASYNC`, one pass,
  whatever mode the caller passed.
- `get_new_folio()`: not given the mode. Whether allocation blocks is decided
  by the caller's callback, not by the mode.
- Callbacks add their own mode tests; for example `nfs_migrate_folio()` in
  `fs/nfs/write.c` waits only outside `MIGRATE_ASYNC`.
