- Values and owners: models have these right; see the comment above
  `enum scx_ops_state` in `kernel/sched/ext/internal.h`.
- There is no do_enqueue_task() or dispatch_enqueue() here;
  `scx_do_enqueue_task()` and `scx_dispatch_enqueue()` in
  `kernel/sched/ext/ext.c` do those jobs.
- `scx_dispatch_enqueue()`: stores `SCX_OPSS_NONE` with release only when the
  caller passed `SCX_ENQ_CLEAR_OPSS`.
- Order inside `scx_dispatch_enqueue()`: the custody flag is updated and
  `ops.dequeue()` is called before the release store. A waiter in
  `ops_dequeue()` writes `p->scx.flags` as soon as it sees `NONE`.
- `finish_dispatch()`: reads `ops_state` with plain `atomic_long_read()`; it
  claims the task with a cmpxchg from `QUEUED` to `DISPATCHING` before it
  dispatches it.
- `finish_dispatch()` on `QUEUED` with matching qseq: still drops the
  dispatch if `scx_task_on_sched()` says the task is not on the dispatching
  scheduler.
- `ops_dequeue()` on `SCX_OPSS_QUEUEING`: `BUG()`, it does not wait.
- `ops_dequeue()` on `SCX_OPSS_QUEUED`: if `SCX_TASK_IN_CUSTODY` is clear, a
  dispatcher is between `task_leave_custody()` and its final store, so it
  retries with `cpu_relax()`. Otherwise it tries cmpxchg to `NONE`.
- `ops.dequeue()` in `ops_dequeue()`: called after the switch, for any state
  found, and only if `task_leave_custody()` returns true. It is not called
  before the cmpxchg.
- `scx_reenq_wait_dispatching()`: a second waiter on `DISPATCHING`. A task
  can be found on a DSQ while still `DISPATCHING`, because the dispatcher
  stores `NONE` after it drops the DSQ lock. The re-enqueue paths call it
  before `scx_dispatch_dequeue()` or `dispatch_dequeue_locked()`.
- **Unsafe usage**: acquiring the lock of a task's rq while the task is
  `SCX_OPSS_DISPATCHING`; `ops_dequeue()` spins on that state with that lock
  held.
  - Safe: the rq lock was already held when `DISPATCHING` was claimed and no
    other is taken, as in `dispatch_to_local_dsq()` when the current rq is
    both source and destination.
  - Safe: set `p->scx.holding_cpu`, store `NONE` with release, then switch
    locks and test `holding_cpu` again, as `dispatch_to_local_dsq()` does;
    `scx_dispatch_dequeue()` resets it to -1 when dequeue won.
