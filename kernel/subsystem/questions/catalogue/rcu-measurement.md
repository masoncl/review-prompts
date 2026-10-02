# Questions: RCU (measurement set)

- guide: rcu.md
- title: RCU Subsystem

A wide set of questions about RCU, its API and its implementation, used to
measure what a model already knows before deciding what the built guide should
spend its words on. The hand-written guide it will replace is 558 words, so
most of what is asked here cannot be in the built guide; the point is to find
which few things must be. The trimmed set a guide is built from is
`../rcu.md`. Format: `../../../docs/subsystem-questions.md`.

# Where to look

## rcu.core-files: Source files

- section: Finding your way
- relevance: 4 - code people expect under kernel/rcu/ is not all there
- words: 110

Which files hold Tree RCU's core, its preemptible-reader, expedited,
callback-offloading and stall-warning parts, Tiny RCU, SRCU, the Tasks
flavours, the code shared by all flavours, the batching behind kfree_rcu(), and
the torture and scalability tests? A table. Start from `kernel/rcu/`.

## rcu.headers: Headers

- section: Finding your way
- relevance: 3 - turns a search into a lookup
- words: 90

Which headers under `include/linux/` declare the reader and updater API, the
list, hlist, nulls-list and bit-locked-list helpers, SRCU, Tasks Trace RCU, the
segmented callback list, rcuref, rcuwait and rcu_sync? A table.

## rcu.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - the usage rules are written down and reviewers cite them
- words: 80

Which files under `Documentation/RCU/` are the authority on the rules a user
must follow, on handling the pointer returned by `rcu_dereference()`, on
lockdep checking, on `rcu_barrier()`, on stall warnings, and on the
requirements and data structures of the implementation?

## rcu.build-flavors: Build-time implementations

- section: Finding your way
- relevance: 4 - what a reader may do depends on which one is built
- words: 90

Which Kconfig options select between the RCU implementations and between the
SRCU implementations, what selects each, and what does a user of the API have
to assume differs between them? Start from `kernel/rcu/Kconfig`.

# Readers

## rcu.reader-rules: Inside a read-side section

- section: Read-side critical sections
- relevance: 5 - the first thing checked in any RCU patch
- words: 100

What may code do, and not do, between `rcu_read_lock()` and
`rcu_read_unlock()`: block, be preempted, take a spinlock or a mutex, nest? How
does the answer change with preemptible RCU and with PREEMPT_RT, and what
catches a violation at run time?

## rcu.implicit-readers: Implicit readers

- section: Read-side critical sections
- relevance: 5 - decides whether code with no rcu_read_lock() is a bug
- words: 90

Besides `rcu_read_lock()`, which regions of code does `synchronize_rcu()` wait
for: preemption, softirqs or interrupts disabled, interrupt and NMI handlers?
What do `rcu_read_lock_bh()` and `rcu_read_lock_sched()` add today, and are
there still separate bh and sched grace-period primitives?

## rcu.reader-guards: Scope-based guards

- section: Read-side critical sections
- relevance: 3 - new code uses them and the unlock is invisible
- words: 70

Which scope-based guards exist for RCU and SRCU readers, how is each written at
a call site, and what static annotations do the reader primitives carry for
the compiler's context analysis? Start from the end of
`include/linux/rcupdate.h` and of `include/linux/srcu.h`.

## rcu.not-watching: RCU not watching

- section: Read-side critical sections
- relevance: 4 - a reader there protects nothing
- words: 90

In which execution contexts is RCU not watching, so that `rcu_read_lock()`
protects nothing, how does code test for that, and what must code that runs
there do before it can use RCU? Start from `rcu_is_watching()`.

## rcu.lockdep-helpers: Reader-held predicates

- section: Read-side critical sections
- relevance: 4 - they do not mean the same thing without lockdep
- words: 100

