- Which op may call which kfunc is checked at load time, by
  `scx_kfunc_context_filter()` in `kernel/sched/ext/ext.c`. A kfunc that is
  not allowed makes the program fail to load.
- There is no kf_mask field, no scx_kf_allowed() and no enum scx_kf_mask in
  this tree.
- `SCX_CALL_OP()` and its variants (`kernel/sched/ext/internal.h`): the third
  argument is the locked rq or `NULL`; a non-`NULL` one is recorded with
  `update_locked_rq()`. It is not a mask.
- Table: `scx_kf_allow_flags[]`, indexed by `SCX_OP_IDX()`. Its values are
  `SCX_KF_ALLOW_UNLOCKED` and the rest of `enum scx_kf_allow_flags`.
- Op absent from the table, for example `tick` or `cgroup_move`: may call
  only kfuncs of `scx_kfunc_ids_any`, `scx_kfunc_ids_idle` and
  `scx_kfunc_ids_cid`.
- `select_cpu` and `enqueue` allow the same two groups; `dispatch` allows the
  enqueue and dispatch groups.
- By program type, in the same filter:

| Program | Allowed sets |
|---|---|
| `BPF_PROG_TYPE_SYSCALL` | unlocked, select_cpu, idle, any, cid |
| other non-struct_ops | idle, any, cid |
| struct_ops that is not sched_ext | none |
| `sched_ext_ops_cid` struct_ops | per-op table, minus `scx_kfunc_ids_cpu_only` |

- `prog->aux->st_ops` not yet set: the filter allows everything;
  `check_kfunc_call()` runs the filter after `check_attach_btf_id()` has set
  it.
- scx_kf_allowed_on_arg_tasks() is not here; `scx_kf_arg_task_ok()` does that
  job. It has two callers, `scx_bpf_task_cgroup()` and
  `select_cpu_from_kfunc()`.
- Run-time state a kfunc may still read: `scx_locked_rq()` to learn which rq
  lock is held, `current->scx.kf_tasks[]`, `this_rq()->scx.in_select_cpu`, by
  which `select_cpu_from_kfunc()` tells a call from `ops.select_cpu()`, and
  the per-CPU `direct_dispatch_task`, by which `scx_dsq_insert_commit()`
  tells a call from `ops.select_cpu()` or `ops.enqueue()` from one from
  `ops.dispatch()`.
