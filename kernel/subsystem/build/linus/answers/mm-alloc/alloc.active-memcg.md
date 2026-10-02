- `current_obj_cgroup()` in `mm/memcontrol.c`: returns the root memcg's objcg,
  not NULL, for a root-cgroup task, a kernel thread, a task without `mm`, and
  non-task context without `int_active_memcg`.
- Charge skipped: callers test `!objcg || obj_cgroup_is_root(objcg)`; see
  `__memcg_slab_post_alloc_hook()`, `__memcg_kmem_charge_page()` and
  `pcpu_memcg_pre_alloc_hook()`; a NULL test alone does not mean "not
  charged".
- NULL return: only for `in_nmi()` when `CONFIG_MEMCG_NMI_UNSAFE` is set.
- The objcg is per node: `memcg->nodeinfo[nid]->objcg` with `numa_node_id()`;
  the field is in `struct mem_cgroup_per_node`, `struct mem_cgroup` has none.
- Override walk: goes up `parent_mem_cgroup()` until a per-node `objcg` is
  non-NULL, and ends at the root objcg.
- Offlined override memcg: `__memcg_reparent_objcgs()` cleared its `objcg`, so
  the charge lands on the nearest ancestor that still has one.
- Task's own cgroup on the kmem path: `mem_cgroup_from_task(current)` in
  `current_objcg_update()`, which does not read `mm->owner`;
  `get_mem_cgroup_from_mm()` does.
- `get_mem_cgroup_from_current()`: does not read the override.
- `get_mem_cgroup_from_mm()`: reads the override only when `mm` is NULL.
- `set_active_memcg(NULL)`: ends the override, so in task context the
  allocation is charged to the current task again.
- `set_active_memcg(root_mem_cgroup)`: suppresses the charge, as
  `filemap_add_folio()` in `mm/filemap.c` does for kernel files.
- **Potentially unsafe usage**: calling `set_active_memcg()` on a memcg
  without taking a reference in the same function.
  - Unsafe: when nothing else keeps the memcg alive until the old value is
    restored; `current_obj_cgroup()` dereferences it with no RCU lock and no
    reference, and `get_mem_cgroup_from_mm()` uses `css_get()`, not
    `css_tryget()`.
  - Safe: the memcg is pinned by an object the caller holds, as
    `fanotify_alloc_event()` uses `group->memcg`, taken in group creation and
    dropped in `fsnotify_final_destroy_group()`.
  - Safe: the memcg is `root_mem_cgroup`, which is never freed (its css has
    `CSS_NO_REF`), as in `filemap_add_folio()`.
