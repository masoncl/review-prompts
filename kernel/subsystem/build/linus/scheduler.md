# Scheduler Subsystem

## Main structures

### Objects and how they relate

- Runqueue lock: the field is `__lock` in `struct rq`; there is no field named
  lock. Reach it through `rq_lockp()` or `__rq_lockp()`.
- Class order, highest first: `stop_sched_class`, `dl_sched_class`,
  `rt_sched_class`, `fair_sched_class`, `ext_sched_class`,
  `idle_sched_class`. `ext_sched_class` is below fair, not above it.
- `for_each_active_class()`: skips `fair_sched_class` when
  `scx_switched_all()`, and skips `ext_sched_class` when `scx_enabled()` is
  false. `for_each_class()` skips nothing.
- Changing class, priority, group or affinity: there is no
  check_class_changed() or __setscheduler_prio() here. `sched_change_begin()`
  and `sched_change_end()` in `kernel/sched/core.c` bracket the change.
- `curr` and `h_curr` in `struct cfs_rq`: `rq->cfs.curr` is the entity of the
  picked task, `rq->donor`. `h_curr` is set at every level of the hierarchy,
  to the entity on the running path at that level.
- `struct cfs_tg_state`: besides the queue and the group entity it holds the
  group entity's statistics, a `struct sched_statistics`;
  `__schedstats_from_se()` in `kernel/sched/stats.h` reaches them from the
  entity.
- Group entity lookup: `tg_se()` or `cfs_rq_se()`. Both return `NULL` for
  `root_task_group`, whose per-CPU queue is `rq->cfs` itself.
- `struct task_group`, RT side: still per-CPU pointer arrays, `rt_se` and
  `rt_rq`. When `rt_group_sched_enabled()` is false, `set_task_rq()` attaches
  every task to the arrays of `root_task_group`.
- CFS bandwidth: `throttle_cfs_rq()` marks the hierarchy and removes no
  entity. Each task dequeues itself in `throttle_cfs_rq_work()`, on return to
  user space, and waits on `throttled_limbo_list` of its `struct cfs_rq`.
- A throttled task: `p->throttled` is set and `p->se.on_rq` is 0, but
  `p->on_rq` is unchanged, since `dequeue_task_fair()` is called directly. So
  `task_on_rq_queued()` is true for a task that is in no tree.
- `CONFIG_SCHED_PROXY_EXEC`: depends on `!SCHED_CLASS_EXT` and `!PREEMPT_RT`
  in `init/Kconfig`. A kernel with `rq->donor` distinct from `rq->curr` never
  has `ext_sched_class`.
- DL servers: each is a `struct sched_dl_entity` embedded in `struct rq`, with
  no task behind it.
- `dl_server` in `struct rq` and in `struct task_struct`: `__pick_task_dl()`
  records in the runqueue which server picked the task;
  `put_prev_set_next_task()` moves that to the picked task.
- `struct scx_sched` in `kernel/sched/ext/internal.h`: one loaded BPF
  scheduler. `struct sched_ext_ops` is embedded in it, in a union with
  `struct sched_ext_ops_cid`.
- With `CONFIG_EXT_SUB_SCHED` there can be several `struct scx_sched`: the
  root one, `scx_root`, and children attached to cgroups. `p->scx.sched` names
  the one that owns a task; `sched` in `struct scx_dispatch_q` names the one
  that owns a DSQ, and is `NULL` for the per-runqueue reject and rescue DSQs.
- `struct sched_cache_group` (`CONFIG_SCHED_CACHE`): one per
  `struct mm_struct`, refcounted. Each task of that mm holds its own
  reference in `sched_cache_grp`. It carries the preferred CPU of the process
  for cache-aware balancing.
- `struct sched_domain_shared`: not only on the LLC domain. On asymmetric
  capacity it is also attached to the lowest `SD_ASYM_CPUCAPACITY_FULL`
  domain that is not a NUMA domain. `sd_balance_shared` points to that one if
  it exists, else to the LLC one. See `update_top_cache_domain()` in
  `kernel/sched/topology.c`.
- Callers of `move_queued_task_locked()`, for example push and pull in RT and
  deadline, hold both runqueue locks.

## Where to look

**Core files**

| Job | File | Built as; easy to miss |
|---|---|---|
| Fair class | `kernel/sched/fair.c` | own object; `kernel/sched/Makefile` builds only `core.o`, `fair.o`, `build_policy.o`, `build_utility.o` |
| Stop class | `kernel/sched/stop_task.c` | not on its own; included by `kernel/sched/build_utility.c`, not `kernel/sched/build_policy.c` |
| Load tracking | `kernel/sched/pelt.c` | not on its own; included by `kernel/sched/build_policy.c` |
| System calls | `kernel/sched/syscalls.c` | not on its own; via `kernel/sched/build_policy.c`; holds `sched_yield` and also in-kernel helpers such as `yield()`, `yield_to()`, `set_user_nice()`, `idle_cpu()`; the `membarrier` syscall is in `kernel/sched/membarrier.c` |
| sched_ext sources | `kernel/sched/ext/` | no flat sched_ext files exist in `kernel/sched/`; the directory has no Makefile; `kernel/sched/build_policy.c` includes its five `.c` files under `CONFIG_SCHED_CLASS_EXT` |
| sched_ext core | `kernel/sched/ext/ext.c` | holds `DEFINE_SCHED_CLASS(ext)` and both struct_ops registrations; cid mapping and arena allocator are split out to `kernel/sched/ext/cid.c` and `kernel/sched/ext/arena.c` |
| sched_ext hooks for the rest of the scheduler | `kernel/sched/ext/ext.h` | included at the end of `kernel/sched/sched.h`; `struct scx_rq` itself is in `kernel/sched/sched.h` |
| sched_ext idle tracking | `kernel/sched/ext/idle.c`, `kernel/sched/ext/idle.h` | `kernel/sched/ext/idle.c` is not built on its own; included by `kernel/sched/build_policy.c`, not by `kernel/sched/ext/ext.c` |
| sched_ext sub-schedulers | `kernel/sched/ext/sub.c`, `kernel/sched/ext/sub.h` | body of `kernel/sched/ext/sub.c` under `CONFIG_EXT_SUB_SCHED`; without it that file has only stub kfuncs, for example `scx_bpf_sub_grant()` returning `-EOPNOTSUPP`; more `#ifdef CONFIG_EXT_SUB_SCHED` blocks are elsewhere, for example in `kernel/sched/ext/ext.c` and `kernel/sched/sched.h` |
| sched_ext ops table and internal types | `kernel/sched/ext/internal.h`, `kernel/sched/ext/types.h` | headers; `kernel/sched/ext/internal.h` has two ops tables, `struct sched_ext_ops` and `struct sched_ext_ops_cid`, plus `struct scx_sched`; `kernel/sched/ext/types.h` has `enum scx_consts` and `struct scx_cmask` |

## Scheduling classes

**Order of the classes**

- `sched_class_above(_a, _b)`: `((_a) < (_b))`; the lower address is the
  higher class, and `SCHED_DATA` places stop first, at
  `__sched_class_highest`.
- Comment above `DEFINE_SCHED_CLASS()` in `kernel/sched/sched.h`: says the
  classes are laid out in reverse order; the linker script and the
  `BUG_ON()`s in `sched_init()` show highest first.
- `wakeup_preempt()` in `kernel/sched/core.c`: compares `p->sched_class` with
  `rq->next_class`, not with the class of `rq->curr`; it calls
  `rq->next_class->wakeup_preempt` both for an equal and for a higher class,
  and for a higher class also calls `resched_curr()` and raises
  `rq->next_class`.
- `rq->next_class`: set to the class of the picked task in `__schedule()`;
  raised by `wakeup_preempt()` and by `sched_change_end()`.
- There is no check_class_changed() here; `sched_change_end()` does the class
  comparison.
- `next_active_class()`: skips `fair_sched_class` when `scx_switched_all()`,
  and skips `ext_sched_class` when `scx_enabled()` is false.
- `task_should_scx()` in `kernel/sched/ext/ext.c`: when `scx_enabled()` and
  `scx_switching_all` is set, returns true for every policy, so
  `SCHED_NORMAL`, `SCHED_BATCH` and `SCHED_IDLE` tasks map to ext.
- `task_should_scx()`: tests `scx_switching_all` before `SCX_DISABLING`, so a
  task still maps to ext during teardown while switch-all is set.
- `sched_fork()`: a second, open-coded copy of the mapping; it returns
  `-EAGAIN` for a `dl_prio()` child and never calls
  `__setscheduler_class()`.
- `scx_setscheduler_class()`: what `scx_root_enable_workfn()` and
  `scx_root_disable()` use to pick a task's new class; it returns
  `stop_sched_class` for a stop task and otherwise
  `__setscheduler_class(p->policy, p->prio)`.
- Changing a task into stop or idle through `sched_change`:
  `switching_to_stop()` and `switching_to_idle()` are `BUG()`.

**Class callbacks**

- `struct sched_class` has no member named after `pick_next_task()` and there
  is no pick_next_task_fair function; the fast path in `__pick_next_task()`
  calls `pick_task_fair()` directly and is skipped when `scx_enabled()`.
- `pick_task(rq, rf)`: takes `struct rq_flags *`; returns a task, NULL or
  `RETRY_TASK`.
- `pick_task` may drop the rq lock: `pick_task_fair()` through
  `sched_balance_newidle()`, `pick_task_scx()` through dispatch; both can
  return `RETRY_TASK`, and the core then restarts from the highest class.
- `pick_task_fair()`: can finish the delayed dequeue of the entity it picked
  and pick again; that task is then off the runqueue.
- `balance(rq, rf)`: two arguments; a search for `.balance` shows stop, dl, rt
  and idle define it, fair and ext do not.
- `prev_balance()`: not called on the fair fast path of
  `__pick_next_task()`.
- `enqueue_task` and `dequeue_task`: the class itself calls
  `add_nr_running()` and `sub_nr_running()`; core `enqueue_task()` and
  `dequeue_task()` do not touch `rq->nr_running`.
- `dequeue_task`: returns `bool`; `sched_change_begin()` and
  `deactivate_task()` ignore the result, only `block_task()` acts on it.
- `p->on_rq`: written by `activate_task()` and `deactivate_task()`, not by
  core `enqueue_task()`; `deactivate_task()` sets `TASK_ON_RQ_MIGRATING` and
  warns on `DEQUEUE_SLEEP`.
- `__block_task()`: called by core `block_task()` when the class returns
  `true`; fair calls it itself only when it completes a dequeue with
  `DEQUEUE_DELAYED`; after it the class must not touch `p`.
- `put_prev_task`: also called for a task the class has already dequeued, as
  in `sched_change_begin()`; the class tests its own queued state, as
  `put_prev_task_fair()` does with `se->on_rq`.
- `put_prev_task` with `next == p`: `__schedule()` calls it so, followed by
  `set_next_task` with `first` true, when the donor is unchanged and
  `prev != next` under `sched_proxy_exec()`.
- `set_next_task`: `sched_change_end()` calls it whenever `ctx->running`,
  whether or not the task was re-enqueued.
