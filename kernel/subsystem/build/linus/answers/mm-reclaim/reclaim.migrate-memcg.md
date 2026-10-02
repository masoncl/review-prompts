- `mem_cgroup_migrate()`: gets a new objcg reference for `new` from
  `get_migration_objcg()`, then drops `old`'s with `obj_cgroup_put()`. No
  css reference is moved.
- `get_migration_objcg()`: re-derives the objcg for the node of `new` when
  the nodes differ.
- Page counters: changed in one case. If the new objcg is root and the old
  one was not, `memcg_uncharge()` settles the charge.
- Caller: only `folio_migrate_flags()`. `__folio_migrate_mapping()` does not
  call it.
- `old` must be off the LRU: `VM_BUG_ON_FOLIO(folio_test_lru(old))`.
- `old` with no objcg: early return; warns unless `old` is hugetlb.
- `migrate_folio_done()`: uses `mod_node_page_state()` on `folio_pgdat()`.
  It skips the `NR_ISOLATED_ANON` or `NR_ISOLATED_FILE` decrement for
  movable_ops pages and for `MR_DEMOTION`.
- **Unsafe usage**: calling `folio_migrate_flags()` before
  `folio_migrate_mapping()`. `mem_cgroup_migrate()` warns if `old` is still
  on the deferred split queue, and `__folio_migrate_mapping()` reads
  `folio_memcg()` of `old` for its zone statistics.
  - Safe: mapping first, then flags, as `__migrate_folio()` does.
- **Unsafe usage**: returning an error from a `migrate_folio` callback after
  `folio_migrate_flags()` ran. `old` is handed back with `memcg_data` 0; on
  LRU putback `folio_lruvec()` warns and uses the root memcg.
  - Safe: make `folio_migrate_flags()` the last step that can precede a
    return of 0, as `__migrate_folio()` does.
