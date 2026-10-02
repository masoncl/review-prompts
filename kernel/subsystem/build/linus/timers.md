# Timer Subsystem

## Main structures

### Objects and how they relate

- `struct timerqueue_linked_node` and `struct timerqueue_linked_head`: what
  hrtimers are queued in. `struct hrtimer` embeds the node, and
  `struct hrtimer_clock_base` holds the head as `active`. It is an rbtree
  whose nodes also carry previous/next links (`struct rb_node_linked`).
- hrtimer sort key: the hard expiry only (`node.expires`, soft expiry plus
  slack). `_softexpires` is not part of the key; `__hrtimer_run_queues()`
  tests it to decide whether the first timer may run yet.
- `struct timerqueue_head` and `struct timerqueue_node`: not used by
  `kernel/time/hrtimer.c`. They queue, for example, `struct alarm`,
  `struct cpu_timer` and `struct tmigr_event`.
- `struct hrtimer` has no state word. `is_queued` says whether it is in the
  queue; `running` in its `struct hrtimer_clock_base` says whether its
  callback runs. `seq` in the same clock base lets `hrtimer_active()` read
  both without the lock.
- `struct timer_base`: with `CONFIG_NO_HZ_COMMON` each CPU has three,
  `BASE_LOCAL` (timers with `TIMER_PINNED`), `BASE_GLOBAL` (all others) and
  `BASE_DEF` (`TIMER_DEFERRABLE`, which wins over `TIMER_PINNED`). Without it
  there is one base and all three names are 0. There is no BASE_STD.
- `struct timer_list` flags: hold the CPU and the bucket index, not the base
  index. `get_timer_base()` recomputes the base from `TIMER_PINNED` and
  `TIMER_DEFERRABLE` each time.
- Wheel timer placement: `mod_timer()` and `add_timer()` queue on the calling
  CPU's base; `add_timer_on()` queues on the named CPU and sets
  `TIMER_PINNED`. Exceptions: `__mod_timer()` leaves a timer where it is when
  its callback is running on its old base, or when it is pending and the new
  expiry falls in the same bucket.
- hrtimer placement differs: a start without `HRTIMER_MODE_PINNED` can queue
  the timer on another CPU's `struct hrtimer_cpu_base`, picked by
  `get_nohz_timer_target()` in `get_target_base()` when
  `timers_migration_enabled` is on. `kernel/time/timer.c` defines that key
  but the wheel never reads it.
- Timer migration (`kernel/time/timer_migration.c`, built only with
  `CONFIG_SMP` and `CONFIG_NO_HZ_COMMON`) moves no timer. An idle
  CPU queues only an expiry time, as a `struct tmigr_event`, in its
  `struct tmigr_group`. Another CPU, normally the migrator, then calls
  `timer_expire_remote()`, which runs the idle CPU's `BASE_GLOBAL` in place.
- Consequence for callbacks: a timer with `TIMER_PINNED` runs on the CPU that
  holds it. `timer_expire_remote()` is the only remote caller of
  `__run_timer_base()` and passes `BASE_GLOBAL`; `BASE_LOCAL` and `BASE_DEF`
  are run only through `run_timer_base()`, which uses `this_cpu_ptr()`.
- `struct tmigr_hierarchy`: owns the root `struct tmigr_group` and the
  per-level group lists; one exists per value of `tmigr_get_capacity()`.
  That function returns `SCHED_CAPACITY_SCALE` for every CPU unless
  `CONFIG_BROKEN` is set, so there is one hierarchy otherwise.
- `struct hrtimer_cpu_base` and the clockevent, with
  `CONFIG_HRTIMER_REARM_DEFERRED`: `hrtimer_interrupt()` does not program the
  `struct clock_event_device`. It sets `deferred_rearm` and
  `TIF_HRTIMER_REARM`; `__hrtimer_rearm_deferred()` programs the device later,
  for example on interrupt exit or in the scheduler.
- While `deferred_rearm` is set: starting or removing an hrtimer on that CPU
  does not touch the hardware; it at most sets `deferred_needs_update`.
- `struct tick_sched` `sched_timer`: queued as an hrtimer only with
  `TS_FLAG_HIGHRES`. In low-resolution NOHZ mode the clockevent handler is
  `tick_nohz_lowres_handler()`, which calls `tick_nohz_handler()` directly;
  `sched_timer` then only stores the next tick time.
- Next-event query: for the next timer, `tick_nohz_next_event()` asks only
  `get_next_timer_interrupt()`. That function folds hrtimers in through
  `hrtimer_get_next_event()`, which returns `KTIME_MAX` in high-resolution
  mode, where the tick is itself an hrtimer.
- `TIMER_SOFTIRQ` and `HRTIMER_SOFTIRQ`: both are raised through
  `raise_timer_softirq()`. With `force_irqthreads()`, which is always true
  under `CONFIG_PREEMPT_RT`, they are run by the per-CPU `ktimerd` thread
  (`run_ktimerd()` in `kernel/softirq.c`) instead of the normal softirq path.
- jiffies: `tick_do_timer_cpu` names the CPU that normally advances it, but
  it is `TICK_DO_TIMER_NONE` after that CPU stops its tick, and the next CPU
  in `tick_sched_do_timer()` takes over. `tick_nohz_update_jiffies()` and
  `tick_limited_update_jiffies64()` also advance jiffies from other CPUs.
- Names in this tree: `timer_container_of()` (there is no from_timer()),
  `timer_delete()`, `timer_delete_sync()`, `timer_shutdown_sync()` (there is
  no del_timer_sync()), and `hrtimer_setup()` (there is no hrtimer_init()).
