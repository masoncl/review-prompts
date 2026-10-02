- `p == current`: `try_to_wake_up()` takes neither `p->pi_lock` nor a rq lock;
  it calls `ttwu_do_wakeup()` under `guard(preempt)`.
- Match on `p->saved_state` only: `ttwu_state_match()` stores `TASK_RUNNING`
  in `p->saved_state`; `try_to_wake_up()` returns 1 with no enqueue and no
  change to `p->__state`.
- `ttwu_runnable()`: tests `p->is_blocked`; only inside that test does it
  re-enqueue a `p->se.sched_delayed` task with `ENQUEUE_DELAYED`.
- `proxy_needs_return()` (`CONFIG_SCHED_PROXY_EXEC`): when
  `task_cpu(p) != p->wake_cpu` it can call `block_task()` with `TASK_WAKING`
  and make `ttwu_runnable()` return 0.
- `ttwu_runnable()` returning 0 for a queued task: `try_to_wake_up()` goes on
  to `select_task_rq()` and `ttwu_queue()`, so a queued task can migrate on
  wake-up.
- `p->on_rq` 0 and `p->on_cpu` set: the waker first tries
  `ttwu_queue_wakelist()` towards `task_cpu(p)`; it spins in
  `smp_cond_load_acquire()` only if that is refused.
- There is no WF_ON_CPU here; `ttwu_queue_cond()` takes no flags and applies
  the same tests to the `p->on_cpu` attempt and to `ttwu_queue()`.
- `ttwu_queue_cond()` tests, in order:

  | Test | Result |
  |---|---|
  | `scx_allow_ttwu_queue()` false | no hand-off |
  | `p->sched_class == &stop_sched_class` (`CONFIG_SMP`) | no hand-off |
  | target not `cpu_active()` | no hand-off |
  | target not in `p->cpus_ptr` | no hand-off |
  | target does not `cpus_share_cache()` with this CPU | hand-off |
  | target is this CPU | no hand-off |
  | target `rq->nr_running` is 0 | hand-off |
  | otherwise | no hand-off |

- `scx_allow_ttwu_queue()`: false only for a task in `ext_sched_class` whose
  scheduler lacks `SCX_OPS_ALLOW_QUEUED_WAKEUP`.
- Idle test: `ttwu_queue_cond()` reads `rq->nr_running` only; it does not call
  `available_idle_cpu()`.
- Hand-off list: `__ttwu_queue_wakelist()` queues `p->wake_entry.llist` with
  `__smp_call_single_queue()`; `struct rq` has no wake-list member of its own.
- `p->pi_lock` on hand-off: held until `ttwu_queue()` or
  `ttwu_queue_wakelist()` has returned; `sched_ttwu_pending()` later enqueues
  under the target rq lock only, with `p->__state` at `TASK_WAKING`.
- `p->sched_remote_wakeup`: records `WF_MIGRATED`, not that the waker is
  remote; `sched_ttwu_pending()` turns it back into `WF_MIGRATED` for
  `ttwu_do_activate()`.
- `psi_ttwu_dequeue()` (`CONFIG_PSI`): on a wake-up that changes CPU it takes
  the old rq lock through `__task_rq_lock()` when `p->psi_flags` is set,
  before the target rq lock is taken.
