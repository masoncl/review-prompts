# Scheduler Subsystem Delta

## Scheduler Patterns [SCHED]

| Pattern ID | Check | Risk | Details |
|------------|-------|------|---------|
| SCHED-001 | Runqueue lock ordering | Deadlock | Multi-runqueue operations need consistent lock ordering |
| SCHED-002 | Task state transitions | Race conditions | TASK_RUNNING transitions require proper barriers |
| SCHED-003 | CPU affinity violations | System instability | Migration must respect cpumask and hotplug state |
| SCHED-004 | Load balancing invariants | Performance degradation | Per-entity load must match hierarchy aggregation |
| SCHED-005 | Bandwidth enforcement | Starvation/DoS | RT/DL throttling must prevent monopolization |
| SCHED-006 | Priority inheritance | Priority inversion | PI chain updates need proper locking |
| SCHED-007 | Context switch atomicity | Data corruption | switch_to() and surrounding code is non-preemptible |
| SCHED-008 | Per-CPU runqueue access | Data corruption | Runqueue access requires proper locking |

## Runqueue Locking
- **Lock ordering**: Always lock runqueues in ascending order to prevent deadlock
- **Double runqueue lock**: Use `double_rq_lock()`/`double_rq_unlock()` for locking 2 runqueues at once
- **Lock release timing**: Don't release rq lock with task in inconsistent state
- **Raw spinlocks**: Runqueue locks are raw_spinlock_t (never sleep, even on RT)

## Task States and Transitions
- **State changes**: Use `set_current_state()` with proper barriers
- **Wakeup races**: Check task->state after adding to runqueue
- **TASK_DEAD**: Special handling required, task cannot be rescheduled
- **TASK_RUNNING**: Only state where task can be on runqueue
- **Voluntary sleep**: Must set state before condition check to avoid lost wakeups

## CPU Affinity and Migration
- **cpumask validation**: Check cpumask_subset() against allowed CPUs
- **Hotplug coordination**: Migration during hotplug needs special care
- **Per-CPU kthreads**: Use `kthread_bind()` or `set_cpus_allowed_ptr()`
- **Active migration**: May need to stop_one_cpu() for forced migration
- **Migration disabled**: Check `is_migration_disabled()` before migration

## Scheduling Classes
### Real-Time (SCHED_FIFO/SCHED_RR)
- **RT bandwidth**: `sched_rt_runtime_us` and `sched_rt_period_us` prevent CPU monopolization
- **RT throttling**: Tasks may be throttled when bandwidth exhausted
- **Global RT throttle**: Check `sched_rt_runtime()` for enforcement
- **Priority range**: 1-99, higher number = higher priority for userspace (for kernel priorities are inverted)

### Deadline (SCHED_DEADLINE)
- **Admission control**: For a root_domain comprising M CPUs, -deadline tasks can be created while the sum of their bandwidths stays below M * (sched_rt_runtime_us / sched_rt_period_us)
- **Deadline invariants**: runtime ≤ deadline ≤ period
- **CBS (Constant Bandwidth Server)**: Enforces bandwidth isolation
- **Migration**: DL tasks migrate to maintain GEDF SMP invariant - on an M CPUs system the M earliest DL tasks are executing on a CPU
- **Throttling**: Task blocked when runtime exhausted, unblocked at replenishment instant (new period)

 ### CFS (SCHED_NORMAL/SCHED_BATCH/SCHED_IDLE)
- **EEVDF algorithm**: Selects eligible task (positive lag = owed service) with earliest virtual deadline `vd = vruntime + slice/weight`
- **vruntime**: Per-entity monotonic counter of weighted CPU time; must be normalized when migrating between CPUs
- **min_vruntime**: Per-cfs_rq monotonic clock tracking progress; MUST NEVER decrease
- **Lag (vlag)**: Tracks service deficit/surplus `vlag = avg_vruntime - vruntime`; preserved across enqueue/dequeue by place_entity()
- **Load weight**: Derived from nice value via `prio_to_weight[]`; affects vruntime rate and CPU share (~10% per nice level)
- **PELT updates**: Must call update_load_avg() BEFORE any entity state change (enqueue/dequeue/migration) to maintain hierarchy consistency
- **RB-tree**: Sorted by deadline, augmented with min_vruntime for O(log n) eligibility pruning in __pick_eevdf()
- **on_rq flag**: Must be 1 iff entity in RB-tree (0 otherwise); double enqueue or on_rq mismatch corrupts runqueue
- **Base slice**: sysctl_sched_base_slice (default 700us) determines timeslice; deadline updated when `vruntime >= deadline`
- **CFS bandwidth**: Group throttling uses runtime_remaining; must properly dequeue on throttle, enqueue on unthrottle

