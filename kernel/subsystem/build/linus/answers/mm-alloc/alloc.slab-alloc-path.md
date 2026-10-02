- `slab_alloc_node()`: calls `alloc_from_pcs()` without testing
  `cache_has_sheaves()`, then `___slab_alloc()` directly. There is no
  __slab_alloc_node() or __slab_alloc() here.
- Partial-list getters: `get_from_partial()`, `get_from_partial_node()` and
  `get_from_any_partial()`. There is no get_partial(), get_partial_node() or
  get_any_partial().
- `___slab_alloc()`: returns one object. A new slab goes through
  `alloc_from_new_slab()`, or `alloc_single_from_new_slab()` for debug caches
  and `CONFIG_SLUB_TINY`, which put the rest of the slab on the node list.
- Sheaf refill chain: `refill_sheaf()`, `refill_objects()`,
  `__refill_objects_node()` (`get_partial_node_bulk()` and
  `get_freelist_nofreeze()`), `__refill_objects_any()`, then `new_slab()` and
  `alloc_from_new_slab()`. There is no __refill_objects().
- `refill_objects()`: always fills from `numa_mem_id()` first; it takes no
  node argument, so sheaf refill never honours a node request.
  `kmem_cache_alloc_bulk_noprof()` has no node argument.
- `apply_strict_numa_policy()`: runs in `slab_alloc_node()` and
  `__kmalloc_nolock_noprof()`, before `alloc_from_pcs()`. It only changes
  `NUMA_NO_NODE`.
- `___slab_alloc()` with a node and no `__GFP_THISNODE`: first pass uses
  `trynode_flags`, the caller's flags reduced to `GFP_NOWAIT`,
  `__GFP_NOMEMALLOC` and `__GFP_ACCOUNT` bits plus `__GFP_NOWARN` and
  `__GFP_THISNODE`, for both the partial list and the new slab. The second
  pass uses the caller's flags. `node` is never rewritten to `NUMA_NO_NODE`.
- `pfmemalloc_match()`: called in `get_from_partial_node()` and
  `get_partial_node_bulk()`, not in `___slab_alloc()`. A slab that
  `___slab_alloc()` has just allocated is not tested.
- `alloc_from_pcs()`: makes no reserve test. Sheaves are kept free of reserve
  objects elsewhere: `__pcs_replace_empty_main()` refills with
  `__GFP_NOMEMALLOC`, and `can_free_to_pcs()` rejects them on free.
