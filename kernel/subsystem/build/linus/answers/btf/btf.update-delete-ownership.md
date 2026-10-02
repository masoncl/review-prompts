- check_and_free_fields is not in this tree; `check_and_cancel_fields()` in
  `kernel/bpf/hashtab.c` replaces it and calls `bpf_obj_cancel_fields()`.
- Update and delete: cancel timer, wq and task work only; no path below calls
  `bpf_obj_free_fields()`.

| Path | Function that cancels | When |
|---|---|---|
| array, per-CPU array update | `array_map_update_elem()`, `bpf_percpu_array_update()` | in place, after the copy |
| per-CPU hash, existing key | `pcpu_copy_value()` | in place, under the bucket lock |
| rhash, existing key | `rhtab_map_update_existing()` | in place, after the copy |
| preallocated hash update | `htab_map_update_elem()` | under the bucket lock, after the old element is in `extra_elems` |
| non-preallocated hash update, delete | `htab_elem_free()` | after unlock, before `bpf_mem_cache_free()` |
| preallocated hash delete | `free_htab_elem()` | before `pcpu_freelist_push()` |
| LRU hash update, delete, eviction | `htab_lru_push_free()`, `htab_lru_map_delete_node()` | after unlock |
| rhash delete | `rhtab_delete_elem()` | before `bpf_mem_cache_free_rcu()` |

- Full free with `bpf_obj_free_fields()`:
  - array: `array_map_free()` only.
  - preallocated hash: `htab_free_prealloced_fields()` from `htab_map_free()`
    only.
  - non-preallocated hash and rhash: the allocator destructor
    `htab_mem_dtor()`, `htab_pcpu_mem_dtor()` or `rhtab_mem_dtor()`.
- Allocator destructor: called only from `free_all()` in
  `kernel/bpf/memalloc.c`, when the object returns to slab; `unit_alloc()` and
  `alloc_bulk()` hand an object out again without calling it.
- `free_all()` callers: for example `__free_rcu()`, the RCU tasks trace
  callback, and `drain_mem_cache()` from `bpf_mem_alloc_destroy()`.
- Destructor context: a `struct htab_btf_record` holding a `btf_record_dup()`
  copy, set by `bpf_ma_set_dtor()` from `map_check_btf`; the destructor does
  not use `map->record`.
- Reuse timing: a preallocated element and a `bpf_mem_cache_free()` element
  are reusable at once, with no grace period; a rhash element freed with
  `bpf_mem_cache_free_rcu()` is not reusable before an RCU grace period.
- Guarantee on reuse: only the timer, wq and task work slots were cancelled;
  `BPF_KPTR_REF`, `BPF_KPTR_PERCPU`, `BPF_LIST_HEAD` and `BPF_RB_ROOT` keep
  what the old value held, and `alloc_htab_elem()` does not clear them.
- Timer, wq and task work in a reused element: cancelled at delete, but
  `__bpf_async_init()` does not test whether the element is still linked, so a
  program holding the old value pointer can initialise a timer or wq again.
- `BPF_MAP_TYPE_RHASH`: `rhtab_map_ops` in `kernel/bpf/hashtab.c`; always
  `BPF_F_NO_PREALLOC`, updates an existing key in place.
