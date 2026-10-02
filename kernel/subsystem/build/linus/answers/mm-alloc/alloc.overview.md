- Per-CPU slab layer: there is no kmem_cache_cpu in this tree. Each
  `struct kmem_cache` has a per-CPU `struct slub_percpu_sheaves` with a `main`,
  a `spare` and an `rcu_free` `struct slab_sheaf`.
- `struct slab_sheaf`: an array of object pointers, not a slab. No slab is
  owned by a CPU; there is no per-CPU current slab and no per-CPU partial list.
- `struct node_barn`: per cache and per node, a stock of full and empty
  sheaves that CPUs swap with, loosely bounded by `MAX_FULL_SHEAVES` and
  `MAX_EMPTY_SHEAVES`. It sits between the per-CPU sheaves and
  `struct kmem_cache_node`.
- Slab allocation order: per-CPU sheaf, then barn, then node partial list, then
  a new slab. See `alloc_from_pcs()` and `___slab_alloc()` in `mm/slub.c`.
- Object held in a sheaf: free to its user, but still counted in `inuse` of its
  `struct slab`.
- Sheaves and barns are themselves kmalloc objects; kmalloc caches get theirs
  late, in `bootstrap_kmalloc_sheaves()`.
- Caller-owned sheaf: `kmem_cache_prefill_sheaf()` hands a `struct slab_sheaf`
  to the caller, linked to no CPU or barn until `kmem_cache_return_sheaf()`.
  For example `mt_get_sheaf()` in `lib/maple_tree.c`.
- `frozen` in `struct slab`: means the slab failed a consistency check and is
  never allocated from again. `SL_partial` marks a slab on the node partial
  list.
- `struct slabobj_ext`: a struct that holds one pointer-sized union. An object
  has one or two of them, depending on whether the slab needs an objcg and
  whether `slab_obj_ext_has_codetag()` is true.
- A free page is in one of these places: `struct free_area`, a
  `struct per_cpu_pages` list, `trylock_free_pages` in `struct zone`, where
  a `FPI_NOLOCK` free parks it when a lock cannot be taken, or, under
  `CONFIG_UNACCEPTED_MEMORY`, `unaccepted_pages` in `struct zone`.
- Page type of a free page: only pages in `struct free_area` carry
  `PGTY_buddy`. A page on a pcp list or on `trylock_free_pages` has no page
  type.
- `memcg_data` of a charged folio: holds a `struct obj_cgroup *` for LRU folios
  as well as kmem pages; `folio_memcg()` goes through `folio_objcg()`. In a
  slab the same word holds the `struct slabobj_ext` vector, flagged
  `MEMCG_DATA_OBJEXTS`.