- Task handed to `put_prev_task`: `rq->donor`, not `rq->curr`; the
  `put_prev_task()` helper and `put_prev_set_next_task()` warn if
  `rq->donor != prev`.
- Task handed to `set_next_task` from the pick: the picked task, which
  `__schedule()` makes `rq->donor` afterwards.

**Enqueue and dequeue flags**

| Flag | Who sets it | What the class does |
|---|---|---|
| `DEQUEUE_MOVE`, `ENQUEUE_MOVE` | callers, with SAVE/RESTORE | position not kept: rt delists and re-adds (`move_entity()`); not a migration flag |
| `DEQUEUE_MIGRATING`, `ENQUEUE_MIGRATING` | only `dequeue_task_dl()` and `enqueue_task_dl()`, from `task_on_rq_migrating()` | dl moves its bandwidth as for SAVE/RESTORE |
| `ENQUEUE_MIGRATED` | `activate_task()` when `task_on_rq_migrating(p)`; `ttwu_do_activate()` for `WF_MIGRATED` | fair clears `se->exec_start` |
| `DEQUEUE_SPECIAL` | `block_task()` for `is_special_task_state()` | fair does not delay the dequeue |
| `DEQUEUE_THROTTLE` | `throttle_cfs_rq_work()`, direct call to `dequeue_task_fair()` | fair does not delay the dequeue |
| `ENQUEUE_REPLENISH` | setters, through `scope->flags`; also passed directly inside `kernel/sched/deadline.c` | dl calls `replenish_dl_entity()` |
| `ENQUEUE_RQ_SELECTED` | `ttwu_do_activate()` for `WF_RQ_SELECTED` | ext reads it as `SCX_ENQ_CPU_SELECTED` |
| `ENQUEUE_QUEUED` | `enqueue_task_fair()`, for `place_entity()` | fair-internal; no core caller passes it |

- Low 16 bits: same value on the dequeue and the enqueue side;
  `sched_change_begin()` warns on `flags & 0xFFFF0000`.
- `kernel/sched/fair.c`: tests none of `DEQUEUE_SAVE`, `ENQUEUE_RESTORE`,
  `DEQUEUE_MOVE`, `ENQUEUE_MOVE`; fair keys on `DEQUEUE_SLEEP` and
  `ENQUEUE_WAKEUP`.
- `DEQUEUE_SAVE` without `ENQUEUE_RESTORE`, core: `psi_enqueue()` and
  `sched_info_enqueue()` run with no dequeue before them.
- `DEQUEUE_SAVE` without `ENQUEUE_RESTORE`, dl: `sub_running_bw()` and
  `sub_rq_bw()` in `dequeue_dl_entity()` are not added back by
  `enqueue_dl_entity()`.
- `uclamp_rq_inc()` and `uclamp_rq_dec()`: do not test SAVE or RESTORE.
- MOVE on one side only, rt: `move_entity()` is evaluated separately on each
  side, so `WARN_ON_ONCE()` on `rt_se->on_list` fires in
  `__enqueue_rt_entity()` or `__dequeue_rt_entity()`.
- ext, dequeue without `DEQUEUE_SLEEP`: `dequeue_task_scx()` adds
  `SCX_DEQ_SCHED_CHANGE`.
- ext, `DEQUEUE_SAVE` on the current task: `dequeue_task_scx()` skips
  `scx_task_slice_ended()`; `ENQUEUE_RESTORE` on it forces the local DSQ.
- `DEQUEUE_SLEEP`: no caller passes it to a `sched_change` scope;
  `deactivate_task()` warns on it, and with it fair may return `false` and
  leave the task queued.

**Changing a queued task**

- Locks asserted: only `lockdep_assert_rq_held(task_rq(p))`, in both
  `sched_change_begin()` and `sched_change_end()`; `p->pi_lock` is not
  asserted.
- Clock: begin calls `update_rq_clock()` itself unless `DEQUEUE_NOCLOCK` is
  passed, then forces `DEQUEUE_NOCLOCK` for both sides.
- Flags: begin adds nothing but `DEQUEUE_NOCLOCK`; the caller passes
  `DEQUEUE_SAVE`.
- "Running" means `task_current_donor()`, not `task_current()`.
- `ctx->queued`: sampled after `switching_from`, so a `sched_delayed` fair
  task that `switching_from_fair()` dequeued is not re-enqueued by end.
- `switched_from`: called in begin, after the dequeue and the put; end calls
  `switching_to`, the enqueue, the set, then `switched_to`.
- `prio_changed`: called by end with no NULL test whenever `ENQUEUE_CLASS` is
  clear, also when nothing about the priority changed; the old value comes
  from `get_prio` if the class has one (dl: the deadline).
- End with `ENQUEUE_CLASS`: reschedules or raises `rq->next_class` only if
  `ctx->running`; a queued, not running task relies on `switched_to`.
- `set_cpus_allowed_force()`: takes only the rq lock, with `__task_rq_lock`.
- Balance callbacks: `prio_changed`, `switched_from` and `switched_to` may
  queue them; the caller runs them before unlock, as `rt_mutex_setprio()`
  does with `__balance_callbacks()`, or splices them off before unlock, as
  `__sched_setscheduler()` does with `splice_balance_callbacks()`;
  `assert_balance_callbacks_empty()` warns under `CONFIG_PROVE_LOCKING`
  otherwise.
- **Potentially unsafe usage**: a `sched_change` scope under the rq lock
  alone.
  - Unsafe: when the scope writes a field read under `p->pi_lock` alone, such
    as `p->sched_class`, which `select_task_rq()` reads after asserting only
    `p->pi_lock`.
  - Safe: an empty scope that writes no attribute, as `scx_bypass()` in
    `kernel/sched/ext/ext.c` does.
- **Potentially unsafe usage**: writing `p->prio` under `DEQUEUE_SAVE`
  without `DEQUEUE_MOVE`.
  - Unsafe: when `p` is in `rt_sched_class` and the value changes;
    `move_entity()` leaves the entity on the list of the old priority.
  - Safe: when the rt or dl priority cannot change, as in `set_user_nice()`,
    which returns early for rt and dl policy and whose `effective_prio()`
    keeps a boosted `p->prio`.
- **Unsafe usage**: passing an enqueue-only flag to `sched_change_begin()`;
  it warns on `flags & 0xFFFF0000`.
  - Safe: OR `ENQUEUE_HEAD` or `ENQUEUE_REPLENISH` into `scope->flags` inside
    the scope, as `rt_mutex_setprio()` does.
- **Unsafe usage**: changing `p->sched_class` in a scope opened without
  `DEQUEUE_CLASS`; `sched_change_end()` warns and no switch callback runs.
  - Safe: compare with `__setscheduler_class()` first and add
    `DEQUEUE_CLASS`, as `__sched_setscheduler()` does.
- **Unsafe usage**: opening a second scope before the first has ended; the
  context is one per-CPU `struct sched_change_ctx` and begin overwrites it.
  - Safe: one scope at a time under the rq lock, as `sched_move_task()` does.
- **Potentially unsafe usage**: writing `p->sched_class` outside a scope.
  - Unsafe: once the task can be queued or be the donor of a runqueue; core
    `dequeue_task()` then calls the new class for a task the old class
    queued.
  - Safe: in `sched_fork()`, where `__sched_fork()` has set `p->on_rq` to 0
    and `wake_up_new_task()` has not yet run.

## Task state

**on_rq, on_cpu and is_blocked**

- `p->is_blocked`: exists, `u8` in `struct task_struct`
  (`include/linux/sched.h`), present with or without
  `CONFIG_SCHED_PROXY_EXEC`.

| `p->is_blocked` | Meaning | Written by | Lock |
|---|---|---|---|
| 1 | task entered `__schedule()`, not as a preemption, with a sleeping `__state`, no pending signal, and has not been woken | `try_to_block_task()`, before it decides whether to dequeue | rq lock |
| 0 | woken, or never blocked | `ttwu_do_wakeup()`; `find_proxy_task()` for `rq->curr` | rq lock; none when `try_to_wake_up()` wakes `current` |

- `p->is_blocked == 1` with `p->on_rq == 1`: the task stayed queued, either
  delayed (`p->se.sched_delayed`) or mutex-blocked under proxy execution.
- `p->is_blocked` is not `task_is_blocked()`: `task_is_blocked()` in
  `kernel/sched/sched.h` tests `p->blocked_on` and `sched_proxy_exec()`.
- `p->blocked_on` set with `p->is_blocked == 0`: a task preempted in the mutex
  slow path before it blocked, or woken without its `blocked_on` being
  cleared; it is picked and runs itself.
- `p->on_rq`: changes under the rq lock alone; `p->pi_lock` is not required
  (`block_task()` from `__schedule()`, `deactivate_task()`).
- `p->on_cpu`: an unconditional `u8`, not limited to SMP builds.
- `task_is_runnable()` in `include/linux/sched.h`: the helper for "is
  runnable"; `task_on_rq_queued()` is not, it is true for a delayed task.
- `task_is_runnable()` does not test `p->is_blocked`: it returns true for a
  mutex-blocked task that proxy execution kept on the runqueue.

**rq->donor and rq->curr**

- `update_se()` in `kernel/sched/fair.c`: charges `sum_exec_runtime`,
  thread-group runtime and `cgroup_account_cputime()` to `rq->curr`; vruntime,
  deadline and RT/DL runtime are charged to the donor's entity.
- `wakeup_preempt()` in `kernel/sched/core.c`: chooses the hook by comparing
  `p->sched_class` with `rq->next_class`, not with `rq->donor->sched_class`;
  the class hooks then compare priority or deadline with `rq->donor`.
- `rq->next_class`: set in `__schedule()` from the picked task before
  `find_proxy_task()` runs; `proxy_resched_idle()` sets it to
  `idle_sched_class`.
- There is no proxy_tag_curr() here. `pick_next_pushable_task()` and
  `pick_next_pushable_dl_task()` skip a task that is `task_on_cpu()`;
  `enqueue_task_rt()`, `put_prev_task_rt()` and the deadline equivalents skip
  the pushable list for a task with `task_is_blocked()`.
- `rq->donor != rq->curr` is also visible inside `__schedule()`:
  `proxy_migrate_task()` sets the donor to `rq->idle` and drops the rq lock
  while `rq->curr` is still the previous task.
- `proxy_reset_donor()`: called from the wakeup path
  (`proxy_needs_return()`), sets `rq->donor` back to `rq->curr` and
  reschedules, so a split can end outside `__schedule()`.

**Consistency at unlock**

- `ttwu_runnable()` in `kernel/sched/core.c`: tests `p->se.sched_delayed` and
  calls `proxy_needs_return()` only inside `if (p->is_blocked)`.
- A queued task that is delayed or proxy-migrated must therefore have
  `p->is_blocked == 1` when the rq lock is released.
- With `p->is_blocked == 0` the waker skips both and sets `TASK_RUNNING`: a
  delayed task stays delayed and a later `pick_next_entity()` that selects it
  dequeues it.
- `p->on_rq == 0` with `p->on_cpu == 0`: the waker moves and enqueues `p`
  without the old rq lock, so `rq->donor` and the class curr pointers must
  not point at `p` when `__block_task()` stores 0.
