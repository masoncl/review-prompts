# Questions: Locking (measurement set)

- guide: locking.md
- title: Locking and Synchronization

A wide set of questions about the kernel's locking and synchronization
primitives, used to measure what a model already knows before deciding what
the built guide should spend its words on. The hand-written guide it will
replace is 3,389 words, much of it a method for tracing races rather than facts
about a tree. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## locking.core-files: Core files

- section: Finding your way
- relevance: 4 - the API is spread over many headers and the RT substitutions live apart
- words: 120

Which files hold the spinlock and rwlock API layers, the queued spinlock, the
mutex, the rw_semaphore, the rtmutex and the PREEMPT_RT substitutions built on
it, the per-CPU rw_semaphore, sequence counters, local locks, wound/wait
mutexes, lockdep, the scope-based guard macros and the compiler lock
annotations? A table. Start from `kernel/locking/` and `include/linux/`.

## locking.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - several rules are only written down there
- words: 80

Which documents in the tree are the authority on lock types and their nesting,
on lockdep, on sequence counters, on memory barriers and atomic operations, on
the memory model, on RCU usage and on the compiler-based lock annotations?
Start from `Documentation/locking/`.

## locking.debug-configs: Debugging options

- section: Finding your way
- relevance: 3 - says which mistakes a test run would have caught
- words: 100

Which configuration options turn on checking of lock ordering, of sleeping in
atomic context, of raw spinlock nesting, of RCU usage, of freeing held locks, of
per-CPU accesses with preemption enabled and of data races, and what does each
catch? A table. Start from `lib/Kconfig.debug`.

## locking.tests: Tests and torture modules

- section: Finding your way
- relevance: 2 - what to run after changing a primitive
- words: 70

Which in-tree tests exercise the locking primitives and lockdep itself, where
is each, and how is it enabled? Start from `kernel/locking/locktorture.c` and
`lib/locking-selftest.c`.

# Lock types

## locking.lock-categories: Lock categories

- section: Kinds of lock
- relevance: 5 - every nesting and context rule is phrased in these
- words: 90

Into which categories does the kernel documentation sort its lock types, which
primitive belongs to which category on a normal kernel, and which change
category on PREEMPT_RT? Start from `Documentation/locking/locktypes.rst`.

## locking.context-table: Exclusion by context

- section: Kinds of lock
- relevance: 5 - the wrong variant deadlocks or races and nothing in the diff shows it
- words: 120

For each acquisition variant of `raw_spinlock_t`, `spinlock_t`, `local_lock_t`,
`struct mutex` and `struct rw_semaphore`, does holding it exclude other tasks,
softirqs on this CPU and hard interrupts on this CPU, and can the acquisition
sleep, on a normal kernel and on PREEMPT_RT? A table.

## locking.irq-variant-choice: Interrupt-masking variants

- section: Kinds of lock
- relevance: 4 - the unconditional enable on unlock is the classic mistake
- words: 80

What is the difference between the `_irq`, `_irqsave` and `_bh` variants of
`spin_lock()`, what usage of the `_irq` variant is unsafe, and when is it the
correct choice?

## locking.irq-shared-lock: Locks shared with interrupt handlers

- section: Kinds of lock
- relevance: 5 - same-CPU deadlock that only lockdep or luck finds
- words: 100

When a lock is taken both in process context and in a hard or soft interrupt
handler, what usage is unsafe, and which acquisitions that use plain
`spin_lock()` on such a lock are nevertheless correct? Name in-tree code or
documentation that shows both. Start from `Documentation/locking/spinlocks.rst`
and `Documentation/kernel-hacking/locking.rst`.

## locking.nested-irq-masking: Nesting under a masking lock

- section: Kinds of lock
- relevance: 3 - unlock order decides whether interrupts come back on too early
- words: 70

When a second spinlock is taken inside a region entered with
`spin_lock_irq()` or `spin_lock_irqsave()`, what state does the inner region
inherit, and what goes wrong if the outer lock is released first with its
interrupt-enabling unlock?

## locking.raw-spinlock-use: Raw spinlocks

- section: Kinds of lock
- relevance: 4 - decides what may run inside the section on RT
- words: 80

When is `raw_spinlock_t` the required type rather than `spinlock_t`, what may
code holding one not do, and what does the documentation say about how long
such sections may be?

## locking.rwlock-semantics: Reader-writer spinlocks

- section: Kinds of lock
- relevance: 3 - fairness and reader recursion differ from what people assume
- words: 90

For `rwlock_t`, may a reader take the read lock again while holding it, how
are waiting writers treated by new readers in process context and in interrupt
context, and what changes on PREEMPT_RT? Start from
`kernel/locking/qrwlock.c` and the recursive read lock section of
`Documentation/locking/lockdep-design.rst`.

