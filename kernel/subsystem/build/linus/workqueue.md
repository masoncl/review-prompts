# Workqueues

## Main structures

### Objects and how they relate

- Non-ordered unbound workqueue: has one pwq per possible CPU plus `dfl_pwq`,
  not one per pod; CPUs of one pod share a `struct worker_pool`, not a pwq.
  See `apply_wqattrs_prepare()` and `get_unbound_pool()` in
  `kernel/workqueue.c`.
- `dfl_pwq`: spans the whole effective cpumask; `unbound_wq_update_pwq()`
  installs it in a CPU's slot when it cannot allocate a pwq.
- Ordered workqueue: every `cpu_pwq` slot and `dfl_pwq` hold the same pwq.
- Ordered workqueue during an attrs or unbound-cpumask change: has several
  pwqs on `wq->pwqs`; the new one is `plugged` and runs nothing until every
  older pwq is released and `pwq_release_workfn()` calls
  `unplug_oldest_pwq()`.
- `max_active` on a per-CPU or BH pool (`is_percpu_pool()` true): compared
  with `pwq->nr_active`.
- `struct wq_node_nr_active`: `nr` is an `atomic_t` that no single lock
  serialises; `lock` covers `pending_pwqs` and nests inside `pool->lock`.
- BH workqueue: has no `max_active` limit; `__alloc_workqueue()` stores
  `INT_MAX`.
- Per-CPU and BH pools: static per-CPU arrays (`cpu_worker_pools`,
  `bh_worker_pools`) set up in `workqueue_init_early()`; only unbound pools
  are created on demand.
- Concurrency management (`pool->nr_running`): applies only to per-CPU kthread
  pools while bound to their CPU.
- Unbound and BH pools: always `POOL_DISASSOCIATED`, so their workers carry
  `WORKER_UNBOUND` and `need_more_worker()` is true whenever the worklist is
  not empty.
- BH pool: has one `struct worker` with `task` NULL, created for every
  possible CPU in `workqueue_init()`; `workqueue_softirq_action()` runs it
  from `tasklet_action()` and `tasklet_hi_action()` in `kernel/softirq.c`.
- Unbound pool identity: `nice`, `affn_strict`, `__pod_cpumask`, and `cpumask`
  only when `affn_strict` is clear; see `wqattrs_equal()`.
- `affn_scope` and `ordered`: belong to the workqueue only; `wqattrs_equal()`
  does not compare them and `wqattrs_clear_for_pool()` resets them in a
  pool's attrs, so an ordered workqueue can share a pool with non-ordered
  ones.
- `WQ_PERCPU`: marks a per-CPU workqueue.
- `mayday_cursor`: a dummy `struct work_struct` in every pwq that
  `assign_rescuer_work()` leaves on `pool->worklist` to mark its position, so
  a worklist entry is not always a real work item; `assign_work()` removes it
  and returns `false`.
- `pwq_release_worker`: a `struct kthread_worker` that workqueue itself uses;
  `put_pwq()` queues `release_work` on it when the refcount reaches zero,
  because the pwq cannot be released under `pool->lock`.

## Choosing a workqueue

**System workqueues**

- All twelve are created at the end of `workqueue_init_early()` in
  `kernel/workqueue.c`; the rows below are the ones easy to get wrong.

| Pointer | Name string | Kind | Use |
|---|---|---|---|
| `system_dfl_long_wq` | "events_dfl_long" | unbound, `WQ_MAX_ACTIVE` | unbound items that may run long |
| `system_freezable_power_efficient_wq` | "events_freezable_pwr_efficient" | per-CPU or unbound | freezable and power-efficient |
| `system_wq` | "events" | per-CPU | deprecated; use `system_percpu_wq` |
| `system_unbound_wq` | "events_unbound" | unbound | deprecated; use `system_dfl_wq` |

- `system_wq` and `system_unbound_wq`: each is its own
  `struct workqueue_struct`, not an alias; it shares the name string and
  the worker pools with its replacement.
- Flushing `system_percpu_wq` does not wait for items queued on `system_wq`,
  and the same holds for the unbound pair.
- Queueing on a deprecated one: `__queue_work()` tests `__WQ_DEPRECATED` and
  calls `pr_warn_once()`, then queues the item normally.
