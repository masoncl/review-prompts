- `can_be_sleepable()` in `kernel/bpf/verifier.c`: besides fentry, fexit,
  fmod_ret and iter, accepts `BPF_PROG_TYPE_TRACING` with `BPF_TRACE_RAW_TP`,
  `BPF_TRACE_FSESSION`, `BPF_TRACE_FENTRY_MULTI`, `BPF_TRACE_FEXIT_MULTI` and
  `BPF_TRACE_FSESSION_MULTI`.
- `BPF_PROG_TYPE_RAW_TRACEPOINT` and `BPF_PROG_TYPE_TRACEPOINT`: accepted by
  `can_be_sleepable()`, like `BPF_PROG_TYPE_KPROBE` and
  `BPF_PROG_TYPE_STRUCT_OPS`.
- `BPF_PROG_TYPE_LSM`: accepted unless `expected_attach_type` is
  `BPF_LSM_CGROUP`.
- `BPF_PROG_TYPE_EXT` and `BPF_PROG_TYPE_RAW_TRACEPOINT_WRITABLE`: not
  accepted, so a sleepable program of either type fails to load.
- `BPF_PROG_TYPE_SYSCALL`: never reaches `can_be_sleepable()`;
  `check_attach_btf_id()` returns first, and rejects one that is not
  sleepable.
- Message from `check_attach_btf_id()` when `can_be_sleepable()` is false:
  "Program of this type cannot be sleepable".
- `btf_id_allow_sleepable()`: returns `-EINVAL` unless `btf_is_kernel()`, so a
  sleepable fentry, fexit or fsession program cannot attach to another BPF
  program.
- `check_attach_sleepable()` with `CONFIG_FUNCTION_ERROR_INJECTION`: accepts a
  target that is on the error-injection list and not in
  `btf_non_sleepable_error_inject`.
- `check_attach_sleepable()` without `CONFIG_FUNCTION_ERROR_INJECTION`: accepts
  only names that pass `has_arch_syscall_prefix()`.
- Multi attach types: the load-time placeholder id passes
  `btf_id_allow_sleepable()`; each real target is checked by
  `bpf_check_attach_btf_id_multi()` when the link is created.
- Checks made at attach:

| Program | Where | Sleepable program accepted when |
|---|---|---|
| `BPF_PROG_TYPE_KPROBE` | `__perf_event_set_bpf_prog()` | event is a uprobe |
| `BPF_PROG_TYPE_KPROBE` | `bpf_kprobe_multi_link_attach()` | never |
| `BPF_PROG_TYPE_TRACEPOINT` | `__perf_event_set_bpf_prog()` | syscall tracepoint |
| `BPF_PROG_TYPE_RAW_TRACEPOINT`, `BPF_TRACE_RAW_TP` | `bpf_raw_tp_link_attach()` | `tracepoint_is_faultable()` |
| `BPF_TRACE_ITER` | `bpf_iter_link_attach()` | `bpf_iter_target_support_resched()` |

- `BPF_TRACE_RAW_TP`: `bpf_check_attach_target()` also tests
  `tracepoint_is_faultable()` at load.
- `in_sleepable()`: returns only `env->cur_state->in_sleepable`; it does not
  read `prog->sleepable`.
- `env->cur_state->in_sleepable`: set per verification state, in
  `do_check_common()` from its `is_sleepable` argument (`prog->sleepable` in
  `do_check_main()`) and in `push_async_cb()` from `is_async_cb_sleepable()`.
- `is_async_cb_sleepable()`: false for a `struct bpf_timer` callback, true for
  a `struct bpf_wq` or task-work callback, whatever `prog->sleepable` is.
- Global subprogs: `do_check_subprogs()` verifies one once for each context
  (sleepable, non-sleepable) it is called from, taken from
  `in_sleepable_context()` at the call; see `called[]` and `verified[]` in
  `struct bpf_func_info_aux`.
- `in_sleepable_context()`: `!in_rcu_cs()`; false in a non-sleepable state and
  also inside an RCU, preempt-disabled or IRQ-saved region or with a lock held.
- `check_helper_call()`: tests `might_sleep` against `in_sleepable_context()`,
  not `in_sleepable()`.
- `check_kfunc_call()`: tests `KF_SLEEPABLE` twice, first against
  `in_sleepable()` and, after the RCU and preempt counters are updated,
  against `in_sleepable_context()`.
- `bpf_copy_from_user_proto`: `bpf_base_func_proto()` returns it whatever
  `prog->sleepable` is; only the `might_sleep` test rejects the call.
- Proto chosen by `prog->sleepable`: for example `BPF_FUNC_get_task_stack` in
  `bpf_base_func_proto()` picks `bpf_get_task_stack_sleepable_proto`.
- `specialize_kfunc()`: a third marking; a kfunc with no `KF_SLEEPABLE` gets
  its implementation chosen from `insn_aux_data[].non_sleepable`, for example
  `bpf_arena_alloc_pages()` and `bpf_arena_alloc_pages_non_sleepable()`.
- Maps: the switch in `check_map_prog_compatibility()` is wider than its
  error message, for example `BPF_MAP_TYPE_PROG_ARRAY`, `BPF_MAP_TYPE_QUEUE`
  and `BPF_MAP_TYPE_LPM_TRIE` are allowed.
- `__bpf_prog_map_compatible()` in `kernel/bpf/core.c`: an owner-tracked map
  such as a prog array takes only programs whose `sleepable` matches the first
  one.
