- `s->cpu_sheaves`: allocated for every cache in `do_kmem_cache_create()`;
  the fast paths make no NULL test.
- Cache without a per-CPU layer: `s->sheaf_capacity == 0`, tested by
  `cache_has_sheaves()` in `mm/slab.h`.
- `bootstrap_sheaf` in `init_percpu_sheaves()`: one static empty sheaf that
  `pcs->main` of every CPU points at when the capacity is 0; its `size` 0
  equals the capacity, so `alloc_from_pcs()` and `free_to_pcs()` both fall
  into the replace helpers, which test `cache_has_sheaves()` and back off.
- Capacity 0: see `calculate_sheaf_capacity()`. It is 0 under
  `CONFIG_SLUB_TINY`, with any `SLAB_DEBUG_FLAGS` bit, with `SLAB_NO_SHEAVES`
  (the two boot caches in `kmem_cache_init()`) and with `SLAB_NOLEAKTRACE`.
- kmalloc caches: capacity 0 until `bootstrap_kmalloc_sheaves()` runs.
- Per-node pointers: `s->per_node[nid].barn` and `s->per_node[nid].node`,
  `struct kmem_cache_per_node_ptrs` in `mm/slab.h`.
- `struct kmem_cache_node` has no barn member, and `struct kmem_cache` has no
  node array of its own.
- `slab_barn_nodes` (online nodes) decides where a barn exists; `slab_nodes`
  (nodes with memory) decides where a `struct kmem_cache_node` exists. An
  online node that never had memory has a barn, for a cache with sheaves,
  and no `struct kmem_cache_node`.
- `get_barn()`: uses `numa_node_id()`, while slab lists use `numa_mem_id()`.
  It can return NULL, and every caller tests for that.
- `struct slab_sheaf`: `capacity` and `pfmemalloc` share a union with
  `barn_list` and `rcu_head`; they are valid only while a caller of
  `kmem_cache_prefill_sheaf()` holds the sheaf. Elsewhere the capacity is
  `s->sheaf_capacity`. `node` is set only for a full `rcu_free` sheaf.