- `struct k_itimer`: the POSIX timer object; there is no struct posix_timer.
- `struct tk_data` in `kernel/time/timekeeping.c`: wraps a
  `struct timekeeper`, its shadow copy, the seqcount and the lock.
  `timekeeper_data[]` holds one per `enum timekeeper_ids`; `tk_core` is the
  `TIMEKEEPER_CORE` entry.

## Where to look

**Core files**

| Job | File in this tree | Easy to miss |
|---|---|---|
| hrtimer base structs | `include/linux/hrtimer_bases.h` | There is no hrtimer_defs.h. `struct hrtimer_cpu_base`, `struct hrtimer_clock_base`, `enum hrtimer_base_type` and `hrtimer_callback_running()` are defined here. `include/linux/hrtimer.h` does not include it; users include it themselves, for example `kernel/time/hrtimer.c` and `kernel/time/tick-internal.h`. |
| hrtimer deferred rearm | `include/linux/hrtimer_rearm.h` | Included by `include/linux/hrtimer.h`. All stubs without `CONFIG_HRTIMER_REARM_DEFERRED`. `__hrtimer_rearm_deferred()` is in `kernel/time/hrtimer.c`. |
| hrtimer header alias | `include/linux/hrtimer_api.h` | One line: includes `linux/hrtimer.h`. |
| hrtimer queue | `include/linux/timerqueue.h`, `lib/timerqueue.c` | `struct hrtimer` embeds `struct timerqueue_linked_node`. Of the linked helpers only `timerqueue_linked_add()` is in `lib/timerqueue.c`; the others are inline in the header. `kernel/time/timer_migration.h` uses the plain `struct timerqueue_node`. |
| Sleep helpers, inline part | `include/linux/delay.h` | `fsleep()` and `usleep_range()` are static inline here, not in `kernel/time/sleep_timeout.c`. |
| hrtimer-based timeouts | `kernel/time/sleep_timeout.c` | `schedule_hrtimeout_range_clock()` and its wrappers are defined here but declared in `include/linux/hrtimer.h`. `hrtimer_setup_sleeper_on_stack()` and `hrtimer_nanosleep()` are in `kernel/time/hrtimer.c`. |
| Jiffies timeout declarations | `include/linux/sched.h` | `schedule_timeout()` and its variants are declared here. |
| Tick, NOHZ and highres | `kernel/time/tick-sched.c` | Built on `CONFIG_TICK_ONESHOT`, not on `CONFIG_NO_HZ_COMMON`: with `CONFIG_HIGH_RES_TIMERS`, `hrtimer_switch_to_hres()` calls `tick_setup_sched_timer()`. There is no tick_sched_timer(); the callback of `sched_timer` is `tick_nohz_handler()`. |
| Tick, broadcast entry | `include/linux/tick.h`, `kernel/time/tick-common.c` | `tick_broadcast_enter()` is inline in the header. It calls `tick_broadcast_oneshot_control()`, which is in `kernel/time/tick-common.c` with `CONFIG_GENERIC_CLOCKEVENTS` and a stub that returns 0 otherwise. That calls `__tick_broadcast_oneshot_control()` only when the local device has `CLOCK_EVT_FEAT_C3STOP`. `__tick_broadcast_oneshot_control()` is in `kernel/time/tick-broadcast.c` with `CONFIG_GENERIC_CLOCKEVENTS_BROADCAST`, and a stub in `kernel/time/tick-sched.h` that returns `-EBUSY` otherwise. |
| Tick, no clockevents | `kernel/time/tick-legacy.c` | `legacy_timer_tick()`, built on `CONFIG_LEGACY_TIMER_TICK`. `CONFIG_GENERIC_CLOCKEVENTS` is `def_bool !LEGACY_TIMER_TICK`, so `kernel/time/clockevents.c` and `kernel/time/tick-common.c` are not built then. |
| Timekeeping, struct | `include/linux/timekeeper_internal.h` | `struct timekeeper` is defined here. `kernel/time/timekeeping_internal.h` only forward-declares it. |
| Timekeeping, internal headers | `kernel/time/timekeeping.h`, `kernel/time/timekeeping_internal.h` | Both exist. `kernel/time/tick-internal.h` includes `kernel/time/timekeeping.h`; `kernel/time/timekeeping.c` gets it that way. |
| Timekeeping, update | `kernel/time/timekeeping.c` | There is no timekeeping_update(); `timekeeping_update_from_shadow()` does that job. |
| Clocksource registration | `include/linux/clocksource.h` | `clocksource_register_hz()` is inline here and calls `__clocksource_register_scale()` in `kernel/time/clocksource.c`. |

## Timer wheel timers

**Timer wheel function names**

- `timer_destroy_on_stack()`: releases a timer set up with
  `timer_setup_on_stack()`; destroy_timer_on_stack is not defined in this tree.
- `timer_delete_sync_try()`: the name of the non-waiting try variant, declared in
  `include/linux/timer.h`.
- del_timer(), del_timer_sync(), try_to_del_timer_sync() and from_timer(): no
  function or macro of these names is defined in this tree, and there are no
  compatibility aliases; a patch that calls them does not build.
- Old spelling inside `kernel/time/timer.c`: the static helpers
  `__try_to_del_timer_sync()` and `del_timer_wait_running()` keep it; they are
  not API.

**Deletion and shutdown guarantees**

- `__timer_delete_sync()`: second parameter is `bool shutdown`, the same as
  `__timer_delete()`; neither takes a flags word.