Which helpers say whether the caller is inside an RCU reader, and what does
each return when lockdep is not built in or has been switched off? So what
usage of them in ordinary control flow is unsafe, and what usage is correct?
Start from `rcu_read_lock_held()` and `RCU_LOCKDEP_WARN()`.

# Publishing and reading pointers

## rcu.dereference-variants: Pointer load primitives

- section: Pointers
- relevance: 5 - each form states who may call it
- words: 130

Give a table of the primitives that load an RCU-protected pointer: the plain,
checked, protected, raw, bh, sched, any-reader and SRCU forms, and the one that
fetches the value without allowing a dereference. For each, who may call it
and what it checks. Start from `rcu_dereference_check()`.

## rcu.dependency-ordering: Dependency ordering

- section: Pointers
- relevance: 4 - the compiler can break it and no barrier is visible
- words: 100

What ordering does `rcu_dereference()` give between the pointer load and later
accesses through it, which operations on the returned pointer can break that
ordering, and which are safe? Start from
`Documentation/RCU/rcu_dereference.rst`.

## rcu.assign-pointer: Publishing a pointer

- section: Pointers
- relevance: 4 - the initialiser form is misused
- words: 90

What ordering does `rcu_assign_pointer()` provide and how is it implemented,
including any case where it uses a plain store? When may `RCU_INIT_POINTER()`
be used instead, and what does `rcu_replace_pointer()` do?

## rcu.sparse-annotations: Sparse annotation

- section: Pointers
- relevance: 2 - a build-time check, but patches get it wrong
- words: 70

What does marking a pointer `__rcu` make sparse check, which accessors strip or
add the annotation, and what are `unrcu_pointer()` and `rcu_pointer_handoff()`
for?

## rcu.list-helpers: Removed list entries

- section: Lists
- relevance: 4 - what a reader standing on the entry sees
- words: 100

For the RCU list and hlist helpers, what state is a removed entry left in (its
forward and backward pointers) and why? What follows for re-adding the entry,
for deleting it twice, and for a reader that is standing on it? Start from
`list_del_rcu()` and `hlist_del_init_rcu()`.

## rcu.list-traversal-checks: Traversal lockdep argument

- section: Lists
- relevance: 3 - how update-side traversal is written without a splat
- words: 80

What does the optional last argument of `list_for_each_entry_rcu()` and
`hlist_for_each_entry_rcu()` do, which config option turns the check on, and
how should an update-side traversal under a lock be written? What are the SRCU
and lockless forms?

## rcu.nulls-lists: Nulls lists

- section: Lists
- relevance: 2 - a few hash tables, but subtle
- words: 70

What problem do nulls lists solve for lookups in RCU hash tables whose objects
can be reused, and what must a lookup do when it reaches the end of a chain?
Start from `include/linux/rculist_nulls.h` and
`Documentation/RCU/rculist_nulls.rst`.

# Grace periods and reclamation

## rcu.gp-wait-api: Waiting for a grace period

- section: Waiting for readers
- relevance: 4 - the calling context differs for each
- words: 110

Which primitives wait for or follow a grace period (blocking, expedited,
callback), and from which contexts may each be called? What does
`synchronize_rcu()` do differently before the scheduler is running, and when
expediting is forced by boot parameter or sysfs?

## rcu.lazy-callbacks: Lazy callbacks

- section: Waiting for readers
- relevance: 4 - a callback can sit for seconds
- words: 80

Can `call_rcu()` delay starting a grace period: under which configuration, on
which CPUs and for how long? What should code use when it needs the callback
soon? Start from `CONFIG_RCU_LAZY` in `kernel/rcu/Kconfig`.

## rcu.callback-context: Callback context

- section: Waiting for readers
- relevance: 4 - decides what a callback may call
- words: 90

In what contexts can an RCU callback be invoked, what may a callback therefore
not do, may it re-queue itself, and how is the number of callbacks run in one
batch limited? Start from `rcu_do_batch()`.

