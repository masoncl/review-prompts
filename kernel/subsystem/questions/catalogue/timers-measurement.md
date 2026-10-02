# Questions: Timers and Timekeeping (measurement set)

- guide: timers.md
- title: Timer Subsystem

A wide set of questions about `kernel/time/`: the timer wheel, hrtimers, the
sleep helpers, timekeeping, clocksources and clock event devices, the tick and
NOHZ. It is used to measure what a model already knows before deciding what
the built guide should spend its words on. The hand-written guide it will
replace is 581 words and covers only the driver-facing part (arming, deleting
and freeing timers, callback context). POSIX timers, itimers, alarmtimers, NTP
and the vDSO are left out. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## timers.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 120

Which files hold the timer wheel, the code that pulls timers off idle CPUs,
hrtimers, the sleep and timeout helpers, timekeeping, clocksources, clock
event devices, the tick (common, oneshot, broadcast, NOHZ), and the public and
internal headers for each? A table. Start from `kernel/time/` and
`include/linux/timer.h`.

## timers.timer-kinds: Choosing a timer kind

- section: Finding your way
- relevance: 4 - the callback context decides what the callback may do
- words: 100

Compare a `struct timer_list` timer, an hrtimer in each of its expiry modes
and a `struct delayed_work`: the resolution of each, the context its callback
runs in on a kernel without PREEMPT_RT, whether interrupts are enabled there,
and whether the callback may sleep. A table.

# The timer wheel

## timers.timer-api-names: Timer wheel function names

- section: Timer wheel interface
- relevance: 5 - the names have changed more than once and old ones do not compile
- words: 100

What does this tree call the functions and macros that initialise a
`struct timer_list` (including one on the stack), arm it, delete it, shut it
down, and get from the callback's argument to the structure that embeds the
timer? Which older names for these do not exist in this tree? Start from
`include/linux/timer.h`.

## timers.timer-flags: Timer flags

- section: Timer wheel interface
- relevance: 3 - each flag changes where or how the callback runs
- words: 80

Which flags may be passed when a `struct timer_list` is initialised, what does
each change, and which other bits of the `flags` word belong to the core?
Start from `TIMER_INIT_FLAGS`.

## timers.arming-variants: Arming an already pending timer

- section: Timer wheel interface
- relevance: 3 - the variants differ in what they do to a pending or inactive timer
- words: 90

For each function that arms a timer-wheel timer, what does it do when the
timer is already pending and when it is inactive, and what does it return?
Include the variants that only modify a pending timer or only shorten a
timeout. Start from `__mod_timer()` and `add_timer()`.

## timers.wheel-granularity: Expiry accuracy

- section: Timer wheel internals
- relevance: 3 - code that needs precision must not use the wheel
- words: 80

How accurate is the expiry of a timer-wheel timer: how is the requested expiry
mapped to a bucket, can the callback run earlier than requested, how large can
the delay be relative to the timeout, and what happens to a timeout longer
than the wheel can hold? Start from `calc_wheel_index()`.

## timers.wheel-bases: Per-CPU timer bases

- section: Timer wheel internals
- relevance: 3 - decides which CPU a callback runs on
- words: 80

How many timer bases does each CPU have, which timers go into which, on which
CPU does `mod_timer()` queue a timer, and how is a timer put on a chosen CPU?
Start from `get_timer_this_cpu_base()` and `add_timer_on()`.

## timers.idle-cpu-timers: Timers of idle CPUs

- section: Timer wheel internals
- relevance: 3 - explains why a callback can run on a CPU that never armed it
- words: 90

When a CPU goes idle with timer-wheel timers queued, which of them can be
expired by another CPU, which code decides who expires them, and on which CPU
does the callback then run? If this tree has no such mechanism, say how an
idle CPU's timers are handled instead. Start from
`kernel/time/timer_migration.c`.

## timers.timer-callback-context: Timer wheel callback context

- section: Timer wheel internals
- relevance: 4 - what the callback may do follows from this
- words: 80

In what context does the expiry code call a timer-wheel callback: which
softirq, which locks are held or dropped, are interrupts enabled, may the
callback free the object holding the timer, and what is checked when the
callback returns? Start from `expire_timers()` and `call_timer_fn()`.

## timers.cpu-hotplug: CPU hotplug