- `proxy_deactivate()`: calls `proxy_resched_idle()` before `block_task()` for
  that reason; the task is not `rq->curr` and not `on_cpu`, so nothing else
  holds the waker off.
- `proxy_migrate_task()`: releases the rq lock with
  `p->on_rq == TASK_ON_RQ_MIGRATING`, `task_cpu(p)` already the target, and
  `p` on no runqueue. Safe because `__task_rq_lock()` in `ttwu_runnable()`
  spins while `task_on_rq_migrating()`, and `proxy_resched_idle()` ran first.
- `sched_balance_newidle()`, called from the pick in `__schedule()`: releases
  the rq lock while prev has `on_rq == 0` and is still `rq->curr`. Safe
  because `on_cpu` is 1 until `finish_task()`; the waker queues on the wake
  list or spins on `p->on_cpu`.
- `finish_task()` clears `on_cpu` before `finish_lock_switch()` releases the
  lock, so the context switch itself is not such a path.

**Delayed dequeue**

- `__dequeue_task()` in `kernel/sched/fair.c` makes the delay decision and
  returns false; `dequeue_entity()` returns void and never delays.
- dequeue_entities() and finish_delayed_dequeue_entity() are not defined
  here; `dequeue_hierarchy()` walks the levels and `__dequeue_task()` with
  `DEQUEUE_DELAYED` calls `__block_task()` last.
- `DEQUEUE_SPECIAL` or `DEQUEUE_THROTTLE` in the flags: no delay, even with
  `DEQUEUE_SLEEP` and an ineligible entity.
- `task_is_throttled(p)`: `dequeue_task_fair()` returns true before
  `__dequeue_task()` is reached.
- `DEQUEUE_SLEEP | DEQUEUE_DELAYED` is passed in three places:
  `pick_next_entity()`, `wait_task_inactive()` and `switching_from_fair()`.
- Migration and `DEQUEUE_SAVE`/`ENQUEUE_RESTORE` changes (affinity, nice,
  cgroup move) dequeue without `DEQUEUE_DELAYED`: `se.sched_delayed` stays
  set and the task is enqueued again still delayed.
- Nothing watches eligibility: a delayed task that is not woken leaves when
  `pick_next_entity()` selects it, or through `wait_task_inactive()` or
  `switching_from_fair()`.
- `pick_next_entity()` is also called from `wakeup_preempt_fair()`, so a
  delayed task can reach `p->on_rq == 0` during the wakeup of another task.
- **Potentially unsafe usage**: using `p` after `dequeue_task()` with
  `DEQUEUE_SLEEP | DEQUEUE_DELAYED`.
  - Unsafe: holding only the rq lock; `__block_task()` has stored
    `p->on_rq = 0` and `try_to_wake_up()` may be enqueuing `p` on another rq.
  - Safe: holding `p->pi_lock` as well, which `try_to_wake_up()` takes before
    it reads `p->on_rq`; `wait_task_inactive()` does so through
    `task_rq_lock()`.

**Proxy execution**

- Boot parameter `sched_proxy_exec`, static key `__sched_proxy_exec`
  (default true, defined under `CONFIG_SCHED_PROXY_EXEC`), test
  `sched_proxy_exec()`; see `setup_proxy_exec()` in `kernel/sched/core.c`.
- `__schedule()` calls `find_proxy_task()` when `next->is_blocked` is set, not
  when `next->blocked_on` is set; the walk loops while `p->is_blocked`.
- `p->blocked_on`: guarded by `p->blocked_lock`, which
  `__set_task_blocked_on()` and `__clear_task_blocked_on()` assert;
  `clear_task_blocked_on()` clears it without the mutex `wait_lock`.

| Step in `find_proxy_task()`, for chain task `p` | `rq->curr` in chain | Otherwise |
|---|---|---|
| `p->blocked_on` is NULL, or mutex has no owner | only if `p` itself is `rq->curr`: clear `p->is_blocked`, return `p` | `proxy_deactivate(rq, p)`, return NULL |
| `owner->on_rq` is 0, or `sched_delayed` | `proxy_resched_idle()` | clear `p->blocked_on`, `proxy_deactivate(rq, p)` |
| owner on another CPU | `proxy_resched_idle()` | `proxy_migrate_task()` to the owner's CPU, return NULL |

- `proxy_migrate_task()`: moves `p`, the chain task whose owner is remote,
  which need not be the donor.
- `proxy_migrate_task()` sequence: `proxy_resched_idle()`,
  `deactivate_task()`, `proxy_set_task_cpu()`, drop the rq lock,
  `attach_one_task()` on the target, retake the lock.
- Return migration: on wakeup `proxy_needs_return()` sees
  `task_cpu(p) != p->wake_cpu`, dequeues `p` unless it is `rq->curr`, and
  `try_to_wake_up()` places it with `select_task_rq()` starting from
  `p->wake_cpu`.
- `find_proxy_task()` returning `rq->idle`: `__schedule()` jumps to
  `keep_resched` and switches to idle with need-resched set, so the pick is
  retried.

## Locks, affinity and migration

**Runqueue lock**

- `__rq_lockp()` in `kernel/sched/sched.h`: tests `rq->core_enabled` only.
  `rq_lockp()` tests `sched_core_enabled()`, which is the static key
  `__sched_core_enabled` and `rq->core_enabled`.
- `raw_spin_rq_lock_nested()` and `raw_spin_rq_trylock()`: test
  `sched_core_disabled()` first and then take `&rq->__lock`; otherwise they
  loop on `__rq_lockp()`.
- `raw_spin_rq_unlock()`: unlocks `rq_lockp()`. `lockdep_assert_rq_held()`,
  `rq_pin_lock()`, `rq_unpin_lock()` and `rq_repin_lock()` use `__rq_lockp()`.
- Lock other than the embedded one: only when `rq->core_enabled` is set and
  `rq->core != rq`. For the core leader `rq->core == rq`, so it gets its own
  `__lock`.
- `rq->core` is written by CPU hotplug, not by core-scheduling enable: see
  `sched_core_cpu_starting()`, `sched_core_cpu_deactivate()` and
  `sched_core_cpu_dying()` in `kernel/sched/core.c`. `rq->core_enabled` is
  written by `__sched_core_flip()`.
- `__sched_core_flip()`: for each online core, spins until
  `rq->core->core_pick_in_flight` is zero before it writes `core_enabled`.
  With `sched_core_enabled(rq)` on an online CPU, `pick_next_task()` raises
  the counter and drops it at `out_set_next`.
- `rq_pin_lock()`: also calls `assert_balance_callbacks_empty()`, which warns
  under `CONFIG_PROVE_LOCKING` when `rq->balance_callback` holds anything but
  `balance_push_callback`.
- Guards: there is no guard for `raw_spin_rq_lock_irq()`. The raw guard is
  `raw_spin_rq_lock_irqsave`; `__task_rq_lock` is a guard too. Search
  `kernel/sched/sched.h` for `DEFINE_LOCK_GUARD_1` and `DEFINE_LOCK_GUARD_2`.
- **Potentially unsafe usage**: taking `&rq->__lock` directly instead of
  through a wrapper.
  - Unsafe: when `rq->core_enabled` can be set for `rq`. Other CPUs then
    serialise on `&rq->core->__lock`, which this does not take.
  - Safe: `sched_core_lock()`, which takes the embedded lock of every CPU in
    `cpu_smt_mask()`, the core leader included.
  - Safe: after `sched_core_disabled()` returned true with preemption off, as
    `raw_spin_rq_lock_nested()` does. This pairs with `synchronize_rcu()` in
    `__sched_core_enable()`.

**Lock order**

- `rq_order_less()` in `kernel/sched/sched.h`: compares `rq->core->cpu`
  first and `rq->cpu` second. It never compares lock pointers.
- `rq_order_less()` core-first order: selected by `CONFIG_SCHED_CORE` at build
  time. It applies whether or not core scheduling is enabled at run time,
  because `sched_core_cpu_starting()` sets `rq->core` without testing whether
  core scheduling is enabled.
- `p->pi_lock` under a runqueue lock: no trylock escape exists. The only
  trylock in `_double_lock_balance()` is `raw_spin_rq_trylock(busiest)`, and
  only without `CONFIG_PREEMPTION`.
- `_double_lock_balance()` with `CONFIG_PREEMPTION`: always unlocks `this_rq`,
  calls `double_rq_lock()` and returns 1.
- `_double_lock_balance()` without `CONFIG_PREEMPTION`: returns 0 without
  dropping `this_rq` when both share a lock, when the trylock succeeds, or
  when `rq_order_less(this_rq, busiest)`. Otherwise it drops and returns 1.
- `kernel/sched/cpupri.c`: takes no lock. Nothing from cpupri nests inside a
  runqueue lock.
- Timer base lock of `struct hrtimer_cpu_base`: nests inside the runqueue lock
  and inside `cfs_b->lock`; `start_cfs_bandwidth()` asserts `cfs_b->lock` and
  starts the period timer.
- `CONFIG_SCHED_PROXY_EXEC`: `find_proxy_task()` takes `mutex->wait_lock` and
  then `p->blocked_lock` while it holds the runqueue lock.
  `proxy_needs_return()` takes `p->blocked_lock` under the runqueue lock.
- Other locks seen taken under a runqueue lock, for example: `dl_b->lock` in
  `dl_task_offline_migration()`, `rd->rto_lock` in `tell_cpu_to_push()`,
  `cp->lock` in `cpudl_set()`, `cfs_b->lock` in `throttle_cfs_rq()`. Search
  `kernel/sched/` for `raw_spin_lock` to list the rest.

**Locking a task's runqueue**

- `task_rq_lock()` and `__task_rq_lock()`: macros in `kernel/sched/sched.h`.
  The bodies are `_task_rq_lock()` and `___task_rq_lock()` in
  `kernel/sched/core.c`.
- `___task_rq_lock()`: requires `p->pi_lock`; it opens with
  `lockdep_assert_held(&p->pi_lock)`.
- `p->pi_lock` alone: keeps `task_cpu()` stable only while `p->on_rq` is 0.
  A queued task is moved under the runqueue lock alone, as `detach_task()`
  in `kernel/sched/fair.c` does.
- Runqueue lock alone: keeps `task_cpu()` stable only while `p->on_rq` is
  non-zero. After `__block_task()` stores 0 for a task that is not on a CPU,
  `try_to_wake_up()` can move the task under `p->pi_lock` alone; a caller
  that does not hold `p->pi_lock` must not touch `p` afterwards.
- `p->on_cpu`: written by `prepare_task()` and `finish_task()` under the
  runqueue lock. `p->pi_lock` does not cover it.
- **Potentially unsafe usage**: locking `task_rq(p)` and then treating `p` as
  being on that runqueue, with no test after the lock is taken.
  - Unsafe: when the task can be queued or woken meanwhile. The task may have
    moved, or be `TASK_ON_RQ_MIGRATING`, before the lock is held.
  - Safe: under `p->pi_lock` for a task in `TASK_WAKING` that is off the
    runqueue, as `migrate_task_rq_dl()` does. `try_to_wake_up()`, which
    holds `p->pi_lock`, changes the CPU of such a task.
  - Safe: take `p->pi_lock` and a known runqueue lock, then test
    `task_rq(p) == rq`, as `migration_cpu_stop()` and `push_cpu_stop()` do.
  - Safe: `task_rq_lock()`, which re-tests after it locks.