### sched_ext (SCHED_EXT - BPF Extensible Scheduler)
- **BPF ops callbacks**: Scheduler behavior defined by BPF programs via ops (select_cpu, enqueue, dispatch, etc.); enables dynamic scheduling algorithms
- **Dispatch queues (DSQ)**: Tasks queued in local (per-CPU), global (per-node), or custom DSQs; can use FIFO or PRIQ (vtime) ordering but NOT mixed
- **ops_state tracking**: Atomic `p->scx.ops_state` prevents concurrent BPF operations on same task; transitions: NONE → QUEUEING → QUEUED → DISPATCHING
- **Direct dispatch**: Optimization allowing enqueue path to dispatch directly to local DSQ; tracked via per-CPU `direct_dispatch_task` marker
- **Failsafe mechanisms**: Watchdog timeout (runnable task stalls), scx_error() on invalid ops, and SysRq-S all trigger automatic revert to CFS; system integrity always maintained

## Load Balancing
- **Pull model**: Idle CPUs pull tasks from busy CPUs
- **Migration paths**: Balance callbacks run with specific lock states
- **Affinity constraints**: Respect task's allowed CPUs
- **Load calculation**: Based on runnable + running task load
- **PELT (Per-Entity Load Tracking)**: Decaying average of utilization

## Bandwidth and Throttling
- **CFS bandwidth**: `cfs_rq->runtime_remaining` tracking
- **Throttle/unthrottle**: Must maintain runqueue invariants
- **Hierarchical throttling**: Parent throttle affects all children
- **RT global throttling**: Default 95% limit to prevent lockup

## Priority Inheritance (PI)
- **PI chain**: Must update entire chain atomically
- **Boosting**: Lower priority task inherits higher priority from blocked task
- **Deadlock detection**: PI chain checked to prevent cycles
- **RT mutex**: Primary use case for PI

## Common Pitfalls
- **Lost wakeups**: Task state set after condition becomes true
- **Runqueue corruption**: Task on multiple runqueues simultaneously
- **Load calculation errors**: Load weight changes without updating hierarchy
- **Lock imbalance**: Acquiring runqueue lock without release on all paths
- **Preemption leaks**: Disabling preemption without re-enabling
- **Hot-unplug races**: Task migrated to CPU being taken offline
- **Nested sleeps**: Sleeping while in TASK_RUNNING state

## Quick Checks
- **preempt_disable() balance**: Every disable must have matching enable
- **rq lock holding**: Check `lockdep_assert_rq_held()` in rq accessors
- **task_rq() safety**: Task must be pinned or caller holds pi_lock/rq lock
- **wake_up_process()**: Safe for any task state, handles races internally
- **set_task_cpu()**: Only safe during migration with proper locks
- **Migration disabled sections**: Cannot block/sleep inside
- **Double enqueue**: Never enqueue task already on runqueue
- **Schedule in atomic**: Never call schedule() with preemption disabled or locks held (except rq lock in scheduler code)

## Deadline Scheduler Specifics
- **Root domain**: DL tasks tracked per root domain for migration
- **Global earliest deadline first**: System-wide EDF across CPUs
- **Zero-laxity**: Deadline equals current time requires immediate execution

## Debugging Features
- **debug**: Exposes /proc/sched_debug with runqueue state
- **schedstats**: Per-task scheduling statistics when enabled
- **trace events**: scheduler tracepoints for detailed analysis
- **lockdep annotations**: Validate locking rules in scheduler code