## locking.mutex-rules: Mutex rules

- section: Sleeping locks
- relevance: 4 - the rules are stricter than a semaphore's and are enforced only with debugging on
- words: 90

Which usage rules does `struct mutex` impose (who may unlock, recursion,
contexts it may be used from, exiting or freeing memory while held), and which
configuration option makes the kernel check them? Start from
`Documentation/locking/mutex-design.rst`.

## locking.mutex-unlock-lifetime: Unlocking and object lifetime

- section: Sleeping locks
- relevance: 5 - a use-after-free inside the unlock itself that no reader of the diff sees
- words: 90

When the last thing a task does with an object is unlock a lock embedded in
it, after which another task may free the object, for which lock types is that
unsafe and for which is it correct, and why? Start from the comment above
`mutex_unlock()` in `kernel/locking/mutex.c`.

## locking.mutex-variants: Mutex acquisition variants

- section: Sleeping locks
- relevance: 3 - return conventions differ between the variants
- words: 80

What do `mutex_lock_interruptible()`, `mutex_lock_killable()`,
`mutex_lock_io()`, `mutex_trylock()` and `atomic_dec_and_mutex_lock()` each do
and return, and from which contexts may `mutex_trylock()` be called?

## locking.mutex-internals: Mutex internals

- section: Sleeping locks
- relevance: 3 - needed to change the mutex, not to use it
- words: 100

How does `struct mutex` encode its owner and state, what are the fast path,
the optimistic spinning path and the slow path, and how does lock handoff to a
waiter work? Start from `__mutex_lock_common()` and the flag definitions in
`kernel/locking/mutex.h`.

## locking.rwsem-semantics: Reader-writer semaphores

- section: Sleeping locks
- relevance: 4 - reader recursion deadlocks once a writer queues
- words: 100

For `struct rw_semaphore`: may a task take it for read twice, how are readers
arriving behind a waiting writer treated, what do `downgrade_write()` and
`down_read_non_owner()` do, and which acquisitions can fail? What changes on
PREEMPT_RT?

## locking.percpu-rwsem: Per-CPU reader-writer semaphore

- section: Sleeping locks
- relevance: 3 - the write side is far more expensive than it looks
- words: 80

What is a `struct percpu_rw_semaphore`, what do its read and write sides cost,
what mechanism switches readers between their fast and slow paths, and may a
reader sleep? Start from `kernel/locking/percpu-rwsem.c`.

## locking.completions: Completions

- section: Sleeping locks
- relevance: 3 - on-stack completions and reuse have their own hazards
- words: 90

What is a completion for, how do `complete()` and `complete_all()` differ,
when must `reinit_completion()` be used, and what usage of a completion
declared on the stack is unsafe? Start from `include/linux/completion.h` and
`Documentation/scheduler/completion.rst`.

## locking.rtmutex: RT mutexes

- section: Sleeping locks
- relevance: 3 - priority inheritance has an owner and cannot be used like a semaphore
- words: 80

What does `struct rt_mutex` add over a mutex, how is priority inheritance
propagated along a chain of blocked tasks, and who uses rtmutexes on a
non-RT kernel? Start from `rt_mutex_adjust_prio_chain()`.

## locking.ww-mutex: Wound/wait mutexes

- section: Sleeping locks
- relevance: 3 - the error returns are part of the protocol
- words: 110

How are several `struct ww_mutex` locks of one class taken without a fixed
order: what is the acquire context, what do the `-EDEADLK` and `-EALREADY`
returns require the caller to do, and how do the wait-die and wound-wait
classes differ? Start from `Documentation/locking/ww-mutex-design.rst`.

## locking.local-lock: Local locks

- section: CPU local locks
- relevance: 4 - replaces bare preempt and irq disabling around per-CPU data
- words: 100

What is a `local_lock_t`, what does each of `local_lock()`,
`local_lock_irq()` and `local_lock_irqsave()` do on a normal kernel and on
PREEMPT_RT, and what is the scope of the protection it gives? Start from
`include/linux/local_lock_internal.h`.

## locking.local-lock-scope-usage: Replacing irq disabling with local locks

- section: CPU local locks
- relevance: 4 - two different local locks do not exclude each other on RT
- words: 80

When `local_irq_save()` or `preempt_disable()` sections that protect per-CPU
data are converted to local locks, what substitution is unsafe, and what is
the correct one? Start from the local_lock caveats in
`Documentation/locking/locktypes.rst`.

## locking.local-trylock: Local trylocks

- section: CPU local locks
- relevance: 4 - the only local lock usable from any context
- words: 80

What is a `local_trylock_t`, how does it differ from `local_lock_t` in layout
and in which operations accept it, from which contexts may `local_trylock()` be
called, and what does it do in hard interrupt or NMI context on PREEMPT_RT?