- section: Timer wheel internals
- relevance: 2 - matters to pinned timers and to changes in the core
- words: 70

What happens to the timer-wheel timers and the hrtimers queued on a CPU that
goes offline, including pinned ones, and which hotplug callbacks do it? Start
from `timers_dead_cpu()` and `hrtimers_cpu_dying()`.

# Deleting and freeing timers

## timers.delete-variants: Deletion and shutdown guarantees

- section: Stopping a timer
- relevance: 5 - choosing the wrong one is a use-after-free
- words: 110

For each function that deletes or shuts down a timer-wheel timer, what is
guaranteed when it returns (not queued, callback not running, cannot be armed
again) and what does it return? A table. Start from `__timer_delete()` and
`__timer_delete_sync()`.

## timers.shutdown-state: Shutdown state

- section: Stopping a timer
- relevance: 4 - explains what a later arm does and why
- words: 60

How does this tree record that a timer-wheel timer has been shut down, what do
the arming functions do when they find it in that state, and how is such a
timer made usable again? If this tree has no shutdown operation, say so.

## timers.sync-delete-usage: Waiting for a running callback

- section: Stopping a timer
- relevance: 5 - the deadlocks are invisible in a diff
- words: 110

What usage of the functions that wait for a running timer-wheel callback is
unsafe (the calling context, the locks the caller holds, calling from the
callback itself), and what that looks similar is correct? Which of these
mistakes does the kernel detect, and with what? Start from
`__timer_delete_sync()`.

## timers.free-after-delete: Freeing the embedding object

- section: Stopping a timer
- relevance: 5 - the most common timer bug
- words: 100

Before an object that embeds a timer is freed, what usage is unsafe and what
that looks similar is correct? Cover a callback that re-arms its own timer,
and a timer and a work item that each start the other.

## timers.pending-check: Pending checks

- section: Stopping a timer
- relevance: 4 - reads as synchronisation and is not
- words: 70

What does `timer_pending()` report, what can change right after it returns,
and what does it say about whether the callback is running? What usage of it
is unsafe, and what that looks similar is correct?

## timers.rt-expiry: Expiry and cancellation on PREEMPT_RT

- section: Stopping a timer
- relevance: 3 - the constraints on callers are stricter there
- words: 90

On a PREEMPT_RT kernel, where do timer-wheel callbacks and softirq-mode
hrtimer callbacks run, how does a caller wait for a running callback instead
of spinning, and what does that require of the caller's context? Start from
`del_timer_wait_running()` and `hrtimer_cancel_wait_running()`.

# High-resolution timers

## timers.hrtimer-api-names: hrtimer function names

- section: hrtimer interface
- relevance: 5 - the initialisation interface was replaced
- words: 90

What does this tree call the functions that initialise an hrtimer (embedded,
on the stack, and the sleeper form), change its callback afterwards, start it
and cancel it? Which older names for these do not exist in this tree? Start
from `include/linux/hrtimer.h`.

## timers.hrtimer-modes: hrtimer modes

- section: hrtimer interface
- relevance: 4 - the mode decides the callback context, and a mismatch warns
- words: 100

Which mode bits does `enum hrtimer_mode` define, which of them take effect
when the timer is set up and which when it is started, what is checked when
the two disagree, and what happens on PREEMPT_RT to a timer marked neither
hard nor soft? Start from `__hrtimer_setup()` and
`hrtimer_start_range_ns_common()`.

## timers.hrtimer-clocks: hrtimer clocks

- section: hrtimer interface
- relevance: 3 - an unsupported clock id is not an error return
- words: 80

Which clock ids can an hrtimer be based on and what happens when another id is
passed, what is done with a relative timer on `CLOCK_REALTIME`, and what
happens to queued timers when the realtime clock is set? Start from
`hrtimer_clockid_to_base()` and `clock_was_set()`.

## timers.hrtimer-callback: hrtimer callback contract

- section: hrtimer interface
- relevance: 4 - re-arming wrongly either loses the timer or loops
- words: 100

In what context and with which locks held does an hrtimer callback run, what
may it return and what does the core do for each value, and what happens when
the callback starts its own timer and then also asks to be restarted? Start
from `__run_hrtimer()`.

## timers.hrtimer-forward-usage: Forwarding a periodic hrtimer

- section: hrtimer interface
- relevance: 3 - forwarding a queued timer corrupts the queue
- words: 70

