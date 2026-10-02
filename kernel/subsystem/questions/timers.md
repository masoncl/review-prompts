# Questions: Timer Subsystem

- guide: timers.md
- title: Timer Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/timers-measurement.md` is the
wider set the readers were measured on and `catalogue/timers-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## timers.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## timers.core-files: Core files

- section: Finding your way
- relevance: 4 - files and headers have been split, and readers name ones that are gone

A table and nothing else, job to file: the timer wheel; pulling timers off idle CPUs; hrtimers;
the sleep and timeout helpers; timekeeping; clocksources; clock event devices; the tick (common,
oneshot, broadcast, NOHZ); the public and internal headers of the timer wheel and of hrtimers.
Where a reader is likely to look for a file or header that does not exist in this tree, say so
in the row. Start from `kernel/time/` and `include/linux/timer.h`.

# Timer wheel timers

## timers.timer-api-names: Timer wheel function names

- section: Timer wheel timers
- relevance: 5 - the names have changed more than once and old ones do not compile

Which functions and macros in `include/linux/timer.h` set up a `struct timer_list` that is
embedded or on the stack, arm it, delete it, shut it down, and get from the callback's argument to
the structure that embeds the timer? What naming pattern do they share? Does this tree still
define del_timer, del_timer_sync, try_to_del_timer_sync or from_timer? Start from
`include/linux/timer.h`.

## timers.delete-variants: Deletion and shutdown guarantees

- section: Timer wheel timers
- relevance: 5 - choosing the wrong one is a use-after-free

For each function that deletes or shuts down a timer-wheel timer, what is guaranteed about the
timer when the function returns, and what does its return value mean? Answer as a table of the
functions to choose between. Start from `__timer_delete()` and `__timer_delete_sync()`.

## timers.shutdown-state: Shutdown state

- section: Timer wheel timers
- relevance: 4 - explains what a later arm does and why

After a timer-wheel timer has been shut down, what do the arming functions do and return when
they are called on it, how can code tell that a timer is in that state, and how is it made
usable again? If this tree has no shutdown operation, say so.

## timers.timer-callback-context: Timer wheel callback context

- section: Timer wheel timers
- relevance: 4 - what the callback may do follows from this

In what context, and with interrupts in which state, does a timer-wheel callback run, and for
which timers is that different? What does the core check when the callback returns? Start from
`expire_timers()` and `call_timer_fn()`.

## timers.callback-frees-object: Freeing from the callback

- section: Timer wheel timers
- relevance: 4 - decides whether a callback that frees its own object is a bug

May a timer-wheel callback free the object that holds its timer? What does `call_timer_fn()` read
from the timer after the callback returns?

## timers.pending-check: timer_pending checks

- section: Timer wheel timers
- relevance: 4 - reads as synchronisation and is not

What are the requirements for code that acts on the return value of `timer_pending()` in order to
assure safe usage? What does the return value guarantee about a callback that is running, and
which lock, if any, keeps the result true after the call returns?

## timers.sync-delete-usage: Waiting for a running callback

- section: Timer wheel timers
- relevance: 5 - the deadlocks are invisible in a diff

What are the requirements for calling `timer_delete_sync()` and `timer_shutdown_sync()` in order
to assure safe usage? Which violations of those requirements does the kernel detect, and with
what? Start from `__timer_delete_sync()`.

## timers.free-after-delete: Freeing the embedding object

- section: Timer wheel timers
- relevance: 5 - the most common timer bug

What are the requirements for a `struct timer_list` embedded in an object, before that object is
freed, in order to assure safe usage? Which deletion function meets them for a callback that
re-arms its own timer, for a re-arm that comes from some other path, and for a timer and a work
item that each start the other?

# hrtimers

## timers.hrtimer-api-names: hrtimer function names

- section: hrtimers
- relevance: 5 - the initialisation interface was replaced

Which functions in `include/linux/hrtimer.h` set up an hrtimer that is embedded, one that is on
the stack, and a sleeper? Does this tree still define hrtimer_init, hrtimer_init_on_stack or
hrtimer_init_sleeper? Start from `include/linux/hrtimer.h`.

## timers.hrtimer-callback-change: hrtimer callback changes

- section: hrtimers
- relevance: 5 - a direct write to the callback pointer is what older code did

May code assign the callback pointer of `struct hrtimer` directly? Which function changes the
callback of an hrtimer after setup, and what are the requirements for calling it in order to
assure safe usage?

## timers.hrtimer-state: Queued and running state

- section: hrtimers
- relevance: 4 - readers test a state field that is gone, and treat the answer as a guarantee

How does code ask whether an hrtimer is queued and whether its callback is running, and what do
those queries read? What do `hrtimer_active()` and `hrtimer_is_queued()` guarantee after they
return to a caller that holds no lock? Start from `include/linux/hrtimer_types.h` and
`hrtimer_active()`.

## timers.hrtimer-modes: hrtimer modes

- section: hrtimers
- relevance: 4 - the mode decides the callback context, and a mismatch warns

Which bits of `enum hrtimer_mode` take effect when the timer is set up and which when it is
started, and what is checked when the two disagree? What happens on PREEMPT_RT to a timer marked
neither hard nor soft? Start from `__hrtimer_setup()` and `hrtimer_start_range_ns_common()`.

## timers.hrtimer-user-start: User-controlled expiry times

- section: hrtimers
- relevance: 4 - new interface with a return value the caller must handle

Does this tree have a separate way to start an hrtimer whose expiry time comes from user space,
and if so what does it do differently from `hrtimer_start_range_ns()`, what does it return, and
what must the caller do with that? If there is none, say so and stop.

## timers.hrtimer-callback: hrtimer callback contract

- section: hrtimers
- relevance: 4 - re-arming wrongly either loses the timer or loops

In what context and with which locks held does an hrtimer callback run, what may it return and
what does the core do for each value, and what happens when the callback starts its own timer
and then also asks to be restarted? Start from `__run_hrtimer()`.

## timers.hrtimer-cancel: Cancelling an hrtimer

- section: hrtimers
- relevance: 5 - same use-after-free and deadlock classes as the timer wheel

What do `hrtimer_cancel()` and `hrtimer_try_to_cancel()` each guarantee and return? What are the
requirements for calling `hrtimer_cancel()` in order to assure safe usage? Does this tree have an
hrtimer operation that also prevents re-arming?

# Sleeping and delays

## timers.sleep-helpers: Sleep and delay helpers

- section: Sleeping and delays
- relevance: 4 - picking the wrong one busy-waits or oversleeps

According to `Documentation/timers/delay_sleep_functions.rst` and the body of `fsleep()`, which of
`udelay()`, `usleep_range()`, `msleep()`, `fsleep()` and `schedule_timeout()` is used when? How
far from the requested time can each return, early as well as late? Which file implements the
sleeping ones? Start from `Documentation/timers/delay_sleep_functions.rst`.

# Reading clocks

## timers.clock-accessors: ktime_get family

- section: Reading clocks
- relevance: 4 - the wrong accessor deadlocks in NMI or jumps across suspend

For each accessor in the `ktime_get` family, which clock does it read, and may it be called from
NMI and tracing context? Answer as a table. Start from `include/linux/timekeeping.h` and
`Documentation/core-api/timekeeping.rst`.

## timers.clocks-stop-or-jump: Clocks that stop or jump

- section: Reading clocks
- relevance: 4 - a timeout measured on the wrong clock is wrong after suspend or after the wall clock is set

Which of the clocks that the `ktime_get` family reads stop across suspend, and which jump when the
wall clock is set? Start from `Documentation/core-api/timekeeping.rst`.

# Model gaps

## timers.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.