- Return 0 or 1 from `timer_delete()`, `timer_delete_sync()`,
  `timer_shutdown()`, `timer_shutdown_sync()`: the queue state found on the
  last pass, nothing more; it is found under `base->lock`, except that
  `timer_delete()` can return 0 from the lockless `timer_pending()` test alone.
- Return 1 from a sync variant with a self-re-arming callback: may mean that the
  instance the callback just re-armed was removed.
- Return value when another path can re-arm concurrently: says nothing about
  the queue state after the function returns, for the non-shutdown variants.
- `timer_shutdown()` while the callback runs: clears `timer->function` at once,
  so the running callback's own re-arm is already discarded.
- `timer_shutdown_sync()` while the callback runs: `__try_to_del_timer_sync()`
  leaves `timer->function` alone until the callback has returned; a re-arm made
  by the callback during the wait succeeds and is removed on the next pass.
  Exception: a callback that re-arms with `add_timer_on()` onto a different
  `struct timer_base`; see "Waiting for a running callback".

**Shutdown state**

- `add_timer()`, `add_timer_local()`, `add_timer_global()`, `add_timer_on()` on a
  shut-down timer: return `void`, so the caller gets no indication at all.
- `mod_timer()`, `mod_timer_pending()`, `timer_reduce()` on a shut-down timer:
  return 0.
- Shutdown state: is only `timer->function == NULL`; there is no bit for it in
  `timer->flags`, and the arming paths test nothing else.
- `timer->function == NULL` does not prove a shutdown: a timer set up with a
  NULL callback, as `sock_init_data_uid()` in `net/core/sock.c` does, looks the
  same and has its arming discarded the same way; so does a zeroed
  `struct timer_list` without `CONFIG_DEBUG_OBJECTS_TIMERS`.
- Reading `timer->function` outside `kernel/time/timer.c`: is unlocked;
  shutdown writes it under `base->lock`, which callers cannot take.

**Timer wheel callback context**

- `TIMER_IRQSAFE` callback: runs with interrupts disabled and `base->lock`
  released; `expire_timers()` drops the lock with `raw_spin_unlock()` before
  the call.
- Preempt-count warning text: `"timer: %pS preempt leak: %08x -> %08x\n"`, from
  `WARN_ONCE()` in `call_timer_fn()`.
- Threaded expiry: when `force_irqthreads()` is true, `raise_timer_softirq()` in
  `include/linux/interrupt.h` hands `TIMER_SOFTIRQ` to the per-CPU `ktimerd`
  thread (comm "ktimers/%u"), which runs it from `run_ktimerd()` in
  `kernel/softirq.c`; it is not run by `ksoftirqd`.
- `force_irqthreads()`: false without `CONFIG_IRQ_FORCED_THREADING`; with it,
  always true with `CONFIG_PREEMPT_RT` and a static key without
  `CONFIG_PREEMPT_RT`, so threaded expiry is not limited to
  `CONFIG_PREEMPT_RT`.
- CPU the callback runs on: not always the CPU in `timer->flags`;
  `timer_expire_remote()`, reached from `tmigr_handle_remote()` in the timer
  softirq, expires the `BASE_GLOBAL` base of another CPU.
- Timers on `BASE_GLOBAL`: those with neither `TIMER_PINNED` nor
  `TIMER_DEFERRABLE`, under `CONFIG_NO_HZ_COMMON`; see `get_timer_cpu_base()`.

**Freeing from the callback**

- `call_timer_fn()`: receives the callback as its `fn` argument and reads
  nothing from the timer after the callback returns; see `call_timer_fn()` in
  `kernel/time/timer.c`.
- `expire_timers()`: reads `timer->function` and `timer->flags` under
  `base->lock` before the call, and afterwards does not read the timer.

**timer_pending checks**

- True result: no caller lock keeps it true; `expire_timers()` detaches the
  timer under `base->lock` alone, at any moment.
- False result: stays false only while every arming path, the callback's own
  re-arm included, runs under a lock the caller holds.
- **Potentially unsafe usage**: deciding from `timer_pending()` what the timer
  core will do next, such as whether a reference owned by the queued timer must
  be dropped or taken.
  - Unsafe: when expiry or another CPU can change the queue state between the
    test and the action, the action does not test again under `base->lock`,
    and no lock held across the test is also taken by the callback and by
    every arming path; the test and the action then disagree.
  - Safe: act on a 1 from `timer_delete()` or a 0 from `mod_timer()`, each
    decided under `base->lock`, on a timer that is never shut down, as
    `sk_stop_timer()` and `sk_reset_timer()` in `net/core/sock.c` do.
  - Safe: as a shortcut in front of a call that tests again under `base->lock`,
    as `__timer_delete()` and `__mod_timer()` do themselves.
  - Safe: when the test runs under a lock that the callback and every arming
    path also take, as `__vector_schedule_cleanup()` in
    `arch/x86/kernel/apic/vector.c` does under `vector_lock`;
    `expire_timers()` detaches the timer before the callback, so a callback
    that makes a true result stale still takes the lock after the caller.

**Waiting for a running callback**

- Softirq context: allowed; `__timer_delete_sync()` warns only for
  `in_hardirq()` on a timer without `TIMER_IRQSAFE`, with `WARN_ON()`.
- Lockdep map: `__timer_delete_sync()` acquires and releases
  `timer->lockdep_map` under `CONFIG_LOCKDEP` for every timer, `TIMER_IRQSAFE`
  included.