## rcu.rcu-barrier: Callback barriers

- section: Waiting for readers
- relevance: 4 - a missing one is a crash at module unload
- words: 90

What does `rcu_barrier()` wait for and what does it not wait for, when is it
required, and which barrier goes with each of SRCU, the Tasks flavours and
`kfree_rcu()`?

## rcu.polled-gp: Polled grace periods

- section: Waiting for readers
- relevance: 3 - names and the cookie type have changed over time
- words: 100

What is the polled grace-period API: which functions take a cookie, start a
grace period, test the cookie and conditionally wait? How do the full-state
variants differ and what type do they use, and are there expedited and SRCU
forms? Start from `get_state_synchronize_rcu()`.

## rcu.rcu-head-init: Initialising an rcu_head

- section: Waiting for readers
- relevance: 3 - old initialisers are remembered
- words: 80

Does a `struct rcu_head` need initialising before it is passed to `call_rcu()`,
which initialisers and destructors exist and what are they for, and what
happens when the same rcu_head is queued twice before it is invoked?

## rcu.memory-ordering: Grace-period memory ordering

- section: Waiting for readers
- relevance: 3 - what an updater may assume after the wait
- words: 80

What memory-ordering guarantee does a grace period give to the updater and to
a callback, on which CPUs, where is it documented, and which pieces of the
implementation provide it?

## rcu.kfree-rcu-forms: Forms of kfree_rcu

- section: Freeing after a grace period
- relevance: 5 - the forms, the field type and the contexts have all changed
- words: 110

Which forms of `kfree_rcu()` and `kvfree_rcu()` does this tree provide, what
arguments does each take, what type must the field named in the two-argument
form have, what limits the field's offset, and from which contexts may each
form be called? Start from `kvfree_rcu_arg_2()` in `include/linux/rcupdate.h`.

## rcu.kfree-rcu-context: Locks under kvfree_call_rcu

- section: Freeing after a grace period
- relevance: 4 - decides which locks its implementation may take
- words: 110

From which contexts is `kvfree_call_rcu()` reached in-tree: which locks can the
caller hold, can it be in hardirq? Which kinds of lock may its implementation
and callees therefore take, and how does this tree deal with PREEMPT_RT and
with lockdep's wait-context check on that path? Start from `kvfree_call_rcu()`
in `mm/slab_common.c` and `__kfree_rcu_sheaf()`.

## rcu.kfree-rcu-internals: Batching behind kfree_rcu

- section: Freeing after a grace period
- relevance: 3 - needed only when changing it
- words: 110

How does the batched kfree_rcu() implementation hold objects until a grace
period has elapsed: the per-CPU structure, its channels, the fallback when no
page is available, any slab fast path, and what finally frees the objects?
Start from `struct kfree_rcu_cpu`.

# Rules for updaters

## rcu.remove-before-reclaim: Unlink before reclaim

- section: Update-side rules
- relevance: 5 - use after free that no tool reports
- words: 120

In what order must an updater unlink an object from an RCU-protected
structure, start the grace period and free the object? What usage is unsafe,
and what that looks similar is correct, for example a callback that does more
than free? Name in-tree code that shows the correct form.

## rcu.existence-vs-liveness: Existence is not liveness

- section: Update-side rules
- relevance: 5 - the commonest misuse of a lookup under RCU
- words: 110

What does finding an object under `rcu_read_lock()` guarantee about it and
what does it not, and what must a reader do to keep using the object after
`rcu_read_unlock()`? What usage of a reference count there is unsafe and what
is correct? Start from `Documentation/RCU/rcuref.rst`.

## rcu.typesafe-slab: Type-safe slab caches

- section: Update-side rules
- relevance: 4 - the object can be reused under the reader
- words: 100

What does `SLAB_TYPESAFE_BY_RCU` guarantee and not guarantee about an object a
reader holds a pointer to, what must a lookup do after finding such an object,
and what are the rules for the cache's constructor and for initialising
objects on allocation?

