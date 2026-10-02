# Questions: RCU Subsystem

- guide: rcu.md
- title: RCU Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/rcu-measurement.md` is the wider
set the readers were measured on and `catalogue/rcu-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## rcu.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Read-side critical sections

## rcu.build-flavors: PREEMPT_RCU and Tiny builds

- section: Read-side critical sections
- relevance: 4 - what a reader may do depends on which one is built

Which builds of RCU and of SRCU can this tree produce, and which guarantees to a user of the API
differ between them? Which configuration symbols select `CONFIG_PREEMPT_RCU`? Start from
`kernel/rcu/Kconfig`.

## rcu.reader-rules: Inside a read-side section

- section: Read-side critical sections
- relevance: 5 - the first thing checked in any RCU patch

What are the requirements for code between `rcu_read_lock()` and `rcu_read_unlock()`? How do they
change with `CONFIG_PREEMPT_RCU` and with `CONFIG_PREEMPT_RT`, and what catches a violation at run
time?

## rcu.implicit-readers: Implicit readers

- section: Read-side critical sections
- relevance: 5 - decides whether code with no rcu_read_lock() is a bug

Besides code between `rcu_read_lock()` and `rcu_read_unlock()`, which regions of code does
`synchronize_rcu()` wait for, and does that depend on `CONFIG_PREEMPT_RCU`?

## rcu.bh-sched-readers: BH and sched readers

- section: Read-side critical sections
- relevance: 5 - decides which call an updater must make for readers marked this way

What do `rcu_read_lock_bh()` and `rcu_read_lock_sched()` do beyond what `rcu_read_lock()` does,
and which grace-period primitive waits for the readers they mark?

## rcu.not-watching: RCU not watching

- section: Read-side critical sections
- relevance: 4 - a reader there protects nothing

In which execution contexts is RCU not watching, so that `rcu_read_lock()` protects nothing, how
does code test for that, and what must code that runs there do before it can use RCU? Start
from `rcu_is_watching()`.

## rcu.lockdep-helpers: rcu_read_lock_held family

- section: Read-side critical sections
- relevance: 4 - they do not mean the same thing without lockdep

What do `rcu_read_lock_held()` and the other predicates of its family return when lockdep is not
built in, when it has been switched off, and when RCU is not watching, and which of them differ
from the rest? What are the requirements for code that tests one of them outside
`RCU_LOCKDEP_WARN()` in order to assure safe usage? Start from `rcu_read_lock_held()` and
`RCU_LOCKDEP_WARN()`.

# Pointers and lists

## rcu.dereference-variants: Pointer load primitives

- section: Pointers and lists
- relevance: 5 - each form states who may call it

A table of the primitives that load an RCU-protected pointer, to choose between: for each, who may
call it and what it checks. Start from `rcu_dereference_check()`.

## rcu.dependency-ordering: Dependency ordering

- section: Pointers and lists
- relevance: 4 - the compiler can break it and no barrier is visible

What are the requirements for code that uses the pointer `rcu_dereference()` returns in order to
assure safe usage, that is, to keep the ordering between the load and later accesses through the
pointer? Start from `Documentation/RCU/rcu_dereference.rst`.

## rcu.assign-pointer: Publishing a pointer

- section: Pointers and lists
- relevance: 4 - the initialiser form is misused

What ordering does `rcu_assign_pointer()` provide, and is there a value it stores with none? What
are the requirements for using `RCU_INIT_POINTER()` in place of `rcu_assign_pointer()` in order to
assure safe usage? What does `rcu_replace_pointer()` require of its caller?

## rcu.list-helpers: Removed list entries

- section: Pointers and lists
- relevance: 4 - what a reader standing on the entry sees

In what state do `list_del_rcu()` and `hlist_del_init_rcu()` leave the entry they remove, and why?
What does that state allow the caller to do with the entry afterwards, and what does it guarantee
to a reader that is standing on the entry?

## rcu.list-usage: Ordinary list operations

- section: Pointers and lists
- relevance: 4 - which list calls are safe against concurrent readers is not obvious from the names

What are the requirements for calling the list operations of `include/linux/list.h` on a list that
readers traverse under RCU, in order to assure safe usage? Start from `include/linux/rculist.h`.

# Grace periods and callbacks

## rcu.gp-wait-api: Waiting for a grace period

- section: Grace periods and callbacks
- relevance: 4 - the calling context differs for each

A table of the ways to wait for or follow an RCU grace period, to choose between: from which
contexts each may be called and what it costs. Then what the table cannot show: what
`synchronize_rcu()` does differently before the scheduler is running, and when expediting is
forced by boot parameter or sysfs.

## rcu.flavor-matching: Matching readers and updaters

- section: Grace periods and callbacks
- relevance: 5 - waiting with the wrong flavour waits for nothing

Which grace-period primitive matches each kind of reader that this tree has? What are the
requirements for pairing a kind of reader with a grace-period primitive in order to assure safe
usage? Name in-tree code that shows it.

## rcu.callback-context: Callback context

- section: Grace periods and callbacks
- relevance: 4 - decides what a callback may call

In what contexts can an RCU callback be invoked, what may a callback therefore not do, and may
it queue itself again? Start from `rcu_do_batch()`.

## rcu.lazy-callbacks: Lazy callbacks

- section: Grace periods and callbacks
- relevance: 4 - a callback can sit for seconds

Can `call_rcu()` delay starting a grace period: under which configuration, on which CPUs and for
how long? What should code use when it needs the callback soon? Start from `CONFIG_RCU_LAZY` in
`kernel/rcu/Kconfig`.

## rcu.rcu-barrier: Callback barriers

- section: Grace periods and callbacks
- relevance: 4 - a missing one is a crash at module unload

