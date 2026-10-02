# Questions: Locking and Synchronization

- guide: locking.md
- title: Locking and Synchronization

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/locking-measurement.md` is the
wider set the readers were measured on and `catalogue/locking-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## locking.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## locking.core-files: Core files

- section: Finding your way
- relevance: 4 - the API is spread over many headers and the RT substitutions live apart

A table and nothing else, job to file: the spinlock and rwlock API layers; the queued spinlock;
the mutex; the rw_semaphore; the rtmutex and the PREEMPT_RT substitutions built on it; the per-CPU
rw_semaphore; sequence counters; local locks; wound/wait mutexes; lockdep; the scope-based guard
macros; the compiler lock annotations. Where a job has no file of its own in this tree, name the
file that holds it and say so in the row. Start from `kernel/locking/` and `include/linux/`.

## locking.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - several rules are only written down there

A table and nothing else, subject to the document in the tree that is the authority on it: lock
types and their nesting; lockdep; sequence counters; memory barriers and atomic operations; the
memory model and access marking; the compiler-based lock annotations. Start from
`Documentation/locking/`.

# Contexts and what excludes what

## locking.context-table: bh, irq and irqsave variants

- section: Contexts and what excludes what
- relevance: 5 - the wrong variant deadlocks or races and nothing in the diff shows it

A table of the acquisition variants to choose between (the plain, bh, irq and irqsave forms
of `raw_spinlock_t`, `spinlock_t` and `local_lock_t`, and the sleeping locks
`struct mutex` and `struct rw_semaphore`): what holding each excludes (other tasks, softirqs on
this CPU, hard interrupts on this CPU) and whether acquiring it can sleep, on a normal kernel
and on PREEMPT_RT.

## locking.preempt-migrate-irq: Preemption, migration and interrupt disabling

- section: Contexts and what excludes what
- relevance: 5 - each gives a different subset of what per-CPU code needs

A table of `preempt_disable()`, `migrate_disable()`, `local_bh_disable()` and
`local_irq_disable()`, to choose between: what each guarantees and does not (staying on the
CPU, exclusion against other tasks on it, against softirqs, against interrupts, being an RCU
reader, permission to sleep), on a normal kernel and on PREEMPT_RT.

## locking.rcu-readers: RCU readers implied by locks

- section: Contexts and what excludes what
- relevance: 5 - whether a spinlock or disabled preemption protects an RCU pointer differs on PREEMPT_RT, and models get it backwards

Does holding a `spinlock_t` or a `raw_spinlock_t`, or having preemption, bottom halves or
interrupts disabled, keep an RCU-protected object from being freed, on a normal kernel and on
PREEMPT_RT? Which dereference primitive accepts each of these as protection without a lockdep
complaint?

## locking.context-predicates: Context predicates

- section: Contexts and what excludes what
- relevance: 4 - the wrong predicate guards a sleeping lock with a test that misses cases

What does each of `in_interrupt()`, `in_softirq()`, `in_atomic()`, `irqs_disabled()` and
`preemptible()` guarantee when it returns true and when it returns false, and how does the
configuration change that? Start from `include/linux/preempt.h`.

## locking.context-guard-usage: Trylocks from any context

- section: Contexts and what excludes what
- relevance: 4 - a guard that misses preempt-disabled callers sleeps in atomic context on RT

What are the requirements for taking a `spinlock_t` or a `local_lock_t` in code that can be
reached from any context in order to assure safe usage? From which contexts may the trylock
variants of each be called? Name in-tree code that decides at run time whether it may take the
lock.

## locking.irq-shared-lock: Locks shared with interrupt handlers

- section: Contexts and what excludes what
- relevance: 5 - same-CPU deadlock that only lockdep or luck finds

What are the requirements for acquiring a `spinlock_t` that is taken both in process context and
in a hard or soft interrupt handler in order to assure safe usage? In which of those acquisitions
may plain `spin_lock()` be used? Name in-tree code or documentation that shows both. Start from
`Documentation/locking/spinlocks.rst` and `Documentation/kernel-hacking/locking.rst`.

## locking.nested-irq-masking: Nesting under irq-disabling locks

- section: Contexts and what excludes what
- relevance: 3 - unlock order decides whether interrupts come back on too early

When a second spinlock is taken inside a region entered with `spin_lock_irq()` or
`spin_lock_irqsave()`, what interrupt state does the inner region inherit? What are the
requirements for the unlock variant used for each of the two locks, when the outer lock is
released first, in order to assure safe usage?