**Moving a task between CPUs**

- Checks in `set_task_cpu()`: unconditional `WARN_ON_ONCE()` calls. There is
  no CONFIG_SCHED_DEBUG option in this tree. Only the lock check is
  conditional, on `CONFIG_LOCKDEP` and `debug_locks`.
- Lock check: tests `p->pi_lock` or `__rq_lockp(task_rq(p))`, where
  `task_rq(p)` is still the old runqueue.
- Queued-but-not-migrating check: applies to `fair_sched_class` tasks in
  `TASK_RUNNING` only.
- Migration-disabled check: suppressed when `proxy_migrated` is true, that is
  `sched_proxy_exec()`, `p->is_blocked` and `task_cpu(p) != p->wake_cpu`.
- `set_task_cpu()` makes no test of `p->cpus_ptr` against `new_cpu`.
- Unchanged CPU: `trace_sched_migrate_task()` and `__set_task_cpu()` still
  run. Only the `p->sched_class->migrate_task_rq` callback,
  `p->se.nr_migrations` and `perf_event_task_migrate()` are skipped.
- `set_task_cpu()` calls no rseq or mm_cid hook itself; there is no
  rseq_migrate() here. `__set_task_cpu()` calls
  `rseq_sched_set_ids_changed()`.
- New tasks: `sched_cgroup_fork()` and `wake_up_new_task()` call
  `__set_task_cpu()` under `p->pi_lock`, not `set_task_cpu()`, so the
  `migrate_task_rq` callback and the checks do not run.
- `proxy_set_task_cpu()` under `CONFIG_SCHED_PROXY_EXEC`: calls
  `__set_task_cpu()` and restores `p->wake_cpu`. `proxy_migrate_task()` uses
  it to move a blocked task, possibly to a CPU outside `p->cpus_ptr`.
- Helper choice for a queued task:

| Helper | Locks on entry | Locks on return |
|---|---|---|
| `move_queued_task()` | source runqueue | destination runqueue only |
| `move_queued_task_locked()` in `kernel/sched/sched.h` | both runqueues | both runqueues |

- **Potentially unsafe usage**: `set_task_cpu()` on a task whose `p->on_rq` is
  `TASK_ON_RQ_QUEUED`.
  - Unsafe: with one runqueue lock held. `_task_rq_lock()` relies on
    `task_on_rq_migrating()` to reject a task in flight. For a fair task in
    `TASK_RUNNING` `set_task_cpu()` warns in any case.
  - Safe: call `deactivate_task()` first, which sets
    `TASK_ON_RQ_MIGRATING`, as `move_queued_task()` and `detach_task()` do.
  - Safe: a non-fair task with `p->pi_lock` and both runqueue locks held, as
    `dl_task_offline_migration()` called from `dl_task_timer()`.

**Changing affinity**

- `p->cpus_ptr` under migration disable: narrowed only after the task entered
  `__schedule()`; see "CPU mask under migration disable".
- `p->user_cpus_ptr`: an affinity change writes it only with `SCA_USER`.
  `sched_setaffinity()` sets it; `set_cpus_allowed_force()` resets it to
  NULL. `task_user_cpus()` returns `cpu_possible_mask` when it is NULL.
- `p->user_cpus_ptr` contents: protected by `p->pi_lock`; see
  `dup_user_cpus_ptr()`.
- `set_cpus_allowed_ptr()` on a task with `p->user_cpus_ptr`:
  `__set_cpus_allowed_ptr()` replaces the requested mask by its intersection
  with `p->user_cpus_ptr`, unless that is empty. `p->cpus_mask` can end up
  narrower than requested.
- `do_set_cpus_allowed()`: static in `kernel/sched/core.c`. Outside callers
  use `set_cpus_allowed_force()`, which needs `p->pi_lock` held by the
  caller, as `__kthread_bind_mask()` does.
- `-EINVAL` for a mask outside the allowed CPUs: the test is
  `cpumask_subset()` against `task_cpu_possible_mask()`, for non-kthreads
  only. There is no per-CPU kthread test.
- `-EINVAL` for `cpu_active_mask`: only when the mask has no CPU in it; the
  mask need not be a subset. Kthreads and migration-disabled tasks are tested
  against `cpu_online_mask` instead.
- `dl_task_check_affinity()` (`-EBUSY`) and the cpuset intersection: in
  `__sched_setaffinity()` in `kernel/sched/syscalls.c`, before
  `__set_cpus_allowed_ptr()` is called. Kernel callers of
  `set_cpus_allowed_ptr()` get neither.
- Equal mask without `SCA_MIGRATE_ENABLE`: returns 0 at once and does not
  wait. With `SCA_USER` it still swaps `p->user_cpus_ptr`.
- `affine_move_task()` `-EINVAL`: returned with a warning when no
  `p->migration_pending` exists after the install step.
- `affine_move_task()` returns without waiting when `task_cpu(p)` is in
  `&p->cpus_mask`, when `p` is the runqueue's donor but not its current task,
  or when `SCA_MIGRATE_ENABLE` is set and the task is on a CPU.
- Second wait in `affine_move_task()`: after `wait_for_completion()`, the
  caller that installed `my_pending` waits in `wait_var_event()` until every
  later caller has dropped its reference.

**Migration disable**

- `__migrate_disable()` and `__migrate_enable()`: inline in
  `include/linux/sched.h`. They change `rq->nr_pinned` through
  `this_rq_pinned()`. `migrate_disable()` in `kernel/sched/core.c` is the
  exported copy for modules.
- `___migrate_enable()` in `kernel/sched/core.c`: the slow path. It runs only
  when `p->cpus_ptr != &p->cpus_mask`, that is, only if the task entered
  `__schedule()` while disabled.
- `migrate_disable()` and `migrate_enable()` themselves do not block: the
  outermost calls run under `guard(preempt)()`. `__set_cpus_allowed_ptr()`
  with `SCA_MIGRATE_ENABLE` returns before `wait_for_completion()`.
- `task_cpu(p)` seen by other CPUs: not guaranteed stable with
  `CONFIG_SCHED_PROXY_EXEC`. `proxy_migrate_task()` can move a blocked
  migration-disabled task to another runqueue; `try_to_wake_up()` returns it.
- `affine_move_task()` for a task that is on a CPU or in `TASK_WAKING`: does
  not test `is_migration_disabled()`. It queues `migration_cpu_stop()`, which
  makes the test, leaves the request pending and clears `stop_pending`.
- `affine_move_task()` for a task that is neither: tests
  `is_migration_disabled()` itself, skips `move_queued_task()` and waits.
- CPU offline: the wait for `rq->nr_pinned` to reach zero is in
  `balance_hotplug_wait()`, under `CONFIG_HOTPLUG_CPU`. `balance_push()` does
  not wait; it wakes that waiter.

**CPU mask under migration disable**

- Call site: `__schedule()` calls `migrate_disable_switch()` for `prev` after
  `local_irq_disable()` and `rcu_note_context_switch()`, before `rq_lock()`.
  The runqueue lock is not held on entry.
- Locks: it takes `p->pi_lock` and the runqueue lock itself with
  `scoped_guard (task_rq_lock, p)`, and drops both before returning.
- It runs on every entry to `__schedule()`, whether or not `prev` is then
  switched out.
- Change: `do_set_cpus_allowed()` with `SCA_MIGRATE_DISABLE` and
  `cpumask_of(rq->cpu)`. There is no __do_set_cpus_allowed() in this tree.
- `set_cpus_allowed_common()` with `SCA_MIGRATE_DISABLE` or
  `SCA_MIGRATE_ENABLE`: writes `p->cpus_ptr` and returns.
  `p->nr_cpus_allowed`, `p->cpus_mask` and `p->user_cpus_ptr` keep their
  values.
- Between `migrate_disable()` and the next `__schedule()`: `p->cpus_ptr`
  still equals `&p->cpus_mask`.
- **Potentially unsafe usage**: deciding that a task may be moved from
  `p->nr_cpus_allowed` or `p->cpus_ptr` alone.
  - Unsafe: from `p->nr_cpus_allowed`, which migration disable never changes,
    or from `p->cpus_ptr` of a task that may be on a CPU; `set_task_cpu()`
    warns for a migration-disabled task.
  - Safe: from `p->cpus_ptr` of a task that is not on a CPU, since it has
    passed `migrate_disable_switch()`; `can_migrate_task()` in
    `kernel/sched/fair.c` also rejects `task_on_cpu()`.
  - Safe: test `is_migration_disabled()` as well, as `select_task_rq()` does;
    `get_push_task()` tests `p->migration_disabled`.
  - Safe: test `is_migration_disabled()` before the mask, as
    `task_can_run_on_remote_rq()` in `kernel/sched/ext/ext.c` does.

## Blocking and waking

**The schedule path**

- Barrier: `__schedule()` calls `rq_lock()` then `smp_mb__after_spinlock()`;
  there is no smp_mb__before_spinlock() in this tree.
- `smp_mb__after_spinlock()`: orders the caller's state store, which may be a
  plain `__set_current_state()`, before the `signal_pending_state()` load in
  `try_to_block_task()`.
- `TASK_RUNNING` store on a still-queued task, for `p != current`: made by
  `ttwu_runnable()` under the same rq lock, so the lock itself orders it
  against the `prev_state` read.
- `hrtick_schedule_enter()` (`CONFIG_SCHED_HRTICK`): runs right after the
  barrier; while `rq->hrtick_sched` is set, `hrtick_start()` called during the
  pick only records the delay, and `hrtick_schedule_exit()` arms the timer.
- `rq->clock_update_flags = RQCF_UPDATED`: stored directly after
  `update_rq_clock()`, before `try_to_block_task()` and the pick, so
  `RQCF_ACT_SKIP` covers only that one `update_rq_clock()` call.
- `block_task()` flags: `DEQUEUE_SLEEP | DEQUEUE_NOCLOCK`, plus
  `DEQUEUE_SPECIAL` when `is_special_task_state()` matches `prev_state`.
- `should_block`: `__schedule()` passes `!task_is_blocked(prev)`; it is false
  only when `sched_proxy_exec()` is true and `prev->blocked_on` is set, and
  then `prev` stays queued.
- Signal branch of `try_to_block_task()`: besides storing `TASK_RUNNING` it
  writes `*task_state_p`, so `trace_sched_switch()` reports a running `prev`,
  and calls `clear_task_blocked_on()`; `p->is_blocked` stays 0.
- `switch_count = &prev->nvcsw`: assigned after `try_to_block_task()`
  whatever it returned, so a sleep cancelled by a signal that still switches
  counts as voluntary.
- `preempt` has two meanings: `sched_mode > SM_NONE` for `schedule_debug()`
  and `rcu_note_context_switch()`; `sched_mode == SM_PREEMPT` from the
  `prev_state` read onwards.
- `SM_RTLOCK_WAIT`: preemption only in the first meaning; `prev` blocks on its
  state like `SM_NONE`.