## locking.local-lock-nested-bh: Per-CPU data under disabled bottom halves

- section: CPU local locks
- relevance: 4 - on RT disabling bottom halves may no longer serialize anything
- words: 100

On PREEMPT_RT, what does `local_bh_disable()` do, does it still keep two
sections on the same CPU from running at once, which option controls that,
and what are `local_lock_nested_bh()` and its guard for? Start from
`kernel/softirq.c` and `kernel/Kconfig.preempt`.

# PREEMPT_RT

## locking.rt-substitutions: Substitutions on PREEMPT_RT

- section: What changes on RT
- relevance: 5 - the same source line is a different lock
- words: 110

What is each of `spinlock_t`, `rwlock_t`, `struct mutex`,
`struct rw_semaphore`, `local_lock_t`, `raw_spinlock_t` and
`struct semaphore` implemented as on PREEMPT_RT, and in which file? A table.

## locking.rt-spinlock-semantics: spinlock_t on PREEMPT_RT

- section: What changes on RT
- relevance: 5 - code that relied on side effects of spin_lock breaks silently
- words: 110

On PREEMPT_RT, what does acquiring a `spinlock_t` do to preemption, to
migration, to RCU, to the task's sleep state and to interrupts when the
`_irq` or `_irqsave` variant is used? Start from
`kernel/locking/spinlock_rt.c`.

## locking.rt-unsafe-usage: Usage that breaks on PREEMPT_RT

- section: What changes on RT
- relevance: 5 - compiles and runs on every non-RT kernel
- words: 120

What usage of `spinlock_t`, `rwlock_t` or `local_lock_t` is correct on a
non-RT kernel but unsafe on PREEMPT_RT (consider explicit preemption or
interrupt disabling, hard interrupt context and raw spinlocks held), and what
that looks similar is correct on both? Start from the PREEMPT_RT caveats in
`Documentation/locking/locktypes.rst`.

## locking.rt-hardirq-context: Hard interrupt context on PREEMPT_RT

- section: What changes on RT
- relevance: 4 - decides whether a handler may take a spinlock_t at all
- words: 90

On PREEMPT_RT, which interrupt handlers, timers and irq_work items still run
in hard interrupt context and which are moved to threads, and how does lockdep
on a non-RT kernel know the difference? Start from `IRQF_NO_THREAD`,
`HRTIMER_MODE_HARD` and `IRQ_WORK_HARD_IRQ`.

## locking.context-predicates: Context predicates

- section: What changes on RT
- relevance: 4 - the wrong predicate guards a sleeping lock with a test that misses cases
- words: 110

What do `in_task()`, `in_hardirq()`, `in_serving_softirq()`, `in_softirq()`,
`in_interrupt()`, `in_nmi()`, `in_atomic()`, `irqs_disabled()` and
`preemptible()` each report, and which of them are unreliable under some
configuration? Start from `include/linux/preempt.h`.

## locking.context-guard-usage: Run-time context checks

- section: What changes on RT
- relevance: 4 - a guard that misses preempt-disabled callers sleeps in atomic context on RT
- words: 90

When code that can be reached from any context must decide at run time whether
it may take a `spinlock_t` or `local_lock_t`, what test is unsafe, and what is
correct, including the use of trylock variants? Name in-tree code that does it.

# Lockdep

## locking.lockdep-model: Lockdep data model

- section: The validator
- relevance: 4 - explains what a splat does and does not prove
- words: 110

What does lockdep record per lock class, per held lock and per task, which
kinds of rule does it check from that (ordering, interrupt safety, wait
context, recursion), and does it need the deadlock to happen to report it?
Start from `struct lock_class`, `struct held_lock` and
`Documentation/locking/lockdep-design.rst`.

## locking.lockdep-wait-types: Wait types

- section: The validator
- relevance: 5 - this is how raw-versus-sleeping nesting is checked on every kernel
- words: 120

What are the values of `enum lockdep_wait_type`, which inner and outer wait
type does each lock type (and RCU) carry, what wait type does the current
context impose, and which acquisitions does `check_wait_context()` skip?

## locking.nesting-table: Nesting by lock type

- section: The validator
- relevance: 5 - the table reviewers need when a patch adds a lock inside another
- words: 110

While holding each of `raw_spinlock_t`, `spinlock_t`, `local_lock_t`,
`struct mutex` and an RCU read-side section, which lock types may be acquired
and which may not? A table. Say which document states the rule.

## locking.raw-nesting-config: Raw lock nesting checks

- section: The validator
- relevance: 4 - decides whether a non-RT test run reports the nesting
- words: 80