## rcu.flavor-matching: Matching readers and updaters

- section: Update-side rules
- relevance: 5 - waiting with the wrong flavour waits for nothing
- words: 120

Which grace-period primitive matches which kind of reader: RCU, SRCU, Tasks,
Tasks Rude, Tasks Trace? What mixture of reader and updater flavours is unsafe,
and what that looks like a mismatch is correct, for example readers that only
disable preemption, or an object read under two flavours? Name in-tree code.

## rcu.long-loops-qs: Quiescent states in long loops

- section: Update-side rules
- relevance: 3 - stalls come from loops that never report one
- words: 80

What must a long-running loop in kernel code do so that RCU and Tasks RCU grace
periods can complete on a kernel without full preemption, and which helpers
exist for softirq and kthread loops? Start from `cond_resched_tasks_rcu_qs()`
and `rcu_softirq_qs_periodic()`.

# Other flavours

## rcu.srcu-basics: SRCU domains

- section: SRCU
- relevance: 4 - the API differs from RCU in every call
- words: 100

How is an SRCU domain defined or initialised and destroyed, what do the read
lock and unlock take and return, which updater primitives exist, and what does
SRCU let a reader do that RCU does not? Start from `include/linux/srcu.h`.

## rcu.srcu-reader-flavors: SRCU reader kinds

- section: SRCU
- relevance: 4 - kinds cannot be mixed on one domain
- words: 110

Which kinds of SRCU reader does this tree have besides `srcu_read_lock()`, how
is a domain declared for each, what happens if kinds are mixed on one domain,
and which kinds may be released from a different context than they were
acquired in? Start from `srcu_check_read_flavor()`.

## rcu.srcu-usage: SRCU deadlocks and cleanup

- section: SRCU
- relevance: 4 - sleeping readers make new deadlocks possible
- words: 100

What usage inside or around an SRCU reader deadlocks or leaks: waiting for the
same domain, holding a lock the updater needs, cleaning up a domain with
callbacks pending? What that looks similar is correct?

## rcu.tasks-flavors: Tasks flavours

- section: Tasks RCU
- relevance: 4 - three flavours with different readers and APIs
- words: 130

For Tasks RCU, Tasks Rude RCU and Tasks Trace RCU: what counts as a reader,
which update-side functions exist for each (say if one is missing or static),
which Kconfig option builds it and what the functions become when it is off,
and who uses each. A table.

## rcu.tasks-trace-implementation: Tasks Trace implementation

- section: Tasks RCU
- relevance: 4 - where the code is and what it costs has changed
- words: 100

How is Tasks Trace RCU implemented in this tree: where are
`rcu_read_lock_trace()` and `synchronize_rcu_tasks_trace()` defined, what
grace-period machinery do they use, what per-task state does a reader keep,
and is there a second reader API that returns a cookie?

# The implementation

## rcu.tree-structures: Core structures

- section: Tree RCU internals
- relevance: 3 - the map of the implementation
- words: 110

What are `struct rcu_state`, `struct rcu_node` and `struct rcu_data`, how do
they form the combining tree, which fields record which CPUs still owe a
quiescent state, and which lock protects them? Start from `kernel/rcu/tree.h`.

## rcu.gp-sequence: Grace-period sequence numbers

- section: Tree RCU internals
- relevance: 3 - every comparison of two of them depends on the encoding
- words: 90

How is a grace-period sequence number encoded, which helpers take a snapshot
and test for completion, how is wrap handled, and which structure carries the
normal and expedited numbers together? Start from `rcu_seq_snap()` in
`kernel/rcu/rcu.h`.

## rcu.gp-kthread: Grace-period kthread

- section: Tree RCU internals
- relevance: 3 - a change has to go in the right phase
- words: 110

List the phases the grace-period kthread goes through for one grace period and
the function for each, how quiescent states are reported up the tree, and what
forces a quiescent state from a CPU that has not reported. Start from
`rcu_gp_kthread()`.