- `SM_RTLOCK_WAIT` and `saved_state`: `__schedule()` never touches it;
  `current_save_and_set_rtlock_wait_state()` in the caller does.
- `SM_RTLOCK_WAIT` and signals: `signal_pending_state()` still runs and
  returns 0, because `TASK_RTLOCK_WAIT` has neither `TASK_INTERRUPTIBLE` nor
  `TASK_WAKEKILL`.
- `SM_IDLE`: is -1, so preemption in neither meaning; `try_to_block_task()`
  is never called; a switch is still counted, in `prev->nivcsw`.
- `SM_IDLE` shortcut: with `rq->nr_running` 0 and `scx_enabled()` false it
  sets `next = prev` and `rq->next_class = &idle_sched_class` by hand and
  jumps past the pick.

**Wake-up paths**

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

**Sleep and wake ordering**

- `prepare_to_wait()`, `prepare_to_wait_exclusive()` and
  `prepare_to_wait_event()`: call `set_current_state()`, not
  `__set_current_state()`, although they hold `wq_head->lock`.
- Lockless `waitqueue_active()` wakers: rely on that barrier and need their
  own `smp_mb()` after the condition store; `wq_has_sleeper()` in
  `include/linux/wait.h` supplies it.
- **Potentially unsafe usage**: `__set_current_state()` to a sleeping state
  before `schedule()`.
  - Unsafe: when a condition test follows and the waker stores the condition
    without a lock that the sleeper holds across the state store; the store
    can pass the condition load, which the `smp_store_mb()` in
    `set_current_state()` prevents.
  - Safe: the state store is under the lock that the waker holds when it
    stores the condition, as `___down_common()` in
    `kernel/locking/semaphore.c` does under `sem->lock`.
  - Safe: `do_wait_for_common()` in `kernel/sched/completion.c`, under
    `x->wait.lock`, which `complete()` holds across the store and the wake-up.
  - Safe: no condition is tested and `schedule()` is called unconditionally,
    as `schedule_timeout_interruptible()` in `kernel/time/sleep_timeout.c`
    does.
- **Potentially unsafe usage**: a call that can sleep between
  `set_current_state()` and `schedule()`.
  - Unsafe: when the call sleeps on most passes, or no loop tests the
    condition again; the call returns in `TASK_RUNNING`, so the following
    `schedule()` does not block.
  - Safe: the call seldom sleeps and the loop stores the state and tests the
    condition again, so a sleep costs one extra pass; `resolve_symbol()` in
    `kernel/module/main.c`, the condition of a
    `wait_event_interruptible_timeout()`, does so after
    `sched_annotate_sleep()`.
  - Safe: `wait_woken()` with `woken_wake_function()`; the state is stored
    only inside `wait_woken()`, after the caller's condition test.
- `__might_sleep()` warning for that usage: built only with
  `CONFIG_DEBUG_ATOMIC_SLEEP`, and silent once `sched_annotate_sleep()` has
  cleared `current->task_state_change`.
- `TASK_INTERRUPTIBLE` and `TASK_KILLABLE` loops: with a matching signal
  pending, `try_to_block_task()` stores `TASK_RUNNING` and `schedule()` returns
  without sleeping, so the loop needs its own signal exit.
- `___wait_event()`: gets that exit from the return value of
  `prepare_to_wait_event()`.
- Special states: `is_special_task_state()` in `include/linux/sched.h` defines
  the set; besides stopped, traced and dead it holds `TASK_PARKED`,
  `TASK_FROZEN` and `TASK_WAKING`.
- Setter checks under `CONFIG_DEBUG_ATOMIC_SLEEP`: `set_current_state()` and
  `__set_current_state()` warn on a special state; `set_special_state()` warns
  on a normal one.
- `set_special_state()` user: `__kthread_parkme()` in `kernel/kthread.c`
  stores `TASK_PARKED` with it.

## Fair class

**Fair task queueing**

- Rbtree: the task's entity goes into `rq->cfs.tasks_timeline`, whatever
  its group; `enqueue_task_fair()` calls `__enqueue_entity()` on `&rq->cfs`.
- `__enqueue_entity()` and `__dequeue_entity()`: warn if the runqueue is not
  `&rq->cfs` or the entity is not a task.
- `cfs_rq_of(se)`: still the group's runqueue, used for accounting only.
- `enqueue_hierarchy()`: walks every level to the root; `enqueue_entity()`
  there updates PELT, `load`, `nr_queued` and `on_rq`, inserts in no tree.
- A task that is `rq->cfs.curr` is placed but not inserted; `curr` stays
  outside the tree until `put_prev_task_fair()`.
- `pick_task_fair()`: one `pick_next_entity(rq, true)` on `rq->cfs`; it does
  not call `group_cfs_rq()` and does not descend.
- `se->h_load` of the task: the stored hierarchical weight; `se->load` stays
  the per-level weight (nice for a task, shares for a group entity).
- `calc_delta_fair()`, `avg_vruntime_weight()` callers and
  `hrtick_start_fair()` use `se->h_load`, not `se->load`.
- `__calc_prop_weight()`: its callers start from `NICE_0_LOAD`; at each level
  it multiplies by `se->load.weight` and divides by `cfs_rq->load.weight` (by
  `NICE_0_LOAD` at the top level), floor `MIN_SHARES` per level.
- `reweight_eevdf()`: applies the result to `se->h_load` and rescales lag,
  deadline and protection.
- `se->h_load` is refreshed only by callers of `reweight_eevdf()`, for example
  `enqueue_task_fair()`, `set_next_task_fair()` and `task_tick_fair()`; a
  queued task that is not running keeps a stale value in between.
- `reweight_entity()`: changes `se->load`, `cfs_rq->load` and the PELT load
  only; it does not touch `vruntime`, `vlag` or `deadline`.
- `calc_group_shares`: a static call, not a function; default
  `calc_concur_shares()`, which scales `tg->shares` by the smaller of
  `tg_tasks()` and `tg_cpus()`.
- `__sched_cgroup_mode_update()`: switches the static call from the debugfs
  file `cgroup_mode`; it selects one of five functions, `calc_concur_shares()`
  among them.
- `__calc_smp_shares()`: holds the load fraction formula; clamps to
  `MIN_SHARES`..`shares_max`, and `shares_max` can exceed `tg->shares`.

**Group entities and runqueues**

- Storage: `struct task_group` has a `__percpu` `cfs_rq` pointer and no `se`
  array; entity and runqueue sit together in `struct cfs_tg_state`.
- Accessors: `tg_cfs_rq()`, `tg_se()` and `cfs_rq_se()` in
  `kernel/sched/sched.h`; `tg_se()` returns NULL for the root group.
- A group entity is never in an rbtree and never picked.
- Group entity `vruntime`, `deadline`, `slice`: not maintained;
  `update_curr()` returns before the vruntime update for a non-task entity.
- Group entity is used for: its `load.weight` (input to
  `__calc_prop_weight()`), PELT propagation, `on_rq` accounting in the
  parent's `load` and `nr_queued`, and the `parent` chain that the per-level
  walks follow.
- `cfs_rq->h_curr`: the running entity of each level, set by
  `set_next_entity()`; `update_curr()`, `throttle_cfs_rq()` and
  `kernel/sched/pelt.c` read it.
- `cfs_rq->curr` and `cfs_rq->next`: set only on `rq->cfs`, always to a task
  entity; see `set_next_task_fair()` and `set_next_buddy()` callers.
- A group's `struct cfs_rq`: its `tasks_timeline`, `sum_w_vruntime` and
  `sum_weight` stay empty.
- A group's `struct cfs_rq` holds: `load`, the four counters, `h_curr`,
  `avg`, `h_load`, bandwidth state and `throttled_limbo_list`.
- `sched_delayed`: set only on task entities; the only caller of
  `set_delayed()` is `__dequeue_task()`, with `&p->se`.
- `dequeue_hierarchy()`: stops dequeueing parents once a level's
  `cfs_rq->load.weight` is non-zero; there is no dequeue_entities() here.

**cfs_rq task counters**

- `nr_queued`: entities accounted at this level by `account_entity_enqueue()`
  (tasks and group entities with this `cfs_rq_of()`); on `rq->cfs` it is not
  the size of the rbtree.
- `rq->cfs.h_nr_queued`: the number of tasks competing in the tree, `curr`
  and delayed tasks included.
- "Anything to pick" and "only one task": test `rq->cfs.h_nr_queued`, as
  `pick_task_fair()`, `pick_eevdf()` and `update_curr()` do.
- First or last entity of a level: test `nr_queued`, as `enqueue_entity()`,
  `dequeue_entity()` and `tg_throttle_down()` do.
- `sched_fair_runnable()`: tests `rq->cfs.nr_queued > 0`; valid for
  emptiness only, not for a count of tasks.
- `place_entity()`: reads `h_nr_queued` as the number of other tasks; a
  caller that already counted the entity passes `ENQUEUE_QUEUED` or lowers
  the counter around the call, as `requeue_delayed_entity()` does.
- `sched_idle_rq()`: compares `rq->nr_running` with `rq->cfs.h_nr_idle`.
- Counter walks: `enqueue_hierarchy()`, `dequeue_hierarchy()`,
  `set_delayed()` and `clear_delayed()` go to the root; none stops at a
  throttled level.
- A throttled task on a limbo list: in none of the four counters and not in
  `rq->nr_running`.
- Delayed tasks: no counter field; `cfs_h_nr_delayed()` returns
  `h_nr_queued - h_nr_runnable` of `rq->cfs`.

**Entity fields**

- `vlag` and `vprot`: two separate members of `struct sched_entity`; they
  share no storage.
- `se->vlag` of a queued entity: the stale value from the last
  `update_entity_lag()` or `reweight_eevdf()`, not a protection value.
- Each rbtree node carries three subtree values: `min_vruntime`, `min_slice`
  and `max_slice`; see `min_vruntime_update()`.
- `cfs_rq_max_slice()`: reads `max_slice` of the root node and `curr->slice`.
- `entity_lag()`: clamps to plus or minus
  `calc_delta_fair(cfs_rq_max_slice(cfs_rq) + TICK_NSEC, se)`; the limit
  depends on the longest slice queued, not on `se->slice`.
- `calc_delta_fair()`: scales by `se->h_load`, so the clamp follows the
  hierarchical weight.
- `update_entity_lag()` on a `sched_delayed` entity: the new lag is not
  below the stored `se->vlag`, and with `DELAY_ZERO` not above 0.
- `update_entity_lag()`: returns true when the stored lag differs from
  `avg_vruntime() - se->vruntime`; `requeue_delayed_entity()` then places
  the entity again.
- `rescale_entity()`: called from `reweight_eevdf()`; scales `vlag`, a
  relative `deadline` and a relative `vprot` by old over new `h_load` weight.

**Virtual time of a runqueue**

- Fields: `zero_vruntime`, `sum_w_vruntime` (sum of key times weight) and
  `sum_weight`, plus `curr` when it is on_rq.
- Weights in the sums: `avg_vruntime_weight(cfs_rq, se->h_load.weight)`; not
  `se->load.weight`, and not passed through `scale_load_down()`.
