- Id kind: the 16-bit private id, `mem_cgroup_private_id()`, from the
  `mem_cgroup_private_ids` xarray.
- Reference source: `mem_cgroup_private_id_get_online()`; record the id of the
  memcg it returns, which may be an ancestor.
- Cluster lock: `__swap_cgroup_set()` and `__swap_cgroup_get()` assert
  `ci->lock`.
- `swap_pte_batch()`: compares PTEs only. It does not look at the owner.
- Swap-in read: `__swap_cache_add_check()`, when given `memcg_id`, returns the
  id and gives `-EBUSY` unless every slot in the range has the same id.
- **Potentially unsafe usage**: storing `mem_cgroup_private_id()` of a memcg
  without holding id references.
  - Unsafe: in `ci->memcg_table`. `__mem_cgroup_uncharge_swap()` puts
    `nr_pages` references on whatever memcg the id resolves to, and an id
    whose `id.ref` reached zero is erased and can be allocated again by
    `mem_cgroup_alloc()`.
  - Safe: in a workingset shadow entry, as `workingset_eviction()` does.
    `workingset_test_recent()` looks the id up under RCU, accepts NULL, and
    puts no id reference.
- **Potentially unsafe usage**: clearing several slots with one
  `__swap_cgroup_clear()` and uncharging the returned id for all of them.
  - Unsafe: when the slots can have different owners. Only the first slot's id
    is returned; the rest are checked by `VM_WARN_ON_ONCE()` alone.
  - Safe: one slot at a time, as `__swap_cluster_free_entries()` does.
  - Safe: `memcg1_swapin()` on a folio from `__swap_cache_alloc()`, where
    `__swap_cache_add_check()` required one id for the whole range.