What usage of `hrtimer_forward()` and `hrtimer_forward_now()` is unsafe, and
what that looks similar is correct? What do they return?

## timers.hrtimer-cancel: Cancelling an hrtimer

- section: hrtimer interface
- relevance: 5 - same use-after-free and deadlock classes as the timer wheel
- words: 100

What do `hrtimer_cancel()` and `hrtimer_try_to_cancel()` each guarantee and
return, what usage of them is unsafe (context, locks held, a callback that
re-arms), and does this tree have an hrtimer operation that also prevents
re-arming?

## timers.hrtimer-user-start: User-controlled expiry times

- section: hrtimer interface
- relevance: 4 - new interface with a return value the caller must handle
- words: 80

Does this tree have a separate way to start an hrtimer whose expiry time comes
from user space, and if so what does it do differently from
`hrtimer_start_range_ns()`, what does it return, and what must the caller do
with that? If there is none, say so and stop.

## timers.hrtimer-struct: hrtimer data structures

- section: hrtimer internals
- relevance: 4 - the layout has changed and out-of-tree habits break
- words: 100

Which fields does `struct hrtimer` have in this tree, how are "queued" and
"callback running" recorded, how are the per-CPU base and its clock bases laid
out and which structure orders the queued timers, and which headers define
them? Start from `include/linux/hrtimer_types.h`.

## timers.hrtimer-state-queries: hrtimer state queries

- section: hrtimer internals
- relevance: 3 - each answers a different question and two are lockless
- words: 70

What do `hrtimer_active()`, `hrtimer_is_queued()` and
`hrtimer_callback_running()` each report, which can be called without the base
lock, and what can a caller conclude from each?

## timers.hrtimer-expiry-path: hrtimer expiry and reprogramming

- section: hrtimer internals
- relevance: 3 - anyone changing hrtimer.c has to keep this sequence
- words: 110

Trace an hrtimer expiry in high-resolution mode from the clock event interrupt
to the hardware being programmed for the next event: which function runs the
hard queues, how are softirq-mode timers handed over, when is the device
re-armed and can that be deferred, and what is done when the handler keeps
finding expired timers? Start from `hrtimer_interrupt()`.

## timers.hrtimer-lowres: hrtimers without high resolution

- section: hrtimer internals
- relevance: 2 - explains late expiry on some configurations
- words: 60

When high-resolution mode is not active, from where are hrtimers expired and
how often, what does `hrtimer_resolution` hold, and how and when does a CPU
switch to high-resolution mode? Start from `hrtimer_run_queues()`.

# Sleeping, delays and jiffies

## timers.sleep-helpers: Sleep and delay helpers

- section: Sleeping and jiffies
- relevance: 4 - picking the wrong one busy-waits or oversleeps
- words: 100

Which mechanism is behind each of `udelay()`, `usleep_range()`, `msleep()`,
`fsleep()` and `schedule_timeout()`, where is each implemented, how much
longer than asked can each sleep, and which does the documentation recommend
for which duration? Start from `Documentation/timers/delay_sleep_functions.rst`.

## timers.jiffies-usage: Jiffies arithmetic

- section: Sleeping and jiffies
- relevance: 3 - wraparound bugs appear only after days of uptime
- words: 80

What usage of `jiffies` in comparisons, timeouts and unit conversions is
unsafe, and what that looks similar is correct? Cover wraparound, reading the
64-bit counter on 32-bit machines, and converting from seconds or
milliseconds. Start from `include/linux/jiffies.h`.

## timers.delayed-work: Delayed work

- section: Sleeping and jiffies
- relevance: 3 - a timer in disguise with its own cancel rules
- words: 90

How does a `struct delayed_work` use a timer (which flags, which callback, in
what context the work is queued), and what does each of the cancel, flush and
disable functions for it guarantee on return? Start from
`include/linux/workqueue.h`.

# Timekeeping

## timers.timekeeper-layout: Timekeeper data

- section: Timekeeping
- relevance: 3 - every change to timekeeping.c goes through this
- words: 100

Where does the timekeeper live in this tree, how many are there, how do
readers and the updater synchronise, and how is an update prepared and then
published? Start from `struct tk_data` in `kernel/time/timekeeping.c`.

## timers.clock-accessors: Clock read accessors

- section: Timekeeping
- relevance: 4 - the wrong accessor deadlocks in NMI or jumps across suspend
- words: 110

