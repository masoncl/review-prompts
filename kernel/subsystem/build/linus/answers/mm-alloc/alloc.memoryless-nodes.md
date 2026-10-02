- `CONFIG_HAVE_MEMORYLESS_NODES`: defined only in `arch/powerpc/Kconfig`; on
  every other architecture `numa_mem_id()` is `numa_node_id()` and
  `cpu_to_mem()` is `cpu_to_node()`, so both can return a memoryless node.
- `get_node()`: returns `s->per_node[node].node`.
- `slab_nodes`: filled from `N_MEMORY`, not `N_NORMAL_MEMORY`, in
  `kmem_cache_init()`, and extended by `slab_mem_going_online_callback()` on
  `NODE_ADDING_FIRST_MEMORY`.
- `slab_nodes` bits are never cleared, so a node that lost its memory keeps a
  non-NULL `struct kmem_cache_node`.
- `get_from_partial_node()`: takes the `struct kmem_cache_node *`, not a nid,
  and returns NULL on `!n || !n->nr_partial`; `get_partial_node_bulk()` has
  the same test.
- `get_from_partial()`: maps `NUMA_NO_NODE` to `numa_mem_id()` and passes
  `get_node()` of that straight in, relying on the NULL test above.
- `___slab_alloc()`: does not rewrite a requested node that lacks a
  `struct kmem_cache_node`; it tries the node with `__GFP_THISNODE` added,
  then retries with the caller's flags, which lets the page allocator fall
  back.
- Caller's `__GFP_THISNODE` with a requested memoryless node:
  `get_from_partial()` returns NULL without trying other nodes, and
  `new_slab()` keeps the flag (`GFP_CONSTRAINT_MASK`).
- **Potentially unsafe usage**: dereferencing the result of `get_node()` with
  no NULL test.
  - Unsafe: when the nid comes from `numa_node_id()`, from a caller's node
    argument, or from `numa_mem_id()` on an architecture without
    `CONFIG_HAVE_MEMORYLESS_NODES`; the pointer is NULL for a node that never
    had memory.
  - Safe: when the nid is `slab_nid()` of an allocated slab, as in
    `inc_slabs_node()`; `slab_mem_going_online_callback()` installs the
    structure before the node's memory can be allocated.
  - Safe: after a NULL test, as `get_from_partial_node()` does.
