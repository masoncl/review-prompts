- `__bpf_prog_enter_sleepable()`: makes no recursion check;
  `__bpf_prog_enter_sleepable_recur()` adds it with
  `bpf_prog_get_recursion_context()`, and `bpf_trampoline_enter()` picks by
  `bpf_prog_check_recur()`.
- Tasks Trace RCU: is SRCU on `rcu_tasks_trace_srcu_struct`; see
  `include/linux/rcupdate_trace.h`, where `call_rcu_tasks_trace()` is
  `call_srcu()`.
- Free paths such as `__bpf_prog_array_free_sleepable_cb()`,
  `bpf_selem_free_trace_rcu()` and `__free_rcu()` in `kernel/bpf/memalloc.c`:
  run from `call_rcu_tasks_trace()` and free in that callback, with no chained
  `call_rcu()`.
- `srcu_readers_active_idx_check()` in `kernel/rcu/srcutree.c`: runs
  `synchronize_rcu()` or `synchronize_rcu_expedited()` for
  `SRCU_READ_FLAVOR_SLOWGP`, which is why one wait covers non-sleepable
  programs too.
- Hash map values: `htab_elem_free()` uses `bpf_mem_cache_free()`, so a value
  pointer held across a sleep stays valid memory but may now belong to another
  element.
- `KF_RCU` argument: a trusted register passes without any RCU region; see
  the `KF_ARG_PTR_TO_BTF_ID` case in `check_kfunc_args()`.
- Runners other than the trampoline: take `rcu_read_lock_trace()` or
  `rcu_read_lock_tasks_trace()`, and `migrate_disable()`, themselves, for
  example `bpf_iter_run_prog()` and `__bpf_trace_run()`; search for
  `rcu_read_lock_trace`, `rcu_read_lock_tasks_trace` and
  `guard(rcu_tasks_trace)`.
- `bpf_prog_run_array_sleepable()` and `bpf_prog_run_array_uprobe()`: take
  `rcu_read_lock()` around each non-sleepable program in the array.
- **Potentially unsafe usage**: a helper or kfunc dereferencing an
  RCU-protected pointer without taking `rcu_read_lock()` itself.
  - Unsafe: when a sleepable program can call it outside an RCU region and the
    object is freed after `call_rcu()` or `kfree_rcu()` alone; the caller holds
    only `rcu_read_lock_trace()`.
  - Safe: the callee takes `rcu_read_lock()` and pins the object before
    unlocking, as `bpf_task_from_pid()` does.
  - Safe: the kfunc is flagged `KF_RCU_PROTECTED`, as `bpf_iter_task_new()`
    is; `check_kfunc_call()` rejects the call unless `in_rcu_cs()`.
  - Safe: the memory returns to slab only after Tasks Trace and the callee
    asserts `bpf_rcu_lock_held()`, as `__htab_map_lookup_elem()` does for
    elements that `__free_rcu()` frees.
- **Potentially unsafe usage**: freeing with `kfree_rcu()` or `call_rcu()`
  alone an object of a kind sleepable programs use.
  - Unsafe: when the object was published where a running sleepable program
    can find it and the code that reads it there takes no `rcu_read_lock()`;
    `__bpf_prog_enter_sleepable()` holds no classic RCU.
  - Safe: the object was never published, as the `alloc_selem` that
    `bpf_local_storage_update()` passes to `bpf_selem_free()` with `reuse_now`
    true.
  - Safe: the reader takes `rcu_read_lock()` before it loads the pointer, as
    `bpf_task_work_acquire_ctx()` does for the ctx that
    `bpf_task_work_destroy()` frees with `kfree_rcu()`.
  - Safe: `call_rcu_tasks_trace()`, as `bpf_selem_free()` does with
    `reuse_now` false.