What does `CONFIG_PROVE_RAW_LOCK_NESTING` change in lockdep, what is its
default, and does wrapping an acquisition in a test that the kernel is not
PREEMPT_RT keep lockdep from reporting an invalid wait context?

## locking.wait-override: Wait type override maps

- section: The validator
- relevance: 3 - the sanctioned way to silence an intentional nesting
- words: 80

What is `DEFINE_WAIT_OVERRIDE_MAP()` for, how is it used around an
acquisition, and which in-tree code uses it and why?

## locking.lockdep-irq-states: Interrupt safety states

- section: The validator
- relevance: 4 - the report names these states and people misread them
- words: 100

Which usage states does lockdep keep per class for hard and soft interrupts,
what combination of them on two locks does it report as an inversion, and
which states exist besides the interrupt ones? Start from
`kernel/locking/lockdep_states.h`.

## locking.lockdep-subclasses: Subclasses and nest locks

- section: Annotations
- relevance: 4 - same-class nesting is reported as recursion without them
- words: 100

How is taking two locks of the same class annotated: what do the `_nested`
variants, `mutex_lock_nest_lock()` and `lock_set_cmp_fn()` each tell lockdep,
how many subclasses are there, and what does lockdep no longer check once a
subclass is used?

## locking.lockdep-keys: Lock class keys

- section: Annotations
- relevance: 3 - one init site means one class, wanted or not
- words: 90

What decides which class a lock belongs to, how do `lockdep_set_class()`,
`lockdep_register_key()` and `lockdep_unregister_key()` change that, and what
must hold for a key that lives in dynamically allocated memory?

## locking.lockdep-asserts: Assertion helpers

- section: Annotations
- relevance: 4 - documents the locking contract where a comment would rot
- words: 120

Which helpers assert that a lock is held, held for write or read, or not held,
and that interrupts or preemption are in a given state, and what does each
compile to without lockdep? A table. Include the rwsem and non-lockdep
variants. Start from `include/linux/lockdep.h`.

## locking.lockdep-pinning: Lock pinning

- section: Annotations
- relevance: 3 - a pinned lock released by a callee is a warning, and folded entries make it fire wrongly
- words: 110

What do `lockdep_pin_lock()`, `lockdep_unpin_lock()` and
`lockdep_repin_lock()` do to the held lock entry, when does lockdep warn, and
how does that interact with several lock instances sharing one held lock entry
through a nest lock? Start from `match_held_lock()` and `__lock_release()`.

## locking.lockdep-limits: Limits and shutdown

- section: Annotations
- relevance: 3 - after the first report nothing else is checked
- words: 90

What are the limits on held locks per task, subclasses, classes and chains,
what happens when one is exceeded or when lockdep prints its first report,
and what do `lockdep_off()`, `lockdep_set_novalidate_class()` and
`lockdep_set_notrack_class()` do?

## locking.sleep-checks: Sleep and lock debugging hooks

- section: Annotations
- relevance: 3 - they catch the bug on the common path, not only the contended one
- words: 90

What do `might_sleep()`, `might_lock()`, `might_alloc()`, `cant_sleep()` and
`non_block_start()` each check, and under which configuration options?

## locking.reclaim-lockdep: Allocation under locks

- section: Annotations
- relevance: 4 - the deadlock needs memory pressure to happen but lockdep can see it without
- words: 100

How does lockdep learn that a lock is taken in the memory reclaim path and that
an allocation happens under a lock, which allocation flags matter, and what do
`memalloc_nofs_save()` and `memalloc_noio_save()` change? Start from
`fs_reclaim_acquire()`.

# Annotations checked at build time

## locking.context-analysis: Compiler context analysis

- section: Static lock annotations
- relevance: 5 - the annotation keywords changed meaning and checker
- words: 110

What is the compiler-based context analysis in this tree, which compiler and
configuration options does it need, how is a directory or file opted in, and
which synchronization primitives does it know about? If this tree has none, say
so. Start from `Documentation/dev-tools/context-analysis.rst`.

## locking.annotation-keywords: Annotation keywords

- section: Static lock annotations
- relevance: 4 - reviewers must know whether a wrong annotation now breaks a build
- words: 120

What do `__must_hold()`, `__acquires()`, `__releases()`, `__cond_acquires()`,
`__guarded_by()` and `__pt_guarded_by()` and their shared variants declare,
which tool checks them in this tree, and what do they expand to under sparse?
A table. Start from `include/linux/compiler-context-analysis.h`.

## locking.context-analysis-escapes: Opting code out of the analysis

- section: Static lock annotations
- relevance: 3 - each escape hatch hides a different amount
- words: 90

How is code that the analysis cannot follow handled: what do
`context_unsafe()`, `__context_unsafe()`, `__no_context_analysis` and the
lockdep assertions each do for the analysis, and how are guarded members
initialised before the lock is in use?