## locking.cpu-hotplug-lock: CPU hotplug exclusion

- section: Contexts and what excludes what
- relevance: 4 - pinning a task and keeping a CPU online are different things

What kind of lock is behind `cpus_read_lock()`, may it be taken in atomic context, and which of
`preempt_disable()`, `migrate_disable()`, `local_irq_disable()` and `cpus_read_lock()` keep the
current CPU, and which keep other CPUs, from going offline? Start from `kernel/cpu.c` and
`Documentation/core-api/cpu_hotplug.rst`.

# Kinds of lock and nesting

## locking.lock-categories: Lock categories

- section: Kinds of lock and nesting
- relevance: 5 - every nesting and context rule is phrased in these

Into which categories does the kernel documentation sort its lock types, which primitive
belongs to which category on a normal kernel, and which change category on PREEMPT_RT? Start
from `Documentation/locking/locktypes.rst`.

## locking.raw-spinlock-use: Raw spinlocks

- section: Kinds of lock and nesting
- relevance: 4 - decides what may run inside the section on RT

When is `raw_spinlock_t` the required type rather than `spinlock_t`, what may code holding one
not do, and what does the documentation say, and not say, about how long such sections may be?

## locking.nesting-table: Nesting by lock type

- section: Kinds of lock and nesting
- relevance: 5 - the table reviewers need when a patch adds a lock inside another

A table: while holding each of `raw_spinlock_t`, `spinlock_t`, `local_lock_t`, `struct mutex`
and an RCU read-side section, which lock types may be acquired and which may not. Say which
document states the rule.

## locking.lockdep-wait-types: Lockdep wait types

- section: Kinds of lock and nesting
- relevance: 5 - this is how raw-versus-sleeping nesting is checked on every kernel

A table of the lock types, RCU included, against the inner and outer wait type each carries, in
the values of `enum lockdep_wait_type`. Then what wait type each execution context imposes,
and which acquisitions `check_wait_context()` skips.

## locking.raw-nesting-config: Raw lock nesting checks

- section: Kinds of lock and nesting
- relevance: 4 - decides whether a non-RT test run reports the nesting

What does `CONFIG_PROVE_RAW_LOCK_NESTING` change in lockdep, what is its default, and does
wrapping an acquisition in a test that the kernel is not PREEMPT_RT keep lockdep from reporting
an invalid wait context?

## locking.wait-override: Wait type override maps

- section: Kinds of lock and nesting
- relevance: 3 - the sanctioned way to silence an intentional nesting

What are the requirements for an acquisition wrapped in a `DEFINE_WAIT_OVERRIDE_MAP()` map in
order to assure safe usage? Which wait types may the map be set to, and what does lockdep then
check and stop checking? Name in-tree users and the wait type each sets.

# PREEMPT_RT and local locks

## locking.rt-substitutions: Substitutions on PREEMPT_RT

- section: PREEMPT_RT and local locks
- relevance: 5 - the same source line is a different lock

A table of what each of `spinlock_t`, `rwlock_t`, `struct mutex`, `struct rw_semaphore`,
`local_lock_t`, `raw_spinlock_t` and `struct semaphore` is on PREEMPT_RT: what it is built on
and whether acquiring it can then sleep.

## locking.rt-spinlock-semantics: spinlock_t on PREEMPT_RT

- section: PREEMPT_RT and local locks
- relevance: 5 - code that relied on side effects of spin_lock breaks silently

On PREEMPT_RT, which of the side effects of taking a `spinlock_t` that code written for other
kernels relies on still hold and which do not: on preemption, on migration, on being an RCU
reader, on the task's sleep state, and on interrupts when the irq or irqsave form is used?
Start from `kernel/locking/spinlock_rt.c`.

## locking.rt-hardirq-context: Hard interrupt context on PREEMPT_RT

- section: PREEMPT_RT and local locks
- relevance: 4 - decides whether a handler may take a spinlock_t at all

On PREEMPT_RT, which interrupt handlers, timers and irq_work items still run in hard interrupt
context and which are moved to threads, and how does lockdep on a non-RT kernel know the
difference? Start from `IRQF_NO_THREAD`, `HRTIMER_MODE_HARD` and `IRQ_WORK_HARD_IRQ`.

## locking.rt-unsafe-usage: Usage that breaks on PREEMPT_RT

