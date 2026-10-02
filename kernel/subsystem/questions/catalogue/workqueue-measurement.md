# Questions: Workqueues (measurement set)

- guide: workqueue.md
- title: Workqueues

A wide set of questions about workqueues (`kernel/workqueue.c` and
`include/linux/workqueue.h`), used to measure what a model already knows before
deciding what the built guide should spend its words on. The hand-written guide
it will replace is a single bullet of 20 words about `flush_work()` and
shutdown, so its one topic, a work item's lifetime against teardown, is the
centre of this set and the rest is the map around it. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## wq.core-files: Core files

- section: Finding your way
- relevance: 3 - turns a search into a lookup
- words: 80

Which files hold the workqueue implementation, its public header, the header
that defines the work item type, the header private to the implementation and
the scheduler, the documentation, the tracepoints, the debugging scripts, the
test module and the Rust binding? A table. Start from `kernel/workqueue.c`.

## wq.structures: Core structures

- section: Finding your way
- relevance: 3 - every comment in the file is phrased in these
- words: 100

What does each of `struct work_struct`, `struct delayed_work`,
`struct rcu_work`, `struct workqueue_struct`, `struct pool_workqueue`,
`struct worker_pool` and `struct worker` represent, and how is each linked to
the others? Which pools exist for each CPU and which are shared?

## wq.work-data: Work item data word

- section: Finding your way
- relevance: 4 - cancelling and disabling are encoded here
- words: 90

What does the `data` word of a `struct work_struct` hold while the item is
queued, and what does it hold while the item is off queue? List the fields
packed into it in each state and their widths. Start from `enum work_bits`.

## wq.pending-bit: Ownership of the pending bit

- section: Finding your way
- relevance: 4 - every queue, cancel and flush is a transfer of this bit
- words: 90

What does owning `WORK_STRUCT_PENDING_BIT` of a work item entitle the owner to
do, which functions set it, and at what point relative to the call of the work
function is it cleared? Start from `queue_work_on()`, `process_one_work()` and
`try_to_grab_pending()`.

## wq.locks: Locks

- section: Finding your way
- relevance: 3 - the field annotations refer to them by letter
- words: 90

Which locks does `kernel/workqueue.c` use, what does each protect, and in what
order do they nest? Where in the file is the key to the one and two letter
annotations on structure fields?

# Queueing and execution

## wq.queue-return: Queueing return value

- section: Queueing
- relevance: 4 - a caller that takes a reference per queueing depends on it
- words: 80

What does `queue_work()` return, and in which situations does it return without
the item having been put on a queue? What happens to an item queued on a
workqueue that is being drained or destroyed, and what does the caller see?
Start from `queue_work_on()` and `__queue_work()`.

## wq.requeue-while-running: Queueing a running item

- section: Queueing
- relevance: 4 - decides whether an event can be lost
- words: 70

Can a work item be queued again while its function is still running, and if so
can the two executions overlap? What does the workqueue code guarantee about an
event recorded just before a `queue_work()` call that returned false?

## wq.non-reentrancy: Non-reentrancy conditions

- section: Queueing
- relevance: 3 - the guarantee has conditions people forget
- words: 70

Under which conditions is a work item guaranteed to be executed by at most one
worker at a time across the system, and what actions by the user void that
guarantee? How does `__queue_work()` enforce it when the item was last on a
different pool?

## wq.self-requeue: Self-requeueing work

- section: Queueing
- relevance: 5 - a poller that requeues itself is the usual thing left running at teardown
- words: 90

For a work item whose function queues the item again, which of `flush_work()`,
`cancel_work()`, `cancel_work_sync()` and the disable functions stop it for
good, and which leave it able to run again? What usage is unsafe when tearing
down such an item, and what that looks similar is correct?

## wq.context: Execution context

- section: Queueing
- relevance: 3 - what a work function may and may not do
- words: 70

In what context does a work function run for a normal workqueue, which locks or
states must it not leave held when it returns, and how does the workqueue code
detect a function that returns with one leaked? Start from
`process_one_work()`.

