# What the rcu measurement found

Three models were asked the 49 questions in `rcu-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels up to 7.0), reader A a few releases behind it, and reader B
older again, with whole mechanisms out of date. The hand-written guide was
never checked against current sources, so differences between it and the built
guide are expected and are noted near the end.

RCU is a subject all three know well in concept. What they get wrong is almost
all of one kind: names, types and whole mechanisms that moved in the last few
releases, plus a handful of absolutes.

## What all three readers got wrong

- **The full-state polled cookie** is `struct rcu_gp_seq` with fields `norm`
  and `exp`. All three called it struct rcu_gp_oldstate with rgos_norm and
  rgos_exp, which is nowhere in the tree. The same type is now what
  `rcu_segcblist.gp_seq[]` holds, and `rcu_segcblist_advance()` takes no
  sequence argument: it polls each segment, so either a normal or an expedited
  grace period completes it.
- **kfree_rcu().** The two-argument forms cast the named field to
  `struct kvfree_rcu_head *`, so that type is accepted as well as
  `struct rcu_head`. `kfree_rcu_nolock()` exists, works in any context and
  needs a real `struct kvfree_rcu_head` field. One reader hedged on it, one
  left it out and one said it did not know. The offset limit of 4096 is there
  so the start of a large or vmalloc object can be found by aligning down; two
  readers gave other reasons.
- **Locks under `kvfree_call_rcu()`.** None described the slab-sheaf fast
  path correctly: `__kfree_rcu_sheaf()` takes a `local_trylock()` and can take
  a `spinlock_t`, is skipped on PREEMPT_RT, and is made acceptable to lockdep
  with `DEFINE_WAIT_OVERRIDE_MAP(kfree_rcu_sheaf_map, LD_WAIT_CONFIG)`.
- **SRCU reader kinds.** The kinds are normal, NMI-safe, fast and
  fast-updown. Every reader either left out fast-updown or put
  `srcu_down_read_fast()` with the fast kind; the code checks it against
  `SRCU_READ_FLAVOR_FAST_UPDOWN`. All missed the `srcu_fast_updown` and
  `rcu_tasks_trace` scope guards. The mixing check only runs under
  `CONFIG_PROVE_RCU`.
- **Initialising an rcu_head.** `init_rcu_head()` is for statically allocated
  heads and heap heads need nothing; a double `call_rcu()` with debug objects
  prints "Double-freed CB" and leaks the callback, it does not WARN.
- **Reader-held predicates.** Only the `rcu_read_lock*_held()` family returns 0
  when RCU is not watching or the CPU is offline; `srcu_read_lock_held()` does
  not. Without `CONFIG_DEBUG_LOCK_ALLOC` the sched and any forms return
  `!preemptible()`, not 1.
- **Lock order around the rcu_node lock.** All three asserted an order against
  the runqueue and `pi_lock` that the code does not have.
- Smaller things: the lazy flush variable is `jiffies_lazy_flush` (two readers
  said jiffies_till_flush); the default rcutorture scenarios are
  `configs/rcu/CFLIST`, not a TREE01 to TREE10 list;
  `Documentation/RCU/rcu_dereference.rst` covers data dependencies as well as
  address dependencies.

## What only some readers got wrong

Reader B, and nobody else:

- kfree_rcu() batching is in `kernel/rcu/tree.c` (it is in
  `mm/slab_common.c`), a one-argument `kvfree_rcu(ptr)` exists (only the
  `_mightsleep` forms are head-less), and a kfree_rcu() user at module unload
  needs `rcu_barrier()` (it needs `kvfree_rcu_barrier()`).
- Tasks Trace RCU has its own grace-period kthread with IPIs. In this tree it
  is a set of inline wrappers in `include/linux/rcupdate_trace.h` around the
  SRCU-fast domain `rcu_tasks_trace_srcu_struct`, with a second,
  cookie-returning reader `rcu_read_lock_tasks_trace()`.
- `preempt_disable()` is an RCU reader only when RCU is not preemptible. It is
  a reader on every build. This one would change a verdict.
- Laziness of `call_rcu()` applies on idle CPUs. It applies only on offloaded
  CPUs.
- A plain increment of a reference count under `rcu_read_lock()` is always
  unsafe. `Documentation/RCU/rcuref.rst` has the case where it is correct.
- Names that are gone: rcu_idle_enter(), rcu_implicit_dynticks_qs(),
  call_rcu_flush(), srcu_read_lock_lite(), CONFIG_SPARSE_RCU_POINTER.
- There is no Tiny SRCU (there is), and the early-boot shortcut in
  `synchronize_rcu()` lasts until the scheduler is fully running (it lasts only
  while `rcu_scheduler_active` is `RCU_SCHEDULER_INACTIVE`).

Readers A and B:

- rcu_barrier_tasks_rude() exists. It does not, and `call_rcu_tasks_rude()` is
  static.
- `CONFIG_PREEMPT_RCU` follows `CONFIG_PREEMPTION`. It defaults on with
  `PREEMPT`, `PREEMPT_RT` or `PREEMPT_DYNAMIC`, so a lazy-preemption kernel
  without dynamic preemption has non-preemptible RCU.
- With Tasks Trace RCU configured out the reader calls become no-ops. They
  become `BUG()` stubs.
- SRCU-lite still exists; reader A also had `srcu_read_lock_fast()` as usable
  where RCU is not watching, which is the opposite of what it checks.
- The any-reader load is `rcu_dereference_all()`; reader A gave
  `rcu_dereference_raw_check()` and reader B left the form out.

Readers A and C both described how BPF waits for two flavours with names that
are gone (rcu_trace_implies_rcu_gp(), bpf_map_free_mult_rcu_gp()). Since Tasks
Trace became SRCU-fast its grace period implies an RCU one, and
`bpf_map_put()` relies on that with a single `call_rcu_tasks_trace()`.

## What the readers already knew

Where the files and headers are and which document covers what (apart from
reader B's kfree_rcu() location); what a reader may and may not do; that
regions with preemption, softirqs or interrupts disabled are readers (A and
C); the pointer load and publish primitives; how removed list entries are left;
unlink before reclaim; existence is not liveness; type-safe slab caches; the
shape of the grace-period kthread; stall warnings. These are dropped from the
build set or shrunk to the point a reader missed.

## Where the hand-written guide is stale

- Its section on the calling context of `kvfree_call_rcu()` says that adding a
  `spinlock_t`, `local_lock` or `local_trylock` there draws a lockdep "Invalid
  wait context" report and that a check of `CONFIG_PREEMPT_RT` does not help.
  This tree does exactly that in `__kfree_rcu_sheaf()`, behind a
  `!IS_ENABLED(CONFIG_PREEMPT_RT)` test, and keeps lockdep quiet with a
  wait-type override map. The rule is missing that precondition. It also says
  `CONFIG_PROVE_RAW_LOCK_NESTING` defaults to y; it is `default y if
  ARCH_SUPPORTS_RT`.
- It calls kfree_rcu() a shorthand for `call_rcu()` with a callback that calls
  `kfree()`. With `CONFIG_KVFREE_RCU_BATCHED` no `call_rcu()` is made per
  object, the field may be a `struct kvfree_rcu_head`, and there is a
  `kfree_rcu_nolock()` form it does not know about.
- Its table of variants has no Tasks Rude row and presents Tasks Trace as a
  flavour of its own; it is now SRCU underneath.
- It gives `rcu_barrier()` as what module unload needs. That does not cover
  objects handed to kfree_rcu().
- It says `rcu_assign_pointer()` is `smp_store_release()`. A compile-time
  constant NULL is stored with `WRITE_ONCE()`.
- Correct and kept as questions: unlink before reclaim, and that INIT_RCU_HEAD
  is gone (the tree has no such name).

## Left out of the build set

The hand-written guide is 558 words, which is under the 600-word floor for a
built guide, so the build set is sized to 600 words (480 to 720) with no
question budgeted under 40. It holds 11 of the 49 questions with 535 words of
budget, chosen by importance to someone reviewing a patch that uses RCU. A
first cut held 13 at 25 to 45 words each, and its answers came out as
fragments that meant nothing without the question beside them; two questions
gave up their room so that the rest could be written as sentences. The table
of source files went because all three readers already knew it, and its one
surprise, that the batching behind kfree_rcu() is in `mm/slab_common.c`, is
carried by the question on locks under `kvfree_call_rcu()`. The polled
grace-period API went although every reader named a cookie type that is gone,
because a patch that uses the old name does not compile.

Left out although a reader got them wrong: everything under "Tree RCU
internals" (structures, sequence numbers, kthread, node locking, callback
lists, preempted readers, idle tracking, expedited, offloading, stalls, boot):
a patch to `kernel/rcu/` needs the source, not sixty words. Also left out: the
Kconfig selection of preemptible RCU, initialising an rcu_head, the list
traversal lockdep argument, scope guards, dependency ordering (the document is
the authority and the readers know to go there), SRCU basics and deadlocks,
the Tasks flavours table (what matters from it is carried by the questions on
Tasks Trace, on barriers and on matching flavours), and the torture tests.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 112 corrections, 30% rewritten on average
reader B: 141 corrections, 72% rewritten on average
reader C: 103 corrections, 19% rewritten on average

question                            reader A      reader B      reader C
rcu.core-files                      13% ( 3)      10% ( 3)       7% ( 1)
rcu.headers                          4% ( 1)       1% ( 1)       0% ( 0)
rcu.docs                             0% ( 0)      22% ( 0)      10% ( 1)
rcu.build-flavors                   33% ( 1)      86% ( 3)      18% ( 1)
rcu.reader-rules                    15% ( 2)      75% ( 2)      10% ( 1)
rcu.implicit-readers                 7% ( 1)      74% ( 1)       4% ( 1)
rcu.reader-guards                   68% ( 2)      84% ( 1)      18% ( 3)
rcu.not-watching                     3% ( 1)      82% ( 1)      16% ( 3)
rcu.lockdep-helpers                 27% ( 1)      70% ( 1)      19% ( 3)
rcu.dereference-variants             9% ( 2)      55% ( 3)      15% ( 2)
rcu.dependency-ordering             59% ( 3)      87% ( 3)      44% ( 3)
rcu.assign-pointer                  22% ( 1)      66% ( 3)       2% ( 1)
rcu.sparse-annotations              35% ( 1)      92% ( 2)      15% ( 1)
rcu.list-helpers                    22% ( 1)      56% ( 3)       8% ( 0)
rcu.list-traversal-checks           28% ( 3)      82% ( 4)      16% ( 1)
rcu.nulls-lists                      8% ( 0)      60% ( 1)      35% ( 2)
rcu.gp-wait-api                     19% ( 4)      84% ( 8)      16% ( 6)
rcu.lazy-callbacks                  13% ( 2)      81% ( 1)      19% ( 3)
rcu.callback-context                54% ( 3)      70% ( 1)      40% ( 3)
rcu.rcu-barrier                     14% ( 4)      79% ( 2)      10% ( 1)
rcu.polled-gp                       22% ( 3)      62% ( 3)      22% ( 3)
rcu.rcu-head-init                   41% ( 2)      72% ( 3)      28% ( 2)
rcu.memory-ordering                 65% ( 2)      75% ( 3)      16% ( 2)
rcu.kfree-rcu-forms                 59% ( 5)      82% ( 8)      24% ( 4)
rcu.kfree-rcu-context               52% ( 4)      87% ( 2)      39% ( 2)
rcu.kfree-rcu-internals             21% ( 3)      83% ( 3)      30% ( 2)
rcu.remove-before-reclaim           21% ( 2)      70% ( 4)      20% ( 2)
rcu.existence-vs-liveness           32% ( 1)      80% ( 2)      15% ( 1)
rcu.typesafe-slab                   18% ( 1)      80% ( 1)      12% ( 2)
rcu.flavor-matching                 15% ( 2)      67% ( 3)      23% ( 3)
rcu.long-loops-qs                   43% ( 4)      85% ( 1)      35% ( 2)
rcu.srcu-basics                     18% ( 2)      68% ( 7)      14% ( 3)
rcu.srcu-reader-flavors             83% ( 6)      95% ( 4)      30% ( 2)
rcu.srcu-usage                      24% ( 2)      70% ( 3)      54% ( 2)
rcu.tasks-flavors                   35% ( 7)      58% ( 5)      10% ( 4)
rcu.tasks-trace-implementation      66% ( 3)      85% ( 2)      16% ( 3)
rcu.tree-structures                 19% ( 2)      81% ( 3)      23% ( 3)
rcu.gp-sequence                     29% ( 2)      75% ( 3)      14% ( 2)
rcu.gp-kthread                      10% ( 1)      78% ( 3)      13% ( 1)
rcu.node-locking                    66% ( 2)      89% ( 3)      23% ( 2)
rcu.callback-lists                  41% ( 2)      89% ( 3)      19% ( 2)
rcu.preemptible-readers             31% ( 2)      86% ( 3)      20% ( 1)
rcu.eqs-tracking                    41% ( 1)      75% ( 4)       9% ( 2)
rcu.expedited-internals             41% ( 4)      83% ( 4)      44% ( 3)
rcu.nocb                            31% ( 3)      77% ( 6)      25% ( 2)
rcu.stall-warnings                  24% ( 1)      66% ( 2)       4% ( 1)
rcu.early-boot-hotplug              19% ( 2)      78% ( 3)      20% ( 2)
rcu.torture-tests                   28% ( 3)      80% ( 3)      16% ( 3)
rcu.change-checklist                40% ( 2)      46% ( 3)      24% ( 3)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `rcu.dependency-ordering`, `rcu.callback-context`, `rcu.srcu-usage`, `rcu.node-locking`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `rcu.build-flavors`, `rcu.reader-rules`, `rcu.not-watching`, `rcu.assign-pointer`, `rcu.list-helpers`, `rcu.gp-wait-api`, `rcu.existence-vs-liveness`, `rcu.typesafe-slab`, `rcu.tasks-flavors`, `rcu.torture-tests`.
Put back because a guide has to say what each main structure is before anything else: `rcu.srcu-basics`.

## Questions reorganised

Subjects now: read-side critical sections (5 questions), pointers and lists (5), grace periods and
callbacks (5), freeing after a grace period (5), SRCU (3), Tasks RCU (2), changing RCU (2); 28
questions before, 29 after, none merged or dropped. The locking build set had ten RCU questions, nine
of which duplicated these and are gone from it. `locking.rcu-list-api`, on ordinary list operations on
an RCU-traversed list, asked something this set did not and is here as `rcu.list-usage`. Clauses taken
over from the others: freeing at once with no grace period (`rcu.remove-before-reclaim`), the polled
interface and a callback wanted soon (`rcu.gp-wait-api`), nulls lists (`rcu.typesafe-slab`), what an
SRCU grace period costs (`rcu.srcu-basics`).
