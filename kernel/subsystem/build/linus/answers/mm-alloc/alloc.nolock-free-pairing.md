- Valid after `kmalloc_nolock()`: `kfree_nolock()`, `kfree_rcu_nolock()`
  (`include/linux/rcupdate.h`), `kfree()`, `kfree_rcu()`.
- `kfree()` and `kfree_rcu()` only where spinning is allowed.
- What lets `kfree()` and `kfree_rcu()` run without the matching alloc hooks:
  `delete_object_full()` and `paint_ptr()` in `mm/kmemleak.c` return silently
  for an unknown object, and `kfence_free()` returns false for a non-KFENCE
  address.
- In-tree frees with a function other than `kfree_nolock()`, for example:
  - `free_slab_obj_exts()` in `mm/slub.c` calls `kfree()` when `allow_spin`,
    on a vector that `alloc_slab_obj_exts()` may have got in no-spin mode;
  - `bpf_selem_free()` and `bpf_selem_free_trace_rcu()` in
    `kernel/bpf/bpf_local_storage.c` use `kfree_rcu()` and `kfree()` on
    objects from `bpf_map_kmalloc_nolock()`.
- `free_slab_obj_exts()` picks by the `allow_spin` of the free; nothing
  records how the vector was allocated.
- **Unsafe usage**: `kfree_nolock()` on an object that did not come from a
  `SLAB_ALLOC_NOLOCK` allocation.
  - Unsafe: an object from `kmalloc()` or `kmem_cache_alloc()` may be
    registered with kmemleak or belong to KFENCE; `kfree_nolock()` calls
    neither `kmemleak_free_recursive()` nor `kfence_free()`.
  - Unsafe: a large kmalloc object; `virt_to_slab()` is NULL, so
    `kfree_nolock()` warns once and returns without freeing.
  - Safe: the same flag chose the allocation and the free, as in
    `__kfree_rcu_sheaf()`, where `to_alloc_flags(free_flags)` allocates the
    sheaf and `__free_empty_sheaf()` frees it by `free_flags`.
  - Safe: the vector of a slab discarded by `free_new_slab_nolock()`; that
    slab was allocated by the same no-spin request.
- `kfree_nolock()` never tries `n->list_lock`; it calls `defer_free()` when
  `can_free_to_pcs()` is false or `free_to_pcs()` fails.
- There is no free_deferred_objects() here; `deferred_percpu_work_fn()` in
  `mm/slub.c` drains the per-CPU `deferred_percpu_work` llists from
  `irq_work`.
