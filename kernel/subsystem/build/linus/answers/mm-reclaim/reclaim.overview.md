- Reclaim writeback: `pageout()` in `mm/vmscan.c` writes only shmem folios
  (`shmem_writeout()`) and anon swap-cache folios (`swap_writeout()`).
- Dirty file-LRU folio in `shrink_folio_list()`: gets `folio_set_reclaim()` and
  goes to `activate_locked`; reclaim never writes it. `mm/vmscan.c` makes no
  `writepages` call.
- `struct mem_cgroup_per_node`: holds the lruvec and one `objcg` per memcg per
  node.
- Memcg offline: `mem_cgroup_css_offline()` calls `memcg_reparent_objcgs()`,
  which splices the child's LRU lists into the parent's lruvec
  (`lru_reparent_memcg()` or `lru_gen_reparent_memcg()`) and repoints the
  objcgs to the parent, per node, under both `lru_lock`s.
- Folio and lruvec: a folio is on at most one lruvec. It is on none while
  isolated or while it sits in the per-CPU `lru_add` batch of
  `struct cpu_fbatches`; the other batches there do not take a folio off its
  list.
- Unevictable folio: counted in its lruvec but not linked on a list; see
  `lruvec_add_folio()` in `include/linux/mm_inline.h`.
- `struct lruvec`: holds `lists` and, with `CONFIG_LRU_GEN`, `lrugen`. Which
  one takes a folio is chosen at run time, per lruvec, by `lrugen->enabled`,
  not by `CONFIG_LRU_GEN` alone.
- `struct lru_gen_memcg` (`memcg_lru` in `struct pglist_data`): per-node list
  of the memcgs' `struct lru_gen_folio`. MGLRU root reclaim picks memcgs from
  it in `shrink_many()`, which does not call `mem_cgroup_iter()`;
  `shrink_node_memcgs()` does.
- MGLRU names: `struct lru_gen_folio`, `struct lru_gen_mm_state`,
  `struct lru_gen_mm_walk`, `struct lru_gen_memcg` are in
  `include/linux/mmzone.h`; `struct lru_gen_mm_list` is in
  `include/linux/mm_types.h`.
- Swap cache: is the set of PFN words in the swap tables, not an xarray.
  `swap_space` in `mm/swap_state.c` is a single placeholder
  `struct address_space` that `folio_mapping()` returns for swap-cache folios.
- `swap_cache_get_folio()`: lockless lookup that returns the folio unlocked; a
  caller that maps the folio or reads `folio->swap` must first lock it and
  recheck that it still serves the entry, normally with
  `folio_matches_swap_entry()`.
- `folio_dup_swap()`: called under the folio lock, for example from
  `ttu_anon_swapbacked_folio()` in `mm/rmap.c`; it warns
  (`VM_WARN_ON_FOLIO()`) when the folio is not locked or not in the swap
  cache.
- Slot data: is in one of four places: the swap cache folio, zswap, the device,
  or nowhere when the slot is zero-filled.
- `softleaf_t`: the name for a non-present page table entry value; today an
  alias of `swp_entry_t`. `softleaf_type()` in `include/linux/leafops.h` tells
  swap, migration, device, hwpoison and marker entries apart.
- Entry helpers: there is no is_migration_entry(), non_swap_entry() or
  pte_to_swp_entry() here; `softleaf_is_migration()`, `softleaf_is_swap()` and
  `softleaf_from_pte()` do those jobs.
- `migrate_pages()`: a function in `mm/migrate.c`; there is no struct of that
  name.
- `struct memory_tier`: private to `mm/memory-tiers.c`. `mm/vmscan.c` calls
  only `next_demotion_node()` and `node_get_allowed_targets()` from it.