- That `pr_warn_once()` is one call site, so only the first such item in a
  boot is reported, whichever of the two workqueues it used.
- `schedule_work()`, `schedule_work_on()`, `schedule_delayed_work()` and
  `schedule_delayed_work_on()`: all queue on `system_percpu_wq`.

**Per-CPU or unbound**

- Neither `WQ_PERCPU` nor `WQ_UNBOUND`: `__alloc_workqueue()` does
  `WARN_ONCE()`, sets `WQ_PERCPU`, and the allocation succeeds.
- Both flags: `WARN_ONCE()`, `WQ_PERCPU` is cleared, the workqueue is unbound,
  and the allocation succeeds.
- Each `WARN_ONCE()` is one call site, so only the first offending workqueue
  in a boot is reported; a clean log does not show a later caller is right.
- After `__alloc_workqueue()` exactly one of the two flags is set in
  `wq->flags`; the rest of `kernel/workqueue.c` tests only `WQ_UNBOUND`.
- `WQ_BH` without `WQ_PERCPU`: accepted, and trips the neither-flag warning;
  `system_bh_wq` is created with `WQ_BH | WQ_PERCPU`.
- `WQ_POWER_EFFICIENT` with `wq_power_efficient` set: `WQ_PERCPU` is replaced
  by `WQ_UNBOUND` before the both-flags test, so no warning.
- `wq_power_efficient`: also forced true in `workqueue_init_early()` when
  `housekeeping_enabled(HK_TYPE_TICK)`, before the system workqueues are
  created.
- Default affinity scope of an unbound workqueue: `wq_affn_dfl` starts as
  `WQ_AFFN_CACHE_SHARD`, not `WQ_AFFN_CACHE`.

**Workqueue flags**

- `WQ_BH`: `__WQ_BH_ALLOWS` is `WQ_BH | WQ_HIGHPRI | WQ_PERCPU`; any other
  flag gives `WARN_ON_ONCE()` and NULL.
- `Documentation/core-api/workqueue.rst` says `WQ_HIGHPRI` is the only flag
  allowed with `WQ_BH`; the code also allows `WQ_PERCPU`.
- `WQ_MEM_RECLAIM` with `WQ_BH`: refused by the `__WQ_BH_ALLOWS` test;
  `init_rescuer()` has no test of `WQ_BH`.
- `WQ_SYSFS` with `__WQ_ORDERED`: accepted; `workqueue_sysfs_register()` has
  no test of `__WQ_ORDERED`. See "Ordered workqueues" for what sysfs can then
  change.
- `WQ_SYSFS` without `CONFIG_SYSFS`: accepted and does nothing;
  `workqueue_sysfs_register()` is a stub that returns 0.
- `__WQ_DEPRECATED`: a fifth internal flag, beside `__WQ_DESTROYING`,
  `__WQ_DRAINING`, `__WQ_ORDERED` and `__WQ_LEGACY`; only
  `workqueue_init_early()` sets it.

**max_active limits**

- `WQ_MAX_ACTIVE` is 2048 and `WQ_DFL_ACTIVE` is 1024, in
  `include/linux/workqueue.h`.
- There is no WQ_MAX_UNBOUND_PER_CPU and no wq_update_pwq_max_active() here;
  `wq_update_node_max_active()` in `kernel/workqueue.c` computes the limits
  of an unbound workqueue.
- Unbound workqueue: the count is per NUMA node, in
  `struct wq_node_nr_active`, shared by every pwq whose pool is on that node;
  see `pwq_tryinc_nr_active()`.
- `Documentation/core-api/workqueue.rst` says `max_active` is always a
  per-CPU attribute, even for unbound workqueues; `pwq_tryinc_nr_active()`
  counts per CPU only for per-CPU pools.
- Unbound pool not contained in one node: counted in the extra
  `NUMA_NO_NODE` slot of `wq->node_nr_active`, whose `max` is the full
  `max_active`.
- `min_active`: the floor of each node's share, not of each pwq's;
  `wq_update_node_max_active()` is the only code that applies it.
- All CPUs of an unbound workqueue offline: every node's limit becomes
  `min_active`.
