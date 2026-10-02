# What the workqueue measurement found

Three models were asked the 40 questions in `workqueue-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current and the
most accurate (it assumed kernels from 6.14 to 6.18), reader A close behind it
(6.12 to 6.17), and reader B older (6.9 to 6.12) and out of date on mechanisms
as well as names. The hand-written guide is one bullet of 20 words and was
never checked against current sources; what it says is looked at near the end.

Readers A and C know the hand-written guide's one topic well. Both describe the
current `__cancel_work_sync()` step by step (take a disable count, flush, drop
the count), say that `flush_work()` does not stop requeueing, and order a
teardown correctly (stop the sources, then cancel or disable, then free). What
all three get wrong is what has moved recently: the names of the system
workqueues, what `alloc_workqueue()` now demands of its flags, and what happens
at the edges (queueing on a workqueue that is being destroyed, enabling a
delayed item, flushing a system-wide workqueue).

## What all three readers got wrong

- **Queueing on a deprecated system workqueue warns.** `system_wq` and
  `system_unbound_wq` are created with `__WQ_DEPRECATED`, and `__queue_work()`
  does a `pr_warn_once()` naming the work function, then queues the item.
  Reader A did not know, reader C said the deprecation is only a header
  comment, reader B said nothing is deprecated. No reader listed
  `system_dfl_long_wq`.
- **Neither per-CPU nor unbound.** `__alloc_workqueue()` does a `WARN_ONCE()`
  and sets `WQ_PERCPU` when the flags have neither `WQ_PERCPU` nor
  `WQ_UNBOUND`, and a `WARN_ONCE()` and drops `WQ_PERCPU` when they have both.
  Readers A and C hedged or said there is no check; reader B said per-CPU is
  simply the default and that both cannot happen.
- **Queueing on a workqueue that is draining or being destroyed.** From outside
  the workqueue's own items, `__queue_work()` does a `WARN_ONCE()`, clears
  PENDING and drops the item, and `queue_work()` still returns true. Readers A
  and C said PENDING stays set, so that later calls return false; reader B said
  a drain accepts new work and a destroyed workqueue returns false.
- **Enabling a delayed item.** `enable_delayed_work()` only calls
  `enable_work()`; it does not touch the timer. All three said the delayed
  forms all act on the timer.
- **Flushing a system-wide workqueue.** The `flush_workqueue()` macro checks a
  fixed list that has `system_percpu_wq` and `system_dfl_wq` in it and neither
  `system_wq`, `system_unbound_wq` nor the BH workqueues, and at run time
  `__warn_flushing_systemwide_wq()` does `pr_warn()` and `dump_stack()` before
  the flush goes ahead. Readers A and C used `system_wq` as the example and
  thought the warning was compile time only; reader B had a `WARN_ON`.
- **The default affinity scope** is `WQ_AFFN_CACHE_SHARD`, a scope no reader
  listed. All three said `WQ_AFFN_CACHE`.
- **CPU hotplug.** `queue_work_on()` for an offline CPU runs the item on some
  other CPU, and `queue_delayed_work_on()` with a delay can leave the timer on
  the offline CPU until it returns. Reader A called it unspecified, reader C
  expected a warning that the code does not have, reader B said the work stays
  bound.
- **What is refused on an ordered workqueue.** `workqueue_set_max_active()` and
  `workqueue_set_min_active()` warn and return; `apply_workqueue_attrs()` and
  `WQ_SYSFS` are not refused. Readers A and C said they are; none named the
  second function.
- **Legacy macros.** `__WQ_LEGACY` is also tested by
  `current_is_workqueue_mem_reclaim()`, and `create_workqueue()` passes
  `WQ_PERCPU`. No reader had both.

## What two readers got wrong

- **`schedule_work()` uses `system_percpu_wq`** (A and B said `system_wq`).
- **`WQ_MAX_ACTIVE` is 2048 and the default 1024** (A said 512 and 256, B 512
  and 128). Both also said `Documentation/core-api/workqueue.rst` agrees with
  the comment on `alloc_workqueue()`. It does not: the document says the limit
  is per CPU even for an unbound workqueue, the comment and the code make it
  system wide, split over NUMA nodes with `min_active` as a floor.
- **`WQ_BH` may be combined with `WQ_PERCPU` as well as `WQ_HIGHPRI`**
  (`__WQ_BH_ALLOWS`); both system BH workqueues are. A and B said `WQ_HIGHPRI`
  only. Reader A also allowed `cancel_work_sync()` on a BH item from hard
  interrupt context; `__cancel_work_sync()` warns on that.
- **`cancel_work_sync()` on the `work` member of a delayed item** (A and B). It
  does not leave a stale timer, it spins: without `WORK_CANCEL_DELAYED`,
  `try_to_grab_pending()` returns -EAGAIN for as long as the timer is armed, and
  `work_grab_pending()` loops until it fires. `flush_work()` on the member does
  not see the timer at all.
- **The cancel path is exempt from `check_flush_dependency()`** (A and B left
  it out; `from_cancel` returns early).
- **Timer names** (A and B). del_timer_sync() and __init_timer() are gone; the
  tree has `timer_delete_sync()` and `__timer_init()`. `queue_rcu_work()` uses
  `call_rcu_hurry()`, and `flush_rcu_work()` runs `rcu_barrier()` only when the
  item is pending.
- **rcu_free_pwq()** (A and C) does not exist; `pwq_release_workfn()` frees
  with `kfree_rcu()`. Both also left `pool->cb_lock`, the `CONFIG_PREEMPT_RT`
  lock for cancelling BH work, out of the list of locks.
- **Where the test module is** (A and C did not know): `lib/test_workqueue.c`.

## What reader B got wrong as well

- The cancel mechanism. It described a loop that retries
  `try_to_grab_pending()` on -EAGAIN while the item runs. -EAGAIN only means
  that queueing is in progress on another CPU; the wait is the disable count
  and `__flush_work()`. It gave the return value as "pending or running"; it is
  true only if the item was pending.
- `cancel_work_sync()` stops a self-requeueing item "for good". It re-enables
  the item before it returns.
- `flush_work()` waits for the current execution only. It waits for the last
  queueing instance, pending or running, and warns and returns false for an
  item with no function.
- `disable_work()` nests "a handful" deep and returns true if it changed state.
  The count is 16 bits, and it returns whether the item was pending.
- There is no device-managed constructor. `devm_alloc_workqueue()` and
  `devm_alloc_ordered_workqueue()` exist.
- Calling `flush_work()` on a freezable item from a suspend or resume callback
  is safe. Those callbacks run while workqueues are frozen, so it is the unsafe
  case. `cancel_work_sync()` does not block there: it takes the item off the
  inactive list.
- A BH workqueue's `max_active` of 0 means 1. It must be 0 and becomes
  `INT_MAX`.
- The system workqueues `system_percpu_wq`, `system_dfl_wq` and
  `system_dfl_long_wq`, `WQ_PERCPU` and `__WQ_DEPRECATED` were all missing or
  in doubt, and `system_long_wq` was given as unbound. Internal flags
  WQ_DRAINING and WQ_DYING, and the mask WORK_STRUCT_WQ_DATA_MASK, do not
  exist.
- `cancel_delayed_work()` returns false for an item already on a worklist. It
  steals it and returns true.
- The scripts under `tools/workqueue/` use tracefs. They are drgn scripts that
  read the structures, so a change to a field name breaks them.

## What a reader said it did not recognise

Reader A did not know whether queueing on a deprecated workqueue warns, how the
neither-flag case is handled, or where the test module is. Reader B was unsure
whether `WQ_PERCPU` exists and what the Rust binding is called. Reader C was
unsure of the test module and of whether flushing a system-wide workqueue is
checked at run time.

## What the readers already knew

The teardown order and when `disable_work_sync()` is needed rather than
`cancel_work_sync()` (A and C without a correction); that `cancel_work()` and
`cancel_delayed_work()` do not wait for a running function; the mechanism of
`cancel_work_sync()` and the disable count in the off-queue data word (A and
C); that a work function may free its own item and that the core does not
dereference it afterwards (C; A with one correction); on-stack items and their
destroy calls; that initialising a live item corrupts the list; the
non-reentrancy conditions (C); `struct delayed_work`, its irqsafe timer and the
zero-delay shortcut (C); the lockdep annotations behind the flush deadlocks;
what `WQ_MEM_RECLAIM` provides; the files, apart from the types header (B) and
the test module.

## Where the hand-written guide is stale

`workqueue.md` says that once `queue_work()` is called, `flush_work()` and
"other workqueue shutdown methods" keep the work struct from being leaked on
shutdown. It names nothing that has gone, but as a rule it is too loose to
review against. `flush_work()` waits for the last queueing instance and does
nothing about the next one; `cancel_work_sync()` refuses queueing only while it
waits; only `disable_work_sync()` keeps later queueing out, and the guide
predates it. `destroy_workqueue()` drains what is queued but cannot see a
delayed item whose timer has not fired. And what goes wrong is not a leak: the
structure is freed while the item is pending or running. The built guide
spends its words on those distinctions and on the names that have changed.

## What was left out of the build set, and why

Eleven questions were kept, with the same text as in the measurement set, and
their budgets add up to 535 words. The guide is sized to 600 words, the floor
for a guide whose hand-written original is shorter, and no question is given
fewer than 40: a first build at half that size, with 20 to 35 words a question,
came out as fragments that meant nothing without the question beside them. With
readers A and C already right about most of the centre, the choice was by
importance: the names and flags every reader had wrong, the teardown guarantees
that reader B had wrong and that decide a verdict, and, with the room the larger
size gave, the two flag questions of relevance 5 that were next in line:
`wq.ordered`, where no reader had right which later changes are refused, and
`wq.mem-reclaim`, where two readers left out that the cancel path is exempt
from `check_flush_dependency()`. Three questions, `wq.system-wqs`, `wq.ordered`
and `wq.mem-reclaim`, had a clause reworded in both files after the
measurement, to ask for flag names in full and to stop presupposing that
something is refused or exempt; what they ask is the same.

- `wq.core-files`. Every reader names the two files that matter. What they
  missed (the types header, the test module) a reviewer of workqueue users does
  not need, and each answer in the built guide names the function to read, so
  there is no "where to look" part.
- `wq.flag-table`. The flags readers had wrong are covered where they bite:
  `WQ_PERCPU` by `wq.bound-or-unbound`, `__WQ_DEPRECATED` by `wq.system-wqs`. A
  table of all fourteen does not fit.
- `wq.bh`, `wq.freezable`, `wq.max-active`. Each had a real correction for two
  readers, listed above, and each would be the next to come back if the guide
  were allowed more words; none is about lifetime against teardown.
- `wq.teardown-order`, `wq.cancel-async`, `wq.onstack`, `wq.reinit`,
  `wq.wait-from-callback`: readers A and C answer them with no correction, or
  with one that changes no verdict.
- `wq.queue-return`: the one fact all readers had wrong is asked for again by
  `wq.destroy`.
- `wq.delayed-work`, `wq.mod-delayed`, `wq.rcu-work`: the corrections were
  timer and RCU function names, which a patch shows.
- `wq.structures`, `wq.work-data`, `wq.pending-bit`, `wq.locks`,
  `wq.non-reentrancy`, `wq.requeue-while-running`, `wq.context`,
  `wq.affinity-scopes`, `wq.hotplug`, `wq.legacy-create`, `wq.devm`,
  `wq.module-unload`, `wq.flush-workqueue`, `wq.debug-facilities`,
  `wq.change-checklist`: the implementation and its edges. Changes to
  `kernel/workqueue.c` itself are rare next to changes that use it, and the
  file's own comments are long and, where the checker looked, accurate (one
  exception: the comment above `set_work_data()` still names
  mark_work_canceling(), which is gone).

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 80 corrections, 27% rewritten on average
reader B: 98 corrections, 70% rewritten on average
reader C: 50 corrections, 14% rewritten on average

question                      reader A      reader B      reader C
wq.core-files                  6% ( 3)      22% ( 3)       5% ( 1)
wq.structures                 21% ( 1)      73% ( 2)       0% ( 0)
wq.work-data                  34% ( 1)      80% ( 1)       3% ( 1)
wq.pending-bit                39% ( 2)      70% ( 1)       6% ( 2)
wq.locks                      12% ( 1)      75% ( 1)      16% ( 3)
wq.queue-return               11% ( 2)      88% ( 4)      15% ( 2)
wq.requeue-while-running      28% ( 2)      64% ( 1)      12% ( 2)
wq.non-reentrancy             47% ( 1)      79% ( 1)       0% ( 0)
wq.self-requeue               16% ( 1)      62% ( 1)       0% ( 0)
wq.context                    19% ( 1)      67% ( 1)      16% ( 1)
wq.system-wqs                 44% ( 6)      53% ( 6)      49% ( 2)
wq.flag-table                 15% ( 5)      61% ( 1)       6% ( 1)
wq.bound-or-unbound           72% ( 1)      95% ( 1)      55% ( 1)
wq.max-active                 31% ( 3)      78% ( 4)       0% ( 0)
wq.mem-reclaim                29% ( 3)      76% ( 1)      15% ( 1)
wq.freezable                  37% ( 2)      68% ( 3)       8% ( 1)
wq.bh                         39% ( 2)      76% ( 3)       4% ( 1)
wq.ordered                    30% ( 3)      70% ( 3)      18% ( 1)
wq.legacy-create              40% ( 2)      80% ( 1)      27% ( 1)
wq.affinity-scopes            47% ( 2)      58% ( 2)      44% ( 2)
wq.flush-work                  0% ( 2)      66% ( 4)       6% ( 1)
wq.flush-workqueue            31% ( 3)      83% ( 3)      33% ( 3)
wq.cancel-async                9% ( 0)      70% ( 2)       5% ( 1)
wq.cancel-sync                 0% ( 3)      71% ( 4)       4% ( 1)
wq.disable                    10% ( 1)      78% ( 4)      10% ( 3)
wq.wait-from-callback         23% ( 1)      79% ( 3)       5% ( 1)
wq.delayed-work               12% ( 2)      60% ( 5)       0% ( 0)
wq.mod-delayed                17% ( 1)      57% ( 2)       6% ( 1)
wq.delayed-cancel-usage       43% ( 2)      69% ( 2)      26% ( 2)
wq.rcu-work                   48% ( 4)      74% ( 4)      22% ( 1)
wq.free-embedding             40% ( 1)      84% ( 4)       2% ( 1)
wq.teardown-order              0% ( 0)      60% ( 1)       0% ( 0)
wq.destroy                    29% ( 2)      83% ( 2)       4% ( 1)
wq.devm                       21% ( 1)      81% ( 1)       5% ( 1)
wq.onstack                    15% ( 1)      71% ( 1)       0% ( 0)
wq.reinit                     28% ( 1)      52% ( 1)       0% ( 0)
wq.module-unload              36% ( 3)      86% ( 1)      38% ( 1)
wq.hotplug                    55% ( 4)      78% ( 4)      54% ( 4)
wq.debug-facilities            5% ( 1)      43% ( 3)       7% ( 1)
wq.change-checklist           41% ( 3)      86% ( 6)      38% ( 4)
```