- section: PREEMPT_RT and local locks
- relevance: 5 - compiles and runs on every non-RT kernel

What are the requirements for acquiring a `spinlock_t`, `rwlock_t` or `local_lock_t` on PREEMPT_RT
in order to assure safe usage, where they differ from the requirements on a non-RT kernel? Start
from the PREEMPT_RT caveats in `Documentation/locking/locktypes.rst`.

## locking.local-trylock: Local trylocks

- section: PREEMPT_RT and local locks
- relevance: 4 - the only local lock usable from any context

What is a `local_trylock_t` for that a `local_lock_t` cannot do, which operations accept each,
and from which contexts may `local_trylock()` be called? What does it do in hard interrupt or
NMI context on PREEMPT_RT?

## locking.local-lock-nested-bh: Bottom halves and per-CPU data

- section: PREEMPT_RT and local locks
- relevance: 4 - on RT disabling bottom halves may no longer serialize anything

On PREEMPT_RT, does `local_bh_disable()` keep two sections on the same CPU from running at once,
and which configuration option, if any, changes that? What are the requirements for per-CPU data
that is accessed with bottom halves disabled in order to assure safe usage, and what is
`local_lock_nested_bh()` for? Start from `kernel/softirq.c` and `kernel/Kconfig.preempt`.

## locking.local-lock-scope-usage: Converting to local locks

- section: PREEMPT_RT and local locks
- relevance: 4 - two different local locks do not exclude each other on RT

What are the requirements for the `local_lock_t` that replaces `local_irq_save()` or
`preempt_disable()` sections that protect per-CPU data in order to assure safe usage? Start from
the local_lock caveats in `Documentation/locking/locktypes.rst`.

# Sleeping and reader-writer locks

## locking.mutex-rules: Mutex rules

- section: Sleeping and reader-writer locks
- relevance: 4 - the rules are stricter than a semaphore's and are enforced only with debugging on

What are the requirements for `struct mutex` in order to assure safe usage, where they are
stricter than those for `struct semaphore`? What enforces each requirement: which are checked only
with a debugging option on, and by which option? Start from
`Documentation/locking/mutex-design.rst`.

## locking.mutex-unlock-lifetime: Unlocking and object lifetime

- section: Sleeping and reader-writer locks
- relevance: 5 - a use-after-free inside the unlock itself that no reader of the diff sees

What does `mutex_unlock()` require of the lifetime of the object that holds the `struct mutex`,
when unlocking is the last thing a task does with the object and another task may then free it? Do
the unlock functions of `spinlock_t` and `struct rw_semaphore` require the same? Start from the
comment above `mutex_unlock()` in `kernel/locking/mutex.c`.

## locking.rwsem-semantics: Reader-writer semaphores

- section: Sleeping and reader-writer locks
- relevance: 4 - reader recursion deadlocks once a writer queues

What are the requirements for taking and releasing a `struct rw_semaphore` for read in order to
assure safe usage? How are readers that arrive behind a waiting writer treated, and what changes
on PREEMPT_RT?

## locking.rwlock-semantics: Reader-writer spinlocks

- section: Sleeping and reader-writer locks
- relevance: 3 - fairness and reader recursion differ from what people assume

For `rwlock_t`, may a reader take the read lock again while holding it, how are waiting writers
treated by new readers in process context and in interrupt context, and what changes on
PREEMPT_RT? Start from `kernel/locking/qrwlock.c` and the recursive read lock section of
`Documentation/locking/lockdep-design.rst`.

# Lockdep

## locking.lockdep-model: Meaning of a lockdep report

- section: Lockdep
- relevance: 4 - explains what a splat does and does not prove

Which kinds of rule does lockdep check, and what does it treat as one lock when it records an
order between two locks? Does a deadlock have to happen for lockdep to report it? Start from
`Documentation/locking/lockdep-design.rst`.

## locking.lockdep-irq-states: Interrupt safety states

- section: Lockdep
- relevance: 4 - the report names these states and people misread them

How are the interrupt-safety states in a lockdep report to be read: what do in-interrupt and
interrupt-enabled usage of a class mean, what combination of them on two locks is reported as
an inversion, and what else is tracked in the same way besides hard and soft interrupts? Start
from `kernel/locking/lockdep_states.h`.

## locking.lockdep-subclasses: Subclasses and nest locks

- section: Lockdep
- relevance: 4 - same-class nesting is reported as recursion without them

