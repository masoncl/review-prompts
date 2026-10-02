- `BPF_RES_SPIN_LOCK`: a kind of its own (`struct bpf_res_spin_lock`); holds
  nothing; `bpf_obj_free_fields()` does nothing for it.
- `BPF_TASK_WORK`: a kind (`struct bpf_task_work`); holds a reference on a
  `struct bpf_task_work_ctx`; released by `bpf_task_work_cancel_and_free()`.
- `BPF_GRAPH_NODE`: `BPF_RB_NODE | BPF_LIST_NODE` only; `BPF_REFCOUNT` is not
  part of it.
- `BPF_UPTR`: not part of `BPF_KPTR`; code that means both passes
  `BPF_KPTR | BPF_UPTR`, as `check_mem_access()` does.
- Map value: may hold every kind except `BPF_LIST_NODE` and `BPF_RB_NODE`; see
  the mask in `map_check_btf()`.
- Allocated object: may hold locks, graph roots and nodes, `BPF_REFCOUNT` and
  `BPF_KPTR`; not `BPF_TIMER`, `BPF_WORKQUEUE`, `BPF_TASK_WORK` or `BPF_UPTR`;
  see the mask in `btf_parse_struct_metas()`.
- Kind outside the mask: `btf_get_field_type()`, or `btf_find_kptr()` for a
  tagged pointer, ignores it, so the member is not recorded and is treated as
  plain data.