# System workqueues and flags

## wq.system-wqs: System workqueues

- section: Choosing a workqueue
- relevance: 5 - the names have changed and the old ones warn
- words: 120

List the system-wide workqueues this tree creates, with the flags each is
created with, each flag's name written in full. Are any of them marked as
deprecated, and if so what happens when an item is queued on one? Which
workqueue do `schedule_work()` and `schedule_delayed_work()` use? A table. Start
from `workqueue_init_early()`.

## wq.flag-table: Workqueue flags

- section: Choosing a workqueue
- relevance: 5 - each flag changes where and when work runs
- words: 130

Give a table of the flags `alloc_workqueue()` accepts and of the internal flags
next to them, saying what each does. Start from `enum wq_flags` in
`include/linux/workqueue.h` and `Documentation/core-api/workqueue.rst`.

## wq.bound-or-unbound: Per-CPU or unbound

- section: Choosing a workqueue
- relevance: 5 - the default is changing and a caller that says nothing gets a warning
- words: 70

How does a caller of `alloc_workqueue()` say whether the workqueue is per-CPU
or unbound, and what does `alloc_workqueue()` do when the flags say neither, or
both? Start from `__alloc_workqueue()`.

## wq.max-active: Concurrency limit

- section: Choosing a workqueue
- relevance: 4 - the numbers and the scope are quoted from memory
- words: 90

What are the maximum and the default for `max_active`, and is the limit applied
per CPU or across the system for a per-CPU workqueue and for an unbound one?
What is `min_active`? Does `Documentation/core-api/workqueue.rst` agree with
the comment on `alloc_workqueue()`?

## wq.mem-reclaim: Memory reclaim workqueues

- section: Choosing a workqueue
- relevance: 5 - a missing flag is a deadlock under memory pressure
- words: 100

What does `WQ_MEM_RECLAIM` give a workqueue, when must a workqueue have it, and
which combinations of flushing or waiting between workqueues with and without
it does `check_flush_dependency()` warn about? Which callers, if any, are
exempt from that check?

## wq.freezable: Freezable workqueues

- section: Choosing a workqueue
- relevance: 4 - waiting on a frozen workqueue hangs suspend
- words: 80

How is a `WQ_FREEZABLE` workqueue frozen and thawed, what happens to an item
queued while it is frozen, and what usage of `flush_work()` or
`cancel_work_sync()` on such an item during suspend is unsafe? Start from
`freeze_workqueues_begin()` and `wq_adjust_max_active()`.

## wq.bh: BH workqueues

- section: Choosing a workqueue
- relevance: 4 - a newer kind with its own context rules
- words: 100

What is a `WQ_BH` workqueue: in what context do its items run, which other
flags and which `max_active` may it be created with, and from which contexts
may `cancel_work_sync()` and `disable_work_sync()` be called on an item last
queued on one? If this tree has no BH workqueues, say so and stop.

## wq.ordered: Ordered workqueues

- section: Choosing a workqueue
- relevance: 5 - a workqueue that merely has max_active of one is not ordered
- words: 90

How does a caller get a workqueue that runs one item at a time in queueing
order, and is an unbound workqueue created with `max_active` of 1 such a
workqueue? If it is not, give the reason from the loop in
`apply_wqattrs_prepare()` that fills `pwq_tbl`, not from a comment: for what is
one `struct pool_workqueue` allocated, and what do several of them share? Which
later changes to an ordered workqueue, if any, does the code refuse? Start from
`alloc_ordered_workqueue()`.

## wq.legacy-create: Legacy creation macros

- section: Choosing a workqueue
- relevance: 3 - still common in drivers
- words: 60

What do `create_workqueue()`, `create_singlethread_workqueue()` and
`create_freezable_workqueue()` expand to in this tree, and what does the
internal flag they all pass change?

## wq.affinity-scopes: Affinity scopes

- section: Choosing a workqueue
- relevance: 2 - matters for performance, not for correctness
- words: 70

