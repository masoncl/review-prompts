- `bpf_obj_cancel_fields()`: exists, defined in `kernel/bpf/syscall.c`; takes
  a `struct bpf_map *` and a value, and only calls
  `bpf_map_free_internal_structs()` in `kernel/bpf/helpers.c`.
- `BPF_TIMER`, `BPF_WORKQUEUE`, `BPF_TASK_WORK`: same calls as
  `bpf_obj_free_fields()` makes (`bpf_timer_cancel_and_free()`,
  `bpf_wq_cancel_and_free()`, `bpf_task_work_cancel_and_free()`); the slot
  ends up NULL.
- Every other kind: not touched.
- Left in the value, where `bpf_obj_free_fields()` would have released it:
  - `BPF_KPTR_REF`, `BPF_KPTR_PERCPU`: the pointer and the reference it owns.
  - `BPF_LIST_HEAD`, `BPF_RB_ROOT`: all linked nodes.
  - `BPF_UPTR`: the pinned page; no caller passes a map that can hold one,
    since `map_check_btf()` allows `BPF_UPTR` only for
    `BPF_MAP_TYPE_TASK_STORAGE`.
  - `BPF_KPTR_UNREF`: the stale pointer value.
- Callers: all in `kernel/bpf/arraymap.c` (update) and
  `kernel/bpf/hashtab.c`, for example the update and delete paths through
  `check_and_cancel_fields()`.