- Sleepable-context check: `lockdep_assert_preemption_enabled()`, made only
  with `CONFIG_PREEMPT_RT` and without `TIMER_IRQSAFE`; it is empty without
  `CONFIG_PROVE_LOCKING`. `__timer_delete_sync()` has no unconditional
  `might_sleep()`; the only other sleep check is in `rt_spin_lock()`, reached
  through `del_timer_wait_running()` on `CONFIG_PREEMPT_RT` while the callback
  runs.
- `TIMER_IRQSAFE` timer on `CONFIG_PREEMPT_RT`: `del_timer_wait_running()` does
  not block on `base->expiry_lock`; the caller spins.
- **Unsafe usage**: calling `timer_delete_sync()` or `timer_shutdown_sync()` on
  a timer without `TIMER_IRQSAFE` while holding a lock that a hardirq handler
  takes, even one the callback never touches.
  - Unsafe: the callback runs with interrupts enabled; a hardirq on its CPU
    that spins on the held lock keeps `base->running_timer` set, and the loop in
    `__timer_delete_sync()` never ends.
  - Safe: `timer_delete()` or `timer_shutdown()` under the lock; neither waits
    for `base->running_timer`.
  - Safe: drop the lock before the sync call, as `ioc_rqos_exit()` in
    `block/blk-iocost.c` does.
- **Potentially unsafe usage**: a callback that re-arms its own timer with
  `add_timer_on()`.
  - Unsafe: when the timer is ever deleted with `timer_delete_sync()` or
    `timer_shutdown_sync()`; `add_timer_on()` does not test
    `base->running_timer` before it moves the timer to a different
    `struct timer_base`, so the sync call can return while the callback still
    runs. Nothing detects this.
  - Safe: when the timer is never deleted, as with `tsc_sync_check_timer_fn()`
    in `arch/x86/kernel/tsc_sync.c`.
  - Safe: re-arm with `mod_timer()`; `__mod_timer()` leaves a timer on its base
    while `base->running_timer` points at it.

**Freeing the embedding object**

- Callback that re-arms its own timer with `mod_timer()`: `timer_delete_sync()`
  is enough; it returns only after the callback has ended and the re-armed
  timer is detached.
- Callback that re-arms with `add_timer_on()` onto a different
  `struct timer_base`: no sync variant covers it; see "Waiting for a running
  callback".
- **Potentially unsafe usage**: `timer_delete_sync()` then `cancel_work_sync()`
  then free, for a timer and a work item that start each other.
  - Unsafe: when nothing stops the work from calling `mod_timer()` between the
    two calls; the timer is then queued in freed memory.
  - Safe: when the teardown has already made the re-arm condition false, as
    `put_unbound_pool()` in `kernel/workqueue.c` does: it destroys all workers
    first, so `too_many_workers()` is false and `idle_cull_fn()` skips
    `mod_timer()`.
  - Safe: `timer_shutdown_sync()` first, then `cancel_work_sync()` or
    `destroy_workqueue()`, as `vc4_bo_cache_destroy()` in
    `drivers/gpu/drm/vc4/vc4_bo.c` does; `__mod_timer()` discards the work's
    re-arm because `timer->function` is NULL.
- `timer_destroy_on_stack()`: only calls `debug_object_free()`, and is empty
  without `CONFIG_DEBUG_OBJECTS_TIMERS`, where it does not dequeue the timer.
- On-stack timer: delete it with `timer_delete_sync()` before
  `timer_destroy_on_stack()`, as `schedule_timeout()` in
  `kernel/time/sleep_timeout.c` does.
- Free of an object that embeds a still-active timer: reported only with both
  `CONFIG_DEBUG_OBJECTS_TIMERS` and `CONFIG_DEBUG_OBJECTS_FREE`;
  `debug_check_no_obj_freed()` is an empty stub without the latter.

## hrtimers

**hrtimer function names**

- Models have the three setup functions and the absence of the hrtimer_init
  names right; see `include/linux/hrtimer.h`.
- `__hrtimer_setup()` and `__hrtimer_setup_sleeper()`: `static` in
  `kernel/time/hrtimer.c`; code outside that file cannot call them.
- Sleeper not on the stack: no setup function exists;
  `hrtimer_setup_sleeper_on_stack()` is the only sleeper setup.
- NULL callback at setup: `WARN_ON_ONCE()` and `hrtimer_dummy_timeout()` is
  installed; it is a static inline in `include/linux/hrtimer.h` and may be
  passed deliberately as a placeholder.

**hrtimer callback changes**

- `function` in `struct hrtimer`: marked `__private`; `__private` expands to
  nothing unless `__CHECKER__` is defined (`include/linux/compiler_types.h`),
  so a direct assignment compiles and only sparse reports it.
- `hrtimer_update_function()`: the function that changes the callback after
  setup; defined out of line in `kernel/time/hrtimer.c` with
  `EXPORT_SYMBOL_GPL()`, only declared in `include/linux/hrtimer.h`.
- Requirements of `hrtimer_update_function()`: the timer is not queued, the
  new callback is not NULL, and the caller excludes a concurrent start.
- Checks in `hrtimer_update_function()`: compiled in only under
  `CONFIG_PROVE_LOCKING`; there it warns once and leaves the old callback.
- Without `CONFIG_PROVE_LOCKING`: a plain store with no lock and no test; a
  NULL pointer is stored and `__run_hrtimer()` calls it unchecked.
- `hrtimer_setup()` on a timer that is already set up: not a callback change;
  `__hrtimer_setup()` clears the whole `struct hrtimer` with `memset()` and
  picks the base again.
