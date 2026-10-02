- `copy_map_value_long()` with a valid `map->record`: `bpf_obj_memcpy()`
  ignores `long_memcpy` and uses plain `memcpy()` between the fields.
- `copy_map_value_long()` length: `round_up(map->value_size, 8)` with or
  without a record; `bpf_long_memcpy()` runs only when the record is NULL or
  an error pointer.
- `copy_map_value_long()` callers: every one is a read-side loop over all
  possible CPUs that copies a per-CPU slot into a staging buffer, for example
  `bpf_percpu_hash_copy()` and `__bpf_array_map_seq_show()`.
- Per-CPU update paths use `copy_map_value()`: `pcpu_copy_value()`,
  `pcpu_init_value()`, `bpf_percpu_array_update()`,
  `bpf_percpu_cgroup_storage_update()`.
- **Unsafe usage**: `copy_map_value_long()` where source or destination holds
  only `map->value_size` bytes; it reads and writes up to 7 bytes past the end.
  - Safe: slots of `round_up(map->value_size, 8)` bytes, which is what
    `bpf_map_value_size()` in `kernel/bpf/syscall.c` sizes per CPU without
    `BPF_F_CPU`, as in `bpf_percpu_array_copy()`.
  - Safe: `copy_map_value()` when `BPF_F_CPU` is set; `bpf_map_value_size()`
    then returns `map->value_size`, as in `bpf_percpu_hash_copy()`.
- `copy_map_value_locked()` without `BPF_F_LOCK`:
  `bpf_sk_storage_clone_elem()` and `diag_get()` in
  `net/core/bpf_sk_storage.c` call it with `lock_src` true whenever the record
  has `BPF_SPIN_LOCK`.
- `copy_map_value_locked()` from BPF programs: `bpf_map_update_elem()` in
  `kernel/bpf/helpers.c` passes `flags` straight to `map_update_elem`, so
  `array_map_update_elem()` and `htab_map_update_elem()` reach it in program
  context.
- `BPF_RES_SPIN_LOCK`: `copy_map_value_locked()` reads
  `map->record->spin_lock_off` only; `btf_parse_fields()` leaves it at
  `-EINVAL` when the value has only a `struct bpf_res_spin_lock`.
- `BPF_F_LOCK` with a `BPF_UPTR` field: `bpf_pid_task_storage_update_elem()`
  returns `-EOPNOTSUPP`; the locked in-place copy does not call
  `bpf_obj_swap_uptrs()`.
- **Potentially unsafe usage**: `memcpy()` of a whole value when
  `map->record` is a valid record.
  - Unsafe: when source or destination is a map element that programs or
    other syscalls can reach; the destination's lock, timer or kptr is
    overwritten, or the source's is copied out.
  - Safe: source is the caller's buffer and destination is a zeroed buffer
    not yet published, with `check_and_init_map_value()` before publishing,
    as `cgroup_storage_update_elem()` in `kernel/bpf/local_storage.c` does.
