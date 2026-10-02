# What the locking measurement found

Three models were asked the 90 questions in `locking-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A and C (both
current; they assumed kernels from 6.12 to 7.0) and B (older, 6.10 to 6.13, and
wrong about fundamentals as well as names); which models they were does not
matter here. The hand-written guide was never checked against current sources,
so differences between it and the built guide are expected and are noted below.

## What all three readers got wrong

- **Disabling bottom halves on PREEMPT_RT.** All three said
  `local_bh_disable()` takes the per-CPU `softirq_ctrl.lock` there, so two
  BH-off sections on one CPU exclude each other. `__local_bh_disable_ip()`
  takes that lock only under `CONFIG_PREEMPT_RT_NEEDS_BH_LOCK`, which has no
  default and so is off; otherwise it does `migrate_disable()` and
  `rcu_read_lock()` and excludes nothing. This is what
  `local_lock_nested_bh()` is for. The same mistake came back in three
  questions per reader.
- **Deciding at run time whether a lock may be taken.** All were weak. The
  tree's helper is `can_spin_trylock()` in `mm/internal.h`; on PREEMPT_RT
  `spin_trylock()` is unsafe in hard interrupt and NMI context while
  `local_trylock()` already fails there by itself; `preemptible()` is always 0
  without `CONFIG_PREEMPT_COUNT` and is true while an RT `spinlock_t` is held.
- **Wait type override maps.** None could say what they are set to or who uses
  them: most are `LD_WAIT_CONFIG`, `tick_freeze_map` alone is `LD_WAIT_SLEEP`,
  and `sched_submit_work()` and `rv_react()` use one to tighten the check.
- **The compiler context analysis.** It needs Clang 23 (two said 22, one did
  not know it exists and described sparse). `__must_hold()`, `__acquires()`
  and the rest are defined in `include/linux/compiler-context-analysis.h` and
  expand to nothing under sparse; the sparse context tracking is not used
  anywhere. `lockdep_assert_held()` expands to `__assume_ctx_lock()` even
  with lockdep off.
- **Raw lock nesting checks.** `CONFIG_PROVE_RAW_LOCK_NESTING` is
  `default y if ARCH_SUPPORTS_RT` and cannot be deselected there; trylocks and
  `LD_WAIT_INV` classes (the per-CPU rw_semaphore is one) are skipped.
- **Raw spinlocks.** All said the documentation requires short sections. It
  says where the type belongs and allows it for tiny sections; it does forbid
  allocating under one even with `GFP_ATOMIC`.
- **Mutex and rwsem behaviour.** `struct mutex` has `first_waiter`, not a
  wait list; its fast paths exist only without `CONFIG_DEBUG_LOCK_ALLOC`;
  `CONFIG_DEBUG_MUTEXES` checks magic, owner and waiters and the other rules
  come from lockdep options. A reader arriving behind a waiting writer still
  steals an rwsem unless the handoff bit is set.
- **Self-rearming timers and work.** All said a synchronous cancel does not
  cope; `timer_delete_sync()` and `cancel_work_sync()` do. The hazard is a
  rearm from another path. del_timer_sync() is gone (reader B used it).
- **Guard class names**: every reader missed some of `mutex_kill`,
  `rwsem_write_kill`, `raw_spinlock_bh`, the `srcu_fast` family and
  `percpu_read`/`percpu_write` (reader B invented rwlock and percpu names).
- **RCU details**: `kfree_rcu_nolock()` exists and no reader knew; there is no
  one-argument `kfree_rcu()`; the SRCU lite readers are gone and the
  `_fast_updown` flavour was missed; the polled `_full` interface takes
  `struct rcu_gp_seq`; a lookup in a `SLAB_TYPESAFE_BY_RCU` cache needs
  `refcount_inc_not_zero_acquire()`; a plain increment under RCU is not always
  wrong (`Documentation/RCU/rcuref.rst`, listing C).
- **Sequence counters**: `__read_seqcount_begin()` is an acquire load;
  `scoped_seqlock_read()` and `raw_seqcount_try_begin()` exist.
- **Shared builds**: `kernel/locking/rwsem.c` also includes `rtmutex.c`.

## What only some got wrong

- Readers A and C: `rwlock_t` on PREEMPT_RT is "reader biased" (new readers
  block once a writer holds the rtmutex); the examples they offered for local
  locks sat in mm/swap.c, which this tree no longer has (`mm/folio.c`).
- Readers A and B: what a lockdep subclass of 8 or more does (it turns lockdep
  off; reader A said it only warns); `IRQF_ONESHOT` and `IRQF_PERCPU` handlers
  were left out of those that stay unthreaded under forced threading.
- Reader B, besides the above: PREEMPT_RT source files that do not exist; a
  `spinlock_t` on RT "does not enter an RCU read-side section" (it takes
  `rcu_read_lock()`); `raw_spinlock_t` is `LD_WAIT_FREE`; a `local_lock_t` may
  not nest inside a `spinlock_t`; wait-die described backwards and wound-wait
  said to be absent; `mutex_trylock()` allowed from interrupt context;
  `refcount_inc_not_zero()` has acquire ordering; `READ_ONCE()` is not enough
  for a reader of a published pointer; a `goto` out of a guard's scope skips
  the unlock; `preempt_disable()` does not hold off any CPU's offlining.

## What the readers already knew

Readers A and C: the lock categories, which variant excludes which context,
the `_irq` and `_irqsave` choice, what each lock becomes on PREEMPT_RT and what
an RT `spin_lock()` does, ordering of atomic operations and the barrier
primitives, freeing after an RCU update, the dereference variants, reference
count ordering, lockdep's data and interrupt states, lock pinning, and the
guard macros themselves.

## Where the hand-written guide is stale

- Its "sparse annotations" section: the keywords are compiler context analysis
  now and sparse sees empty macros.
- `lockdep_pin_lock()` returns a cookie that the unpin takes; the pin count is
  that cookie added, not a counter incremented.
- `CONFIG_PROVE_RAW_LOCK_NESTING` "default y" holds only where RT is
  supported, and "any violation is a bug" leaves out trylocks and the
  override.
- Its table says `spin_lock_bh()` excludes softirqs; on PREEMPT_RT that
  depends on `CONFIG_PREEMPT_RT_NEEDS_BH_LOCK`.
- "Guard with `!preemptible()`": see above; the tree's RT `local_trylock()`
  itself tests `in_nmi()` and `in_hardirq()`.
- "Direct kfree() is always a bug" after `rcu_assign_pointer()`: not when the
  object was never reachable by readers (`rhashtable_rehash_alloc()`).
- "None of preemption, migration or IRQ disable prevent CPU hotplug": the
  last step of any offline runs a stopper on every online CPU, and
  `migrate_disable()` holds the current CPU at `sched_cpu_wait_empty()`,
  though teardown callbacks of later states run first.
- Reclaim lockdep "via `__GFP_FS`, `__GFP_IO`": only `__GFP_FS` with direct
  reclaim takes the map.
- It has no map of the files, and nothing on guards, local trylocks or the RT
  bottom-half change. About two fifths of it is a method for tracing races,
  which a build from a tree does not reproduce; the facts that method rests on
  are kept as the lifetime questions.

## What was left out of the build set

- RCU beyond what locks imply (dereference variants, `kfree_rcu()` forms,
  grace-period interface, SRCU, lists, type-safe slabs, sleeping in readers):
  the RCU guide has its own questions.
- How the guard macros work: the cleanup guide covers them. The lock guard
  class names and the hazards specific to a held lock are kept.
- What readers A and C answer and reader B could look up in the named
  documents: lock categories, `_irq` variants, lockdep's model and interrupt
  states, barrier and atomic ordering, bit operations, publishing primitives.
- Primitives with few users or their own design document: wound/wait mutexes,
  rtmutex chains, per-CPU rw_semaphore, completions, queued spinlock layout,
  lock keys, sleep-check hooks, NMI rules, per-CPU accessors.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 156 corrections, 27% rewritten on average
reader B: 243 corrections, 71% rewritten on average
reader C: 162 corrections, 18% rewritten on average

question                              reader A      reader B      reader C   verdict
locking.core-files                     9% ( 3)      21% ( 3)       7% ( 2)   middling
locking.docs                           5% ( 1)      38% ( 2)       3% ( 1)   middling
locking.debug-configs                 19% ( 4)      59% ( 3)       5% ( 1)   weak: reader B
locking.tests                         24% ( 1)      81% ( 1)      31% ( 1)   weak: reader B
locking.lock-categories                0% ( 0)      82% ( 2)       0% ( 0)   weak: reader B
locking.context-table                  0% ( 0)      57% ( 4)      20% ( 2)   weak: reader B
locking.irq-variant-choice             0% ( 0)      43% ( 1)      17% ( 1)   weak: reader B
locking.irq-shared-lock                0% ( 0)      71% ( 1)      19% ( 4)   weak: reader B
locking.nested-irq-masking            37% ( 1)      72% ( 1)      29% ( 3)   weak: reader B
locking.raw-spinlock-use              51% ( 2)      70% ( 1)      59% ( 3)   all weak
locking.rwlock-semantics              41% ( 2)      88% ( 2)      50% ( 4)   all weak
locking.mutex-rules                   56% ( 1)      68% ( 3)      10% ( 1)   weak: reader A, reader B
locking.mutex-unlock-lifetime         46% ( 1)      90% ( 1)      12% ( 1)   weak: reader A, reader B
locking.mutex-variants                32% ( 1)      54% ( 1)       0% ( 0)   weak: reader B
locking.mutex-internals               31% ( 1)      76% ( 1)       8% ( 1)   weak: reader B
locking.rwsem-semantics               31% ( 1)      86% ( 1)      21% ( 1)   weak: reader B
locking.percpu-rwsem                  37% ( 3)      74% ( 3)      24% ( 2)   weak: reader B
locking.completions                   46% ( 2)      72% ( 4)      25% ( 2)   weak: reader A, reader B
locking.rtmutex                       36% ( 2)      77% ( 3)      43% ( 2)   weak: reader B, reader C
locking.ww-mutex                      22% ( 1)      69% ( 4)       8% ( 1)   weak: reader B
locking.local-lock                    21% ( 1)      63% ( 5)      11% ( 1)   weak: reader B
locking.local-lock-scope-usage        78% ( 3)      88% ( 2)      16% ( 2)   weak: reader A, reader B
locking.local-trylock                 33% ( 1)      69% ( 2)      10% ( 2)   weak: reader B
locking.local-lock-nested-bh          39% ( 3)      80% ( 3)      11% ( 2)   weak: reader B
locking.rt-substitutions               0% ( 1)      42% ( 6)      10% ( 2)   weak: reader B
locking.rt-spinlock-semantics          1% ( 1)      77% ( 5)      18% ( 1)   weak: reader B
locking.rt-unsafe-usage               45% ( 3)      89% ( 3)      23% ( 4)   weak: reader A, reader B
locking.rt-hardirq-context            50% ( 2)      73% ( 4)      14% ( 1)   weak: reader A, reader B
locking.context-predicates            14% ( 1)      79% ( 3)       7% ( 2)   weak: reader B
locking.context-guard-usage           59% ( 3)      88% ( 2)      60% ( 5)   all weak
locking.lockdep-model                 24% ( 1)      76% ( 2)       0% ( 0)   weak: reader B
locking.lockdep-wait-types            37% ( 3)      89% ( 4)      12% ( 2)   weak: reader B
locking.nesting-table                 22% ( 1)      14% ( 1)      48% ( 2)   weak: reader C
locking.raw-nesting-config            39% ( 1)      86% ( 2)       5% ( 1)   weak: reader B
locking.wait-override                 61% ( 1)      92% ( 1)      67% ( 3)   all weak
locking.lockdep-irq-states             9% ( 0)      74% ( 1)      11% ( 1)   weak: reader B
locking.lockdep-subclasses            31% ( 2)      78% ( 3)       5% ( 3)   weak: reader B
locking.lockdep-keys                  57% ( 3)      86% ( 2)      12% ( 1)   weak: reader A, reader B
locking.lockdep-asserts               27% ( 3)      51% ( 2)      18% ( 4)   weak: reader B
locking.lockdep-pinning               15% ( 1)      83% ( 2)      13% ( 1)   weak: reader B
locking.lockdep-limits                17% ( 2)      67% ( 6)      22% ( 2)   weak: reader B
locking.sleep-checks                  39% ( 5)      71% ( 4)       9% ( 1)   weak: reader B
locking.reclaim-lockdep               15% ( 2)      80% ( 3)      15% ( 1)   weak: reader B
locking.context-analysis              12% ( 4)      83% ( 6)      10% ( 3)   weak: reader B
locking.annotation-keywords           24% ( 2)      74% ( 2)      16% ( 4)   weak: reader B
locking.context-analysis-escapes      33% ( 1)      91% ( 3)      22% ( 3)   weak: reader B
locking.guards                        12% ( 2)      73% ( 6)      24% ( 1)   weak: reader B
locking.guard-classes                 14% ( 1)      42% ( 5)      24% ( 3)   weak: reader B
locking.guard-usage                    9% ( 1)      73% ( 3)      33% ( 0)   weak: reader B
locking.rcu-readers                    8% ( 1)      87% ( 2)      40% ( 1)   weak: reader B, reader C
locking.rcu-implicit-readers          12% ( 1)      81% ( 3)       0% ( 0)   weak: reader B
locking.rcu-dereference-variants       7% ( 2)      53% ( 2)       1% ( 1)   weak: reader B
locking.rcu-sleeping                  18% ( 1)      77% ( 2)      58% ( 3)   weak: reader B, reader C
locking.rcu-lockdep                   18% ( 1)      78% ( 3)      43% ( 1)   weak: reader B, reader C
locking.rcu-update-usage               5% ( 0)      73% ( 2)       1% ( 1)   weak: reader B
locking.rcu-update-primitives          9% ( 0)      74% ( 4)       0% ( 0)   weak: reader B
locking.kfree-rcu-variants            46% ( 1)      83% ( 4)      30% ( 2)   weak: reader A, reader B
locking.rcu-grace-period-api          11% ( 1)      86% ( 3)       8% ( 2)   weak: reader B
locking.rcu-lookup-refcount           51% ( 2)      60% ( 3)      39% ( 3)   weak: reader A, reader B
locking.typesafe-by-rcu               49% ( 2)      74% ( 3)      34% ( 2)   weak: reader A, reader B
locking.rcu-list-api                  33% ( 3)      67% ( 3)      30% ( 1)   weak: reader B
locking.srcu                          31% ( 3)      50% ( 3)      10% ( 4)   weak: reader B
locking.srcu-flavours                 52% ( 5)      92% ( 4)      45% ( 4)   all weak
locking.refcount-types                14% ( 3)      68% ( 4)       7% ( 4)   weak: reader B
locking.refcount-ordering              8% ( 0)      69% ( 3)      12% ( 1)   weak: reader B
locking.preempt-migrate-irq           55% ( 4)      25% ( 2)      21% ( 1)   weak: reader A
locking.percpu-access                 22% ( 2)      54% ( 1)       4% ( 1)   weak: reader B
locking.cpu-hotplug-lock              12% ( 1)      75% ( 1)       5% ( 1)   weak: reader B
locking.percpu-teardown-usage         15% ( 1)      87% ( 1)      28% ( 1)   weak: reader B
locking.nmi-context                   29% ( 2)      67% ( 1)      27% ( 1)   weak: reader B
locking.barrier-kinds                  0% ( 0)      45% ( 4)       9% ( 2)   weak: reader B
locking.atomic-ordering                0% ( 0)      56% ( 1)       3% ( 1)   weak: reader B
locking.bitops-ordering               12% ( 1)      75% ( 1)       0% ( 0)   weak: reader B
locking.publish-usage                 29% ( 1)      84% ( 1)      11% ( 1)   weak: reader B
locking.lock-ordering-guarantees      30% ( 2)      80% ( 4)       3% ( 2)   weak: reader B
locking.marked-accesses               41% ( 3)      79% ( 3)      32% ( 2)   weak: reader A, reader B
locking.sleep-wake-ordering           50% ( 3)      71% ( 2)      16% ( 1)   weak: reader A, reader B
locking.seqcount-types                46% ( 3)      79% ( 4)      22% ( 3)   weak: reader A, reader B
locking.seqlock-reader-usage          20% ( 1)      81% ( 1)      25% ( 4)   weak: reader B
locking.seqlock-writer-usage          38% ( 1)      74% ( 4)      10% ( 2)   weak: reader B
locking.seqlock-reader-variants       39% ( 2)      87% ( 3)      31% ( 3)   weak: reader B
locking.object-pins                   25% ( 2)      86% ( 3)      21% ( 2)   weak: reader B
locking.lock-drop-reacquire           45% ( 1)      67% ( 2)       4% ( 1)   weak: reader A, reader B
locking.check-then-lock               17% ( 1)      68% ( 1)       0% ( 0)   weak: reader B
locking.deferred-work-teardown        34% ( 1)      58% ( 2)      16% ( 1)   weak: reader B
locking.lock-order-documentation      30% ( 2)      89% ( 2)      21% ( 2)   weak: reader B
locking.spinlock-layers               18% ( 3)      77% ( 6)      32% ( 3)   weak: reader B
locking.qspinlock                     32% ( 3)      71% ( 3)      25% ( 2)   weak: reader B
locking.rtmutex-shared-builds         48% ( 4)      93% ( 5)      15% ( 3)   weak: reader A, reader B
locking.new-primitive-checklist       43% ( 4)      85% ( 2)      28% ( 1)   weak: reader A, reader B
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `locking.raw-spinlock-use`, `locking.rcu-sleeping`, `locking.srcu-flavours`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `locking.lock-categories`, `locking.lockdep-irq-states`, `locking.guards`, `locking.rcu-dereference-variants`, `locking.rcu-update-usage`, `locking.kfree-rcu-variants`, `locking.rcu-grace-period-api`, `locking.typesafe-by-rcu`, `locking.rcu-list-api`, `locking.srcu`, `locking.atomic-ordering`.
Put back because a guide has to say what each main structure is before anything else: `locking.lockdep-model`.

## Questions reorganised

The subjects are kept, less the two RCU parts: finding your way (2 questions), contexts (8), kinds of
lock and nesting (6), PREEMPT_RT and local locks (8), sleeping and reader-writer locks (4), lockdep (8),
guards and annotations (5), reference counts and lifetime (7), ordering (4), sequence counters (4), the
lock implementations (4); 73 questions before, 62 after. Left to the RCU guide, which already asked them:
`locking.rcu-sleeping`, `.rcu-dereference-variants`, `.srcu`, `.srcu-flavours`, `.rcu-update-usage`,
`.kfree-rcu-variants`, `.rcu-grace-period-api`, `.typesafe-by-rcu`; `locking.rcu-list-api` became
`rcu.list-usage`. `locking.rcu-readers` stays, narrowed to what locks and disabled preemption imply for
RCU. Dropped as inventories: `locking.debug-configs`, `locking.tests`. The rest were only reworded.