- **Potentially unsafe usage**: calling `hrtimer_update_function()` on a
  timer that has been started.
  - Unsafe: while the timer is queued or another context can start it;
    `__run_hrtimer()` reads the pointer under `cpu_base->lock`, and without
    `CONFIG_PROVE_LOCKING` the store takes no lock, so either callback may
    run.
  - Safe: from the timer's own callback before it returns
    `HRTIMER_RESTART`, when nothing else starts the timer, as
    `io_cqring_min_timer_wakeup()` in `io_uring/wait.c` does;
    `__run_hrtimer()` dequeued the timer before the call.
  - Safe: between setup and the first start, as `rt2800mmio_probe_hw()` does
    on the timer that `rt2x00lib_probe_dev()` set up with
    `hrtimer_dummy_timeout()`.
- **Potentially unsafe usage**: calling `hrtimer_setup()` again on a used
  timer.
  - Unsafe: while the timer is queued or its callback runs; the `memset()`
    wipes the queue node and `is_queued`.
  - Safe: after a cancel that did not return -1, under the lock that
    serialises starts, as `common_hrtimer_arm()` does after
    `common_timer_set()` called `timer_try_to_cancel`.

**Queued and running state**

- `struct hrtimer` has no `state` field; the queued state is the bool
  `is_queued`, next to `is_rel`, `is_soft`, `is_hard` and `is_lazy`.
- `hrtimer_is_queued()`: `READ_ONCE(timer->is_queued)`, nothing else.
- `HRTIMER_STATE_ENQUEUED` and `HRTIMER_STATE_INACTIVE`: defined as `true`
  and `false` inside `kernel/time/hrtimer.c` only; code outside cannot use
  them and cannot mask `is_queued` with them.
- `hrtimer_is_queued()` and the callback: independent; it returns false
  while the callback runs, and true while the callback runs if the timer was
  started again meanwhile.
- **Potentially unsafe usage**: acting on `hrtimer_is_queued()` without a
  lock that serialises starts and cancels.
  - Unsafe: when the timer can expire or be started on another CPU, or the
    callback can be running; the value is stale on return.
  - Safe: for a timer that is only started on the local CPU with
    `HRTIMER_MODE_PINNED` and `HRTIMER_MODE_HARD`, tested with interrupts
    disabled on that CPU, as `hrtick_schedule_exit()` in
    `kernel/sched/core.c` does; the callback cannot run then.

**hrtimer modes**

- `hrtimer_start_range_ns_common()`: `static` in `kernel/time/hrtimer.c`;
  holds the mismatch check and is called with the base locked by both
  `hrtimer_start_range_ns()` and `hrtimer_start_range_ns_user()`.
- `HRTIMER_MODE_LAZY_REARM`: takes effect at setup only, as `timer->is_lazy`;
  the start path never tests the bit in its `mode` argument and no check
  compares it.
- `is_lazy` timer that is first on the local CPU: removing it or moving it
  later does not reprogram the clock event device, so one pointless
  interrupt can follow; see `__remove_hrtimer()` and
  `__hrtimer_start_range_ns()`.
- Mismatch check: compares one bit, chosen at build time. Without
  `CONFIG_PREEMPT_RT` it compares `HRTIMER_MODE_SOFT` with `is_soft`; with it,
  `HRTIMER_MODE_HARD` with `is_hard`.
- `HRTIMER_MODE_HARD` at setup but not at start: silent without
  `CONFIG_PREEMPT_RT`, `WARN_ON_ONCE()` with it.
- Effect of a mismatch: the warning only; the timer is still started, with
  the soft or hard expiry chosen at setup.
- `is_rel`: written at start only under `CONFIG_TIME_LOW_RES`, in
  `hrtimer_update_lowres()`; otherwise it stays false.
- `__hrtimer_setup_sleeper()` on `CONFIG_PREEMPT_RT`: adds
  `HRTIMER_MODE_HARD` when `rt_or_dl_task_policy(current)` is true and
  `HRTIMER_MODE_SOFT` was not passed.
- `hrtimer_sleeper_start_expires()`: on `CONFIG_PREEMPT_RT` adds
  `HRTIMER_MODE_HARD` to the start mode when `sl->timer.is_hard` is set, so
  callers pass the plain mode and the check stays quiet.
- **Unsafe usage**: starting the timer of a `struct hrtimer_sleeper` with
  `hrtimer_start_expires()` or `hrtimer_start()`; on `CONFIG_PREEMPT_RT` the
  mismatch check warns when `__hrtimer_setup_sleeper()` added
  `HRTIMER_MODE_HARD`.
  - Safe: `hrtimer_sleeper_start_expires()`, as `do_nanosleep()` does; the
    check in `hrtimer_start_range_ns_common()` defines the requirement.

**User-controlled expiry times**

- `hrtimer_start_range_ns_user()` in `kernel/time/hrtimer.c` is the separate
  start function; `hrtimer_start_expires_user()` in `include/linux/hrtimer.h`
  is its counterpart to `hrtimer_start_expires()`. Both return `bool`.
- Difference from `hrtimer_start_range_ns()`: after the same enqueue, when
  the timer would become the next event to program,
  `hrtimer_check_user_timer()` tests whether the soft expiry is already in
  the past; if so it dequeues the timer again and the clock event device is
  not armed for it.
- Callback on an expired timer: never invoked by the start function; the
  caller may hold a lock the callback takes.
- Return `true`: the timer is queued and the callback will run; this is also
  returned for a timer in the past that is not the first to expire.