- `avg_vruntime()` writes: it calls `update_zero_vruntime()` with the
  computed offset and returns the new `cfs_rq->zero_vruntime`.
- `zero_vruntime` moves on every `avg_vruntime()` call: `place_entity()`,
  `update_entity_lag()`, `update_deadline()` once the deadline is passed,
  `reweight_eevdf()` for a queued entity, `update_protect_slice()` and
  `print_cfs_rq()`.
- `place_entity()`: also calls `update_zero_vruntime()` directly when the
  placed entity is heavier than everything queued.
- `__enqueue_entity()` and `__dequeue_entity()`: do not move
  `zero_vruntime`.
- `entity_tick()`: moves `zero_vruntime` only through `update_curr()`, when
  `update_deadline()` finds the deadline passed.
- `vruntime_eligible()`: reads the same fields and writes nothing.
- `update_zero_vruntime(cfs_rq, delta)`: takes the shift and compensates
  `sum_w_vruntime` itself; there is no avg_vruntime_update().
- `sum_w_vruntime_add()` and `sum_w_vruntime_sub()`: the only writers of the
  sums besides the shift; called from `__enqueue_entity()` and
  `__dequeue_entity()`. There is no avg_vruntime_add() or
  avg_vruntime_sub().
- `reweight_eevdf()`: the function that takes a queued entity out, changes
  `h_load` and `vruntime`, and puts it back.
- `cfs_rq->sum_shift`: with `PARANOID_AVG`, an overflow in
  `sum_w_vruntime_add_paranoid()` raises it and rebuilds both sums from the
  tree.
- **Unsafe usage**: adding `se->h_load.weight` to `sum_weight` or a
  comparison without `avg_vruntime_weight()`.
  - Safe: take every weight through `avg_vruntime_weight()`, as
    `vruntime_eligible()` and `place_entity()` do; it applies `sum_shift`
    under `CONFIG_64BIT`.

**Picking an entity**

- One competition: `pick_next_entity(rq, protect)` runs `pick_eevdf()` on
  `rq->cfs` only; eligibility and deadlines compare tasks of all groups.
- `pick_eevdf()` early returns, in order:

| Test | Returns |
|---|---|
| `cfs_rq->h_nr_queued == 1` | `curr` if on_rq, else the leftmost |
| `PICK_BUDDY`, `protect`, `cfs_rq->next` set and eligible | `cfs_rq->next` |
| `curr` on_rq and eligible, `protect`, `protect_slice(curr)` | `curr` |

- Buddy test: lives in `pick_eevdf()`, not in `pick_next_entity()`; it comes
  before the slice protection of `curr`.
- Leftmost eligible entity: skips the tree search but not the final
  comparison; `curr` is returned instead if `entity_before(curr, best)`.
- `protect` false: skips both the buddy and the slice protection;
  `wakeup_preempt_fair()` passes false for `PREEMPT_WAKEUP_SHORT`,
  `pick_task_fair()` passes true.
- `protect_slice()`: true while `se->vruntime` is before `se->vprot`; it
  does not compare `vlag` with `deadline`.
- `set_protect_slice()`: with `PREEMPT_SHORT` and, under `RUN_TO_PARITY`, a
  shorter slice queued, `vprot` is capped at `ineligible_vruntime()`, the
  point where `curr` stops being eligible.
- `set_next_buddy()`: refuses an entity for which `se_is_idle()` is true.
- Delayed pick: `pick_next_entity()` calls `__dequeue_task()` with
  `DEQUEUE_SLEEP | DEQUEUE_DELAYED` and returns NULL.
- **Unsafe usage**: calling `pick_next_entity()` when `rq->cfs.h_nr_queued`
  may be 0; it dereferences the result of `pick_eevdf()` unchecked.
  - Safe: test `h_nr_queued` first and retry on NULL, as `pick_task_fair()`
    and `wakeup_preempt_fair()` do.

**Load tracking signals**

- State sampled for the elapsed interval: `__update_load_avg_cfs_rq()` reads
  `cfs_rq->load.weight`, `cfs_rq->h_nr_runnable` and `cfs_rq->h_curr`;
  `__update_load_avg_se()` reads `se->on_rq`, `se_runnable()` and
  `cfs_rq->h_curr == se`.
- A change of `h_curr` or `h_nr_runnable` therefore needs the update first
  too; `set_next_entity()` and `put_prev_entity()` do so, and
  `__dequeue_task()` does so before `set_delayed()` for the task's own
  level only.
- `dequeue_entity()` order: `update_load_avg()`, `se_update_runnable()`,
  `account_entity_dequeue()`, then `update_cfs_group()`; `enqueue_entity()`
  calls `update_cfs_group()` before `account_entity_enqueue()`.
- `update_curr()`: not called by `enqueue_entity()` or `dequeue_entity()`;
  `enqueue_hierarchy()` and `dequeue_hierarchy()` call it per level first.
- Ancestor levels: updated by the loops in `enqueue_hierarchy()` and
  `dequeue_hierarchy()`.
- `UPDATE_UTIL_EST`: a fifth flag; `dequeue_entity()` passes it for a task
  going to sleep (`DEQUEUE_SLEEP` without `DEQUEUE_DELAYED`) and
  `__dequeue_task()` when it delays the dequeue.
- `cfs_rq->pelt_clock_throttled`: the only state that freezes
  `cfs_rq_clock_pelt()`; it is set for a runqueue in a throttled hierarchy
  only while `nr_queued` is 0.
- A throttled runqueue that still has entities queued: its PELT clock keeps
  advancing; see `tg_throttle_down()` and the end of `dequeue_entity()`.
- `enqueue_entity()` on the first entity and `tg_unthrottle_up()`: restart
  the clock and add the frozen span to `throttled_clock_pelt_time`.
- Idle CPU: `update_rq_clock_pelt()` sets `rq->clock_pelt` to
  `rq_clock_task()`; the clock does not stall.

**Bandwidth throttling**

- Arming points of `throttle_cfs_rq_work()`: `throttle_cfs_rq()`, on
  `rq->donor` only and only when `cfs_rq->h_curr` is on_rq; and
  `set_next_task_fair()`, when `account_cfs_rq_runtime()` reports a
  throttled level.
- `pick_task_fair()`: arms nothing and skips nothing; a queued task of a
  throttled group stays in the `rq->cfs` tree and can be picked.
- There is no check_cfs_rq_runtime() here; `__account_cfs_rq_runtime()`
  calls `throttle_cfs_rq()`.
- `throttle_cfs_rq()`: returns false without throttling when
  `__assign_cfs_rq_runtime()` obtains runtime.
- `task_throttle_setup_work()`: does nothing for `PF_KTHREAD` or
  `PF_EXITING` tasks, so a kernel thread in a throttled group is never
  dequeued by the throttle.
- `throttle_cfs_rq_work()`: takes the rq lock itself; returns early if the
  task is exiting, left the fair class, or `throttle_count` is 0.
- Limbo list: the one of the task's own `cfs_rq_of()`, which may be a
  descendant of the runqueue that ran out of quota.
- `tg_unthrottle_up()`: stops re-enqueueing as soon as `throttle_count` is
  non-zero again and splices the rest back onto the limbo list.
- `enqueue_throttled_task()`: puts the task straight on the limbo list only
  if the target is in a throttled hierarchy and the task is not the current
  donor; otherwise it clears `p->throttled` and the normal enqueue follows.
- `dequeue_throttled_task()` with `DEQUEUE_SLEEP`: unlinks and clears
  `p->throttled`.
- `dequeue_throttled_task()` without `DEQUEUE_SLEEP`: unlinks, keeps
  `p->throttled`, and calls `detach_task_cfs_rq()` if the task is migrating.

**Cache aware scheduling**

- `CONFIG_SCHED_CACHE`: exists in `init/Kconfig`, default y, depends on SMP;
  code is mainly in `kernel/sched/fair.c` and `kernel/sched/topology.c`.
- Runtime gate: `sched_cache_enabled()` tests the static key
  `sched_cache_active`; it is on only with more than one LLC
  (`sched_cache_present`) and `sysctl_sched_cache_user` set (debugfs
  `llc_balancing/enabled`).
- Preference: one `struct sched_cache_group` per process; `grp->cpu` is
  chosen in `task_cache_work()`, and `account_mm_sched()` copies its LLC
  into `p->preferred_llc`.
- No preference (`-1`): kernel threads, single-threaded processes and
  processes with too many active threads (`invalid_llc_nr()`), a footprint
  above the LLC size (`exceed_llc_capacity()`), a stale epoch, or a conflict
  with `p->numa_preferred_nid`.
- It changes placement in load balancing only; the decisions are made in:
  - `can_migrate_task()`: `migrate_degrades_llc()` refuses a move that
    breaks the preference, when NUMA locality is neutral.
  - `update_sg_lb_stats()`: `llc_balance()` marks `group_llc_balance`;
    `calculate_imbalance()` then pulls one task with `migrate_llc_task`.
  - `need_active_balance()`: `alb_break_llc()` vetoes, and
    `migrate_llc_task` makes it return 1; `alb_stop_fn()` then picks
    `active_load_balance_llc_cpu_stop()`.
- `can_migrate_llc()`: the policy; returns `mig_forbid`, `mig_llc` or
  `mig_unrestricted` from LLC utilisation.
- `LBF_LLC_PINNED`: set when a task is refused for LLC reasons and the
  migration type is not `migrate_llc_task`, so that `sched_balance_rq()`
  does not raise `nr_balance_failed`.
- Override: both `migrate_degrades_llc()` and `llc_balance()` give up once
  `nr_balance_failed` reaches `cache_nice_tries + 1`.
- `task_has_sched_core()` tasks: exempt in `migrate_degrades_llc()`.
- Newly idle balance: `record_sg_llc_stats()` skips it, so LLC utilisation
  is refreshed only by a balance that is not newly idle; the migration
  filter still runs.
- Left alone: wakeup placement (`select_task_rq_fair()`, `wake_affine()`,
  `select_idle_sibling()`), fork and exec placement
  (`sched_balance_find_dst_cpu()`) and `task_numa_migrate()`; none reads
  `p->preferred_llc` or `grp->cpu`.
- Counters: `rq->nr_pref_llc_running` and `sd->llc_counts` are kept by
  `account_llc_enqueue()` and `account_llc_dequeue()`; `set_delayed()` and
  `clear_delayed()` adjust the first for delayed tasks.

## Realtime, deadline and servers

**Realtime bandwidth limits**

- `sysctl_sched_rt_runtime` default: 1000000 us, equal to
  `sysctl_sched_rt_period`; see `kernel/sched/rt.c`.
  `Documentation/scheduler/sched-rt-group.rst` still says 950000.
- `dl_b->bw` at the defaults: `to_ratio()` gives `BW_UNIT`, so `init_dl_bw()`
  sets the deadline admission limit to 100% of each CPU, not 95%.
- `sched_rt_runtime_exceeded()` at the defaults: returns 0 for the root
  `struct rt_rq`, because its runtime is not below its period; it is the only
  place that sets `rt_throttled` to 1, so with `CONFIG_RT_GROUP_SCHED` the root
  group is not throttled at boot values.