## locking.guards: Scope-based lock guards

- section: Scope-based locking
- relevance: 5 - now the usual way locks are taken in new code
- words: 110

What do `guard()`, `scoped_guard()`, `scoped_cond_guard()`, `ACQUIRE()` and
`ACQUIRE_ERR()` each do, and exactly when is the lock released in each case?
Start from `include/linux/cleanup.h`.

## locking.guard-classes: Guard class names

- section: Scope-based locking
- relevance: 4 - the class name is not the function name
- words: 120

Which guard class names exist for spinlocks, raw spinlocks, rwlocks, mutexes,
rw_semaphores, RCU, SRCU, preemption, interrupts, migration, local locks, the
per-CPU rw_semaphore and the CPU hotplug lock, including the conditional
variants? A table. Start from the `DEFINE_LOCK_GUARD_1()` and
`DEFINE_GUARD()` uses under `include/linux/`.

## locking.guard-usage: Guard hazards

- section: Scope-based locking
- relevance: 5 - the lock is held to the end of a scope the reader has to find
- words: 120

What usage of lock guards is unsafe (consider `goto`, the order of definition
against `__free()` variables, conditional lock classes used with `guard()`,
`switch` cases, and a lock held for longer than the code needs), and what is
correct? Start from the comment at the top of `include/linux/cleanup.h`.

# RCU

## locking.rcu-readers: Read-side critical sections

- section: RCU readers
- relevance: 5 - what a grace period actually waits for
- words: 110

Which regions of code does `synchronize_rcu()` wait for besides those between
`rcu_read_lock()` and `rcu_read_unlock()`, how do `rcu_read_lock_bh()` and
`rcu_read_lock_sched()` relate to it, and what is a reader forbidden to do?
Start from the comment above `rcu_read_lock()` in `include/linux/rcupdate.h`.

## locking.rcu-implicit-readers: Spinlocks as RCU readers

- section: RCU readers
- relevance: 4 - right for the grace period, wrong for the debug checks
- words: 90

Does holding a `spinlock_t` or `raw_spinlock_t`, or having preemption
disabled, protect an RCU-protected pointer from being freed, on a normal
kernel and on PREEMPT_RT, and which dereference primitive accepts that
protection without a lockdep complaint?

## locking.rcu-dereference-variants: Dereference variants

- section: RCU readers
- relevance: 4 - each variant states a different protection claim
- words: 120

When is each of `rcu_dereference()`, `rcu_dereference_bh()`,
`rcu_dereference_sched()`, `rcu_dereference_all()`, `rcu_dereference_check()`,
`rcu_dereference_protected()`, `rcu_dereference_raw()` and
`rcu_access_pointer()` the right one, and what does each check? A table.

## locking.rcu-sleeping: Blocking inside readers

- section: RCU readers
- relevance: 4 - legal on one configuration and a bug on the next
- words: 90

What may and may not block inside an RCU read-side critical section under
non-preemptible RCU, preemptible RCU and PREEMPT_RT, and which debugging
options report a violation?

## locking.rcu-lockdep: RCU lockdep checks

- section: RCU readers
- relevance: 3 - explains the "suspicious RCU usage" report
- words: 80

What do `CONFIG_PROVE_RCU`, `RCU_LOCKDEP_WARN()`, `rcu_read_lock_held()` and
the condition argument of `rcu_dereference_check()` and
`list_for_each_entry_rcu()` do, and what checks the `__rcu` pointer
annotation?

## locking.rcu-update-usage: Freeing after an update

- section: RCU updaters
- relevance: 5 - the canonical use-after-free
- words: 110

After an RCU-protected pointer is replaced or an element unlinked, what usage
of the old object is unsafe, which primitives make freeing it correct, and
when is freeing it immediately correct after all? Name in-tree code.

## locking.rcu-update-primitives: Publishing primitives

- section: RCU updaters
- relevance: 3 - the cheap variants are only right in stated cases
- words: 90

What do `rcu_assign_pointer()`, `RCU_INIT_POINTER()`,
`rcu_replace_pointer()` and `rcu_pointer_handoff()` each do, which ordering
does each provide, and when is `RCU_INIT_POINTER()` permitted?

## locking.kfree-rcu-variants: kfree_rcu variants

- section: RCU updaters
- relevance: 4 - the variants differ in where they may be called
- words: 90

Which forms of `kfree_rcu()` and `kvfree_rcu()` does this tree have, including
the forms without an `rcu_head` and any form for contexts where locks cannot
be taken, and from which contexts may each be called?

## locking.rcu-grace-period-api: Waiting for grace periods

- section: RCU updaters
- relevance: 4 - wrong choice stalls a caller or leaks callbacks at unload
- words: 120