- `workqueue_set_min_active()`: sets `min_active` between 0 and
  `saved_max_active`; `WARN_ON()` and return unless the workqueue is unbound,
  not ordered and not BH.
- `workqueue_set_max_active()` on an unbound workqueue: also lowers
  `saved_min_active` to the new maximum if it was higher.

**Ordered workqueues**

- Besides `alloc_ordered_workqueue()`, three macros also pass
  `WQ_UNBOUND | __WQ_ORDERED` and `max_active` 1:
  `alloc_ordered_workqueue_lockdep_map()` (only with `CONFIG_LOCKDEP`),
  `devm_alloc_ordered_workqueue()` and `create_singlethread_workqueue()`.

| Later change | Outcome |
|---|---|
| `workqueue_set_max_active()` | `WARN_ON()` and return |
| `workqueue_set_min_active()` | `WARN_ON()` and return |
| sysfs `max_active` file | read-only, set by `wq_sysfs_is_visible()` |
| sysfs `nice`, `cpumask`, `affinity_scope`, `affinity_strict` | let through |
| `apply_workqueue_attrs()` | let through; the only test of `__WQ_ORDERED` on the path, in `apply_wqattrs_prepare()`, sets `plugged` |
| CPU hotplug, default affinity scope change | `unbound_wq_update_pwq()` returns early |

- `apply_workqueue_attrs_locked()`: its only test of `wq->flags` is for
  `WQ_UNBOUND`; it returns `-EINVAL` when the workqueue lacks it.
- Single pwq after a change: `apply_wqattrs_prepare()` keeps one pwq only
  when the attrs passed in have `ordered` set; it does not look at
  `__WQ_ORDERED` for that.
- **Unsafe usage**: `apply_workqueue_attrs()` on an ordered workqueue with
  attrs fresh from `alloc_workqueue_attrs()`, whose `ordered` is false.
  - Unsafe: `apply_wqattrs_prepare()` then allocates one pwq per possible
    CPU, and the "ordering guarantee broken" test in `alloc_and_link_pwqs()`
    runs only at creation.
  - Safe: attrs copied from `wq->attrs`, as `wq_sysfs_prep_attrs()` does for
    the sysfs stores; `copy_workqueue_attrs()` carries `ordered` over.

**Memory reclaim workqueues**

- `check_flush_dependency()` has two `WARN_ONCE()` calls, both only for a
  target without `WQ_MEM_RECLAIM`: the flusher has `PF_MEMALLOC`, or the
  flusher is a worker running an item of a `WQ_MEM_RECLAIM` workqueue.
- `from_cancel` true: exempt from both warnings; `__cancel_work_sync()`
  passes it, so the four cancel-sync and disable-sync calls never warn.
- `__WQ_LEGACY` on the flusher's workqueue: exempts the second warning only;
  the `PF_MEMALLOC` warning still applies.
- `check_flush_dependency()` has no test for a flush within the same
  workqueue, no test of `WQ_BH`, and no test for the rescuer.
- A BH workqueue as target: it cannot have `WQ_MEM_RECLAIM`, so `flush_work()`
  on its queued or running item from a `WQ_MEM_RECLAIM` worker warns.
- The second warning needs task context: `current_wq_worker()` in
  `kernel/workqueue_internal.h` returns NULL outside `in_task()`.
- `current_is_workqueue_mem_reclaim()`: exported; makes the same test of the
  caller as the second warning, for code that must decide before it
  flushes. It does not cover the `PF_MEMALLOC` case.

**Freezable workqueues**

- Items already active when `freeze_workqueues_begin()` runs, running or
  still on the pool's worklist, all run; `freeze_workqueues_busy()` reports
  busy while any `pwq->nr_active` is nonzero.
- Frozen window in system suspend (with `CONFIG_SUSPEND_FREEZER`): from
  `suspend_freeze_processes()`, which `suspend_prepare()` in
  `kernel/power/suspend.c` calls after the `PM_SUSPEND_PREPARE` notifiers, to
  `suspend_thaw_processes()` in `suspend_finish()`, so it covers
  `dpm_suspend_start()` and `dpm_resume_end()`.
- `pm_wq`: created with `WQ_UNBOUND` only in `kernel/power/main.c`; it is not
  freezable.