- Write to the runtime or period sysctl: the new value reaches no
  `rt_rq->rt_runtime`. The root group's `rt_bandwidth.rt_runtime` is copied
  from the sysctl in `sched_init()` and afterwards changes only through
  `tg_set_rt_bandwidth()`.
- Write that lowers the sysctl ratio while `rt_group_sched_enabled()`:
  `sched_rt_global_validate()` fails with `-EINVAL` if any group, the root
  group included, has a larger ratio; see `tg_rt_schedulable()`.
- `rt_group_sched_enabled()` false in a `CONFIG_RT_GROUP_SCHED` kernel:
  `update_curr_rt()` still accounts and tests the root `struct rt_rq`; it
  tests `rt_bandwidth_enabled()`, not `rt_group_sched_enabled()`.
- `balance_runtime()`: returns at once unless `RT_RUNTIME_SHARE` is set, and
  `kernel/sched/features.h` defines it `false`.
- Server parameters: not derived from the rt sysctls.
  `sched_init_dl_servers()` hard-codes 50 ms / 1000 ms; only
  `sched_server_write_common()` in `kernel/sched/debug.c` changes them.
- Runtime sysctl at -1: the deadline servers keep running.
  `dl_server_start()` tests no sysctl, and `__dl_overflow()` is never true
  when `dl_b->bw` is -1.
- A server gives no protection when its `dl_runtime` is 0 or its
  `dl_bw_attached` is 0; `dl_server_start()` returns early for both.

**Deadline servers**

- `rq->ext_server`: exists under `CONFIG_SCHED_CLASS_EXT`, beside
  `rq->fair_server`; set up by `ext_server_init()`, pick callback
  `ext_server_pick_task()`, both in `kernel/sched/ext/ext.c`.
- `sched_init_dl_servers()`: gives both servers the same parameters, then calls
  `dl_server_detach_bw()` on `ext_server`, so it cannot start until a BPF
  scheduler is enabled.
- sched_ext enable: `dl_server_attach_bw()` on `ext_server` for every CPU; when
  all tasks are switched (`scx_switched_all()`), `dl_server_detach_bw()` on
  `fair_server`. Disable reverses this: `dl_server_swap_bw()` if all tasks
  were switched, otherwise `dl_server_detach_bw()` on `ext_server`.
- Start, complete list of callers of `dl_server_start()`:
  - `enqueue_task_fair()`, when `rq->cfs.h_nr_queued` leaves zero; no other
    call in `kernel/sched/fair.c`
  - the sched_ext enqueue path, when `rq->scx.nr_running` becomes 1
  - `dl_server_attach_bw()` and `dl_server_swap_bw()`, when the CPU is online
  - `sched_server_write_common()`, after applying new parameters
- Stop, complete list of callers of `dl_server_stop()`:
  - `__pick_task_dl()`, at once when `server_pick_task` returns NULL, then it
    picks again; it does not set `dl_yielded`
  - `dl_server_timer()`, when `dl_defer_idle` is set
  - `__dl_server_detach_bw_locked()`, when the server is active
  - `sched_cpu_dying()`, for both servers
  - `sched_server_write_common()`, before applying new parameters
- Last served task dequeued: nothing stops the server. If it is waiting
  throttled it stays `dl_server_active` at least until its timer fires; the
  comment on `dl_server_active` in `include/linux/sched.h` says otherwise.
- `dl_defer_idle`: set by `update_curr_dl_se()` when a charge made while
  `idle_rq()` is true uses up the budget of a waiting server; a charge while
  `idle_rq()` is false, `dl_server_start()` or `dl_server_stop()` clears it.
- There is no dl_server_pick_task() function; the callback is the field
  `server_pick_task`, called from `__pick_task_dl()`.
- `dl_defer`: set to 1 for both servers in `sched_init_dl_servers()`; nothing
  else in the tree sets it, so no in-tree server runs the non-deferred paths.
- `dl_defer` timer: armed for the zero-laxity point by `dl_server_start()`
  itself, not on starvation; `update_curr_dl_se()` cancels it and re-arms it
  for a new period each time served-class runtime uses up the budget of a
  server that waits throttled.
- `dl_defer` also changes:
  - `update_curr_dl_se()` charges a throttled server only if `dl_defer` is set
  - `dl_server_update_idle()` charges idle time only if `dl_defer` is set
  - `update_dl_entity()` uses `update_dl_revised_wakeup()` for a server with
    `dl_defer_running` set, although its deadline equals its period
- After the timer fired (`dl_defer_running` set): the server throttles and
  replenishes like a task and does not defer again until
  `update_curr_dl_se()` or `update_dl_entity()` clears `dl_defer_running`.

**Deadline parameters and admission**

- `__checkparam_dl()` does not check flags beyond the `SCHED_FLAG_SUGOV`
  short-cut; `__sched_setscheduler()` tests the flag mask, and rejects
  `SCHED_FLAG_SUGOV` from user callers with `-EINVAL`.
- Period range: `__checkparam_dl()` rejects an effective period (the deadline
  when `sched_period` is 0) outside `sysctl_sched_dl_period_min` and
  `sysctl_sched_dl_period_max`; defaults 100 us and `1 << 22` us.
- Only `sched_runtime` is compared with `1 << DL_SCALE`; `sched_deadline` is
  tested for zero, for bit 63, and against the runtime and the effective
  period.
- Capacity in `sched_dl_overflow()`: `dl_bw_capacity()` only, scaled by
  `dl_b->bw` in `__dl_overflow()`. The `cpus` count that
  `sched_dl_overflow()` reads with `dl_bw_cpus()` is not passed to the test;
  it spreads the change over `extra_bw` in `__dl_add()` and `__dl_sub()`.
- Limit at the default sysctls: the full capacity of the active CPUs of the
  root domain, which is what `dl_bw_capacity()` returns.
- `cpuset_lock()`: `__sched_setscheduler()` takes it before `task_rq_lock()`
  when the old or the new policy is deadline, so with `CONFIG_CPUSETS` the
  root domain is stable for the test; without it `cpuset_lock()` is an empty
  inline.
- `dl_b->lock` in `sched_dl_overflow()` is taken with plain
  `raw_spin_lock()`; interrupts are already off under `task_rq_lock()`.
- `sched_dl_overflow()` returns -1 on overflow, not an errno;
  `__sched_setscheduler()` turns any non-zero result into `-EBUSY`.

**Deadline bandwidth accounting**

- Servers counted in `total_bw`: only those with `dl_bw_attached` set. After
  boot that is `fair_server` alone; `ext_server` joins when a BPF scheduler is
  enabled, and `fair_server` leaves while all tasks are switched to sched_ext.
- Default share: 50 ms / 1000 ms per attached server per active CPU. With the
  default 100% limit that leaves deadline tasks 95% of each CPU when one server
  is attached.
- `dl_server_init()` adds nothing to `total_bw`. Server bandwidth enters
  through `dl_server_apply_params()` (at init, or for an attached server),
  `dl_server_attach_bw()`, `dl_server_swap_bw()`, `__dl_server_attach_root()`
  and `dl_server_add_bw()`.
- Inactive CPU: `dl_server_add_bw()` and `__dl_server_attach_bw_locked()` skip
  `total_bw` when `cpu_active()` is false; detach skips the subtraction too.
- `dl_server_apply_params()` with `init` false on a detached server: runs the
  overflow test, stores the parameters and leaves `total_bw` unchanged.
- Blocked deadline task: stays in `total_bw`; blocking only changes
  `running_bw`.
- Task that left the class while queued, or is `TASK_DEAD`: stays in
  `total_bw` until its 0-lag time. `task_non_contending()` subtracts at once
  if that time has passed, otherwise `inactive_task_timer()` does.
- cpuset migration in flight: `cpuset_reserve_dl_bw()` adds the bandwidth of
  the moving tasks that change root domain (`dl_task_needs_bw_move()`) to the
  destination root domain with `dl_bw_alloc()` before they move;
  `set_cpus_allowed_dl()` subtracts it from the source afterwards.
- `dl_rebuild_rd_accounting()` is in `kernel/cgroup/cpuset.c`; it calls
  `dl_clear_root_domain_cpu()`, then `dl_add_task_root_domain()` per task.

## Extensible class

**Errors, watchdog and bypass**

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

**Sub-schedulers and cids**

- Sub-scheduler: a `struct scx_sched` attached to one cgroup, scheduling the
  tasks of that cgroup's subtree. `p->scx.sched` names a task's scheduler;
  read it with `scx_task_sched()`. `cgrp->scx_sched` names a cgroup's.
- Selecting sub mode: `ops.sub_cgroup_id` greater than 1 makes `scx_enable()`
  run `scx_sub_enable_workfn()` instead of `scx_root_enable_workfn()`.
- `CONFIG_EXT_SUB_SCHED` (`init/Kconfig`): `def_bool y`, depends on
  `SCHED_CLASS_EXT && CGROUPS`, not on `CGROUP_SCHED`. Without it
  `scx_task_sched()` returns `scx_root` and `scx_parent()` returns `NULL`.
- Conditions for attaching include, in `scx_sub_enable_workfn()`,
  `find_parent_sched()` and `scx_validate_ops()`:
  - a root scheduler is enabled
  - the parent, which is the scheduler of the nearest ancestor cgroup,
    implements `ops.sub_attach()` and accepts
  - the cgroup has no scheduler of its own yet
  - both schedulers are cid-form
  - nesting depth is below `SCX_SUB_MAX_DEPTH`
- Dispatch: `dispatch_one()` calls only the root's `ops.dispatch()`. A child
  runs when its parent calls `scx_bpf_sub_dispatch()` for a direct child.
- Capabilities (`enum scx_cap_flags`): the root holds every capability on
  every cid; a child holds what its parent gave it with
  `scx_bpf_sub_grant()`; `scx_bpf_sub_revoke()` clears it from the child and
  its descendants.
- Local DSQ insert without the capability: `scx_resolve_local_dsq()` diverts
  the task to the rq's reject or rescue DSQ, except that it admits the task
  to the local DSQ when the rq is not online, the task is
  migration-disabled or `p->migration_pending` is set. `scx_reenq_reject()`
  hands a rejected task back to `ops.enqueue()` with `SCX_ENQ_REENQ`.
- Cgroup migration across a scheduler boundary: `scx_cgroup_task_migrating()`
  runs the destination's `ops.init_task()` before the move commits, and
  `scx_cgroup_task_migrated()` re-homes the task.
- cid: a dense id in `[0, num_possible_cpus())`, in the default mapping
  ordered by topology so that a core, an LLC and a NUMA node are each a
  contiguous range. CPU numbers are in `[0, nr_cpu_ids)` and may be sparse.
  See the comment at the top of `kernel/sched/ext/cid.h`.
- cid mapping lifetime: built by `scx_cid_init()` on every root enable from
  the CPUs online then, optionally replaced by `scx_bpf_cid_override()` from
  `ops.init_cids()`, retired at root disable. CPUs that were offline get
  cids at the tail with core, LLC and node fields of -1.
- cids need no config symbol. The tables are built for a cpu-form root too.
- cid-form scheduler: one registered as struct_ops type `sched_ext_ops_cid`
  (`struct sched_ext_ops_cid`). `bpf_scx_reg_cid()` requires exactly one BPF
  arena map. All schedulers of a hierarchy share the form
  (`scx_is_cid_type()`).
