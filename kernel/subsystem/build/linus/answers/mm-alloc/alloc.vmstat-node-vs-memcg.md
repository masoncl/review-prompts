- NULL memcg in `lruvec_stat_mod_folio()` and `mod_lruvec_kmem_state()`: an
  explicit test calls `mod_node_page_state()`; no lruvec is involved.
- `mem_cgroup_lruvec()` with a NULL memcg: returns the root memcg's lruvec;
  `mod_lruvec_state()` on it updates the root memcg's counters as well as the
  node. It returns `pgdat->__lruvec` only when `mem_cgroup_disabled()`.
- "No cgroup" means `memcg_data` is 0 (or the object's slot holds no objcg).
- Folio charged by a root-cgroup task: `charge_memcg()` commits the root
  objcg, so `folio_memcg()` is `root_mem_cgroup` and the root memcg's counters
  are updated too.
- Kernel page or slab object allocated by a root-cgroup task:
  `__memcg_kmem_charge_page()` and `__memcg_slab_post_alloc_hook()` store no
  objcg, so the helpers update the node only.
- `mod_lruvec_kmem_state()`: finds the memcg with `mem_cgroup_from_virt()` in
  `mm/memcontrol.c`; there is no mem_cgroup_from_slab_obj() here.
- `mem_cgroup_from_virt()` on a non-slab address: uses
  `folio_memcg_check()` on the page's folio.
- `folio_memcg()`: goes through the folio's objcg; after
  `__memcg_reparent_objcgs()` the update lands on the parent memcg.
- Per-object slab statistics: `__account_obj_stock()` → `mod_objcg_mlstate()`,
  memcg side only; there is no mod_objcg_state() or
  obj_cgroup_charge_account() here.