- **Unsafe usage**: `flush_work()`, `flush_delayed_work()` or
  `flush_workqueue()` on a freezable workqueue inside the frozen window while
  an item is pending.
  - Unsafe: the item is on `pwq->inactive_works` and `max_active` is 0, so
    the `wait_for_completion()` in `__flush_work()` or `__flush_workqueue()`
    cannot return before `thaw_workqueues()`.
  - Unsafe: `flush_delayed_work()` when only the timer is pending; it queues
    the item first, then waits for it.
  - Safe: `flush_work()` on an idle item; `start_flush_work()` returns
    `false` without waiting.
  - Safe: `cancel_work_sync()` or `cancel_delayed_work_sync()` on a pending
    item, as `r852_suspend()` does; `try_to_grab_pending()` takes it off
    `inactive_works`, and `start_flush_work()` then finds no worker running
    it.
  - Safe: flushing before `freeze_kernel_threads()` or after
    `thaw_processes()`.

**BH workqueues**

- `max_active`: must be 0; any other value gives `WARN_ON_ONCE()` and NULL.
- CPU an item runs on: the CPU of the BH pool it was queued to;
  `queue_work_on()` with another CPU makes `kick_bh_pool()` raise the softirq
  there through `irq_work_queue_on()`.
- Dead CPU: `workqueue_softirq_dead()` runs the dead pool's `bh_worker()`
  from a BH item on the current CPU, in `drain_dead_softirq_workfn()`.
- `cancel_work_sync()` and `disable_work_sync()`: not from hardirq;
  `__cancel_work_sync()` does `WARN_ON_ONCE(in_hardirq())` for a BH item.
- Which branch `__cancel_work_sync()` takes: decided by `WORK_OFFQ_BH` in the
  item's data, set when the item leaves a BH pool in `process_one_work()` or
  `try_to_grab_pending()`.
- **Potentially unsafe usage**: `cancel_work_sync()` or `disable_work_sync()`
  from atomic context on an item meant for a BH workqueue.
  - Unsafe: the item has never been queued, or was last queued on a non-BH
    workqueue; `WORK_OFFQ_BH` is clear and `__cancel_work_sync()` calls
    `might_sleep()`.
  - Safe: the item was last queued on a BH workqueue and the caller is not in
    hardirq; without `CONFIG_PREEMPT_RT`, `__flush_work()` busy-waits with
    `cpu_relax()` instead of sleeping.
- `CONFIG_PREEMPT_RT`: the wait in `__flush_work()` calls
  `workqueue_callback_cancel_wait_running()`, which takes and drops
  `pool->cb_lock`; `bh_worker()` holds that lock while it runs items.

## Queueing

**Ownership of the pending bit**

- `try_to_grab_pending()`: returns only 1, 0 or `-EAGAIN`; there is no
  -ENOENT return and no WORK_OFFQ_CANCELING flag in this tree.
- Timer steal: done with `timer_delete()`; there is no del_timer() timer
  function here.
- `set_work_pool_and_clear_pending()`: `smp_wmb()` before the store, the full
  `smp_mb()` after it.
- PENDING set, `WORK_STRUCT_PWQ` clear, no timer to steal: tells
  `try_to_grab_pending()` that an owner is in transit; it returns `-EAGAIN`
  and `work_grab_pending()` spins.
- Owner in transit, other than `queue_rcu_work()`: keeps IRQs off from taking
  the bit until it queues, arms the timer or clears; `__queue_work()` has
  `lockdep_assert_irqs_disabled()`.
- Grab without `WORK_CANCEL_DELAYED` on a timer-armed item: sees the same
  transit state, so it gets `-EAGAIN` until the timer fires.
- Pool id and `WORK_OFFQ_BH` survive cancel, disable and enable:
  `__cancel_work()` and `enable_work()` write back what `work_offqd_unpack()`
  read and change only the disable count.

**Queueing return value**

- Drop on a draining or destroying workqueue: `__queue_work()` clears
  `WORK_STRUCT_PENDING_BIT` before it returns, keeping the pool id, disable
  count and off-queue flags.
