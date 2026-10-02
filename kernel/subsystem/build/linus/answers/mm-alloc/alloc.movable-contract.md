- `gfp_migratetype()`: defined in `mm/page_alloc.h`, which undefines
  `GFP_MOVABLE_MASK` and `GFP_MOVABLE_SHIFT` right after it.
- Both bits set: `VM_WARN_ON()` (not once, `CONFIG_DEBUG_VM` only) runs
  before the `page_group_by_mobility_disabled` test, so it fires either way.
- Both bits set, value: 3, which a `BUILD_BUG_ON()` ties to
  `MIGRATE_HIGHATOMIC`; with `page_group_by_mobility_disabled` the result
  is `MIGRATE_UNMOVABLE`.
- Both bits set, value 3 afterwards: `prepare_alloc_pages()` stores the
  value untested. `order_to_pindex()` then returns the index of another
  list; for order 0 that is the order-1 `MIGRATE_UNMOVABLE` list.
- There is no gfp_to_alloc_flags_cma() here; `alloc_flags_cma()` in
  `mm/page_alloc.c` sets `ALLOC_CMA` for `MIGRATE_MOVABLE`, under
  `CONFIG_CMA`.
- Names not defined in this tree: MIGRATEPAGE_SUCCESS,
  __SetPageMovableOps(), __SetPageMovable(), __ClearPageMovable(),
  mm/balloon_compaction.c.
- Registration: `set_movable_ops()` in `mm/migrate.c`, one ops pointer per
  page type, with no locking against concurrent callers.
- `set_movable_ops()` types: only `PGTY_offline` and `PGTY_zsmalloc`; any
  other type gives -EINVAL. A new user must also extend `page_movable_ops()`
  and `page_has_movable_ops()`.
- `set_movable_ops()` results: -EBUSY when ops are already set, -ENOSYS
  without `CONFIG_MIGRATION`; NULL ops unregisters.
- Balloon drivers register nothing: `mm/balloon.c` registers `balloon_mops`
  under `CONFIG_BALLOON_MIGRATION`, and a driver supplies `migratepage` in
  `struct balloon_dev_info`.
- `balloon_page_alloc()`: uses `GFP_HIGHUSER_MOVABLE` only under
  `CONFIG_BALLOON_MIGRATION`, else `GFP_HIGHUSER`.
- Marking a page: `SetPageMovableOps()` plus the page type;
  `page_has_movable_ops()` needs both.
- `PG_movable_ops`: has no clear helper, and stays set until the page is
  freed; `migrate_page()` does not clear it.
- Flag aliases: `PG_movable_ops` is `PG_uptodate` and
  `PG_movable_ops_isolated` is `PG_reclaim`.
- `PG_movable_ops_isolated`: owned by the core. `isolate_movable_ops_page()`
  warns, under `CONFIG_DEBUG_VM`, if `isolate_page()` set it.
- `migrate_page()`: success is 0; only then does
  `migrate_movable_ops_page()` clear the isolated flag.
- `isolate_page()`: may be handed a page its owner already released, and
  must then return false, as `balloon_page_isolate()` and
  `zs_page_isolate()` do.
- After `set_movable_ops(NULL, type)`: `page_movable_ops()` returns NULL.
  Only `isolate_movable_ops_page()` checks for that;
  `putback_movable_ops_page()` and `migrate_movable_ops_page()` call
  through it.