What is each of `synchronize_rcu()`, `synchronize_rcu_expedited()`,
`call_rcu()`, `call_rcu_hurry()`, the polled grace period interface and
`rcu_barrier()` for, from which contexts may each be called, and what must a
module that uses `call_rcu()` do before it is unloaded?

## locking.rcu-lookup-refcount: Lookup then reference

- section: RCU updaters
- relevance: 5 - taking a plain reference on an object found under RCU resurrects freed memory
- words: 100

When an object is found under `rcu_read_lock()` and is to be used after the
section ends, what usage is unsafe, and what is the correct way to take the
reference? Start from `refcount_inc_not_zero()` and
`Documentation/RCU/rcuref.rst`.

## locking.typesafe-by-rcu: Type-safe slab memory

- section: RCU updaters
- relevance: 4 - the object can be reused for another instance during the reader's section
- words: 100

What does `SLAB_TYPESAFE_BY_RCU` guarantee and not guarantee to an RCU reader,
what must a lookup do after it takes its reference, and what are the nulls
list variants for? Start from the comment at `SLAB_TYPESAFE_BY_RCU` in
`include/linux/slab.h` and `Documentation/RCU/rculist_nulls.rst`.

## locking.rcu-list-api: RCU list operations

- section: RCU updaters
- relevance: 4 - which list calls are safe against concurrent readers is not obvious from the names
- words: 110

Which list and hlist operations may run concurrently with RCU readers, what
does `list_del_rcu()` leave in the removed entry, and what usage of the
ordinary list operations (deletion with reinitialisation, the `_safe`
iterators, `list_empty()` checks) on an RCU-traversed list is unsafe? Start
from `include/linux/rculist.h`.

## locking.srcu: Sleepable RCU

- section: Other RCU flavours
- relevance: 4 - the domain, the index and the cleanup all have rules
- words: 100

What is SRCU, what does a reader have to keep between lock and unlock, what
does a grace period cost compared with RCU, and what must be true before
`cleanup_srcu_struct()` is called? Start from `include/linux/srcu.h`.

## locking.srcu-flavours: SRCU reader flavours

- section: Other RCU flavours
- relevance: 4 - new flavours exist and may not be mixed on one domain
- words: 110

Which SRCU read-side flavours does this tree have besides
`srcu_read_lock()`, what is each for, how must the `struct srcu_struct` be
defined or initialised for each, and what happens if two flavours are used on
the same domain? Start from `srcu_check_read_flavor()`.

# Counts, per-CPU state and CPUs

## locking.refcount-types: Reference count types

- section: Reference counts
- relevance: 4 - the types differ in what happens at zero and at overflow
- words: 110

How do `refcount_t`, `struct kref`, `rcuref_t`, `struct percpu_ref` and
`struct lockref` differ: what happens on increment from zero and on overflow,
which support a lookup that may race with the final put, and which combine
with a lock (`refcount_dec_and_lock()`, `atomic_dec_and_lock()`)?

## locking.refcount-ordering: Reference count ordering

- section: Reference counts
- relevance: 4 - weaker than the atomic_t calls they replaced
- words: 90

Which memory ordering do `refcount_inc()`, `refcount_inc_not_zero()`,
`refcount_dec()` and `refcount_dec_and_test()` provide, and why is the
ordering on the final decrement needed? Start from
`Documentation/core-api/refcount-vs-atomic.rst`.

## locking.preempt-migrate-irq: Preemption, migration and interrupt disabling

- section: Pinning to a CPU
- relevance: 5 - each gives a different subset of what per-CPU code needs
- words: 120

What does each of `preempt_disable()`, `migrate_disable()`,
`local_bh_disable()` and `local_irq_disable()` guarantee and not guarantee
(staying on the CPU, exclusion against other tasks on it, against softirqs,
against interrupts, being an RCU reader, permission to sleep), on a normal
kernel and on PREEMPT_RT? A table.

## locking.percpu-access: Per-CPU accessors

- section: Pinning to a CPU
- relevance: 3 - the accessor chosen states which protection the caller claims
- words: 100

What protection does each of `this_cpu_ptr()`, `raw_cpu_ptr()`,
`get_cpu_ptr()`, `per_cpu_ptr()`, `this_cpu_add()` and `__this_cpu_add()`
expect from its caller, and what does `CONFIG_DEBUG_PREEMPT` check?
Start from `Documentation/core-api/this_cpu_ops.rst`.

## locking.cpu-hotplug-lock: CPU hotplug exclusion

- section: Pinning to a CPU
- relevance: 4 - pinning a task and keeping a CPU online are different things
- words: 110