- Caller after such a drop: sees `true`; the item is idle, not stuck pending.
- Later `queue_work()` on the dropped item: takes the bit again and returns
  `true`; it is dropped again while the flag is set and queued normally once
  `drain_workqueue()` has cleared `__WQ_DRAINING`.
- Warning for the drop: `WARN_ONCE()`, so only the first drop is reported;
  later drops are silent.
- `__WQ_DESTROYING`: tested together with `__WQ_DRAINING`; chained work is
  accepted under either flag.
- `is_chained_work()`: true only when `current_wq_worker()` (in
  `kernel/workqueue_internal.h`) returns a worker, which needs `in_task()` and
  `PF_WQ_WORKER`; queueing from a timer, softirq or hard IRQ is never chained.
- During `cancel_work_sync()` or `cancel_delayed_work_sync()`: `queue_work()`
  returns `false` and the request is dropped, because the disable count is
  raised for the whole wait.
- `work->entry` not empty on entry to `__queue_work()`: `WARN_ON()`, nothing
  is queued, the caller sees `true` and the pending bit stays set.

**Queueing a running item**

- Overlap across pools: prevented. `__queue_work()` queues the item on the
  pwq of the worker that is running it in its last pool, not on the pool of
  the chosen CPU.
- Condition for that redirect: the running worker's `current_pwq->wq` is the
  workqueue being queued to, and `current_func` equals `work->func`
  (`find_worker_executing_work()`).
- Condition not met (item queued through another workqueue, or `work->func`
  changed): the item goes to the pool of the chosen CPU, and the second run
  can overlap the first unless both land in the same pool with `work->func`
  unchanged.
- `__WQ_ORDERED` workqueue: `__queue_work()` skips the redirect and queues on
  the pwq of the chosen CPU; it relies on ordering for non-reentrancy, and a
  `plugged` pwq activates nothing until `unplug_oldest_pwq()`.
- Same-pool collision: handled in `assign_work()`, not in
  `process_one_work()`; it moves the item to `collision->scheduled` with
  `move_linked_works()`. There is no move_linear_work here.
- `false` from `queue_work()`: guarantees a later start only when the bit was
  held by an instance that is being queued, queued or timer-armed and that is
  then left alone.
- `false` with no later run: the item is disabled; a canceller, disabler or
  `enable_work()` held the bit at that moment; the pending instance is
  cancelled afterwards; or `__queue_work()` drops the pending instance on a
  draining or destroying workqueue, for example when its timer fires there.

**Delayed work and its timer**

- Arming the timer: `__queue_delayed_work()` does not test `__WQ_DRAINING` or
  `__WQ_DESTROYING`; the test is made in `__queue_work()` when the timer
  fires.
- Timer firing during a drain or destroy: never counts as chained, even when
  a work function of that workqueue armed it, because `is_chained_work()`
  needs task context.
- Result of that firing: `WARN_ONCE()`, the item is dropped, and
  `WORK_STRUCT_PENDING_BIT` is cleared, so `delayed_work_pending()` turns
  false without the function having run.
- Timer firing after the workqueue has been freed: `delayed_work_timer_fn()`
  passes the stale `dwork->wq` to `__queue_work()`, which reads `wq->flags`
  with no other check.
- Zero delay: `__queue_delayed_work()` returns before it stores `dwork->wq`
  and `dwork->cpu`; they keep the values of the last nonzero-delay arming, if
  any.
- `flush_delayed_work()`: uses `timer_delete_sync()`; there is no
  del_timer_sync() here.

**Delayed work timer context**

- IRQ state: the callback runs in softirq with hard IRQs disabled;
  `expire_timers()` in `kernel/time/timer.c` drops the base lock without
  enabling IRQs for a `TIMER_IRQSAFE` timer.
- Timer CPU, chosen in `__queue_delayed_work()`:

| `housekeeping_enabled(HK_TYPE_TIMER)` | `cpu` argument | Timer armed with |
|---|---|---|
| true | any, explicit CPU included | `add_timer_on()` on the current CPU if it is a housekeeping CPU, else on `housekeeping_any_cpu(HK_TYPE_TIMER)` |
| false | `WORK_CPU_UNBOUND` | `add_timer_global()`, which clears `TIMER_PINNED` |
| false | explicit CPU | `add_timer_on()` on that CPU |

