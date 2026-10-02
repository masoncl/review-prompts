- `bpf_map_copy_value()` generic branch: picks `copy_map_value_locked()` on
  `flags & BPF_F_LOCK` alone; without the flag a value that has a
  `struct bpf_spin_lock` is copied with `copy_map_value()` and the lock is
  not taken.
- Special fields in the copy: hold the initial state written by
  `check_and_init_map_value()`, which is not zero for `BPF_LIST_HEAD` and
  `BPF_REFCOUNT`.
- `BPF_F_CPU` in `bpf_percpu_hash_copy()` and `bpf_percpu_array_copy()`: the
  CPU is `map_flags >> 32`; one `copy_map_value()` and one
  `check_and_init_map_value()` on a buffer of `map->value_size` bytes.
- `BPF_F_CPU` validation: `bpf_map_check_op_flags()` in
  `include/linux/bpf.h`, called from `map_lookup_elem()`, rejects it for maps
  that are not per-CPU and for a CPU that is not possible.
- `BPF_MAP_TYPE_RHASH`: lookup goes through the generic branch of
  `bpf_map_copy_value()` with `rhtab_map_lookup_elem()`.
- `BPF_MAP_TYPE_RHASH` copy-out of its own: `rhtab_delete_elem()` (when
  `copy` is not NULL) and `__rhtab_map_lookup_and_delete_batch()` in
  `kernel/bpf/hashtab.c` call `rhtab_read_elem_value()` then
  `check_and_init_map_value()`.
- **Potentially unsafe usage**: copying a value into a buffer bound for user
  space without `check_and_init_map_value()` on the buffer.
  - Unsafe: when the map type can have a record and the buffer is not
    zeroed; the bytes the copy skipped reach user space as uninitialised
    heap from `kvmalloc()`.
  - Safe: a map type for which `map_check_btf()` in `kernel/bpf/syscall.c`
    rejects every special field, as `bpf_percpu_cgroup_storage_copy()` in
    `kernel/bpf/local_storage.c` and the `map_peek_elem` branch of
    `bpf_map_copy_value()`.
