- `BPF_MAP_TYPE_RHASH`: allowed for the lock kinds, for `BPF_TIMER`,
  `BPF_WORKQUEUE`, `BPF_TASK_WORK`, and for the kptr kinds and `BPF_REFCOUNT`;
  not for `BPF_LIST_HEAD` or `BPF_RB_ROOT`.
- `BPF_TASK_WORK`: same map types as `BPF_TIMER` and `BPF_WORKQUEUE`.
- `BPF_MAP_TYPE_CGROUP_STORAGE`: listed only for the lock kinds.
- `BPF_MAP_TYPE_PERCPU_CGROUP_STORAGE`: listed for no kind.
- `BPF_F_LOCK` update of an existing key in `htab_map_update_elem()`: both
  in-place paths return after `copy_map_value_locked()` and do not call
  `bpf_obj_cancel_fields()`; `array_map_update_elem()` and
  `rhtab_map_update_existing()` call it after the same locked copy.
- `bpf_obj_free_fields()`: runs once, when the element memory is released.

| Map | Where `bpf_obj_free_fields()` runs |
|---|---|
| non-preallocated hash, rhash | destructor set by `bpf_ma_set_dtor()`, run from `free_all()` in `kernel/bpf/memalloc.c` |
| preallocated hash, LRU hash | `htab_free_prealloced_fields()` from `htab_map_free()` |
| array, percpu array | `array_map_free()` |
| local storage | `bpf_selem_free()`, `bpf_selem_free_trace_rcu()`, `bpf_selem_unlink_nofail()` |
