# Scheduler Subsystem Details

## Runqueue Locking

- Runqueue locks are `raw_spinlock_t` (never sleeps, even on PREEMPT_RT)
- Multi-runqueue operations must lock in consistent order to prevent deadlock
- `double_rq_lock()` / `double_rq_unlock()` handle ordering automatically
  (swaps to ascending order internally via `rq_order_less()`)
- `lockdep_assert_rq_held()` validates rq lock is held in accessors
- `task_rq(p)` expands to `cpu_rq(task_cpu(p))`. Without pinning or holding
  `pi_lock` / rq lock, the task can migrate after `task_cpu(p)` is read,
  so the caller gets CPU A's runqueue while the task is now on CPU B.
- Never release rq lock with a task in inconsistent state — `on_rq`, the
  RB-tree, and `p->__state` must all agree before the lock is dropped.
  Other CPUs observe these fields immediately after unlock:
  - Task in tree but `on_rq == 0`: `try_to_wake_up()` sees `on_rq == 0` and
    calls `activate_task()` → double enqueue corrupts the RB-tree
  - `on_rq == 1` but not in tree: `try_to_wake_up()` sees `on_rq == 1` and
    skips enqueue, but `pick_next_task` never finds the task — permanently lost
  - `TASK_RUNNING` with `on_rq == 0`: `try_to_wake_up()` sees `TASK_RUNNING`
    and returns early (no wakeup needed) — task hangs forever with no way to
    recover

## Task State Transitions

- `set_current_state()` includes a barrier so the state write is ordered
  relative to subsequent memory accesses (the condition check)
- Voluntary sleep pattern: set state BEFORE checking the condition, otherwise
  a wakeup between the check and the state change is lost

```c
// CORRECT — state set before condition check
set_current_state(TASK_UNINTERRUPTIBLE);
if (!condition)
    schedule();
set_current_state(TASK_RUNNING);

// WRONG — lost wakeup if condition changes between check and set_current_state
if (!condition) {
    set_current_state(TASK_UNINTERRUPTIBLE);  // wakeup already happened
    schedule();                                // sleeps forever
}
```

- `TASK_RUNNING` is the only state where a task can be on a runqueue
- `TASK_DEAD` requires special handling — task cannot be rescheduled
- `wake_up_process()` handles state races internally (safe for any task state)

## CPU Affinity and Migration

- `set_cpus_allowed_ptr()` changes a task's allowed CPU mask
- `kthread_bind()` restricts a kthread to a specific CPU
- Migration must respect `cpumask_subset()` against allowed CPUs
- Check `is_migration_disabled()` before migrating a task
- `stop_one_cpu()` may be needed for forced migration
- CPU hotplug requires special care — tasks must not be migrated to a CPU
  being taken offline
- Migration-disabled sections cannot block or sleep

## CFS (SCHED_NORMAL / SCHED_BATCH / SCHED_IDLE)

### EEVDF Algorithm

- Selects the eligible task (positive lag = owed service) with the earliest
  virtual deadline
- Virtual deadline: `vd = vruntime + vslice` where `vslice = calc_delta_fair(slice, se)`
  computes `slice * NICE_0_LOAD / weight` (source comment: `vd_i = ve_i + r_i/w_i`)
- Base slice: `sysctl_sched_base_slice` (default 700μs); deadline updated when
  `vruntime >= deadline`

### Key Fields

- `vruntime`: per-entity monotonic counter of weighted CPU time; must be
  normalized when migrating between CPUs
- `min_vruntime`: per-cfs_rq monotonic clock tracking progress; must never
  decrease
- `vlag`: tracks service deficit/surplus; `vlag = V - vruntime` where V is
  the weighted average vruntime (`avg_vruntime`); preserved across
  enqueue/dequeue by `place_entity()`
- `on_rq`: must be 1 iff entity is in the RB-tree; double enqueue or
  mismatch corrupts the runqueue
- Load weight: derived from nice value via `prio_to_weight[]`; ~10% change
  per nice level

### RB-Tree Structure

The RB-tree is sorted by deadline and augmented with `min_vruntime` per node,
enabling O(log n) eligibility pruning in `__pick_eevdf()`. A subtree can be
skipped entirely if its `min_vruntime` shows no eligible entities.

### PELT (Per-Entity Load Tracking)

- `update_load_avg()` must be called BEFORE any entity state change
  (enqueue/dequeue/migration) to maintain hierarchy consistency
- Tracks a decaying average of utilization per entity and per cfs_rq
- On migration: `DO_ATTACH` attaches load to new CPU, `DO_DETACH` detaches
  from old CPU

### CFS Bandwidth

- Group throttling uses `cfs_rq->runtime_remaining`
- Must properly dequeue on throttle, enqueue on unthrottle
- Hierarchical: parent throttle affects all children

## Real-Time (SCHED_FIFO / SCHED_RR)

- Priority range: 1–99 (userspace); higher number = higher priority.
  Kernel internal priority is inverted (`MAX_RT_PRIO - 1 - rt_priority`)
- RT bandwidth: `sched_rt_runtime_us` / `sched_rt_period_us` prevent CPU
  monopolization (default 95% limit — 950ms per 1000ms period)
- Tasks throttled when bandwidth exhausted; check `sched_rt_runtime()`

## Deadline (SCHED_DEADLINE)

- Invariant: `runtime ≤ deadline ≤ period`
- Admission control: tasks can be created while
  `Σ(runtime_i / period_i) ≤ M × (rt_runtime / rt_period)` where M is CPU count
  in the root domain
- CBS (Constant Bandwidth Server) enforces bandwidth isolation
- Global Earliest Deadline First (GEDF): on an M-CPU system, the M tasks
  with earliest deadlines should be running
- Throttling: task blocked when runtime exhausted, unblocked at next period
  (replenishment)
- DL tasks tracked per root domain for migration decisions

## sched_ext (SCHED_EXT — BPF Extensible Scheduler)

- Scheduler behavior defined by BPF programs via ops callbacks (`select_cpu`,
  `enqueue`, `dispatch`, etc.)
- Dispatch queues (DSQ): tasks queued in local (per-CPU), global, or custom
  DSQs; can use FIFO or PRIQ (vtime) ordering but not mixed
- `ops_state` tracking: atomic `p->scx.ops_state` prevents concurrent BPF
  operations on the same task; transitions: NONE → QUEUEING → QUEUED → DISPATCHING
- Direct dispatch: optimization allowing enqueue path to dispatch directly to
  local DSQ via per-CPU `direct_dispatch_task` marker
- Failsafe: watchdog timeout, `scx_error()`, and SysRq-S all trigger
  automatic revert to CFS

## Priority Inheritance

- When a high-priority task blocks on a lock held by a low-priority task,
  the lock holder temporarily inherits the blocked task's priority
- PI chain must be updated atomically; checked for cycles to detect deadlock
- RT mutex is the primary use case
- `pi_lock` protects PI state; must be held when traversing the chain

## Quick Checks

- `preempt_disable()` / `preempt_enable()` must always be balanced
- `set_task_cpu()` only safe during migration with proper locks held
- Never call `schedule()` with preemption disabled or non-rq locks held
- Never enqueue a task that is already on a runqueue
