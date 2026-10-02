- `bpf_map_put()` with `free_after_mult_rcu_gp`: calls
  `call_rcu_tasks_trace()` only; no `call_rcu()` follows, and there is no
  bpf_map_free_mult_rcu_gp() or rcu_trace_implies_rcu_gp() in this tree.
- `bpf_map_put()` on an ordinary map: waits for no grace period and goes
  straight to `bpf_map_free_in_work()`.
- `free_after_mult_rcu_gp` and `free_after_rcu_gp`: set only by
  `bpf_map_fd_put_ptr()` in `kernel/bpf/map_in_map.c`, on an inner map, when
  `need_defer` is true.
- Choice of flag: by the outer map's `sleepable_refcnt`, not the inner
  map's.
- `need_defer` false: `fd_htab_map_free()` and the error path of
  `bpf_fd_htab_map_update_elem()` pass it, so those puts set neither flag.
- `sleepable_refcnt`: a third count; `__add_used_map()` and
  `bpf_prog_bind_map()` raise it for a sleepable program and
  `__bpf_free_used_maps()` drops it.
- `bpf_map_put()`: warns if `sleepable_refcnt` is nonzero at the last put.
- `bpf_map_free_in_work()`: queues on `system_dfl_wq` with `queue_work()`.
- `bpf_map_free_deferred()` order: `security_bpf_map_free()`,
  `bpf_map_release_memcg()`, `bpf_map_owner_free()`, `bpf_map_free()`.
- `bpf_map_free()`: runs `map_free` under `migrate_disable()`, then
  `btf_record_free()` and `btf_put()`.
- `usercnt` holders: besides fds and bpffs pins, map iterators and sockmap
  links; search for `bpf_map_get_with_uref()` and `bpf_map_inc_with_uref()`.
- `bpf_map_get_fd_by_id()`: calls `__bpf_map_inc_not_zero(map, true)` under
  `map_idr_lock`, which tests `refcnt` only.
- `usercnt` can therefore go from 0 back to 1 while a program holds `refcnt`,
  and `map_release_uref` can run more than once for one map.
- `bpf_map_inc_not_zero()`: takes no uref and asserts
  `rcu_read_lock_held()`.
- `map_release_uref`: `cgroup_array_map_ops` and `perf_event_array_map_ops`
  have none; perf event array uses `map_release`, called per file from
  `bpf_map_release()`.
- `map_release_uref` on hash and array: `bpf_map_free_internal_structs()`
  frees `BPF_TIMER`, `BPF_WORKQUEUE` and `BPF_TASK_WORK` fields only, not
  kptrs.
- Per-CPU hash and per-CPU array ops: have no `map_release_uref`.
- `prog_array_map_clear()`: takes `bpf_map_inc()` and calls
  `schedule_work()`; the slots may still be set when `bpf_map_put_uref()`
  returns.
- `bpf_mem_alloc_destroy()`: with callbacks in flight, `destroy_mem_alloc()`
  copies the allocator and defers `rcu_barrier()` and
  `rcu_barrier_tasks_trace()` to a work item, so `map_free` does not wait.
