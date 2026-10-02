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