- Return `false`: the timer is not queued and the callback will not run.
- Caller on `false`: does the expiry work itself in its own context, for
  example `timerfd_hrtimer_start()` in `fs/timerfd.c` calls
  `__timerfd_triggered()`, and `common_timer_set()` in
  `kernel/time/posix-timers.c` calls `posix_timer_queue_signal()`.
- `alarm_start_timer()` in `kernel/time/alarmtimer.c`: uses it and returns
  `bool` with the same meaning; a caller handles `false` itself, as
  `timerfd_alarm_start()` in `fs/timerfd.c` does.
- `hrtimer_sleeper_start_expires()`: uses `hrtimer_start_expires_user()`; on
  `false` it sets `sl->task` to NULL and the task state to `TASK_RUNNING`.
- **Unsafe usage**: ignoring the return value; the expiry is lost.
  - Safe: test it and handle the expiry, as `timerfd_hrtimer_start()` does.
- **Unsafe usage**: sleeping after `hrtimer_sleeper_start_expires()` without
  testing `sl->task`; for an expired sleeper no timer is queued to wake the
  task.
  - Safe: `if (t->task) schedule();`, as `do_nanosleep()` does.

**hrtimer callback contract**

- Hard timers: `__run_hrtimer()` is reached from `hrtimer_interrupt()`, or
  from `hrtimer_run_queues()` while high resolution mode is not active; both
  are hard interrupt context with interrupts disabled.
- Interrupt state in the callback: `__run_hrtimer()` drops `cpu_base->lock`
  with the flags its caller saved, so soft timers run with interrupts
  enabled.
- Soft timers on `CONFIG_PREEMPT_RT`: the callback runs with
  `cpu_base->softirq_expiry_lock` held, taken in `hrtimer_run_softirq()`; the
  field does not exist without `CONFIG_PREEMPT_RT`.
- `lockdep_hrtimer_enter()` in `include/linux/irqflags.h`: with
  `CONFIG_TRACE_IRQFLAGS`, tells lockdep from `timer->is_hard` whether the
  callback stays in hard interrupt context on RT; with
  `CONFIG_PROVE_RAW_LOCK_NESTING` a callback of a `HRTIMER_MODE_HARD` timer
  is checked as one that may take raw spinlocks only.
- Timer memory after the callback returns: `__run_hrtimer()` reads
  `timer->is_queued` only when the return value is `HRTIMER_RESTART`;
  otherwise it only compares the pointer with `base->running`.
- **Potentially unsafe usage**: freeing the object that holds the timer from
  its callback.
  - Unsafe: when the callback returns `HRTIMER_RESTART`, or another context
    can still start or cancel the timer.
  - Safe: when the callback returns `HRTIMER_NORESTART` and nothing else
    touches the timer, as `tcp_pace_kick()` in `net/ipv4/tcp_output.c` does
    when its `sock_put()` drops the reference taken at the start;
    `__run_hrtimer()` reads `timer->is_queued` only for `HRTIMER_RESTART`.

**Cancelling an hrtimer**

- Models have the return values, the wait loop and the absence of an
  operation that prevents re-arming right; see `hrtimer_cancel()` in
  `kernel/time/hrtimer.c`.
- `hrtimer_cancel_wait_running()` on `CONFIG_PREEMPT_RT`: sleeps on
  `softirq_expiry_lock` only when `timer->is_soft` is set; for a
  `HRTIMER_MODE_HARD` timer, or one on the migration base, it is
  `cpu_relax()`.
- `hrtimer_cancel()` without `CONFIG_PREEMPT_RT`: spins and checks nothing
  about the calling context.
- **Unsafe usage**: `hrtimer_cancel()` on a soft timer from a context that
  can interrupt its callback on the same CPU, such as a hard interrupt
  handler; the callback never finishes and the loop never ends.
  - Safe: `hrtimer_try_to_cancel()`, which returns -1 instead of waiting
    while `hrtimer_callback_running()` is true, and handling -1.
- **Unsafe usage**: `hrtimer_cancel()` while holding a lock the callback
  takes.
  - Safe: take the lock, call `hrtimer_try_to_cancel()`; on -1 drop the lock,
    call `hrtimer_cancel_wait_running()` and retry, as `do_timerfd_settime()`
    in `fs/timerfd.c` does.

## Sleeping and delays

**Sleep and delay helpers**

- `Documentation/timers/delay_sleep_functions.rst`: gives no "10 us – 20 ms"
  or "20 ms and up" ranges. Its order for non-atomic code is `fsleep()` when
  unsure, `msleep()` and its variants whenever possible, `usleep_range()` and
  its variants only when `msleep()` accuracy is not sufficient, `udelay()` and
  its variants for very short delays.
- `schedule_timeout()`: not mentioned in the rst; its rules are in the
  kerneldoc in `kernel/time/sleep_timeout.c`.
- `fsleep()` middle branch: `usleep_range(usecs, usecs + (usecs >> 2))`, taken
  for `10 < usecs < USLEEP_RANGE_UPPER_BOUND`.
- `USLEEP_RANGE_UPPER_BOUND` in `include/linux/delay.h`: 4 ticks in
  microseconds, so it depends on `HZ`: 4000 at `HZ=1000`, 16000 at `HZ=250`,
  40000 at `HZ=100`. `fsleep(20000)` is `msleep(20)` at `HZ=1000` and
  `usleep_range(20000, 25000)` at `HZ=100`.
- `fsleep()` on the `msleep()` branch: the request is rounded up to a whole
  millisecond, then to a whole jiffy by `msecs_to_jiffies()`, and at wheel
  level 0 the wheel adds up to one jiffy. Just above the bound the total can
  exceed 25%; for example `fsleep(4001)` at `HZ=1000` can take up to 6 ms.
