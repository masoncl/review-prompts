# Questions: Workqueues

- guide: workqueue.md
- title: Workqueues

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/workqueue-measurement.md` is the
wider set the readers were measured on and `catalogue/workqueue-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## wq.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Choosing a workqueue

## wq.system-wqs: System workqueues

- section: Choosing a workqueue
- relevance: 5 - the names have changed and the old ones warn

A table of the system-wide workqueues to choose between, with their current names: what each is
for, and whether it is per-CPU or unbound. Then what the table cannot show: which of them are
deprecated and what happens when an item is queued on one, and which workqueue
`schedule_work()` and `schedule_delayed_work()` use. Start from `workqueue_init_early()`.

## wq.bound-or-unbound: Per-CPU or unbound

- section: Choosing a workqueue
- relevance: 5 - the default is changing and a caller that says nothing gets a warning

How does a caller of `alloc_workqueue()` say whether the workqueue is per-CPU or unbound, and
what does `alloc_workqueue()` do when the flags say neither, or both? Start from
`__alloc_workqueue()`.

## wq.flag-table: Workqueue flags

- section: Choosing a workqueue
- relevance: 5 - each flag changes where and when work runs

A table of the flags a caller of `alloc_workqueue()` chooses among: what each changes about where
and when items run. Then which combinations `__alloc_workqueue()` refuses or changes. Start from
`enum wq_flags` in `include/linux/workqueue.h` and `Documentation/core-api/workqueue.rst`.

## wq.max-active: max_active limits

- section: Choosing a workqueue
- relevance: 4 - the numbers and the scope are quoted from memory

What are the maximum and the default for `max_active`, and is the limit applied per CPU or across
the system, for a per-CPU workqueue and for an unbound one? What is `min_active` of a `struct
workqueue_struct` for?

## wq.ordered: Ordered workqueues

- section: Choosing a workqueue
- relevance: 5 - a workqueue that merely has max_active of one is not ordered

How does a caller get a workqueue that runs one item at a time in queueing order, and does an
unbound workqueue created with `max_active` of 1 give the same guarantee? Which later changes to
an ordered workqueue does the code refuse, and which does it let through? Start from
`alloc_ordered_workqueue()` and `apply_wqattrs_prepare()`.

## wq.mem-reclaim: Memory reclaim workqueues

- section: Choosing a workqueue
- relevance: 5 - a missing flag is a deadlock under memory pressure

What does `WQ_MEM_RECLAIM` give a workqueue, when must a workqueue have it, and which
combinations of flushing or waiting between workqueues with and without it does
`check_flush_dependency()` warn about? What, if anything, is exempt from that check?

## wq.freezable: Freezable workqueues

- section: Choosing a workqueue
- relevance: 4 - waiting on a frozen workqueue hangs suspend

What happens to an item queued on a `WQ_FREEZABLE` workqueue while it is frozen? What are the
requirements for a call of `flush_work()` or `cancel_work_sync()` on such an item during suspend
or resume in order to assure safe usage? Start from `freeze_workqueues_begin()` and
`wq_adjust_max_active()`.

## wq.bh: BH workqueues

- section: Choosing a workqueue
- relevance: 4 - a newer kind with its own context rules

What is a `WQ_BH` workqueue: in what context do its items run, which other flags and which
`max_active` may it be created with, and from which contexts may `cancel_work_sync()` and
`disable_work_sync()` be called on an item last queued on one? If this tree has no BH
workqueues, say so and stop.

# Queueing

## wq.pending-bit: Ownership of the pending bit

- section: Queueing
- relevance: 4 - every queue, cancel and flush is a transfer of this bit

What does owning `WORK_STRUCT_PENDING_BIT` of a work item entitle the owner to do, and at what
point relative to the call of the work function is it cleared? What else does the item's data
word tell cancelling, disabling and flushing code, while the item is queued and while it is off
queue? Start from `queue_work_on()`, `process_one_work()` and `try_to_grab_pending()`.

## wq.queue-return: Queueing return value

- section: Queueing
- relevance: 4 - a caller that takes a reference per queueing depends on it

What does `queue_work()` return, and in which situations does it return without the item having
been put on a queue? What happens to an item queued on a workqueue that is being drained or
destroyed, and what does the caller see? Start from `queue_work_on()` and `__queue_work()`.

## wq.requeue-while-running: Queueing a running item

- section: Queueing
- relevance: 4 - decides whether an event can be lost

Can a work item be queued again while its function is still running, and if so can the two
executions overlap? When `queue_work()` returns false, what does the workqueue code guarantee
about the next start of the work function relative to that call?

## wq.delayed-work: Delayed work and its timer

- section: Queueing
- relevance: 4 - the item is invisible to the workqueue until the timer fires

While the timer of a `struct delayed_work` is pending, is `WORK_STRUCT_PENDING_BIT` set, and do
`flush_workqueue()` and `destroy_workqueue()` wait for the item? What does `queue_delayed_work()`
do with a delay of zero?

## wq.delayed-timer-context: Delayed work timer context

- section: Queueing
- relevance: 4 - the timer function queues the item, so its context and CPU decide where the item runs

In what context and on which CPU does the timer function of a `struct delayed_work` run?