What does `rcu_barrier()` wait for and what does it not wait for, when is it required, and which
barrier, if any, goes with each of SRCU, the Tasks flavours and `kfree_rcu()`?

# Freeing after a grace period

## rcu.remove-before-reclaim: Unlink before reclaim

- section: Freeing after a grace period
- relevance: 5 - use after free that no tool reports

What are the requirements for the order in which an updater unlinks an object from an
RCU-protected structure, waits for a grace period and frees the object, in order to assure safe
usage? Name in-tree code that shows it.

## rcu.existence-vs-liveness: Reference counts after RCU lookup

- section: Freeing after a grace period
- relevance: 5 - the commonest misuse of a lookup under RCU

What does finding an object under `rcu_read_lock()` guarantee about it and what does it not, and
what must a reader do to keep using the object after `rcu_read_unlock()`? What are the
requirements for taking a reference count on such an object in order to assure safe usage? Start
from `Documentation/RCU/rcuref.rst`.

## rcu.typesafe-slab: Type-safe slab caches

- section: Freeing after a grace period
- relevance: 4 - the object can be reused under the reader

What does `SLAB_TYPESAFE_BY_RCU` guarantee and not guarantee about an object a reader holds a
pointer to, and what must a lookup therefore do after finding one, about the object and, on a
hash chain, about the chain it ended on? What are the rules for the cache's constructor and for
initialising objects on allocation? Start from the comment at `SLAB_TYPESAFE_BY_RCU` in
`include/linux/slab.h` and `Documentation/RCU/rculist_nulls.rst`.

## rcu.kfree-rcu-forms: Forms of kfree_rcu

- section: Freeing after a grace period
- relevance: 5 - the forms, the field type and the contexts have all changed

A table of the forms of `kfree_rcu()` and `kvfree_rcu()` to choose between, including any
without a head and any for callers that cannot take locks: what each is handed and from which
contexts it may be called. Then what type the field named in the two-argument forms may have,
and what limits its offset and why. Start from `kvfree_rcu_arg_2()` in
`include/linux/rcupdate.h`.

## rcu.kfree-rcu-context: Locks under kvfree_call_rcu

- section: Freeing after a grace period
- relevance: 4 - decides which locks its implementation may take

From which contexts may `kvfree_call_rcu()` be called, and which locks may its caller hold? Which
kinds of lock may its implementation and callees therefore take? Start from `kvfree_call_rcu()` in
`mm/slab_common.c`.

## rcu.kfree-rcu-sheaf: Sheaf path and PREEMPT_RT

- section: Freeing after a grace period
- relevance: 4 - a lock taken on this path must be one that every caller's context allows

How does the path from `kvfree_call_rcu()` into `__kfree_rcu_sheaf()` deal with
`CONFIG_PREEMPT_RT`, and how does it deal with the wait-context check of lockdep?

# SRCU

## rcu.srcu-basics: SRCU domains

- section: SRCU
- relevance: 4 - the API differs from RCU in every call

What does an SRCU reader have to keep between `srcu_read_lock()` and `srcu_read_unlock()`, and
what may it do that an RCU reader may not? What does `cleanup_srcu_struct()` require of the
domain? Start from `include/linux/srcu.h`.

## rcu.srcu-reader-flavors: SRCU reader kinds

- section: SRCU
- relevance: 4 - kinds cannot be mixed on one domain

A table of the kinds of SRCU reader to choose between: what each is for, how the domain must be
declared for it, and whether it may be released from a different context than it was acquired
in. Then what happens when kinds are mixed on one domain, and under which configuration that is
checked. Start from `srcu_check_read_flavor()`.

## rcu.srcu-usage: SRCU deadlocks and cleanup

- section: SRCU
- relevance: 4 - sleeping readers make new deadlocks possible

What are the requirements for code inside an SRCU reader, and for a caller of `synchronize_srcu()`
or `cleanup_srcu_struct()`, in order to assure safe usage?

# Tasks RCU

## rcu.tasks-flavors: Tasks flavours

- section: Tasks RCU
- relevance: 4 - three flavours with different readers and APIs

A table of Tasks RCU, Tasks Rude RCU and Tasks Trace RCU, to choose between: what counts as a
reader and what each is used for. Then what the table cannot show: which update-side functions
each flavour offers to code outside `kernel/rcu/`, and what the reader calls become when a flavour
is configured out.

## rcu.tasks-trace-implementation: Tasks Trace implementation

- section: Tasks RCU
- relevance: 4 - where the code is and what it costs has changed

Where does Tasks Trace RCU live in this tree, and what is it built on? What does the end of a
Tasks Trace grace period guarantee about an RCU grace period? Start from `rcu_read_lock_trace()`.

## rcu.tasks-trace-readers: Tasks Trace reader interfaces

- section: Tasks RCU
- relevance: 4 - a lock call must be paired with the unlock call of the same interface

Which reader interfaces does Tasks Trace RCU offer, and what must a caller carry from the lock
call to the unlock call of each? Start from `rcu_read_lock_trace()`.

# RCU internals and testing

## rcu.node-locking: Locking the rcu_node tree

- section: RCU internals and testing
- relevance: 4 - the wrappers carry the ordering guarantee

What are the requirements for taking and releasing the lock of a `struct rcu_node` in order to
assure safe usage, and what ordering do the required calls add that a plain lock would not? What
order does the code keep between that lock, the offload locks and the scheduler's locks? Start
from `raw_spin_lock_rcu_node()`.

## rcu.torture-tests: Torture tests

- section: RCU internals and testing
- relevance: 4 - the only real test of a change

What is the minimum a change under `kernel/rcu/` should be run against, where is that list of
scenarios kept, and how is it run? Start from `tools/testing/selftests/rcutorture/`.

# Model gaps

## rcu.model-gaps: Other mistakes models make

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