- Explicit `cpu` with timer housekeeping on: the timer can fire on a CPU
  other than `cpu`; the item is still queued for `dwork->cpu`.
- `housekeeping_enabled()`: a stub that returns `false` without
  `CONFIG_CPU_ISOLATION` (`include/linux/sched/isolation.h`).
- Saved `WORK_CPU_UNBOUND`: `__queue_work()` picks the CPU from
  `raw_smp_processor_id()` when the timer fires; a per-CPU workqueue uses that
  CPU, a `WQ_UNBOUND` one passes it to `wq_select_unbound_cpu()`.
- `delayed_work_timer_fn()`: gets the item with `timer_container_of()`; there
  is no from_timer() here.

## Flush, cancel, disable

**Flushing one item**

- Never-initialised item: `__flush_work()` does `WARN_ON(!work->func)` and
  returns false; this catches only a NULL `func`, as in zero-filled memory.
- `cancel_work_sync()` and `disable_work_sync()` on a zero-filled item: hit
  the same `WARN_ON(!work->func)`, through `__cancel_work_sync()`, once
  `wq_online` is set.

**Flushing a workqueue**

- `flush_workqueue()` macro in `include/linux/workqueue.h`: tests eight
  pointers, `system_percpu_wq`, `system_dfl_wq` and `system_dfl_long_wq`
  among them; it does not test `system_wq`, `system_unbound_wq`,
  `system_bh_wq` or `system_bh_highpri_wq`.
- Run time: `__warn_flushing_systemwide_wq()` in `kernel/workqueue.c` is a
  real function; a call site that got the compile-time warning also does
  `pr_warn()` of "Flushing system-wide workqueues will be prohibited in near
  future." and `dump_stack()` on every call, then flushes normally.
- A system workqueue the compiler cannot prove equal to one of the tested
  pointers: the `flush_workqueue()` macro gives no warning at compile time
  or at run time.
- `__WQ_DESTROYING`: `__queue_work()` tests it together with `__WQ_DRAINING`;
  `destroy_workqueue()` sets it before the drain and never clears it.

**Cancelling without waiting:** Models have this right; see `__cancel_work()`
and `try_to_grab_pending()` in `kernel/workqueue.c`.

**Cancelling and waiting**

- There is no WORK_OFFQ_CANCELING here; `__cancel_work_sync()` blocks
  requeueing by raising the disable count (`WORK_CANCEL_DISABLE`), the same
  count `disable_work()` uses.
- `enable_work()` at the end of `__cancel_work_sync()`: skipped when the
  caller passed `WORK_CANCEL_DISABLE` itself, as `disable_work_sync()` and
  `disable_delayed_work_sync()` do; the item then stays disabled.
- Condition of the guarantee: nothing queues the item after the
  `enable_work()` call at the end of `__cancel_work_sync()`, which runs
  before the function returns.
- Item already disabled by another caller: still disabled after
  `cancel_work_sync()` returns, since it undoes only its own increment.

**Disabling a work item**

- `enable_work()`: does not queue the item, and requests refused while it
  was disabled are lost; `enable_and_queue_work()` in
  `include/linux/workqueue.h` enables and queues when the count reaches 0.
- Maximum depth: 65535, enforced in `work_offqd_disable()`; the kerneldoc of
  `disable_work()` says 65536.
- **Unsafe usage**: `enable_work()` without a matching `disable_work()`.
  - Unsafe: the count is already 0; `enable_work()` takes a pending item off
    its worklist through `work_grab_pending()`, so the function never runs;
    `work_offqd_enable()` warns with `WARN_ONCE()`, and the call returns true.
  - Safe: one `enable_work()` for each earlier `disable_work()` or
    `disable_work_sync()`, as `__cancel_work_sync()` does for its own
    increment.

**Disabling delayed work**

- `delayed_work_timer_fn()`: has no check of the disable count; it calls
  `__queue_work()` directly.
- What keeps a disabled delayed item from running: `try_to_grab_pending()`
  with `WORK_CANCEL_DELAYED` deletes the armed timer, or steals the item once
  the handler has queued it, before the count is raised.

**Self-requeueing work**