Which `ktime_get` family function reads which clock, which are coarse, which
are safe from NMI and tracing context and what do those give up, and which
clocks stop or jump across suspend and when the wall clock is set? A table.
Start from `include/linux/timekeeping.h` and
`Documentation/core-api/timekeeping.rst`.

## timers.jiffies-update: Advancing jiffies and wall time

- section: Timekeeping
- relevance: 3 - one CPU has the duty and handing it over is delicate
- words: 100

Which CPU advances jiffies and the wall clock, from which function, and under
which locks and sequence counts? How is that duty handed over when the CPU
goes idle or offline, and what is different with nohz_full CPUs? Start from
`tick_do_timer_cpu` and `tick_do_update_jiffies64()`.

# Clocksources and clock event devices

## timers.clocksource-contract: Clocksource driver contract

- section: Hardware drivers
- relevance: 3 - what every driver under drivers/clocksource must get right
- words: 100

What must a clocksource driver fill in and guarantee about its `read()`
callback, which flags does the driver set and which does the core set, how is
it registered, and how does the core choose among registered clocksources?
Start from `struct clocksource` and `__clocksource_register_scale()`.

## timers.clocksource-watchdog: Clocksource watchdog

- section: Hardware drivers
- relevance: 2 - decides when a TSC-like counter is demoted
- words: 100

How does the clocksource watchdog in this tree decide that a clocksource is
unstable: what does it compare, how often, from which CPUs, with what
thresholds, and what happens to a clocksource that fails? Start from
`clocksource_watchdog()`.

## timers.clockevent-contract: Clock event driver contract

- section: Hardware drivers
- relevance: 3 - the state callbacks replaced a single mode callback long ago
- words: 110

Which states can a clock event device be in, which callbacks does a driver
supply for them and for programming an event, which feature flags exist, how
is a device registered, and how does one become a CPU's tick device? Start
from `struct clock_event_device` and `tick_check_new_device()`.

## timers.clockevent-programming: Programming the next event

- section: Hardware drivers
- relevance: 3 - the error and retry rules are easy to break
- words: 100

How does the core turn an absolute expiry time into a device program call:
what is done when the expiry is in the past or closer than the device minimum,
what does forcing mean, what do the callbacks return, and is there a path that
hands the device a counter value instead of a delta? Start from
`clockevents_program_event()`.

# The tick and NOHZ

## timers.tick-sched: Scheduler tick emulation

- section: Tick
- relevance: 3 - the names here were changed recently
- words: 100

In oneshot mode, what generates the periodic scheduler tick with and without
high-resolution timers, what does the tick handler do, and which per-CPU
structure and flags hold the tick state? Start from
`tick_setup_sched_timer()` and `struct tick_sched`.

## timers.nohz-idle-stop: Stopping the idle tick

- section: Tick
- relevance: 3 - a missed wakeup here is a hang
- words: 110

Which calls does the idle loop make to stop and restart the tick, how is the
next event computed (which subsystems are asked), and under which conditions
is the tick kept running? Start from `tick_nohz_idle_stop_tick()` and
`tick_nohz_next_event()`.

## timers.tick-dependency: Tick dependencies

- section: Tick
- relevance: 2 - only matters to nohz_full, but every new user must set one
- words: 80

What stops a nohz_full CPU from turning its tick off: which dependency bits
exist, at which scopes can they be set, and how is a CPU told to re-evaluate?
Start from `enum tick_dep_bits` and `tick_nohz_dep_set_cpu()`.

# Changing the implementation

## timers.lock-order: Locks and their order

- section: What a change must preserve
- relevance: 3 - all raw spinlocks, several taken from interrupt context
- words: 100

Which locks protect the timer bases, the hrtimer bases, the timer migration
hierarchy, jiffies and the timekeeper, of what type is each, and in what order
may they be taken, including relative to the scheduler's runqueue lock?

## timers.change-checklist: Configurations a change must keep working

- section: What a change must preserve
- relevance: 3 - the code is full of variants that are rarely all built
- words: 100

Which configurations and debugging options does a change to `kernel/time/`
have to keep building and working (high resolution on and off, the NOHZ
variants, PREEMPT_RT, uniprocessor, 32-bit, debug objects, lockdep), and which
selftests and KUnit tests exercise it?
