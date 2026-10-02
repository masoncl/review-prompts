- `bpf_obj_init_field()` in `include/linux/bpf.h`: zeroes the field, then
  sets a non-zero state for four types: `BPF_REFCOUNT` to 1, `BPF_LIST_HEAD`
  and `BPF_LIST_NODE` with `INIT_LIST_HEAD()`, `BPF_RB_NODE` with
  `RB_CLEAR_NODE()`.
- Map values: `map_check_btf()` in `kernel/bpf/syscall.c` does not parse
  `BPF_LIST_NODE` or `BPF_RB_NODE`, so in a map value only `BPF_LIST_HEAD`
  and `BPF_REFCOUNT` end up non-zero.
- `kernel/bpf/hashtab.c` and `kernel/bpf/arraymap.c`: every call to
  `check_and_init_map_value()` is on an output or staging buffer, none on a
  map element.
- `alloc_htab_elem()`, `pcpu_init_value()`, `prealloc_lru_pop()` and
  `prealloc_init()`: do not call `check_and_init_map_value()`.
- Zeroed memory needs no call: `bpf_selem_alloc()` allocates with
  `__GFP_ZERO` and calls `copy_map_value()` with no
  `check_and_init_map_value()`.
- `bpf_map_area_alloc()` and `__alloc()` in `kernel/bpf/memalloc.c`: also
  zero new memory; `unit_alloc()` returns a recycled object without zeroing
  it.
- Zeroed `BPF_LIST_HEAD` in a map element: initialised on first use, for
  example in `__bpf_list_add()` in `kernel/bpf/helpers.c`.
- `check_and_init_map_value()` on any element that can hold a resource, a
  live array or hash element included: also unsafe; `bpf_obj_init_field()`
  overwrites each field with `memset()` and releases nothing.
- **Unsafe usage**: `check_and_init_map_value()` on an element taken from the
  hash map freelist or from `bpf_mem_cache_alloc()`, even after its fields
  were freed; `free_htab_elem()` recycles with no grace period, and
  `htab_map_update_elem()` with `BPF_F_LOCK` finds elements with
  `lookup_nulls_elem_raw()` and takes their lock, which the call would zero.
  - Safe: a staging buffer that only the caller can reach, as in
    `bpf_map_copy_value()` and `bpf_percpu_hash_copy()`.
  - Safe: a buffer fresh from `bpf_map_kmalloc_node()` and not yet published,
    as in `cgroup_storage_update_elem()` (before its `xchg()`) and
    `bpf_cgroup_storage_alloc()` in `kernel/bpf/local_storage.c`.
- `bpf_obj_new()` in `kernel/bpf/helpers.c`: calls `bpf_obj_init()` on a new
  program-allocated object when `meta` is not NULL; `bpf_obj_new_impl()` only
  calls `bpf_obj_new()`.