- `msleep()`: passes `msecs_to_jiffies(msecs)` to
  `schedule_timeout_uninterruptible()` with no extra jiffy. Its timer still
  cannot fire early, because `calc_index()` in `kernel/time/timer.c` rounds
  every timer up to the next bucket of its wheel level.
- `msleep()` and `schedule_timeout()` lateness: up to one jiffy while the
  timeout is below `LVL_START(1)` (63 jiffies, wheel level 0). Above that it is
  up to one granule of the level, `LVL_GRAN()`, which the rst and the
  `msleep()` kerneldoc give as 12.5%.
- `usleep_range()`: `min` is the hrtimer's soft expiry and `max` its hard
  expiry; in high-resolution mode the clock event is programmed for the hard
  expiry. The task then wakes before `max` only when another hrtimer interrupt
  runs in the window, and interrupt and scheduling latency come on top of
  `max`.
- `schedule_timeout()` in `TASK_UNINTERRUPTIBLE`: any `wake_up_process()` on
  the task ends it early and it returns the jiffies left.
  `schedule_timeout_uninterruptible()` alone is therefore not a guaranteed
  minimum delay; `msleep()` and `usleep_range_state()` repeat their timeout
  call until it returns 0.
- `schedule_timeout()` with a timeout of `WHEEL_TIMEOUT_CUTOFF` jiffies or
  more: `calc_wheel_index()` expires the timer at `WHEEL_TIMEOUT_MAX` (about
  12 days at `HZ=1000`), so the call returns early with a non-zero remainder.
- `udelay()`: the generic definition in `include/asm-generic/delay.h` does not
  cap a non-constant argument; a constant argument of `DELAY_CONST_MAX`
  (20000) or more fails to link through `__bad_udelay()`.
- `MAX_UDELAY_MS` in `include/linux/delay.h`: decides whether the `mdelay()`
  defined there, with a constant argument, is one `udelay()` call or a loop of
  `udelay(1000)`.

## Reading clocks

**ktime_get family:** Rows where this tree differs from the usual picture;
every other non-fast `ktime_get` accessor declared in
`include/linux/timekeeping.h` loops on `tk_core.seq` and can spin forever in
NMI.

| Accessor | Clock | NMI and tracing |
|---|---|---|
| `ktime_get_seconds()` | `CLOCK_MONOTONIC` seconds | plain read of `ktime_sec` on 32-bit and 64-bit, no seqcount; `WARN_ON()` if suspended; not `notrace` |
| `ktime_get_real_seconds()` | `CLOCK_REALTIME` seconds | `CONFIG_64BIT`: one `READ_ONCE()`; 32-bit: `tk_core.seq` loop, can spin |
| `__ktime_get_real_seconds()` | `CLOCK_REALTIME` seconds | `noinstr`, no seqcount on any arch; 64-bit `xtime_sec` unprotected on 32-bit |
| `ktime_get_boottime_seconds()`, `ktime_get_clocktai_seconds()` | `CLOCK_BOOTTIME`, `CLOCK_TAI` seconds | `tk_core.seq` loop through `ktime_get_coarse_with_offset()`; can spin |
| `ktime_get_real_fast_ns()` | `CLOCK_REALTIME` | latch, does not spin; not `notrace` |
| `ktime_get_aux()`, `ktime_get_aux_ts64()` | one `CLOCK_AUX` id | seqcount of that aux `struct tk_data`; can spin |
| `ktime_get_coarse_real_ts64_mg()`, `ktime_get_real_ts64_mg()` | `CLOCK_REALTIME` with a floor | `tk_core.seq` loop; can spin |
| `ktime_get_snapshot_id()` | clock id passed in | seqcount of the selected `struct tk_data`; can spin |

- There is no ktime_get_tai_seconds(); the `CLOCK_TAI` seconds accessor is
  `ktime_get_clocktai_seconds()` in `include/linux/timekeeping.h`.
- ktime_get_raw_seconds is defined nowhere; only
  `Documentation/core-api/timekeeping.rst` names it.
- `CLOCK_MONOTONIC_RAW` has no coarse accessor either; the accessors named
  for it are `ktime_get_raw()`, `ktime_get_raw_ns()`, `ktime_get_raw_ts64()`
  and `ktime_get_raw_fast_ns()`.
- There is no ktime_get_snapshot(); `ktime_get_snapshot_id()` in
  `kernel/time/timekeeping.c` does that job and leaves `valid` false when
  `timekeeping_suspended` is set.
- `__ktime_get_real_seconds()`: the accessor for restricted contexts; its
  callers are in `arch/x86/kernel/cpu/mce/core.c` and
  `kernel/debug/kdb/kdb_main.c`.
- `ktime_get_real_fast_ns()`: reads `base_real` from `tk_fast_mono` inside
  the latch loop, so base and realtime offset are consistent with each other.
- `ktime_get_boot_fast_ns()` and `ktime_get_tai_fast_ns()`: add `offs_boot`
  or `offs_tai` read with `data_race()` outside the latch loop; the offset
  can be newer than the base, and torn on 32-bit.
- `ktime_get_real_fast_ns()` is not in `trace_clocks[]` in
  `kernel/trace/trace.c`; the four `notrace` fast accessors are.
- `tk_core.seq` is write-held only inside `timekeeping_update_from_shadow()`
  and `tk_update_leap_state_all()`; the rest of `__timekeeping_advance()`
  works on `shadow_timekeeper` with only the lock held.