- `cancel_work_sync()`: stops a function whose only queuer is itself; the
  item is disabled while the call waits, so the function's own requeue is
  refused, and the function has finished before the item is enabled again.
- `drain_workqueue()` and `destroy_workqueue()` on a workqueue without
  `WQ_BH`: never return while the function keeps requeueing on the same
  workqueue; `is_chained_work()` lets the requeue through and
  `drain_workqueue()` loops with no bound, printing
  "isn't complete after %u tries".

**Cancelling delayed work**

- **Potentially unsafe usage**: passing `&dwork->work` to `flush_work()`,
  `cancel_work_sync()`, `disable_work_sync()`, `cancel_work()` or
  `disable_work()`.
  - Unsafe: with `flush_work()` while `dwork->timer` may be armed;
    `start_flush_work()` returns false at once unless an earlier instance is
    running, and the function runs later when the timer fires.
  - Unsafe: with the cancel and disable forms while `dwork->timer` may be
    armed; `work_grab_pending()` busy-waits on `-EAGAIN` until the timer
    expires, then steals the item.
  - Safe: when the timer cannot be armed, as in
    `ip_vs_control_net_cleanup_sysctl()`, which calls `cancel_work_sync()`
    right after `cancel_delayed_work_sync()` on the same item.
  - Safe: the delayed cancel and disable variants, which pass
    `WORK_CANCEL_DELAYED` so that `try_to_grab_pending()` deletes the timer,
    as `blk_mq_cancel_work_sync()` does with `cancel_delayed_work_sync()`.
- `flush_delayed_work()` with a pending timer: queues with
  `__queue_work(dwork->cpu, dwork->wq, &dwork->work)`; it does not call
  `__queue_delayed_work()` or `queue_work_on()`.

**Waiting from inside work**

- `touch_work_lockdep_map()` and `touch_wq_lockdep_map()`: acquire and at
  once release `work->lockdep_map` and `wq->lockdep_map`, so that lockdep
  records "the waiter depends on this item or workqueue"; they are not
  tied to `WQ_MEM_RECLAIM`.
- Acquire type: `process_one_work()` and both helpers use
  `lock_map_acquire()`, which is exclusive, not `lock_map_acquire_read()`.
- `touch_work_lockdep_map()`: called from `start_flush_work()` only after
  `insert_wq_barrier()`; `flush_work()` or `cancel_work_sync()` that finds
  the item idle records nothing.
- Lock held across `flush_work()` or `cancel_work_sync()`: lockdep reports
  the inversion only on a run where the item was pending or running at the
  `flush_work()` call, or running at the `cancel_work_sync()` call.
- `touch_wq_lockdep_map()` in `__flush_workqueue()`: unconditional after the
  `wq_online` test, so `drain_workqueue()` and `destroy_workqueue()` record
  the dependency even when the workqueue is empty.
- `touch_wq_lockdep_map()` in `start_flush_work()`: only when
  `!from_cancel && (wq->saved_max_active == 1 || wq->rescuer)`.
- `wq->rescuer`: set for every `WQ_MEM_RECLAIM` workqueue (`init_rescuer()`),
  so `flush_work()` on a busy item of such a workqueue, from a function
  running on the same workqueue, is reported whatever `max_active` is.
- `cancel_work_sync()` and `disable_work_sync()`: never touch
  `wq->lockdep_map`.
- The wait itself is not annotated: `init_completion_map()` in
  `include/linux/completion.h` discards the map.
- `check_flush_dependency()` worker test: exempts a caller whose workqueue
  has `__WQ_LEGACY`, which for example `create_workqueue()`,
  `create_freezable_workqueue()` and `create_singlethread_workqueue()` set.

## Lifetime against teardown

**Freeing the containing structure**

- Self-free example: `async_run_entry_fn()` in `kernel/async.c` calls
  `kfree(entry)` on its own container; the item is touched only by
  `INIT_WORK()`, one `queue_work_node()` and the function itself.
- `fs/aio.c`: `struct kioctx` has no `free_work` field; it has `free_rwork`, a
  `struct rcu_work` queued by `free_ioctx_reqs()`; `free_ioctx()` frees the ctx.
- Release-path example: `hci_adv_instances_clear()` in
  `net/bluetooth/hci_core.c` calls `disable_delayed_work_sync()` and then
  `kfree()` on each `struct adv_info`.