## rcu.node-locking: Locking the rcu_node tree

- section: Tree RCU internals
- relevance: 4 - the wrappers carry the ordering guarantee
- words: 100

How must the `rcu_node` lock be acquired and released, why is the field
private, what ordering do the wrappers add, and what is the lock order between
the rcu_node lock, the offload locks and scheduler locks? Start from
`raw_spin_lock_rcu_node()`.

## rcu.callback-lists: Segmented callback list

- section: Tree RCU internals
- relevance: 3 - the counts and segment pointers must agree
- words: 100

How does the segmented callback list order callbacks by grace period: what are
the segments, what do accelerate and advance do, what is recorded per segment,
and which counts must stay consistent? Start from
`include/linux/rcu_segcblist.h`.

## rcu.preemptible-readers: Preempted readers

- section: Tree RCU internals
- relevance: 3 - the unlock slow path runs in awkward contexts
- words: 110

With preemptible RCU, what happens when a reader is preempted and when it
later unlocks: where is the task queued, what does the unlock slow path do,
when is the quiescent state deferred, and how does boosting work? Start from
`rcu_preempt_ctxt_queue()` and `rcu_read_unlock_special()`.

## rcu.eqs-tracking: Idle and user tracking

- section: Tree RCU internals
- relevance: 3 - the names have been changed wholesale
- words: 90

How does RCU know that a CPU is idle or in userspace and so need not be waited
for: which counter, where does it live, which functions snapshot and recheck
it, and what are these called in this tree? Start from
`rcu_watching_snap_save()`.

## rcu.expedited-internals: Expedited grace periods

- section: Tree RCU internals
- relevance: 3 - IPIs and workers, with their own stall checks
- words: 110

How does an expedited grace period work: how are concurrent requests combined,
which CPUs are interrupted and what does the handler do, what runs the work,
and how do normal and expedited grace periods interact? Start from
`synchronize_rcu_expedited()` and `rcu_exp_handler()`.

## rcu.nocb: Callback offloading

- section: Tree RCU internals
- relevance: 3 - a second queueing path for every callback
- words: 110

How does callback offloading work: which kthreads exist, what is the bypass
list for, which locks protect the offloaded lists, how do lazy callbacks fit
in, and can a CPU be switched at run time? Start from
`kernel/rcu/tree_nocb.h`.

## rcu.stall-warnings: Stall warnings

- section: Tree RCU internals
- relevance: 3 - what most people meet RCU through
- words: 100

What triggers an RCU CPU stall warning, which timeouts and parameters control
it, what does the report contain, and what are the usual causes? Start from
`check_cpu_stall()` and `Documentation/RCU/stallwarn.rst`.

## rcu.early-boot-hotplug: Early boot and CPU hotplug

- section: Tree RCU internals
- relevance: 2 - narrow, but every primitive has a boot-time special case
- words: 90

What do `call_rcu()` and `synchronize_rcu()` do before the scheduler and the
grace-period kthread exist, what are the stages of `rcu_scheduler_active`, and
what happens to the callbacks of a CPU that goes offline?

## rcu.torture-tests: Torture tests

- section: Changing RCU
- relevance: 4 - the only real test of a change
- words: 100

Which in-kernel test modules exercise RCU, how are they run from
`tools/testing/selftests/rcutorture/`, how does one test module cover the
different flavours, and what is the minimum a change under `kernel/rcu/` should
be run against?

## rcu.change-checklist: Changing the implementation

- section: Changing RCU
- relevance: 4 - a change touches more builds than the one compiled
- words: 100

What must a change to RCU's implementation keep working besides the code it
touches: the Tiny and Tree builds, preemptible and non-preemptible readers,
offloaded callbacks, PREEMPT_RT, the memory-ordering guarantees, tracepoints,
documentation and the hooks rcutorture uses?