What kind of lock is behind `cpus_read_lock()`, may it be taken in atomic
context, and which of `preempt_disable()`, `migrate_disable()`,
`local_irq_disable()` and `cpus_read_lock()` keep the current CPU, and which
keep other CPUs, from going offline? Start from `kernel/cpu.c` and
`Documentation/core-api/cpu_hotplug.rst`.

## locking.percpu-teardown-usage: Per-CPU state and hotplug callbacks

- section: Pinning to a CPU
- relevance: 3 - the teardown callback races with anything not pinned
- words: 90

When per-CPU state is set up and torn down by CPU hotplug callbacks, what
usage by code running on or reaching into that CPU's state is unsafe, and
which forms of protection are correct when the user needs to sleep? Start from
`cpuhp_setup_state()`.

## locking.nmi-context: Locking from NMI context

- section: Pinning to a CPU
- relevance: 3 - nothing that spins is safe there
- words: 80

Which synchronization may code running in NMI context use, what usage of
spinlocks there is unsafe, and how is work handed to a context that can take
locks? Start from `include/linux/irq_work.h`.

# Memory ordering

## locking.barrier-kinds: Barrier primitives

- section: Barriers and atomics
- relevance: 4 - the reference reviewers reach for
- words: 120

What does each of `smp_mb()`, `smp_rmb()`, `smp_wmb()`,
`smp_store_release()`, `smp_load_acquire()`, `smp_store_mb()`,
`smp_mb__before_atomic()`, `smp_mb__after_atomic()`,
`smp_mb__after_spinlock()` and `smp_mb__after_unlock_lock()` order? A table.
Start from `Documentation/memory-barriers.txt`.

## locking.atomic-ordering: Ordering of atomic operations

- section: Barriers and atomics
- relevance: 5 - most people remember half of the rule
- words: 100

What ordering do atomic operations give by class (plain reads and sets,
read-modify-write without a return value, with one, conditional ones that
fail, and the `_relaxed`, `_acquire` and `_release` forms)? Start from
`Documentation/atomic_t.txt`.

## locking.bitops-ordering: Ordering of bit operations

- section: Barriers and atomics
- relevance: 3 - bit locks and wait-on-bit depend on the right variant
- words: 90

Which ordering do `set_bit()`, `clear_bit()`, `test_and_set_bit()`,
`test_and_set_bit_lock()`, `clear_bit_unlock()`, `test_bit()` and
`test_bit_acquire()` give, and what must accompany `clear_bit()` before
`wake_up_bit()`? Start from `Documentation/atomic_bitops.txt`.

## locking.publish-usage: Publishing initialised data

- section: Barriers and atomics
- relevance: 5 - works on x86, fails on weakly ordered machines
- words: 110

When one CPU initialises an object and then makes a pointer to it visible to
lockless readers, what usage on the writer side and on the reader side is
unsafe, what is correct, and is a plain `READ_ONCE()` of the pointer enough
for the reader? Name the in-tree documents that say so.

## locking.lock-ordering-guarantees: Ordering given by lock and unlock

- section: Barriers and atomics
- relevance: 3 - an unlock followed by a lock is not a full barrier
- words: 90

Which ordering do a lock acquisition and a release provide to accesses inside
and outside the critical section, is an unlock followed by a lock a full
barrier, and which primitives strengthen it? Start from the locking section
of `Documentation/memory-barriers.txt` and
`tools/memory-model/Documentation/locking.txt`.

## locking.marked-accesses: Marked accesses and data races

- section: Barriers and atomics
- relevance: 4 - reviewers ask for READ_ONCE in the wrong places and miss the right ones
- words: 110

When must a lockless access use `READ_ONCE()` or `WRITE_ONCE()`, when is
`data_race()` the right marking, which accesses may stay plain, and what do
KCSAN's `ASSERT_EXCLUSIVE_WRITER()` and `ASSERT_EXCLUSIVE_ACCESS()` express?
Start from `tools/memory-model/Documentation/access-marking.txt`.

## locking.sleep-wake-ordering: Sleeping and waking

- section: Barriers and atomics
- relevance: 5 - the lost wakeup
- words: 110

In an open-coded wait loop, what order of setting the task state, testing the
condition and calling `schedule()` is unsafe, what is correct, which barrier
in `set_current_state()` pairs with which in the waker, and when is
`__set_current_state()` enough? Start from the comment above
`set_current_state()` in `include/linux/sched.h`.

# Sequence counters

## locking.seqcount-types: Sequence counter types

- section: Seqlocks
- relevance: 4 - the type chosen decides who serialises writers and what RT does
- words: 110

How do `seqcount_t`, the `seqcount_LOCKNAME_t` family, `seqlock_t` and
`seqcount_latch_t` differ, what does associating a lock with the counter buy,
and what does it change on PREEMPT_RT? Start from
`Documentation/locking/seqlock.rst` and `include/linux/seqlock_types.h`.