Which of the variants that end in _nested, `mutex_lock_nest_lock()` and `lock_set_cmp_fn()` is
used when two locks of one class are held together? What does each tell lockdep, and what does
lockdep stop checking once it is used?

## locking.lockdep-subclass-limit: Subclass number limit

- section: Lockdep
- relevance: 4 - a subclass taken from a loop index or a depth can pass the limit

What does lockdep do when the subclass passed to `spin_lock_nested()` or `mutex_lock_nested()` is
`MAX_LOCKDEP_SUBCLASSES` or more?

## locking.lockdep-pinning: Lock pinning

- section: Lockdep
- relevance: 3 - a pinned lock released by a callee is a warning, and folded entries make it fire wrongly

What does pinning a lock with `lockdep_pin_lock()` promise the code that pinned it, and what must
be done with what it returns? What are the requirements for pinning a lock whose held-lock entry
is shared by several lock instances through a nest lock in order to assure safe usage? Start from
`match_held_lock()` and `__lock_release()`.

## locking.lockdep-limits: Disabling lockdep checks

- section: Lockdep
- relevance: 3 - after the first report nothing else is checked

What does lockdep still check once it has printed its first report or run out of one of its
tables? What do `lockdep_off()`, `lockdep_set_novalidate_class()` and
`lockdep_set_notrack_class()` each switch off, and what are the requirements for each in order to
assure safe usage?

## locking.reclaim-lockdep: fs_reclaim lockdep map

- section: Lockdep
- relevance: 4 - the deadlock needs memory pressure to happen but lockdep can see it without

How does lockdep learn that a lock is taken in the memory reclaim path and that an allocation
happens under a lock, which allocation flags matter, and what do `memalloc_nofs_save()` and
`memalloc_noio_save()` change? Start from `fs_reclaim_acquire()`.

## locking.lockdep-asserts: Assertion helpers

- section: Lockdep
- relevance: 4 - documents the locking contract where a comment would rot

What does each of `lockdep_assert_held()`, `lockdep_assert_held_write()`,
`lockdep_assert_held_read()`, `lockdep_assert_not_held()`, `lockdep_assert_irqs_disabled()`,
`lockdep_assert_preemption_disabled()`, `rwsem_assert_held()` and `assert_spin_locked()` check in
a build with lockdep, and what in a build without it? Answer as a table. Start from
`include/linux/lockdep.h`.

## locking.lock-order-documentation: Documented lock orders

- section: Lockdep
- relevance: 3 - the order is written down in a few known places

Where does the tree write down lock ordering for the memory management, filesystem, scheduler and
networking cores? What are the requirements for taking two locks of the same type on different
objects together in order to assure safe usage?

# Guards and annotations

## locking.guard-classes: Guard class names

- section: Guards and annotations
- relevance: 4 - the class name is not the function name

By what rule is the guard class for a lock named, and how are the classes for the conditional
forms named? Where are the classes defined? Start from the `DEFINE_LOCK_GUARD_1()` and
`DEFINE_GUARD()` uses under `include/linux/`.

## locking.guards: Scope-based lock guards

- section: Guards and annotations
- relevance: 5 - now the usual way locks are taken in new code

Which of `guard()`, `scoped_guard()`, `scoped_cond_guard()` and `ACQUIRE()` with
`ACQUIRE_ERR()` is used when, and exactly when is the lock released in each case? Start from
`include/linux/cleanup.h`.

## locking.guard-usage: Guard hazards

- section: Guards and annotations
- relevance: 5 - the lock is held to the end of a scope the reader has to find

What are the requirements for a function that takes a lock with `guard()`, `scoped_guard()` or
`scoped_cond_guard()` in order to assure safe usage? Start from the comment at the top of
`include/linux/cleanup.h`.

## locking.context-analysis: Compiler context analysis

- section: Guards and annotations
- relevance: 5 - the annotation keywords changed meaning and checker

Does this tree have a compiler-based context analysis for locks, and which compiler and
configuration option does it need in order to run? How is a file or directory opted in, and what
does the compiler check in a file that is opted in and in one that is not? If this tree has none,
say so. Start from `Documentation/dev-tools/context-analysis.rst`.

## locking.annotation-keywords: Annotation keywords

- section: Guards and annotations
- relevance: 4 - reviewers must know whether a wrong annotation now breaks a build