- Op boundary: `scx_cpu_arg()` converts a CPU to what the op expects and
  `scx_cpu_ret()` converts back; core code keeps CPU numbers.
- `__scx_cid_to_cpu()` and `__scx_cpu_to_cid()`: no range check and no `NULL`
  check of the table; for paths that run only on a live scheduler.
  `scx_cid_to_cpu()` and `scx_cpu_to_cid()` check both and return `-EINVAL`.

**Kfunc calling contexts**

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

**Task ownership in ops_state**

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

## CPU hotplug

**Hotplug callbacks**

- `sched_cpu_deactivate()` context: runs in the cpuhp thread on the outgoing
  CPU, not in the control task; `CPUHP_AP_ACTIVE` is above
  `CPUHP_TEARDOWN_CPU`, so `_cpu_down()` hands it to `cpuhp_thread_fun()`.
- `sched_cpu_deactivate()` error return: only `dl_bw_deactivate()`, the first
  statement, before any state is changed.
- `cpuset_cpu_inactive()`: returns void; `sched_cpu_deactivate()` has no undo
  code and returns 0 after it.
- `sched_cpu_deactivate()` returning an error: the core does not call
  `sched_cpu_activate()`; `cpuhp_reset_state()` in `kernel/cpu.c` puts the
  state back at `CPUHP_AP_ACTIVE` and the rollback runs startup only for
  states above it.
- **Unsafe usage**: returning an error from `sched_cpu_deactivate()` after it
  has changed state; nothing restores `cpu_active()`, `rq->online` or
  `balance_push_callback`.
  - Safe: fail before the first change, as the `dl_bw_deactivate()` call does.
- Teardown failing below `CPUHP_AP_ACTIVE` down to `CPUHP_TEARDOWN_CPU`, for
  example `takedown_cpu()` when `__cpu_disable()` fails:
  `sched_cpu_activate()` runs and is the only undo for
  `sched_cpu_deactivate()`; `CPUHP_AP_SCHED_WAIT_EMPTY` has no startup.
- `sched_cpu_dying()` when `__cpu_disable()` fails: does not run;
  `take_cpu_down()` returns on the error before the DYING callbacks.
- `sched_cpu_dying()` return value: ignored; `take_cpu_down()` runs it
  through `cpuhp_invoke_callback_range_nofail()`, which only prints a warning
  on error.
- `sched_set_rq_offline()` and `nohz_balance_exit_idle()`: called from
  `sched_cpu_deactivate()`; `sched_cpu_dying()` does not touch `rq->online`.
- `sched_cpu_deactivate()` after `synchronize_rcu()`: calls
  `sched_domains_free_llc_id()`, which takes `sched_domains_mutex`, before
  `sched_set_rq_offline()`; `sched_cpu_activate()` has no direct counterpart.
- `sched_cpu_wait_empty()`: calls only `balance_hotplug_wait()` and then
  `sched_force_init_mm()`; it migrates nothing itself and there is no
  sched_force_ipi in this tree.
- `balance_hotplug_wait()` condition: `rq->nr_running == 1 &&
  !rq_has_pinned_tasks(rq)`.
- `sched_force_init_mm()`: `finish_cpu()` in `kernel/cpu.c` relies on it and
  warns if the idle task's `active_mm` is not `init_mm`.
- `balance_push_set(cpu, false)`: among the hotplug callbacks only
  `sched_cpu_activate()` calls it; `sched_cpu_dying()` leaves
  `balance_push_callback` installed, although the comment in
  `sched_cpu_deactivate()` points at `sched_cpu_dying()`.
- Bring-up failing above `CPUHP_AP_SCHED_WAIT_EMPTY` and below
  `CPUHP_AP_ACTIVE`: `sched_cpu_wait_empty()` runs without
  `sched_cpu_deactivate()` having run.
- State seen in that bring-up rollback: `cpu_active()` is still false,
  `balance_push_callback` is still installed from the previous offline or
  from boot, and `cpuhp_reset_state()` has set `cpu_dying()`, so
  `balance_push()` acts.

**Per-CPU timers across hotplug**

- `rq->fair_server`: stopped by `dl_server_stop()` called directly from
  `sched_cpu_dying()` under the rq lock, after `update_rq_clock()`.
- `rq->ext_server`: exists under `CONFIG_SCHED_CLASS_EXT`; stopped in
  `sched_cpu_dying()` right after `rq->fair_server`.
- `rq_offline_fair()`: does not call `dl_server_stop()`; no `->rq_offline`
  hook stops a deadline server.
- `sched_cpu_dying()` ordering: runs after `hrtimers_cpu_dying()` and after
  `__cpu_disable()`, so the CPU's queued hrtimers are already on another
  CPU's base and `cpu_online()` is false when the servers are stopped.
- `dl_server_start()` offline guard: `WARN_ON_ONCE(!cpu_online(cpu_of(rq)))`
  followed by return, placed after the `update_curr` call and before
  `dl_server_active` is set.
- `dl_server_start()`: does not test `rq->online` or `cpu_active()`; its other
  early returns are on `!dl_server()`, `dl_server_active`, `!dl_runtime` and
  `!dl_bw_attached`.
- Between `sched_cpu_deactivate()` and `__cpu_disable()`: the CPU is inactive
  with `rq->online` 0 but still `cpu_online()`, so `dl_server_start()` still
  starts a server there.
- `hrtick_enabled()` in `kernel/sched/sched.h`: tests `cpu_active()`; this is
  what stops hrtick arming after `sched_cpu_deactivate()`; `hrtick_start()`
  has no test of its own.
- `hrtick_clear()` in `sched_cpu_dying()`: called after the rq lock is
  dropped.
- hrtimer started on the dying CPU after `hrtimers_cpu_dying()`:
  `get_target_base()` in `kernel/time/hrtimer.c` selects the base of an
  online housekeeping CPU, even with `HRTIMER_MODE_PINNED`; it does not sit
  on the offline base.
- `dl_se->dl_timer`: not pinned; `start_dl_timer()` uses
  `HRTIMER_MODE_ABS_HARD`; `rq->hrtick_timer` is started with
  `HRTIMER_MODE_ABS_PINNED_HARD`.
- `sched_tick_stop()`: does not cancel the delayed work; under
  `CONFIG_NO_HZ_FULL`, for a CPU that is not a `HK_TYPE_KERNEL_NOISE`
  housekeeping CPU, it sets `TICK_SCHED_REMOTE_OFFLINING` and the next
  `sched_tick_remote()` run moves to `TICK_SCHED_REMOTE_OFFLINE` without
  requeueing.
- Cancelling the remote tick work in `sched_tick_stop()`: would leave
  `TICK_SCHED_REMOTE_OFFLINING`, and `sched_tick_start()` queues the work only
  from `TICK_SCHED_REMOTE_OFFLINE`.
- `rq->scx.rescue.timer` (`CONFIG_EXT_SUB_SCHED`, `kernel/sched/ext/sub.c`):
  a per-rq `TIMER_PINNED` timer; stopped in `sched_cpu_deactivate()` through
  `rq_offline_scx()` and `scx_rescue_flush()`, which calls `timer_delete()`.
- `scx_rescue_timer_arm()`: reached for new work only from
  `scx_resolve_local_dsq()`, after its `scx_rq_online()` test; the timer
  function rearms only while a rescuee exists, and `scx_rescue_flush()`
  empties both.
- `set_rq_offline()`: also called from `rq_attach_root()` in
  `kernel/sched/topology.c` for a CPU that stays up, so a `->rq_offline` hook
  is not a hotplug-only event; `scx_rescue_flush()` returns early when
  `cpu_active()`.
- Per-task `dl_se->dl_timer`: no scheduler hotplug callback stops it;
  `dl_task_timer()` calls `dl_task_offline_migration()` when `rq->online`
  is 0.
- **Unsafe usage**: calling `hrtick_start()` without a preceding
  `hrtick_enabled_fair()` or `hrtick_enabled_dl()` test; `hrtick_clear()` in
  `sched_cpu_dying()` is the last hotplug cancel of the timer, and `hrtick()`
  warns when it runs on a CPU other than `cpu_of(rq)`.
  - Safe: test first under the rq lock, as `hrtick_update()` in
    `kernel/sched/fair.c` does; `hrtick_enabled()` defines the gate.
- **Potentially unsafe usage**: calling `dl_server_start()` for an rq the
  caller did not get from task placement.
  - Unsafe: when the CPU comes from a loop over possible CPUs or from user
    input and `cpu_online()` was not tested; `dl_server_start()` warns and
    returns.
  - Safe: test `cpu_online()` under the rq lock first, as
    `dl_server_attach_bw()` and `dl_server_swap_bw()` do, or return `-EBUSY`
    as `sched_server_write_common()` in `kernel/sched/debug.c` does.
- **Potentially unsafe usage**: `hrtimer_cancel()` on an rq timer while
  holding the rq lock.
  - Unsafe: when the callback can be running on another CPU, as with the
    unpinned `dl_se->dl_timer`; `dl_server_timer()` takes the rq lock.
  - Safe: `hrtimer_try_to_cancel()` as `dl_server_stop()` does; it clears
    `dl_throttled`, and `dl_server_timer()` returns `HRTIMER_NORESTART` when
    `dl_throttled` is 0 under the rq lock.
  - Safe: `hrtick_schedule_exit()`, where `rq->hrtick_timer` is pinned to the
    local CPU and IRQs are off, so `hrtick()` cannot be running.

## Model gaps

### Other mistakes models make

- Models do not know `rq->next_class`. On the `pick_task_fair()` and
  `pick_task_scx()` paths `rq_modified_begin()` runs before the rq lock is
  dropped, and the pick returns `RETRY_TASK` if `rq_modified_above()` is true
  afterwards; see `sched_balance_newidle()` and `do_pick_task_scx()`.
- Models take the balance pass to start at the class of `prev`.
  `prev_balance()` starts at the class of `rq->donor`.
- Models believe check_class_changed() still runs after a class change.
  `sched_change_end()` calls `prio_changed` when `ENQUEUE_CLASS` is clear,
  without a NULL test, so every class defines it.
- Models may read `cid_on_cpu()` in `kernel/sched/sched.h` as sched_ext code.
  It tests a bit of the mm concurrency id under `CONFIG_SCHED_MM_CID`,
  unrelated to `kernel/sched/ext/cid.c`.
- Models set `p->sched_contributes_to_load` in `try_to_block_task()`.
  `block_task(rq, p, task_state)` sets it.
- Models expect `resched_curr()` when fair preempts at the end of a slice or
  on a wakeup. `update_curr()` and `wakeup_preempt_fair()` call
  `resched_curr_lazy()`.
- Models do not expect lock annotations. Functions carry
  `__must_hold(__rq_lockp(rq))` and the like, and `kernel/sched/Makefile` sets
  `CONTEXT_ANALYSIS_core.o`.
- Models take `HRTICK` to default off. `kernel/sched/features.h` turns it and
  `HRTICK_DL` on under `CONFIG_HRTIMER_REARM_DEFERRED`.