Which affinity scopes can an unbound workqueue use, which is the default, and
how is the default changed at boot or at run time? Start from
`enum wq_affn_scope`.

# Waiting and cancelling

## wq.flush-work: Flushing one item

- section: Flush, cancel, disable
- relevance: 5 - the guarantee is narrower than people assume
- words: 100

What exactly does `flush_work()` guarantee when it returns, what does its
return value mean, and what does it not guarantee if the item can be queued
again by someone else? What does it do for an item that is idle, or one that
was never initialised? Start from `__flush_work()` and `start_flush_work()`.

## wq.flush-workqueue: Flushing a workqueue

- section: Flush, cancel, disable
- relevance: 4 - which items it waits for, and the system-wide case
- words: 90

Which work items does `flush_workqueue()` wait for, and which does it not? How
does it differ from `drain_workqueue()`, and what happens at compile time and
at run time when it is called on one of the system-wide workqueues?

## wq.cancel-async: Cancelling without waiting

- section: Flush, cancel, disable
- relevance: 5 - returning true does not mean the function is not running
- words: 80

What do `cancel_work()` and `cancel_delayed_work()` guarantee when they return
true and when they return false, what do they not guarantee about a function
that is already running, and from which contexts may they be called?

## wq.cancel-sync: Cancelling and waiting

- section: Flush, cancel, disable
- relevance: 5 - the mechanism has been rewritten and the guarantee has conditions
- words: 120

What does `cancel_work_sync()` guarantee on return and under what condition,
what does its return value mean, and how does it keep the item from being
queued again while it waits? Describe the mechanism this tree uses, step by
step. Can the item be queued again after it returns? Start from
`__cancel_work_sync()`.

## wq.disable: Disabling a work item

- section: Flush, cancel, disable
- relevance: 5 - the only interface that stops later queueing
- words: 120

What do `disable_work()`, `disable_work_sync()`, `enable_work()` and their
delayed forms do, where is the state kept and how deep can it nest, what do
the return values mean, and what does `queue_work()` do on a disabled item? If
this tree has no such functions, say so and stop.

## wq.wait-from-callback: Waiting from inside work

- section: Flush, cancel, disable
- relevance: 5 - the classic workqueue deadlocks
- words: 110

What usage of `flush_work()`, `cancel_work_sync()`, `flush_workqueue()` or
`destroy_workqueue()` from inside a work function, or while holding a lock the
work function takes, is unsafe, and what that looks similar is correct? Which
of these cases does lockdep catch, and through which annotations? Start from
`touch_work_lockdep_map()` and `touch_wq_lockdep_map()`.

# Delayed work

## wq.delayed-work: Delayed work and its timer

- section: Delayed and RCU work
- relevance: 4 - the item is invisible to the workqueue until the timer fires
- words: 100

What does `struct delayed_work` add to a work item, which function and flags is
its timer set up with, what does a delay of zero do, and on which CPU does the
timer run? While the timer is pending, is the item pending, and is it on any
list the workqueue can see?

## wq.mod-delayed: Modifying a delayed item

- section: Delayed and RCU work
- relevance: 3 - the return value is the reverse of what people guess
- words: 70

What does `mod_delayed_work()` do to an idle item, to one whose timer is
pending, and to one already on a worklist, what does its return value mean, and
what does it do to a disabled item? From which contexts may it be called?

## wq.delayed-cancel-usage: Cancelling delayed work

- section: Delayed and RCU work
- relevance: 5 - the wrong call spins on the timer or does not see it
- words: 90

What usage of `cancel_work_sync()`, `flush_work()` or `disable_work_sync()` on
the `work` member of a `struct delayed_work` is unsafe, and what is the correct
call for each? What does `flush_delayed_work()` do with a timer that has not
yet expired?

## wq.rcu-work: RCU work

- section: Delayed and RCU work
- relevance: 3 - it cannot be cancelled
- words: 60