Which of `__must_hold()`, `__acquires()`, `__releases()`, `__cond_acquires()`, `__guarded_by()`
and `__pt_guarded_by()`, and their shared forms, is used when? Which tools check them in this
tree, and what does each tool do with an annotation that is wrong? Start from
`include/linux/compiler-context-analysis.h`.

# Reference counts and object lifetime

## locking.refcount-types: Reference count types

- section: Reference counts and object lifetime
- relevance: 4 - the types differ in what happens at zero and at overflow

A table of `refcount_t`, `struct kref`, `rcuref_t`, `struct percpu_ref` and `struct lockref`, to
choose between: what each does on an increment from zero and on overflow, and whether it supports
a lookup that may race with the final put.

## locking.dec-and-lock: Decrement and lock helpers

- section: Reference counts and object lifetime
- relevance: 4 - the lock decides whether a lookup can still find the object at the final put

What do `refcount_dec_and_lock()` and `atomic_dec_and_lock()` guarantee to their caller when they
return true, and what when they return false?

## locking.refcount-ordering: Reference count ordering

- section: Reference counts and object lifetime
- relevance: 4 - weaker than the atomic_t calls they replaced

Which memory ordering do `refcount_inc()`, `refcount_inc_not_zero()`, `refcount_dec()` and
`refcount_dec_and_test()` provide, why is the ordering on the final decrement needed, and when
does a lookup need more than the plain increment gives? Start from
`Documentation/core-api/refcount-vs-atomic.rst`.

## locking.object-pins: Keeping an object alive

- section: Reference counts and object lifetime
- relevance: 5 - a pointer used after its lock or RCU section ended is the commonest use-after-free, and most reports of one are wrong

What are the requirements for using a pointer after the lock or the `rcu_read_lock()` section it
was obtained under has ended, in order to assure safe usage? What do `call_rcu()` and
`kfree_rcu()` guarantee to a reader that is still inside its `rcu_read_lock()` section when the
object is released? Name in-tree code that shows each.

## locking.lock-drop-reacquire: Dropping and retaking a lock

- section: Reference counts and object lifetime
- relevance: 5 - everything checked before the drop is stale

What are the requirements for using state that a function examined under a lock, after the
function has dropped the lock and taken it again, in order to assure safe usage? Name two in-tree
functions that drop and retake a lock, and say what each does after retaking it.

## locking.check-then-lock: Checking before locking

- section: Reference counts and object lifetime
- relevance: 4 - a lockless test is either an optimisation or a bug

What are the requirements for a test of shared state that is made without the lock, when the code
then takes the lock to act on the result, in order to assure safe usage? What does
`list_empty_careful()` guarantee to a caller that does not hold the lock? Name in-tree code that
shows each.

## locking.deferred-work-teardown: Cancelling timers and work items

- section: Reference counts and object lifetime
- relevance: 5 - the free races with a callback that nobody is holding a lock for

Before an object used by a timer or a work item is freed, which function stops or waits for each,
and what does that function guarantee when it returns? What are the requirements for calling each
of these functions in order to assure safe usage?

## locking.callback-teardown: RCU callbacks and interrupt handlers

- section: Reference counts and object lifetime
- relevance: 5 - the free races with a callback that nobody is holding a lock for

Before an object used by an RCU callback or an interrupt handler is freed, which function waits
for each, and what does that function guarantee when it returns? What are the requirements for
calling each of these functions in order to assure safe usage?

## locking.percpu-teardown-usage: Per-CPU state and hotplug callbacks

- section: Reference counts and object lifetime
- relevance: 3 - the teardown callback races with anything not pinned

What are the requirements for code that uses per-CPU state set up and torn down by callbacks
registered with `cpuhp_setup_state()` in order to assure safe usage? Which forms of protection
meet them when the user needs to sleep? Start from `cpuhp_setup_state()`.

# Memory ordering

## locking.atomic-ordering: Ordering of atomic operations

- section: Memory ordering
- relevance: 5 - most people remember half of the rule

Into which classes does `Documentation/atomic_t.txt` sort the atomic operations by the ordering
they give, and what ordering does each class give? Start from `Documentation/atomic_t.txt`.

## locking.publish-usage: Publishing initialised data

- section: Memory ordering
- relevance: 5 - works on x86, fails on weakly ordered machines

What are the requirements for the writer that makes a pointer to a newly initialised object
visible to lockless readers, and for a reader that loads the pointer, in order to assure safe
usage? Is a plain `READ_ONCE()` of the pointer enough for the reader? Name the in-tree documents
that say so.

