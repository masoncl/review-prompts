- Preallocated per-CPU hash: `prealloc_init()` also calls
  `bpf_map_alloc_percpu()` once per element, besides the one
  `bpf_map_area_alloc()`.
- `alloc_htab_elem()` errors: `-E2BIG` when `__pcpu_freelist_pop()` returns
  NULL or the map is full, `-ENOMEM` when `bpf_mem_cache_alloc()` returns
  NULL.
- LRU update ops: `prealloc_lru_pop()` failure gives `-ENOMEM`.
- `__pcpu_freelist_pop()`: skips a list whose `raw_res_spin_lock()` fails, so
  `-E2BIG` can occur on a map that is not full.
- `bpf_mem_cache_free()`: the object is reusable on that CPU at once;
  `htab_elem_free()` uses it. An element given to `pcpu_freelist_push()` is
  reusable at once too.
- `bpf_mem_cache_free_rcu()`: reuse waits for one RCU grace period;
  `rhtab_delete_elem()` uses it.
- `alloc_bulk()`: refills first from `free_by_rcu_ttrace` and
  `waiting_for_gp_ttrace`, so an object can be reused before the tasks-trace
  grace period ends.
- Objects freed with `bpf_mem_cache_free()` or `bpf_mem_cache_free_rcu()`:
  return to slab only from `__free_rcu()`, after `call_rcu_tasks_trace()`, or
  while draining.
- `bpf_mem_alloc_set_dtor()`: the destructor runs in `free_all()` when an
  object returns to slab, not when the element is deleted.
- `htab_map_check_btf()`: sets that destructor for a non-preallocated hash,
  since `map->record` is not yet set during `map_alloc`.
- `kmalloc_nolock()` and `kfree_nolock()`: implemented in `mm/slub.c`;
  `bpf_map_kmalloc_nolock()` in `kernel/bpf/syscall.c` adds the memcg switch.
- `bpf_selem_alloc()` in `kernel/bpf/bpf_local_storage.c`: uses
  `bpf_map_kmalloc_nolock()`, not `struct bpf_mem_alloc`.
- `kmalloc_nolock()` limits: returns NULL for a size above
  `KMALLOC_MAX_CACHE_SIZE` and when `can_spin_trylock()` fails; under
  `CONFIG_DEBUG_VM` it warns on gfp bits other than `__GFP_ACCOUNT`,
  `__GFP_ZERO`, `__GFP_NOWARN`, `__GFP_NOMEMALLOC`.
- Verifier: has no preallocation test; a tracing program may use a map
  created with `BPF_F_NO_PREALLOC`.
- `map->objcg`: set only by `bpf_map_save_memcg()`, which `map_create()`
  calls after `map_alloc` has returned.
- `bpf_map_get_memcg()`: returns `root_mem_cgroup` when `map->objcg` is NULL,
  which is the case for `bpf_map_kmalloc_node()` and its siblings called
  from `map_alloc`.
- `bpf_map_area_alloc()`: sets no active memcg and takes `__GFP_ACCOUNT` from
  `bpf_memcg_flags()`, so it is for the creation path only.
- `memcg_bpf_enabled()` false: `bpf_map_save_memcg()` leaves `objcg` NULL and
  `bpf_memcg_flags()` adds nothing.
- Without `CONFIG_MEMCG`: `bpf_map_kmalloc_node()` and its siblings are macros
  for the plain allocators in `include/linux/bpf.h`.
- `bpf_map_kmalloc_node()`: is `kmalloc_node()` plus the memcg switch; it is
  no safer in program context than `kmalloc_node()`.
- **Potentially unsafe usage**: `kmalloc()`, `bpf_map_kmalloc_node()` or
  `kfree()` in an op that a program can reach.
  - Unsafe: when the verifier admits the op for kprobe, tracepoint or perf
    event programs, which can run in NMI or inside the slab allocator;
    `unit_alloc()` and `kmalloc_nolock()` exist to handle that case.
  - Safe: `bpf_mem_cache_alloc()`, as `alloc_htab_elem()` and
    `lpm_trie_node_alloc()` do.
  - Safe: `bpf_map_kmalloc_nolock()` with `kfree_nolock()`, as
    `__bpf_async_init()` in `kernel/bpf/helpers.c` does.
  - Safe: when the verifier admits `map_update_elem` only for the program
    types that `may_update_sockmap()` lists, none of them kprobe, tracepoint
    or perf event, as for `sock_hash_alloc_elem()`.
