- `commit_charge()`: stores a `struct obj_cgroup` pointer in
  `folio->memcg_data`, not a `struct mem_cgroup` pointer.
- LRU folio: `memcg_data` is the objcg pointer with no flag bits.
- Kmem page: `memcg_data` is the objcg pointer with `MEMCG_DATA_KMEM`.
- Reference held: one objcg reference per folio, taken by
  `get_obj_cgroup_from_memcg()` in `charge_memcg()`.
- `charge_memcg()`: takes no css reference for the folio; the folio does not
  pin the memcg.
- `folio_memcg()`: reads `objcg->memcg` through `obj_cgroup_memcg()`, which
  asserts `rcu_read_lock()` or `cgroup_mutex`.
- `memcg_reparent_objcgs()`: rewrites `objcg->memcg` to the parent at offline,
  so `folio_memcg()` can return a different memcg for the same folio later.
- `get_mem_cgroup_from_folio()`: use it to keep the memcg past the RCU
  section.
- Root objcg: `obj_cgroup_get()` and `obj_cgroup_put()` do nothing for it.
- `charge_memcg()`: calls `try_charge_memcg()` directly, not `try_charge()`;
  it skips the call when `obj_cgroup_is_root(objcg)` and still commits.
- Objcg choice: `charge_memcg()` takes the objcg of `folio_nid(folio)`; each
  memcg has one objcg per node in `memcg->nodeinfo[nid]->objcg`.
- Page cache add: `filemap_add_folio()` charges; `__filemap_add_folio()` does
  not.
- `AS_KERNEL_FILE` mappings: `filemap_add_folio()` charges the root memcg via
  `set_active_memcg()`.
- hugetlb: there is no mem_cgroup_hugetlb_try_charge() here;
  `mem_cgroup_charge_hugetlb()` charges and commits in one call.
- Swap-in: `mem_cgroup_swapin_charge_folio(folio, id, mm, gfp)` gets the id
  from its caller and resolves it with `mem_cgroup_from_private_id()`.
- There is no lookup_swap_cgroup_id() and no mem_cgroup_from_id() here.
- `__swap_cache_alloc()` in `mm/swap_state.c`: charges after the folio is in
  the swap cache, and removes it again if the charge fails.
- Folio of order > 1: after the charge, `folio_memcg_alloc_deferred()` is
  called and the folio is dropped if it fails; for example in
  `__swap_cache_alloc()`.
