- `slab_pre_alloc_hook()`: `might_alloc()` and `should_failslab()` only; no
  memcg work.
- `slab_free_hook()`: does not uncharge and does not drop the allocation
  tag. `memcg_slab_free_hook()` and `alloc_tagging_slab_free_hook()` are
  called beside it, for example in `slab_free()` and `free_to_pcs_bulk()`.
- `maybe_wipe_obj_freeptr()`: not part of `slab_post_alloc_hook()`. Each path
  that takes an object off a freelist calls it first, as `slab_alloc_node()`
  and `__refill_objects_node()` do.
- `slab_alloc_node()`: ignores the return value of `slab_post_alloc_hook()`;
  it relies on the memcg hook having set the object pointer to NULL.
- `memcg_alloc_abort_single()`: calls `alloc_tagging_slab_free_hook()`, then
  `slab_free_hook()`, then `__slab_free()` if the hook allows. It does not
  call `memcg_slab_free_hook()` and does not use the sheaves.
- Objects in a `main`, `spare` or barn sheaf: have already passed the free
  hooks and not yet the allocation hooks. A path that pops one must call
  `slab_post_alloc_hook()`, as `kmem_cache_alloc_from_sheaf_noprof()` does.
- Objects in an `rcu_free` sheaf: have passed no free hook yet;
  `__rcu_free_sheaf_prepare()` runs all three after the grace period, with
  `after_rcu_delay` true.
- `__kmalloc_nolock_noprof()`: skips `slab_pre_alloc_hook()` and
  `kfence_alloc()`.
- `kfree_nolock()`: does not call `slab_free_hook()`; it calls
  `memcg_slab_free_hook()`, `alloc_tagging_slab_free_hook()`,
  `kmsan_slab_free()`, `kasan_slab_pre_free()` and `kasan_slab_free()`
  without quarantine itself. It is only for objects from `kmalloc_nolock()`.
- `kmem_cache_alloc_bulk_noprof()`: frees with `__kmem_cache_free_bulk()`
  when allocation fails before the hooks, and the memcg hook frees with
  `kmem_cache_free_bulk()` when the charge of more than one object fails
  after them.
- **Potentially unsafe usage**: freeing with `__slab_free()` or
  `__kmem_cache_free_bulk()`, which run no hooks.
  - Unsafe: for an object that has passed `slab_post_alloc_hook()` and has
    not passed `slab_free_hook()` and the two hooks beside it; KASAN,
    kmemleak, the tag and the charge stay in the allocated state.
  - Safe: for an object taken from a `main`, `spare` or barn sheaf, as
    `sheaf_flush_unused()` does; `slab_free()` runs the hooks before
    `free_to_pcs()`.
  - Safe: for an object that never reached `slab_post_alloc_hook()`, as the
    error path of `__kmem_cache_alloc_bulk()` does.
  - Safe: when the caller first ran the free hooks that still apply:
    `memcg_alloc_abort_single()` (the charge failed, so none to drop) and
    `slab_free_after_rcu_debug()` (the free that deferred the object, for
    example `slab_free()`, already dropped the charge and the tag).
- **Unsafe usage**: freeing an object after `slab_free_hook()` returned
  false.
  - Safe: drop the object from the batch, as `free_to_pcs_bulk()` and
    `slab_free_freelist_hook()` do; KFENCE, the KASAN quarantine or
    `CONFIG_SLUB_RCU_DEBUG` now owns it.