- `WARN_ON(timekeeping_suspended)` is not in every non-fast accessor; for
  example `ktime_get_raw()`, `ktime_get_raw_ts64()`,
  `ktime_get_coarse_ts64()`, `ktime_get_coarse_real_ts64()` and
  `ktime_get_real_seconds()` have none.
- `ktime_get_aux()` and `ktime_get_aux_ts64()`: `__must_check`, return
  `false` when the id is not an aux clock or the clock is not enabled;
  without `CONFIG_POSIX_AUX_CLOCKS` they are stubs that return `false`.
- `ktime_get_coarse_real_ts64_mg()` and `ktime_get_real_ts64_mg()`: for
  filesystem timestamps only; callers are in `fs/inode.c`; not exported.

**Clocks that stop or jump**

- `CLOCK_MONOTONIC` and `CLOCK_MONOTONIC_RAW` stop only for the interval
  between `timekeeping_suspend()` and `timekeeping_resume()`; the rest of the
  suspend sequence is counted.
- Suspend-to-idle: `timekeeping_suspend()` runs only from `tick_freeze()` in
  `kernel/time/tick-common.c`, when the last online CPU enters a cpuidle
  state that has `enter_s2idle`.
- Suspend-to-idle without such a state: `cpuidle_enter_s2idle()` in
  `drivers/cpuidle/cpuidle.c` never reaches `tick_freeze()`, so timekeeping
  is not suspended and no clock is stopped by the timekeeping code.
- `CLOCK_REALTIME`, `CLOCK_BOOTTIME` and `CLOCK_TAI` do not run during
  suspend; `__timekeeping_inject_sleeptime()` steps them forward by the sleep
  time on resume, and only when a source for that time exists.
- Sources of sleep time, in order of preference:
  - a clocksource with `CLOCK_SOURCE_SUSPEND_NONSTOP`, through
    `clocksource_stop_suspend_timing()` in `timekeeping_resume()`
  - `read_persistent_clock64()`, in `timekeeping_resume()`; the `__weak`
    default returns zero, which injects nothing
  - the RTC, through `rtc_resume()` in `drivers/rtc/class.c`, which calls
    `timekeeping_inject_sleeptime64()`
- `timekeeping_inject_sleeptime64()` and `rtc_resume()` exist only under
  `CONFIG_PM_SLEEP` with `CONFIG_RTC_HCTOSYS_DEVICE`, and `rtc_resume()` acts
  only for the device named by `CONFIG_RTC_HCTOSYS_DEVICE`.
- With none of the three sources, all five clocks resume from the value they
  had at `timekeeping_suspend()`; `CLOCK_BOOTTIME` then equals
  `CLOCK_MONOTONIC` plus the old `offs_boot`.
- RTC source: the step happens in device resume, after
  `timekeeping_resume()`; a read of `CLOCK_BOOTTIME`, `CLOCK_REALTIME` or
  `CLOCK_TAI` before `rtc_resume()` does not yet include the sleep time.
- `__timekeeping_inject_sleeptime()` rejects a delta that fails
  `timespec64_valid_strict()` with a printed warning and injects nothing.
- `CLOCK_REALTIME` also steps on a leap second, in
  `accumulate_nsecs_to_secs()`; the same code changes `tai_offset` by the
  opposite amount, so `CLOCK_TAI` does not step.
- `CLOCK_AUX` clocks: `aux_clock_set()` steps only that clock, by changing
  its `offs_aux`; `do_settimeofday64()` and `timekeeping_inject_offset()`
  change `tk_core` only, so an aux clock does not jump when the wall clock is
  set.
- `CLOCK_AUX` across suspend: `timekeeping_suspend()` and
  `timekeeping_resume()` update `tk_core` only; they inject no sleep time
  into an aux timekeeper and do not rebase its `cycle_last`.
- `ktime_get_aux()` has `WARN_ON(timekeeping_suspended)`, and
  `__timekeeping_advance()` returns early for an aux timekeeper while
  `timekeeping_suspended` is set.

## Model gaps

### Other mistakes models make

- Models take hrtimers to be queued on `struct timerqueue_head` through
  `struct timerqueue_node`. `timerqueue_add()` and `timerqueue_getnext()` take
  those types; the hrtimer queue is `struct timerqueue_linked_head` and is
  walked with `timerqueue_linked_first()` and `timerqueue_linked_next()`.
- Models take the two on-stack release functions to share one word order. They
  do not: `timer_destroy_on_stack()` in `include/linux/timer.h` is for
  `struct timer_list`, and `destroy_hrtimer_on_stack()` in
  `include/linux/hrtimer.h` is for `struct hrtimer`.
- Models take the timekeeper to be updated in place. Writers change
  `tk_core.shadow_timekeeper` under `tk_core.lock`, and
  `timekeeping_update_from_shadow()` copies it over `tk_core.timekeeper` inside
  the `tk_core.seq` write section. Exception: `tk_update_leap_state_all()`
  writes `next_leap_ktime` into both copies without the full copy.
- Models leave the auxiliary clocks out of the `ktime_get` family. When
  `ktime_get_aux()` or `ktime_get_aux_ts64()` returns `false`, no time was
  stored through the pointer.
- Models write `clock_was_set()` with no argument. It takes a mask of clock
  bases, `CLOCK_SET_WALL` or `CLOCK_SET_BOOT` from
  `kernel/time/tick-internal.h`, and sends an IPI only to CPUs for which
  `update_needs_ipi()` returns true, unless the cpumask allocation fails.