## locking.sleep-wake-ordering: Sleeping and waking

- section: Memory ordering
- relevance: 5 - the lost wakeup

What are the requirements for the order of setting the task state, testing the condition and
calling `schedule()` in an open-coded wait loop in order to assure safe usage? Which barrier in
`set_current_state()` pairs with which in the waker, and when is `__set_current_state()` enough?
Start from the comment above `set_current_state()` in `include/linux/sched.h`.

## locking.marked-accesses: Marked accesses and data races

- section: Memory ordering
- relevance: 4 - reviewers ask for READ_ONCE in the wrong places and miss the right ones

Which of `READ_ONCE()` or `WRITE_ONCE()`, `data_race()` and a plain access is right for a
lockless access when, and where is asking for a marking wrong? What do KCSAN's
`ASSERT_EXCLUSIVE_WRITER()` and `ASSERT_EXCLUSIVE_ACCESS()` let code state instead? Start from
`tools/memory-model/Documentation/access-marking.txt`.

# Sequence counters

## locking.seqcount-types: Sequence counter types

- section: Sequence counters
- relevance: 4 - the type chosen decides who serialises writers and what RT does

Which of `seqcount_t`, the family with an associated lock such as `seqcount_spinlock_t`,
`seqlock_t` and `seqcount_latch_t` is used when, what does associating a lock with the counter buy, and what does it change on
PREEMPT_RT? Start from `Documentation/locking/seqlock.rst` and
`include/linux/seqlock_types.h`.

## locking.seqlock-reader-variants: Reader variants

- section: Sequence counters
- relevance: 3 - the newer scoped form hides the retry loop

When is each of these read-side forms used: for `seqlock_t`, `read_seqbegin()` with
`read_seqretry()`, `read_seqlock_excl()`, `read_seqbegin_or_lock()` and `scoped_seqlock_read()`;
for a bare sequence counter, `read_seqcount_begin()`, `raw_read_seqcount_begin()`,
`raw_read_seqcount()` and `raw_seqcount_try_begin()`? What does each guarantee to its caller?
Answer as a table. Start from `include/linux/seqlock.h`.

## locking.seqlock-reader-usage: Sequence counter read side

- section: Sequence counters
- relevance: 5 - the section runs on torn data and may run again

What are the requirements for the code between `read_seqcount_begin()` and
`read_seqcount_retry()`, or between `read_seqbegin()` and `read_seqretry()`, in order to assure
safe usage? Name in-tree readers that show it.

## locking.seqlock-writer-usage: Sequence counter write side

- section: Sequence counters
- relevance: 4 - a preempted writer spins every reader

What are the requirements for a write section entered with `write_seqcount_begin()` in order to
assure safe usage, and which write-side forms check them and which skip the check? What are
`write_seqcount_invalidate()` and `raw_write_seqcount_barrier()` for?

# The lock implementations

## locking.rtmutex-shared-builds: Builds that include rtmutex.c

- section: The lock implementations
- relevance: 4 - one source file is compiled several times with different macros

How many times is each of `kernel/locking/rtmutex.c` and `kernel/locking/ww_mutex.h` compiled, and
which macros tell the builds apart? What does each macro change in the code that is built?

## locking.spinlock-layers: Spinlock API layers

- section: The lock implementations
- relevance: 3 - a change at one layer misses the builds that bypass it

Through which layers does a `spin_lock()` call pass, and at which layer are lockdep and preemption
handled? Which configurations bypass or replace a layer, and which layer? Start from
`include/linux/spinlock.h` and `include/linux/spinlock_api_smp.h`.

## locking.mutex-internals: Mutex internals

- section: The lock implementations
- relevance: 3 - needed to change the mutex, not to use it

What do the flag bits in the owner word of `struct mutex` promise the unlock and handoff paths,
and which of the fast, spinning and slow paths exist under which configuration? How does `struct
mutex` keep track of its waiters? Start from `__mutex_lock_common()` and the flag definitions in
`kernel/locking/mutex.h`.

## locking.new-primitive-checklist: Adding a lock operation

- section: The lock implementations
- relevance: 3 - each new variant needs the same set of companions

What comes with an acquisition function, besides its definition, and which checker or build needs
each part? Use `mutex_lock_killable()` as the example. Which in-tree test exercises the lock
operations?

# Model gaps

## locking.model-gaps: Other mistakes models make

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