- Recycled address, same function, same pool: `assign_work()` puts the new item
  on the `scheduled` list of the worker still running the old one; if that
  running function waits for the new item, it deadlocks (comment on
  `find_worker_executing_work()`).
- **Potentially unsafe usage**: `flush_work()` followed by the free.
  - Unsafe: while any source can still queue the item; `__flush_work()` waits
    for the last queueing only and leaves the item enabled.
  - Safe: when the freeing code is the only queuer and queued once, as
    `schedule_on_each_cpu()` does before `free_percpu()`.

**Teardown sequence**

- There is no del_timer_sync() here; `timer_delete_sync()` and
  `timer_shutdown_sync()` in `kernel/time/timer.c` stop a timer source.

**Destroying a workqueue**

- Outside queueing after the destroy started: the `WARN_ONCE()` in
  `__queue_work()` prints "workqueue: cannot queue %ps on wq %s"; see
  "Queueing return value" for what happens to the item and what the caller
  sees.
- `drain_workqueue()` warning: at try 10, then every 100th try up to 1000; the
  loop itself never gives up.
- Busy at the end: `WARN_ON(pwq_busy())`, `pr_warn()`, `show_pwq()`, then
  `show_one_workqueue()`; it does not call `show_all_workqueues()`.
- Leaked workqueue state after that return: sysfs entry removed, rescuer
  stopped and freed, still on the `workqueues` list, `__WQ_DESTROYING` never
  cleared, so outside queueing stays rejected.

**Module unload**

- `flush_scheduled_work()`: still a macro in `include/linux/workqueue.h`; it
  calls `__warn_flushing_systemwide_wq()` and then flushes `system_percpu_wq`.
  No in-tree code calls it.
- What the tree says: the header comments state no reason themselves; they
  say to stop using `flush_scheduled_work()`, that it will be removed, and
  link to a mailing-list message for the reasons and the steps of converting
  to local workqueues.

**Initialising a live item**

- Running but not pending item: nothing is corrupted in the worker;
  `process_one_work()` unlinked `work->entry` before the callback and reads
  nothing from the item afterwards.
- Running but not pending item, what is lost: the last pool id, so
  `flush_work()` and `cancel_work_sync()` return without waiting for the
  running instance, and the next queueing may run concurrently with it.
- Disable count: reset to zero by `WORK_DATA_INIT()`, which silently re-enables
  an item disabled with `disable_work_sync()`.
- Debug coverage: under `CONFIG_DEBUG_OBJECTS_WORK` an item is active only
  between `insert_work()` and `process_one_work()` or
  `try_to_grab_pending()`; a running item is not reported.
- Delayed item with an armed timer: the work object is not active, so only
  `CONFIG_DEBUG_OBJECTS_TIMERS` reports it, and `timer_fixup_init()` deletes
  the timer; `INIT_DELAYED_WORK()` has already wiped `work->data` by then.
- **Potentially unsafe usage**: `INIT_WORK()` before every queueing of the same
  item.
  - Unsafe: when nothing guarantees that the previous queueing has finished;
    `INIT_WORK()` then overwrites `work->data` and `work->entry` of an item
    that may still be on a worklist.
  - Safe: when one lock covers init, queue and `flush_work()`, as
    `__lru_add_drain_all()` in `mm/folio.c` does under its static mutex.
  - Safe: on a freshly allocated item that is flushed before the free, as
    `schedule_on_each_cpu()` does.

## Model gaps

### Other mistakes models make

- Models do not know the size of a `WQ_AFFN_CACHE_SHARD` pod. One LLC is split
  into shards of about `wq_cache_shard_size` cores, 8 by default; an LLC with
  fewer cores than that is one pod; see `llc_calc_shard_layout()`, reached
  from `workqueue_init_topology()`.
- Models take every entry on `pool->worklist` to have a `func` that may be
  called. The `func` of `pwq->mayday_cursor` is `mayday_cursor_func()`, which
  is `BUG()`.
- Models do not know `devm_alloc_workqueue()` and
  `devm_alloc_ordered_workqueue()`. They call `destroy_workqueue()` at driver
  detach through `devm_workqueue_release()`.
