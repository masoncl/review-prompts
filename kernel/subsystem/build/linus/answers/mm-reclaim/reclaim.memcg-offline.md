- Objcgs are per memcg per node: `objcg`, `orig_objcg` and `objcg_list` are
  fields of `struct mem_cgroup_per_node`; `struct mem_cgroup` has none.
- `memcg_reparent_objcgs()`: handles one node at a time and drops the locks
  it took between nodes.
- Per node, in one lock section: LRU lists and `lru_zone_size` first, then
  `__memcg_reparent_objcgs()` repoints that node's active and inherited
  objcgs and splices them onto the parent's node list.
- Locks, same with and without MGLRU: `reparent_locks()` takes `objcg_lock`
  with irqs off, child `lru_lock`, then parent `lru_lock`; `cgroup_mutex` is
  held by the caller (`offline_css()` asserts it).
- MGLRU is chosen at run time by `lru_gen_enabled()`.
- MGLRU sequence: `max_lru_gen_memcg()` on the parent before the locks,
  `recheck_lru_gen_max_memcg()` under them; on failure unlock,
  `cond_resched()`, retry; then `lru_gen_reparent_memcg()` in `mm/vmscan.c`
  splices each child list onto the parent list of the same generation index.
- Classic LRU: `lru_reparent_memcg()` in `mm/folio.c`; for
  `LRU_UNEVICTABLE` only the size is moved, no list is spliced.
- `percpu_ref_kill()` on the node's objcg: after the locks are dropped;
  `orig_objcg` keeps a reference until `__mem_cgroup_free()`.
- `reparent_state_local()`: runs after the node loop, does nothing on the
  default hierarchy or without `CONFIG_MEMCG_V1`.
- There is no reparent_deferred_split_queue(); `deferred_split_lru` in
  `mm/huge_memory.c` is a `struct list_lru`, reparented by
  `memcg_reparent_list_lrus()` from `memcg_offline_kmem()` before
  `memcg_reparent_objcgs()` runs.
- `folio_memcg()` mid-move, LRU folio: parent for folios on nodes already
  processed, child for folios on nodes not yet reached.