Several corrections counted against one question are about another answer in
the same reader's run (the checker reads the whole guide and notes
contradictions), so a count of two or three on an answer that was 0% rewritten,
as for reader A on `wq.cancel-sync`, means the answer was right and its
neighbours were not.

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `wq.module-unload`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `wq.work-data`, `wq.pending-bit`, `wq.queue-return`, `wq.requeue-while-running`, `wq.flag-table`, `wq.max-active`, `wq.freezable`, `wq.bh`, `wq.flush-workqueue`, `wq.cancel-async`, `wq.wait-from-callback`, `wq.delayed-work`, `wq.teardown-order`, `wq.reinit`.

## Questions reorganised

Subjects now: choosing a workqueue (8 questions), queueing (4), flush, cancel, disable (8),
lifetime against teardown (5); 28 questions before, 27 after. `wq.ordered` and `wq.mem-reclaim`
moved in beside the other flag questions and `wq.delayed-cancel-usage` beside the cancel ones.
`wq.work-data` was an inventory of the fields packed into the data word and is dropped; what a
canceller or flusher reads out of that word is now a clause of `wq.pending-bit`, and the disable
count is asked for by `wq.disable`. Reworded to stop asking how the code works inside:
`wq.cancel-sync` (no step by step), `wq.destroy` (no ordered list), `wq.delayed-work`,
`wq.disable`, `wq.ordered`; `wq.system-wqs` and `wq.flag-table` are tables of variants to choose.
