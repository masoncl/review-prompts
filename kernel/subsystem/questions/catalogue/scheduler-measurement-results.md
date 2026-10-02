# What the scheduler measurement found

Three models were asked the 68 questions in `scheduler-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against a
mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C. Reader C
is the most current (it answered for kernels up to 7.0), reader A is a few
releases behind it, and reader B is older still; which models they were does not
matter here. The hand-written guide was never checked against current sources,
so differences between it and the built guide are expected and are noted below.

## What all three readers got wrong

- **The BPF extensible class is a directory.** All three listed
  kernel/sched/ext.c and ext_idle.c and two said outright that no
  `kernel/sched/ext/` exists. The class is in `kernel/sched/ext/` (`ext.c`,
  `idle.c`, `sub.c`, `cid.c`, `arena.c`, `internal.h`, `types.h`), all included
  from `kernel/sched/build_policy.c`. All three also said sub-schedulers and
  cids do not exist; both do, sub-schedulers under `CONFIG_EXT_SUB_SCHED`.
- **The fair class queues tasks flat.** Every reader put a task's entity in its
  group's rbtree and had the pick walk down level by level. Here only task
  entities are queued, and only in `rq->cfs`; `__enqueue_entity()` warns
  otherwise. Group entities and group runqueues do accounting only. A task's
  weight across the levels is computed by `__calc_prop_weight()` and kept in
  `se->h_load`; group shares come from a static call with several modes.
- **`p->is_blocked`** was reported as not existing by all three. It is a field of
  `struct task_struct`, set in `try_to_block_task()`, cleared in
  `ttwu_do_wakeup()`, and tested by `__schedule()` and `ttwu_runnable()`.
- **Class callbacks.** All three listed a pick_next_task member. There is none;
  the callback is `pick_task(rq, rf)`. Readers A and B also left out
  `switching_from` and `get_prio`.
- **Realtime limits.** All gave 950000 us as the default realtime runtime. It is
  1000000, equal to the period, so nothing is throttled by default, and the
  throttling code is only built under `CONFIG_RT_GROUP_SCHED`. What protects
  lower classes is the deadline server, and none of the readers was sure that
  `rq->ext_server` exists beside `rq->fair_server`.
- **Runqueue virtual time.** The fields are `sum_w_vruntime`, `sum_weight`,
  `zero_vruntime` and `sum_shift`. Two readers used avg_vruntime and avg_load
  as field names, the third had the names and the wrong weights.
- **`vlag` and `vprot`** are separate fields. Two readers said they share a
  union; the third did not know `vprot`. All missed `max_slice` in the tree
  augmentation and gave the wrong lag clamp.
- **Names in the fair class.** There is no find_matching_se(), and
  `reweight_eevdf()` and `rescale_entity()` do what all three credit to
  `reweight_entity()`. Readers A and C also used check_preempt_wakeup_fair()
  for `wakeup_preempt_fair()`, dequeue_entities() for `__dequeue_task()`, and
  had slice protection set from set_next_entity(); it is set from
  `set_next_task_fair()`.
- **`CONFIG_SCHED_CACHE`**: two readers said it does not exist and the third
  guessed at what it does. It exists, default y, and affects load balancing
  only.
- **sched_ext kfunc contexts** are checked when the program is loaded, by
  `scx_kfunc_context_filter()`. All three described a run-time mask that is gone.
- **Bypass mode** uses per-CPU bypass dispatch queues. One reader said the local
  queues, one a single global queue. All three said tasks go to the fair class
  after any disable; a sub-scheduler's tasks go back to its parent.
- **Hotplug.** `sched_cpu_deactivate()` calls `dl_bw_deactivate()` first and
  returns before changing anything if it fails; there is no rollback.
  `sched_cpu_dying()` stops both deadline servers. Two readers said
  `dl_server_start()` returns early on an offline CPU; it warns.

## What only some readers got wrong

- Reader B said proxy execution is not in the tree, did not know
  `sched_change_begin()`, used the old `cfs_rq` counter names
  (nr_running, h_nr_running), described CFS bandwidth as dequeueing the group
  entity, put `fair_sched_class` below `ext_sched_class`, named
  scheduler_tick(), and had the hrtimer base lock outside the runqueue lock.
  Almost every answer of B's was more than two thirds rewritten.
- Reader A hedged on the sched_change pattern, said a throttled task's state is
  cleared on migration or class change (it is not), and said only frozen tasks
  are exempt from delayed dequeue.
- Readers A and C said `__schedule()` tests `task_is_blocked(next)`; it tests
  `next->is_blocked`. Both said an owner on another CPU deactivates the donor;
  `proxy_migrate_task()` moves the blocked task to the owner's CPU instead.
- Readers A and C gave the default deadline bandwidth as 95%; it follows the
  realtime sysctls and is 100%.

## What the readers already knew

The entry points for each job, the class order (A and C), the lock order and how
two runqueues are ordered (A and C), priority numbering (A and C), per-CPU
kthreads (A and C), the `cfs_rq` counters (A and C), how a dying CPU is emptied
(C), the `set_task_cpu()` rules (C), the sleep and wake ordering (C fully, A
mostly), and the core files apart from the extensible class.

## Where the hand-written guide is stale

- It says `vlag` doubles as `vprot` through a union. They are separate fields.
- It names __pick_eevdf(); the function is `pick_eevdf()`.
- It gives the realtime limit as 95% by default and tells the reader to check
  `sched_rt_runtime()`, which only exists under `CONFIG_RT_GROUP_SCHED`.
- Its admission formula counts CPUs, which holds only when all CPUs have full
  capacity. `__dl_overflow()` compares against the summed capacity of the root
  domain's active CPUs, and the deadline servers consume bandwidth too.
- It says `vruntime` must be normalised on migration. Lag is preserved instead.
- It says throttling must dequeue and unthrottling enqueue. Tasks are now
  stopped one by one on their way back to user space and wait on
  `throttled_limbo_list`.
- It says `p->on_rq`, the tree and `p->__state` must all agree. Delayed dequeue
  and proxy execution both keep a blocked task queued on purpose.
- It says `dl_server_start()` returns early on an offline CPU. It warns.
- It has nothing on the sched_change pattern, `rq->donor`, proxy execution, the
  flat fair hierarchy, `rq->ext_server`, or where the extensible class lives.

## What was left out of the build set, and why

The build set has 26 of the 68 questions. The hand-written guide is 1,392 words,
so the choice was by importance, not by dropping what readers know: reader B
gets nearly everything wrong and a guide that corrected all of it would be five
times the size. Left out although at least one reader was wrong:

- `sched.lock-order`, `sched.class-order`, `sched.priorities`,
  `sched.percpu-kthreads`, `sched.set-task-cpu`, `sched.balance-push`: readers A
  and C answer them, and the source comment a reviewer would open says the same.
- `sched.state-consistency`: the hand-written guide's first rule. What is new
  about it is in the task state table, delayed dequeue and proxy execution.
- `sched.pelt-signals`, `sched.pelt-migration`, `sched.dl-admission`,
  `sched.dl-runtime`, `sched.pi-boost`, `sched.rt-push-pull`: real, but confined
  to one file each, and the errors were details, not the mechanism.
- `sched.slice-protection`, `sched.lag-placement`, `sched.rb-augment`,
  `sched.reweight`, `sched.wakeup-preempt`: all readers were weak. The entity
  field table and the pick question carry the names; the arithmetic is in
  comments next to the code.
- `sched.scx-dsq`, `sched.scx-ops-state`, `sched.scx-direct-dispatch`: the
  hand-written guide covered these and readers A and C have them mostly right.
- `sched.load-balance`, `sched.select-cpu`, `sched.topology`,
  `sched.core-sched`, `sched.preempt-modes`, `sched.affinity-api`,
  `sched.ttwu-paths`, `sched.schedule-steps`: places to look more than rules.

Two questions were reworded after the measurement, in both files:
`sched.enqueue-flags` now asks for flag names in full and `sched.hotplug-steps`
for a table, because a first build abbreviated the names and wrote the
callbacks as two lists under plain headings.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 141 corrections, 42% rewritten on average
reader B: 190 corrections, 79% rewritten on average
reader C: 153 corrections, 29% rewritten on average

question                     reader A         reader B         reader C
sched.core-files               7% ( 3)        18% ( 4)         6% ( 3)
sched.build-units             14% ( 1)        76% ( 1)        29% ( 1)
sched.entry-points             0% ( 0)        17% ( 1)         1% ( 1)
sched.docs-tests               0% ( 0)        37% ( 1)         4% ( 1)
sched.class-order              0% ( 0)        69% ( 1)         0% ( 0)
sched.class-callbacks         23% ( 3)        41% ( 1)        13% ( 1)
sched.rq-lock                 11% ( 3)        87% ( 3)        10% ( 1)
sched.lock-order               0% ( 0)        80% ( 3)         6% ( 1)
sched.task-rq-lock            34% ( 2)        88% ( 2)        13% ( 1)
sched.lock-guards             58% ( 1)        89% ( 2)        17% ( 1)
sched.rq-pin-clock            43% ( 1)        84% ( 1)         0% ( 0)
sched.balance-callbacks       51% ( 2)        86% ( 2)        35% ( 1)
sched.on-rq-states            29% ( 3)        61% ( 5)        25% ( 2)
sched.state-consistency       60% ( 1)        85% ( 3)        15% ( 3)
sched.sched-change            76% ( 1)        86% ( 3)        31% ( 3)
sched.enqueue-flags           44% ( 1)        68% ( 4)        35% ( 2)
sched.donor-curr              15% ( 1)        72% ( 3)        32% ( 2)
sched.sleep-pattern           25% ( 5)        66% ( 4)         0% ( 2)
sched.schedule-steps          28% ( 3)        82% ( 3)        21% ( 3)
sched.ttwu-paths              47% ( 2)        80% ( 3)        27% ( 2)
sched.special-states          47% ( 2)        80% ( 3)        31% ( 1)
sched.wake-helpers            42% ( 4)        77% ( 3)        16% ( 1)
sched.proxy-exec              56% ( 4)        94% ( 1)        34% ( 5)
sched.preempt-modes           67% ( 4)        83% ( 3)        50% ( 4)
sched.schedule-context        62% ( 2)        86% ( 2)        19% ( 1)
sched.affinity-api            53% ( 3)        86% ( 6)        20% ( 4)
sched.migrate-disable         43% ( 2)        67% ( 1)        20% ( 3)
sched.set-task-cpu            30% ( 2)        85% ( 1)         8% ( 1)
sched.percpu-kthreads          5% ( 0)        94% ( 3)         7% ( 1)
sched.stopper-migration       48% ( 1)        90% ( 1)        18% ( 1)
sched.fair-queueing           78% ( 6)        93% ( 7)        61% ( 6)
sched.cfs-rq-counters          7% ( 1)        82% ( 2)         9% ( 1)
sched.entity-fields           24% ( 4)        74% ( 1)        26% ( 2)
sched.virtual-time            53% ( 4)        85% ( 5)        44% ( 4)
sched.eevdf-pick              74% ( 1)        93% ( 1)        41% ( 2)
sched.rb-augment              42% ( 1)        89% ( 1)        49% ( 1)
sched.slice-deadline          15% ( 1)        78% ( 1)        57% ( 1)
sched.slice-protection        71% ( 2)        94% ( 1)        71% ( 3)
sched.lag-placement           31% ( 2)        77% ( 7)        14% ( 2)
sched.delayed-dequeue         43% ( 1)        81% ( 3)         9% ( 3)
sched.wakeup-preempt          69% ( 2)        81% ( 2)        34% ( 2)
sched.reweight                59% ( 2)        76% ( 2)        67% ( 3)
sched.pelt-signals            35% ( 3)        79% ( 5)        27% ( 6)
sched.pelt-migration          29% ( 2)        78% ( 1)         5% ( 1)
sched.cfs-bandwidth           72% ( 4)        93% ( 5)        33% ( 1)
sched.util-clamp              53% ( 2)        89% ( 4)        16% ( 1)
sched.load-balance            57% ( 1)        79% ( 7)        32% ( 3)
sched.select-cpu              72% ( 1)        87% ( 3)        29% ( 2)
sched.cache-aware             96% ( 1)        91% ( 1)        94% ( 1)
sched.topology                38% ( 1)        65% ( 2)        17% ( 1)
sched.priorities               5% ( 3)        82% ( 3)         0% ( 2)
sched.rt-limits               53% ( 2)        81% ( 3)        45% ( 4)
sched.rt-push-pull            59% ( 2)        94% ( 4)        52% ( 2)
sched.dl-admission            21% ( 3)        81% ( 3)        42% ( 6)
sched.dl-runtime              29% ( 1)        78% ( 2)        16% ( 4)
sched.dl-servers              49% ( 3)        87% ( 1)        47% ( 5)
sched.pi-boost                46% ( 1)        83% ( 2)        35% ( 3)
sched.scx-files               42% ( 2)        68% ( 6)        37% ( 4)
sched.scx-dsq                 51% ( 2)        68% ( 2)        32% ( 3)
sched.scx-ops-state           40% ( 3)        83% ( 2)        25% ( 1)
sched.scx-direct-dispatch     55% ( 2)        86% ( 1)        41% ( 2)
sched.scx-kfunc-contexts      90% ( 1)        87% ( 4)        93% ( 4)
sched.scx-exit                66% ( 5)        84% ( 4)        46% ( 4)
sched.scx-sub-cid             93% ( 2)        94% ( 1)        85% ( 1)
sched.hotplug-steps           39% ( 3)        86% ( 6)        20% ( 4)
sched.balance-push            28% ( 1)        87% ( 3)         0% ( 0)
sched.hotplug-timers          50% ( 3)        82% ( 3)        27% ( 3)
sched.core-sched              46% ( 3)        92% ( 5)        57% ( 2)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `sched.state-consistency`, `sched.affinity-api`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `sched.class-order`, `sched.rq-lock`, `sched.lock-order`, `sched.schedule-steps`, `sched.ttwu-paths`, `sched.set-task-cpu`, `sched.pelt-signals`, `sched.dl-admission`, `sched.scx-ops-state`.

## Questions reorganised

Subjects now: finding your way, scheduling classes (4 questions), task state (5), locks, affinity and
migration (6), blocking and waking (3), fair class (8), realtime, deadline and servers (3), extensible
class (4), CPU hotplug (2); 39 questions before, 38 after, none dropped. `sched.core-files` and
`sched.scx-files` were two tables of job to file and are one, `sched.file-map`. The four questions of
"Using it safely" went to the subject each belongs to, and `sched.cfs-bandwidth` and
`sched.pelt-signals` joined the fair class. Reworded to stop asking for members or a walk through the
code: `sched.entity-fields`, `sched.class-callbacks`, `sched.schedule-steps`, `sched.hotplug-steps`,
`sched.affinity-api`, `sched.dl-servers`.