What is `struct rcu_work`, what does the return value of `queue_rcu_work()`
say about the grace period, can such an item be cancelled or disabled, and how
does teardown code wait for one?

# Lifetime and teardown

## wq.free-embedding: Freeing the containing structure

- section: Lifetime against teardown
- relevance: 5 - the use-after-free this guide exists for
- words: 120

What usage that frees a structure which embeds a `struct work_struct` or
`struct delayed_work` is unsafe, and what that looks similar is correct? Cover
freeing from a release or remove path, freeing from inside the work function
itself, and whether the workqueue code touches the item after the function
returns. Name in-tree code that shows the correct forms, and before citing a
release function as correct check that the work function itself cannot drop the
last reference and so call it: a function that waits for its own work item is
not an example of the correct form. Start from the comment at the top of
`process_one_work()`.

## wq.teardown-order: Teardown sequence

- section: Lifetime against teardown
- relevance: 5 - cancelling before the sources are stopped cancels nothing
- words: 110

In a remove, close or unload path, in what order must code stop the things that
queue a work item (interrupt handlers, timers, other work items, notifiers) and
cancel or disable the item itself? What usage is unsafe, and what that looks
similar is correct? When is `cancel_work_sync()` enough and when is
`disable_work_sync()` needed?

## wq.destroy: Destroying a workqueue

- section: Lifetime against teardown
- relevance: 5 - what it waits for and what it does not
- words: 120

List in order what `destroy_workqueue()` does. Which items does it wait for,
what happens to a delayed item whose timer has not fired, what happens to an
item queued from outside the workqueue after it has started, and what does it
do when it finds the workqueue still busy at the end?

## wq.devm: Managed workqueues

- section: Lifetime against teardown
- relevance: 3 - release order decides whether the queue outlives its users
- words: 60

Does this tree have a device-managed way to allocate a workqueue, what does it
run on release, and what usage is unsafe when work items queued on it live in
memory released by other managed actions?

## wq.onstack: Work items on the stack

- section: Lifetime against teardown
- relevance: 3 - the debug-objects pairing is easy to miss
- words: 60

How must a work item that lives on the stack be initialised and torn down,
which calls pair with which, and what must have happened before the function
that owns the stack frame returns?

## wq.reinit: Initialising a live item

- section: Lifetime against teardown
- relevance: 4 - corrupts the worklist silently
- words: 60

What usage of `INIT_WORK()` or `INIT_DELAYED_WORK()` on an item that may be
pending or running is unsafe, and what that looks similar is correct? What
catches it in a debug build?

## wq.module-unload: Module unload

- section: Lifetime against teardown
- relevance: 4 - the work function's text goes away with the module
- words: 70

What must a module that queues work on a system-wide workqueue do before its
exit function returns, and is cancelling without waiting enough? May it flush
the whole system-wide workqueue instead, and what does the tree say about
doing that?

# Changing the implementation

## wq.hotplug: CPU hotplug

- section: What a change must preserve
- relevance: 3 - per-CPU work does not stay on its CPU
- words: 80

What happens to work queued on a per-CPU workqueue when its CPU goes offline,
what must a caller of `queue_work_on()` or `queue_delayed_work_on()` ensure
about the CPU it names, and what happens to BH work left on a dead CPU?

## wq.debug-facilities: Debugging facilities

- section: What a change must preserve
- relevance: 3 - says which mistakes a test run would have caught
- words: 90

Which debugging facilities cover workqueues (debug objects, lockdep, the
watchdog, the CPU-intensive report, tracepoints, the scripts under
`tools/workqueue/`), which configuration option enables each, and what class of
mistake does each catch?

## wq.change-checklist: Changing the implementation

- section: What a change must preserve
- relevance: 3 - the invariants are spread through comments
- words: 100

What must a change to `kernel/workqueue.c` preserve: who may update a work
item's data word and under which lock, what must be the last access to an item
before its function runs, how pools and pool workqueues are freed, and which
code outside the file reads its structures (scheduler hooks, scripts, the Rust
binding)?
