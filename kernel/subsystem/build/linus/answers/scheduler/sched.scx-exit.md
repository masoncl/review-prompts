- Scope of an exit: `scx_error()` and `scx_exit()` act on one
  `struct scx_sched`; that scheduler and its descendants are disabled, the rest
  of the hierarchy keeps running. Everything is torn down only when the
  target is the root.
- Exit kinds beyond the seven well-known ones, in `enum scx_exit_kind`
  (`kernel/sched/ext/internal.h`):

| Kind | Raised by |
|---|---|
| `SCX_EXIT_PARENT` | `scx_propagate_exit_irq_workfn()`, on every descendant of a scheduler that exits |
| `SCX_EXIT_PARENT_KILL` | `scx_bpf_sub_kill_bstr()`, a parent evicting a direct child |
| `SCX_EXIT_ERROR_REENQ` | `scx_do_enqueue_task()`, a task re-enqueued more than `SCX_REENQ_MAX_REPEAT` times without running |
| `SCX_EXIT_ERROR_RESCUE` | `scx_rescue_check_overload()` in `kernel/sched/ext/sub.c` |

- `SCX_EXIT_UNREG_KERN`: also raised on a sub-scheduler when its cgroup goes
  offline, in `scx_cgroup_lifetime_notify()`.
- SysRq-D (`sysrq_handle_sched_ext_dump()`): dumps state only, disables
  nothing. SysRq-S and the lockup and RCU-stall hooks act on `scx_root`.
- `scx_disable_workfn()`: calls `scx_sub_disable()` if the scheduler has a
  parent, else `scx_root_disable()`.
- Watchdog timeout: per scheduler, `watchdog_timeout` in `struct scx_sched`;
  one shared work runs at half the shortest one (`refresh_watchdog()`).
- `check_rq_for_timeouts()`: compares against the timeout of the task's own
  scheduler, but exits `dsq->sched` when the task sits on a non-local DSQ
  that has an owner, for example an ancestor's bypass DSQ.
- `scx_tick()`: uses the root's `watchdog_timeout` and exits the root.
- Names that are not in this tree:

| Not here | This tree |
|---|---|
| scx_ops_error() | `scx_error()` |
| scx_watchdog_timeout | `watchdog_timeout` in `struct scx_sched` |
| scx_bypass_depth | `bypass_depth` in `struct scx_sched` |
| balance_one() | `dispatch_one()`, `scx_dispatch_sched()` |

- `SCX_RQ_BYPASSING`: not in `enum scx_rq_flags`; only
  `tools/sched_ext/include/scx/` still names it. Bypass state is
  `SCX_SCHED_PCPU_BYPASSING` in `struct scx_sched_pcpu`, per scheduler and
  per CPU; test it with `scx_bypassing(sch, cpu)`.
- `scx_bypass()` (`kernel/sched/ext/ext.c`): its callers are the root and
  sub-scheduler enable and disable paths, plus `scx_fail_parent()` and
  `scx_pm_handler()`. The watchdog, hotplug and the bypass load balancer do
  not call it.
- `scx_bypass()` on a scheduler: also raises `bypass_depth` of every
  descendant, and cycles only tasks whose scheduler is in that subtree.
- `scx_link_sched()`: refuses to attach a child under a parent whose
  `bypass_depth` is non-zero (`-EBUSY`).
- Wakeup while bypassing: `select_task_rq_scx()` returns `prev_cpu`; it does
  not call `scx_select_cpu_dfl()`.
- Enqueue while bypassing: `bypass_enq_target_dsq()` picks the per-CPU bypass
  DSQ (`scx_bypass_dsq()`, id `SCX_DSQ_BYPASS`) of the task's CPU.
- Bypassing sub-scheduler: its tasks go to the bypass DSQ of the nearest
  ancestor that is not bypassing, or the root's if all are.
- Pick while bypassing: `dispatch_one()` uses the local DSQ if it has tasks;
  otherwise `scx_dispatch_sched()` consumes the scheduler's global DSQ, then
  the bypass DSQ of this CPU, and returns before `ops.dispatch()`.
- Host of a bypassing descendant: not bypassing itself, it consumes its
  bypass DSQ on every `SCX_BYPASS_HOST_NTH`-th dispatch and again when
  `ops.dispatch()` produced nothing; see `scx_bypass_dsp_enabled()`.
- Ops skipped while bypassing: `select_cpu`, `enqueue`, `dispatch`, `tick`,
  `update_idle`, `core_sched_before`, `sub_ecaps_updated`. `ops.runnable()`,
  `ops.running()`, `ops.stopping()` and `ops.quiescent()` are still called.
- `scx_prio_less()` while bypassing: a task with `on_cpu` set orders last,
  the rest by `p->scx.runnable_at`.
- After a root disable: `scx_root_disable()` gives every task the class from
  `scx_setscheduler_class()`. That is `fair_sched_class`, except a task in
  `stop_sched_class` stays there and a task whose `p->prio` is in the RT or
  deadline range gets that class.
- After a sub-scheduler disable: tasks keep their class;
  `scx_rehome_task()` moves them to the parent scheduler.
- `scx_sub_disable()` when the parent's `ops.init_task()` fails: the parent is
  failed with `scx_error()` too (`scx_fail_parent()`).
