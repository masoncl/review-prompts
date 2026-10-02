# What the timers measurement found

Three models were asked the 42 questions in `timers-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels from 6.12 up to 7.1), reader A a little behind it (6.12 to
6.17), and reader B older again (6.10 to 6.12), which is before the deletion
functions lost their old names. The hand-written guide was never checked
against current sources, so differences between it and the built guide are
expected and are noted near the end.

All three know what the timer wheel, hrtimers and delayed work are, which
context each callback runs in, and that an object must not be freed while its
timer can still run. Readers A and C also know the current deletion and
shutdown functions and what each guarantees. What they get wrong is what moved
in the last few releases (the hrtimer structure and its headers, the hrtimer
start functions, how the hrtimer interrupt re-arms the device, clock event
programming, the clocksource watchdog), a handful of rules they all state too
strongly or too weakly, and, for reader B, most current names.

## What all three readers got wrong

Names and layouts that moved:

- **The hrtimer headers.** Every reader listed include/linux/hrtimer_defs.h,
  which does not exist. `struct hrtimer_cpu_base`, `struct hrtimer_clock_base`
  and `enum hrtimer_base_type` are in `include/linux/hrtimer_bases.h`, and
  `include/linux/hrtimer_rearm.h` is new.
- **`struct hrtimer` has no state field.** All three described a u8 `state`
  tested against a HRTIMER_STATE_ENQUEUED bit. The structure has the bools
  `is_queued`, `is_rel`, `is_soft`, `is_hard` and `is_lazy`;
  `HRTIMER_STATE_ENQUEUED` is a private `true` in `kernel/time/hrtimer.c`;
  `node` is a `struct timerqueue_linked_node` and a clock base's `active` is a
  `struct timerqueue_linked_head`, not the cached rbtree they described;
  `running` and `seq` are per clock base; `function` is `__private`.
- **`HRTIMER_MODE_LAZY_REARM`** was missing from every list of mode bits.
- **The hrtimer interrupt.** All three described an in_hrtirq flag and a
  reprogram at the end of `hrtimer_interrupt()`. The flag is
  `cpu_base->deferred_rearm`; with `CONFIG_HRTIMER_REARM_DEFERRED` the
  interrupt only sets `TIF_HRTIMER_REARM` and `__hrtimer_rearm_deferred()`
  programs the device on the way out; the softirq is raised with
  `raise_timer_softirq()`; a retry happens when the next expiry is already in
  the past, not when programming fails; and the "interrupt took" warning is
  gone. Reader C said outright that no such deferral exists.
- **Clock event programming.** `clockevents_program_event()` does not clamp a
  short delta up to `min_delta_ns`: it programs `min_delta_ticks` and sets
  `next_event_forced`. There is no CLOCK_EVT_FEAT_KTIME (readers A and B);
  `set_next_ktime()` belongs to `CLOCK_EVT_FEAT_HRTIMER`, and the path that
  hands the device a counter value is `CLOCK_EVT_FEAT_CLOCKSOURCE_COUPLED`
  with `set_next_coupled()` and `ktime_expiry_to_cycles()`.
- **The clocksource watchdog** has been rewritten. The names all three
  offered (cs_read_watchdog(), WATCHDOG_MAX_SKEW, uncertainty_margin,
  CLOCK_SOURCE_VERIFY_PERCPU) are gone; the checks are
  `watchdog_check_freq()` and `watchdog_check_cpu_skew()`, from a timer
  pinned to the boot CPU.

Facts that would change a verdict:

- **Starting a timer whose expiry comes from user space.** Readers B and C
  said no such interface exists and that the start functions return nothing;
  reader A knew a name and little else. `hrtimer_start_range_ns_user()` and
  `hrtimer_start_expires_user()` return false, with the timer dequeued, when
  the timer would be the first to expire and its time has already passed, and
  the caller has to deliver the expiry itself (`fs/timerfd.c`,
  `kernel/time/alarmtimer.c`, `kernel/time/posix-timers.c`,
  `hrtimer_sleeper_start_expires()`).
- **A callback that re-arms its own timer.** Readers A and B said
  `timer_delete_sync()` cannot cope with it. It can: `__timer_delete_sync()`
  tries again once the callback has finished and dequeues what it queued. The
  unsafe case is a re-arm from some other path, which only
  `timer_shutdown_sync()` stops. Reader B said the same of `hrtimer_cancel()`
  and proposed looping on `hrtimer_try_to_cancel()` as the cure, which is what
  `hrtimer_cancel()` already is.
- **Waiting for a running callback.** Each reader missed a part. Reader B
  said deleting a timer synchronously from its own callback is safe and
  detected (it loops for ever, because `__try_to_del_timer_sync()` returns -1
  while `base->running_timer` is the timer), that softirq context is
  forbidden (only hardirq warns, and only without `TIMER_IRQSAFE`) and that
  nothing detects lock deadlocks (lockdep does, through the timer's
  `lockdep_map`). Readers A and C left out that, for a timer without
  `TIMER_IRQSAFE`, holding any lock that is also taken in hardirq context
  deadlocks, even one the callback never touches. Reader C said a plain
  lockdep build reports it; the reports need `CONFIG_PROVE_LOCKING`.
- **`hrtimer_forward()` on a queued timer** does not always warn: it returns 0
  first when the expiry is still in the future, and it never corrupts the
  queue, it just refuses. It is also legal outside the callback on a timer
  that is neither queued nor running.
- **`clock_was_set()`** does not interrupt every CPU. It does nothing but
  notify timerfd unless high resolution or NOHZ is active, and
  `update_needs_ipi()` then picks only the CPUs whose first timer moved.
- **`udelay()` may return early**, its kerneldoc says; every reader said it
  overshoots. None gave the thresholds of `fsleep()` (10 microseconds, then
  `USLEEP_RANGE_UPPER_BOUND`, four ticks) or what the documentation
  recommends, and all three offered duration ranges the document does not
  contain.
- **Lock order.** Nobody had the order: timer base locks lowest index first,
  then the timer migration locks child before parent; the PREEMPT_RT expiry
  locks before the raw base lock; the runqueue lock before the hrtimer base
  lock; `jiffies_lock` dropped before `update_wall_time()`.

## What only some readers got wrong

Readers A and B:

- **Level 0 of the wheel is not exact.** `calc_index()` adds one granule at
  every level, so a callback never runs before its expiry and at level 0 runs
  up to a jiffy after it. A timeout at or past `WHEEL_TIMEOUT_CUTOFF` is
  clamped, so it does fire early (reader B said "never earlier").
- **The tick handler** is `tick_nohz_handler()`; tick_sched_timer() does not
  exist. `struct tick_sched` keeps its state in `flags` (`TS_FLAG_*`), not in
  the separate fields reader B listed.
- **The timekeeper lock** is `tk_core.lock`, a member of `struct tk_data`;
  there is no timekeeper_lock. Reader B also thought there is one timekeeper
  (there is an array, with auxiliary clocks under `CONFIG_POSIX_AUX_CLOCKS`)
  and that `jiffies_lock` is a seqlock.
- **Where timers are queued.** Reader A put every pinned timer in
  `BASE_LOCAL` and gave two bases without NOHZ; reader B had a base called
  BASE_STD and said `mod_timer()` leaves a pinned timer on its CPU. There are
  three bases under `CONFIG_NO_HZ_COMMON` and one otherwise, a deferrable
  timer goes to `BASE_DEF` pinned or not, and `__mod_timer()` always moves the
  timer to the calling CPU's base unless its callback is running or it stays
  in the same bucket.
- **`hrtimer_cancel()` returns 0**, not 1, after it has waited out a running
  callback (reader A); on PREEMPT_RT only a softirq-mode timer sleeps on the
  expiry lock.

Reader A alone: named destroy_timer_on_stack() (it is
`timer_destroy_on_stack()`) and used del_timer_sync() in passing in several
answers while listing it as gone in another; offered the return value of
`timer_delete()` as the correct alternative to `timer_pending()`; said
`secs_to_jiffies()` rounds up (it multiplies by `HZ`); named a hotplug callback
tmigr_cpu_offline() that does not exist.

Reader C alone: said `__mod_timer()` "always" queues on the current CPU; said
debug objects report freeing a timer whose callback is running (the active
state ends at `detach_timer()`, so only a queued timer is caught); offered
"drop the lock and retry" after `timer_delete_sync_try()` returns -1, which no
in-tree caller does; said on PREEMPT_RT the timer softirqs may run in
ksoftirqd (they go to the `ktimers` thread through `raise_timer_softirq()`);
said it did not recognise `hrtimer_start_range_ns_common()`.

Reader B alone, all of it because its picture predates the renames:

- del_timer(), del_timer_sync(), try_to_del_timer_sync() and from_timer() given
  as the current names, plus timer_setup_flags() and TIMER_INIT, which never
  existed. The tree has `timer_delete()`, `timer_delete_sync()`,
  `timer_delete_sync_try()` and `timer_container_of()`.
- "There is no variant that only modifies a pending timer or only shortens a
  timeout": `mod_timer_pending()` and `timer_reduce()`.
- Shutdown guessed to be a bit in `flags`. It is `function` set to NULL under
  the base lock, and every arming path tests for that.
- `schedule_timeout()`, `msleep()` and `usleep_range()` placed in
  `kernel/time/timer.c`; they are in `kernel/time/sleep_timeout.c`.
- `TIMER_IRQSAFE` callbacks run with interrupts disabled, which includes every
  delayed work timer; it said interrupts are always enabled. It also said
  softirq-mode hrtimer callbacks run with interrupts off.
- CLOCK_REALTIME_ALARM and CLOCK_BOOTTIME_ALARM listed as hrtimer clocks, and
  an unknown clock id said to hit a BUG (it warns and uses the monotonic
  base).
- "Both not queued and not running means safe to free" for the hrtimer state
  queries; they are snapshots.
- Things it said it did not know: whether an hrtimer shutdown operation
  exists (none does), whether `secs_to_jiffies()` exists, which KUnit tests
  there are (`kernel/time/time_test.c` only).

## What the readers already knew

Readers A and C needed almost nothing on the timer flags, the arming variants,
the table of what each deletion and shutdown function guarantees, how shutdown
is recorded, the wheel's granularity, how idle CPUs' global timers are expired
through the timer migration hierarchy, and the callback context of each kind of
timer. Reader C was also right about the scheduler tick emulation (no
corrections), the timekeeper layout, the clock accessors and who advances
jiffies. All three had the jiffies comparison rules. These are dropped from the
build set, except the table of what each deletion and shutdown function
guarantees, which the waiting and freeing rules rest on and where reader B had
four things wrong.

## Where the hand-written guide is stale

`timers.md` is about one thing, a driver's timer: how it is armed, stopped and
freed and what its callback may do. Most of that is still right, and the
function names it gives are the current ones. What is wrong or missing:

- "hrtimer callback not returning HRTIMER_RESTART or HRTIMER_NORESTART ->
  undefined". `__run_hrtimer()` compares the value with `HRTIMER_RESTART`;
  anything else is treated as no restart.
- "Callback context: hardirq by default" holds only without PREEMPT_RT, where
  a timer not marked `HRTIMER_MODE_HARD` is moved to softirq expiry. The
  context table has no column for `TIMER_IRQSAFE`, whose callbacks run with
  interrupts disabled, and nothing says that starting a timer with a
  soft or hard bit different from the one it was set up with warns.
- "`timer_delete_sync()` spin-waits". On PREEMPT_RT it sleeps on the base's
  expiry lock, which is why the caller must be preemptible there.
- The deadlock rule is given only for a lock the callback takes. The wider
  one, any lock also taken from hardirq context, is absent.
- The list of renamed functions has the deletion and initialisation functions
  but not `timer_container_of()` (from_timer()), `timer_delete_sync_try()`,
  `timer_destroy_on_stack()`, `hrtimer_update_function()` for the now private
  callback pointer, or the `_user` start functions.
- `timer_shutdown()` without the wait, `disable_delayed_work_sync()` and the
  fact that there is no hrtimer shutdown are not mentioned.
- "`vfree()` ... safe" is true (`vfree()` tests `in_interrupt()`) but is about
  vmalloc, as is most of the "unsafe in callbacks" list, which is generic
  atomic-context advice.
- It has no map of `kernel/time/` at all.

## Left out of the build set

The hand-written guide is 581 words, under the 600-word floor for a built
guide, so the build set is sized to 600 words (480 to 720) with no question
budgeted under 40. It holds 10 of the 42 questions with 540 words of budget,
which with titles and headings comes to about 645, chosen for a reviewer of a
driver's timer first and of `hrtimer.c` second. The first build set held 13
with 465 words, eight of them budgeted under 40, and their answers came out as
fragments that meant little without the question beside them. Thirteen at the
floor overshoot the size, so three went back to the measurement set and the
room went to the ten that stayed. The three: the table of timer kinds and the
pending check, where readers A and C needed one to three corrections each and
what a reviewer decides on (`TIMER_IRQSAFE`, soft and hard expiry, that only
the waiting functions say a callback has finished) is carried by the waiting,
mode and cancel answers; and the hrtimer expiry path, where every reader was
out of date but which serves only someone changing `hrtimer.c`. Left out
although a reader got them wrong: the wheel's bases and granularity, CPU
hotplug and the PREEMPT_RT expiry locks (what a driver needs of these, that on
PREEMPT_RT the wait sleeps, is in the waiting and cancel questions); hrtimer
clocks, the callback contract, forwarding, the state queries and low
resolution mode (readers A and C were nearly right, and the forwarding slip is
a warning, not a wrong verdict); the sleep helpers, jiffies arithmetic and
delayed work, which want a guide of their own size; all of timekeeping,
clocksources, clock event devices, the tick, NOHZ and lock order, where every
reader was out of date but which a 600-word guide cannot carry and which the
old guide never covered; and the checklist of configurations. Left out because
readers A and C already knew them: the timer flags, the arming variants,
shutdown state, timers of idle CPUs, the callback context of the wheel.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A:  90 corrections, 31% rewritten on average, assumed 6.12 to 6.17
reader B: 130 corrections, 75% rewritten on average, assumed 6.10 to 6.12
reader C: 101 corrections, 23% rewritten on average, assumed 6.12 to 7.1

question                           reader A      reader B      reader C
timers.core-files                  10% ( 4)      88% ( 6)       5% ( 4)
timers.timer-kinds                 17% ( 1)      44% ( 4)      11% ( 3)
timers.timer-api-names              4% ( 3)      77% ( 3)      28% ( 3)
timers.timer-flags                  2% ( 1)      77% ( 1)       1% ( 1)
timers.arming-variants             10% ( 1)      84% ( 3)      10% ( 2)
timers.wheel-granularity           11% ( 1)      79% ( 5)       3% ( 1)
timers.wheel-bases                 60% ( 3)      85% ( 3)      24% ( 2)
timers.idle-cpu-timers              0% ( 0)      73% ( 2)      12% ( 1)
timers.timer-callback-context       8% ( 2)      65% ( 2)       2% ( 1)
timers.cpu-hotplug                 35% ( 2)      85% ( 3)      28% ( 1)
timers.delete-variants              7% ( 2)      55% ( 4)      10% ( 2)
timers.shutdown-state               0% ( 0)      92% ( 1)       3% ( 1)
timers.sync-delete-usage           27% ( 2)      78% ( 3)      32% ( 3)
timers.free-after-delete           25% ( 1)      69% ( 1)       6% ( 1)
timers.pending-check               14% ( 1)      63% ( 1)      20% ( 1)
timers.rt-expiry                   34% ( 1)      82% ( 2)      29% ( 2)
timers.hrtimer-api-names           14% ( 4)      70% ( 7)      10% ( 5)
timers.hrtimer-modes               33% ( 2)      74% ( 3)      36% ( 4)
timers.hrtimer-clocks              35% ( 1)      81% ( 3)      42% ( 1)
timers.hrtimer-callback            19% ( 1)      82% ( 2)      26% ( 2)
timers.hrtimer-forward-usage       35% ( 2)      81% ( 4)      23% ( 3)
timers.hrtimer-cancel              24% ( 1)      69% ( 2)       5% ( 1)
timers.hrtimer-user-start          62% ( 1)      95% ( 1)      94% ( 1)
timers.hrtimer-struct              38% ( 4)      68% ( 3)      39% ( 9)
timers.hrtimer-state-queries       33% ( 1)      74% ( 1)       2% ( 1)
timers.hrtimer-expiry-path         47% ( 3)      82% ( 4)      52% ( 4)
timers.hrtimer-lowres              33% ( 1)      74% ( 1)      18% ( 1)
timers.sleep-helpers               63% ( 4)      59% ( 9)      19% ( 4)
timers.jiffies-usage               20% ( 2)      65% ( 1)      21% ( 2)
timers.delayed-work                24% ( 2)      76% ( 3)      28% ( 5)
timers.timekeeper-layout           38% ( 5)      87% ( 3)       5% ( 2)
timers.clock-accessors             33% ( 2)      51% ( 2)      10% ( 3)
timers.jiffies-update              60% ( 6)      83% ( 3)      15% ( 2)
timers.clocksource-contract        49% ( 3)      69% ( 5)      29% ( 3)
timers.clocksource-watchdog        69% ( 2)      90% ( 3)      52% ( 3)
timers.clockevent-contract         36% ( 2)      75% ( 3)      47% ( 3)
timers.clockevent-programming      83% ( 3)      83% ( 3)      56% ( 2)
timers.tick-sched                  27% ( 2)      73% ( 5)       0% ( 0)
timers.nohz-idle-stop              60% ( 3)      86% ( 4)      25% ( 4)
timers.tick-dependency             53% ( 1)      73% ( 2)      43% ( 1)
timers.lock-order                  56% ( 6)      83% ( 6)      45% ( 5)
timers.change-checklist            34% ( 1)      84% ( 3)      13% ( 1)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `timers.sleep-helpers`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `timers.timer-callback-context`, `timers.shutdown-state`, `timers.pending-check`, `timers.hrtimer-callback`, `timers.clock-accessors`.

## Questions reorganised

Subjects now: finding your way, timer wheel timers (7 questions), hrtimers (6), sleeping and
delays (1), reading clocks (1); 18 questions before and after, nothing merged or dropped.
`timers.hrtimer-struct` asked for the fields of `struct hrtimer`; `timers.hrtimer-state` replaces
it and asks how code finds out whether a timer is queued or running, where every reader tested a
state field that is gone, and what that answer is worth a moment later. Its headers are rows of
`timers.core-files`. The rest were reworded to ask two or three things and no inventory;
`timers.hrtimer-modes` no longer asks for the list of mode bits.
