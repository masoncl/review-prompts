- `btf_field_is_nmi_safe()` in `include/linux/bpf.h`: the tree's per-kind
  context classification for freeing, read only through
  `btf_record_has_nmi_unsafe_fields()` in `check_kfunc_call()`;
  `bpf_obj_free_fields()` itself tests no context, and the timer, wq and task
  work callees can move their cancel to irq_work.

| Kind | `btf_field_is_nmi_safe()` | Easy to miss in `bpf_obj_free_fields()` |
|---|---|---|
| `BPF_SPIN_LOCK`, `BPF_RES_SPIN_LOCK`, `BPF_REFCOUNT` | true | no action |
| `BPF_KPTR_UNREF` | true | `WRITE_ONCE()` of 0; no destructor |
| `BPF_TIMER`, `BPF_WORKQUEUE` | true | cancel is inline unless `defer_timer_wq_op()`, then queued to an irq_work |
| `BPF_TASK_WORK` | true | `task_work_cancel()` runs only from irq_work |
| `BPF_KPTR_REF`, `BPF_KPTR_PERCPU` | false | `field->kptr.dtor` or `__bpf_obj_drop_impl()` runs inline |
| `BPF_UPTR` | false | unpins the page; does not clear the slot |
| `BPF_LIST_HEAD`, `BPF_RB_ROOT` | false | takes the `bpf_spin_lock` with irqs off |
| `BPF_LIST_NODE`, `BPF_RB_NODE` | false (default case) | no action |

- `bpf_obj_drop()` and `bpf_percpu_obj_drop()`: `check_kfunc_call()` in
  `kernel/bpf/verifier.c` rejects them with `-EINVAL` when
  `btf_record_has_nmi_unsafe_fields()` is true for the type and the program is
  an `is_tracing_prog_type()` type, or a non-sleepable `BPF_PROG_TYPE_TRACING`
  program other than `BPF_TRACE_ITER`.
- Local storage: `bpf_selem_unlink()` returns `-EOPNOTSUPP` under `in_nmi()`;
  otherwise `bpf_selem_free()` with `reuse_now` false runs
  `bpf_obj_free_fields()` from `bpf_selem_free_trace_rcu()`, an RCU tasks
  trace callback.
- `migrate_disable()`: not called by `bpf_obj_free_fields()`;
  `__bpf_obj_drop_impl()` requires it from the caller, and `bpf_map_free()` in
  `kernel/bpf/syscall.c` provides it around `map_free`.
- `__bpf_obj_drop_impl()`: frees with `bpf_mem_free_rcu()`; it does not call
  `bpf_mem_free()`.