# Flush, cancel, disable

## wq.flush-work: Flushing one item

- section: Flush, cancel, disable
- relevance: 5 - the guarantee is narrower than people assume

What does `flush_work()` guarantee when it returns, given that other code may queue the item
again? What does it do for an item that is idle, and for one that was never initialised? Start
from `__flush_work()` and `start_flush_work()`.

## wq.flush-workqueue: Flushing a workqueue

- section: Flush, cancel, disable
- relevance: 4 - which items it waits for, and the system-wide case

Which work items does `flush_workqueue()` wait for, and which does it not? How does it differ
from `drain_workqueue()`, and what happens at compile time and at run time when it is called on
one of the system-wide workqueues?

## wq.cancel-async: Cancelling without waiting

- section: Flush, cancel, disable
- relevance: 5 - returning true does not mean the function is not running

What do `cancel_work()` and `cancel_delayed_work()` guarantee when they return true and when
they return false, what do they not guarantee about a function that is already running, and
from which contexts may they be called?

## wq.cancel-sync: Cancelling and waiting

- section: Flush, cancel, disable
- relevance: 5 - the mechanism has been rewritten and the guarantee has conditions

What does `cancel_work_sync()` guarantee on return and under what condition, and what does its
return value mean? What keeps the item from being queued again while it waits, and does that
still hold after it returns? Start from `__cancel_work_sync()`.

## wq.disable: Disabling a work item

- section: Flush, cancel, disable
- relevance: 5 - the only interface that stops later queueing

What do `disable_work()` and `enable_work()` guarantee to their caller, and how deep does
disabling nest? What does `queue_work()` do on a disabled item? If this tree has no
`disable_work()`, say so and stop.

## wq.disable-delayed: Disabling delayed work

- section: Flush, cancel, disable
- relevance: 5 - a timer left pending queues the item after the caller believes it is stopped

What do `disable_delayed_work()` and `enable_delayed_work()` do about the timer of a `struct
delayed_work`? If this tree has no `disable_delayed_work()`, say so and stop.

## wq.self-requeue: Self-requeueing work

- section: Flush, cancel, disable
- relevance: 5 - a poller that requeues itself is the usual thing left running at teardown

For a work item whose function queues the item again, which of `flush_work()`, `cancel_work()`,
`cancel_work_sync()`, `disable_work()` and `disable_work_sync()` guarantee that the function does
not run after they return? What are the requirements for code that tears down such an item in
order to assure safe usage?

## wq.delayed-cancel-usage: Cancelling delayed work

- section: Flush, cancel, disable
- relevance: 5 - the wrong call spins on the timer or does not see it

What are the requirements for a call of `cancel_work_sync()`, `flush_work()` or
`disable_work_sync()` on the `work` member of a `struct delayed_work` in order to assure safe
usage, and which function must a caller use for a delayed item in place of each? What does
`flush_delayed_work()` do with a timer that has not yet expired?

## wq.wait-from-callback: Waiting from inside work

- section: Flush, cancel, disable
- relevance: 5 - the classic workqueue deadlocks

What are the requirements for a call of `flush_work()`, `cancel_work_sync()`, `flush_workqueue()`
or `destroy_workqueue()` from inside a work function, or while holding a lock the work function
takes, in order to assure safe usage? Which violations does lockdep catch, and through which
annotations? Start from `touch_work_lockdep_map()` and `touch_wq_lockdep_map()`.

# Lifetime against teardown

## wq.free-embedding: Freeing the containing structure

- section: Lifetime against teardown
- relevance: 5 - the use-after-free this guide exists for

What are the requirements for code that frees a structure which embeds a `struct work_struct` or
`struct delayed_work` in order to assure safe usage, from a release or remove path and from inside
the work function itself? Does `process_one_work()` touch the item after the work function
returns? Name in-tree code that shows each. Start from the comment at the top of
`process_one_work()`.

## wq.teardown-order: Teardown sequence

- section: Lifetime against teardown
- relevance: 5 - cancelling before the sources are stopped cancels nothing

In a remove, close or unload path, in what order must code stop the sources that queue a work item
and cancel or disable the item itself? When is `cancel_work_sync()` enough, and when is
`disable_work_sync()` needed?

## wq.destroy: Destroying a workqueue

- section: Lifetime against teardown
- relevance: 5 - what it waits for and what it does not

Which items does `destroy_workqueue()` wait for, and what happens to a delayed item whose timer
has not fired and to an item queued from outside the workqueue after the destroy has started?
What does it do when it finds the workqueue still busy at the end?

## wq.module-unload: Module unload

- section: Lifetime against teardown
- relevance: 4 - the work function's text goes away with the module

What must a module that queues work on a system-wide workqueue do before its exit function
returns, and is cancelling without waiting enough? May it flush the whole system-wide workqueue
instead, and what does the tree say about doing that?

## wq.reinit: Initialising a live item

- section: Lifetime against teardown
- relevance: 4 - corrupts the worklist silently

What are the requirements for a call of `INIT_WORK()` or `INIT_DELAYED_WORK()` on an item that may
be pending or running, in order to assure safe usage? What catches a violation in a debug build?

# Model gaps

## wq.model-gaps: Other mistakes models make

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