## locking.seqlock-reader-usage: Sequence counter read side

- section: Seqlocks
- relevance: 5 - the section runs on torn data and may run again
- words: 110

What usage inside a sequence counter read section is unsafe (side effects,
following pointers, trusting values before the retry check), and what is
correct? Name in-tree readers that show it.

## locking.seqlock-writer-usage: Sequence counter write side

- section: Seqlocks
- relevance: 4 - a preempted writer spins every reader
- words: 110

What must a sequence counter writer guarantee about serialisation against
other writers and about preemption, which variants check it and which skip the
check, and what do `write_seqcount_invalidate()` and
`raw_write_seqcount_barrier()` do?

## locking.seqlock-reader-variants: Reader variants

- section: Seqlocks
- relevance: 3 - the newer scoped form hides the retry loop
- words: 110

Besides `read_seqbegin()` and `read_seqretry()`, which read-side forms does
`seqlock_t` offer (locking readers, lockless-then-locking readers, any scoped
form), which do bare sequence counters offer (`raw_` forms, try-begin forms),
and when is each used? Start from `include/linux/seqlock.h`.

# Using locks safely

## locking.object-pins: Keeping an object alive

- section: Lifetime across lock boundaries
- relevance: 5 - the pointer outlives the lock that made it valid
- words: 100

After a pointer to a shared object is obtained under a lock or an RCU section,
what usage of it once that protection is dropped is unsafe, what counts as
something that keeps the object alive, and what that looks like a
use-after-free is only a deferred free? Name in-tree code.

## locking.lock-drop-reacquire: Dropping and retaking a lock

- section: Lifetime across lock boundaries
- relevance: 5 - everything checked before the drop is stale
- words: 100

When a function drops a lock in the middle (to sleep, allocate or call out)
and takes it again, what usage of state examined before the drop is unsafe,
and what do correct in-tree functions do after retaking it? Name two.

## locking.check-then-lock: Checking before locking

- section: Lifetime across lock boundaries
- relevance: 4 - a lockless test is either an optimisation or a bug
- words: 100

When code tests shared state without the lock and then takes the lock to act,
what usage is unsafe, and what makes the lockless test correct (consider
rechecking under the lock, `list_empty_careful()`, and tests that only skip
work)? Name in-tree code.

## locking.deferred-work-teardown: Tearing down with work outstanding

- section: Lifetime across lock boundaries
- relevance: 5 - the free races with a callback that nobody is holding a lock for
- words: 110

Before an object used by a timer, a work item, an RCU callback or an interrupt
handler is freed, which call stops or waits for each, what usage is unsafe
(consider self-rearming and calling these while holding a lock the callback
takes), and what are the current names of the timer functions?

## locking.lock-order-documentation: Documented lock orders

- section: Lifetime across lock boundaries
- relevance: 3 - the order is written down in a few known places
- words: 90

Where does the tree write down lock ordering for the memory management,
filesystem, scheduler and networking cores, how does code take two locks of
the same type on different objects without deadlock, and what does a trylock
with back-off cost?

# Changing the implementation

## locking.spinlock-layers: Spinlock API layers

- section: Spinlock implementation
- relevance: 3 - a change at one layer misses the builds that bypass it
- words: 110

Through which layers does `spin_lock()` reach the architecture lock on SMP, on
UP, with `CONFIG_DEBUG_SPINLOCK`, with lockdep and on PREEMPT_RT, which are
inlined under which options, and at which layer are lockdep and preemption
handled? Start from `include/linux/spinlock.h` and
`include/linux/spinlock_api_smp.h`.

## locking.qspinlock: Queued spinlocks

- section: Spinlock implementation
- relevance: 3 - the lock word layout and node count are load-bearing
- words: 110

How is the queued spinlock word laid out, what are the fast, pending and queue
paths, where do the queue nodes live and how many nesting levels do they
allow, and how does the paravirtual variant differ? Start from
`queued_spin_lock_slowpath()`.

## locking.rtmutex-shared-builds: Builds that share the rtmutex code

- section: Sleeping lock implementation
- relevance: 4 - one source file is compiled several times with different macros
- words: 100

Which files include `kernel/locking/rtmutex.c` and
`kernel/locking/ww_mutex.h`, under which build macros, and what does each
inclusion produce? What must a change to either keep working?

## locking.new-primitive-checklist: Adding a lock operation

- section: Sleeping lock implementation
- relevance: 3 - each new variant needs the same set of companions
- words: 100

When a new acquisition variant or lock type is added, what has to come with
it: lockdep annotation and wait type, compiler context annotations, guard
classes, a PREEMPT_RT form, a UP or lockdep-off form, selftests and
documentation? Point at a recent in-tree addition that shows the set.

