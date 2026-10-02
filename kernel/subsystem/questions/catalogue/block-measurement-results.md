# What the block measurement found

Three models were asked the 35 questions in `block-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels up to 7.1), reader A a few releases behind it (up to 6.18), and
reader B older again (6.12 to 6.13), with whole mechanisms out of date. The
hand-written guide was never checked against current sources, so differences
between it and the built guide are expected and are noted near the end.

All three know the architecture: where the files are, how a bio reaches a
driver, what a freeze is for, which operations have no data pages. What they
get wrong is names and orders that moved in the last few releases (the
scheduler switch, the depth fields, integrity preparation, the bio allocator)
and a handful of facts they state with confidence that the code contradicts.

## What all three readers got wrong

- **Zone management operation numbers.** All three numbered them 10 to 13 and
  15, with bit 0 set on only some. The tree has `REQ_OP_ZONE_OPEN` 11,
  `REQ_OP_ZONE_CLOSE` 13, `REQ_OP_ZONE_FINISH` 15, `REQ_OP_ZONE_RESET` 17 and
  `REQ_OP_ZONE_RESET_ALL` 19, so `op_is_write()` is true for every one of
  them, and each reader's list of "writes that carry no data" was short.
- **The order inside `bio_alloc_bioset()`.** It is the per-CPU cache, then the
  slab with reclaim stripped by `try_alloc_gfp()`, then
  `punt_bios_to_rescuer()`, then the mempools. Every reader put the mempool
  straight after the cache. Two named bvec_alloc(), which is gone; the bvec
  slab allocation is open-coded. Two gave a vector count over `BIO_MAX_VECS`
  as a NULL return; `biovec_slab()` calls `BUG()`.
- **`bio_alloc_clone()` can fail under any gfp.** When the source has an
  integrity payload the clone goes through `bio_integrity_alloc()`, which is a
  plain `kmalloc_flex()`. None said so.
- **bio_last_bvec_all()** was named by all three and does not exist.
  `bio_get_first_bvec()` and `bio_get_last_bvec()` are static in
  `block/blk-merge.c`, so a driver cannot call them. Only
  `bio_first_bvec_all()` warns on `BIO_CLONED`; `bio_for_each_segment_all()`
  does not.
- **Dead disk and dying queue are checked in different places.**
  `__bio_queue_enter()` looks only at `GD_DEAD`; `blk_queue_enter()` looks only
  at `blk_queue_dying()`. Every reader blurred the two.
- **`update_nr_hwq_lock`** is taken for write, with `down_write_trylock()` and
  `-EBUSY`, by `elv_iosched_store()` and `queue_requests_store()`. Readers A
  and C said read (comments in the tree still say so); reader B did not know
  the lock. Only adding and deleting a disk take it for read.
- **What the common sysfs store path holds.** `queue_attr_store()` takes no
  lock and no freeze before a plain `->store`; each store function freezes and
  locks for itself. A limits store goes through `queue_limits_start_update()`
  and always `queue_limits_commit_update_frozen()`. Two readers had
  `sysfs_lock` held there, the third had `queue_wb_lat_store()` taking
  `elevator_lock`; it takes `rqos_state_mutex` in `wbt_set_lat()`.
- **`rq_qos_mutex` and the freeze have no single order.** `rq_qos_add()` and
  `rq_qos_del()` assert the mutex and freeze for themselves;
  `ioc_qos_write()` freezes first. One reader made freezing the caller's duty,
  one had the functions take the mutex, one named
  blkg_conf_open_bdev_frozen(), which is not in the tree.
- **BFQ's call of its depth callback at init** comes before it sets
  `q->async_depth`, not after. One reader thought the core makes the call, one
  that it goes through `init_hctx`, one had the order reversed.
- **Changing the hardware queue count.** The schedulers are switched to none
  and the new tag array is allocated before any queue is frozen, and
  `elv_update_nr_hw_queues()` both restores the scheduler and unfreezes. All
  three had the order wrong and offered helper names that do not exist
  (blk_mq_realloc_tag_set_tags(), blk_mq_alloc_sched_tags_batch()).
- **`BLK_STS_RESOURCE`** gets a delayed rerun only when a restart is pending
  (`blk_mq_sched_needs_restart()`); otherwise the queue is rerun at once.
- Zone write plugging details: only emulated zone append is plugged, reset and
  finish act at completion, and with `QUEUE_FLAG_ZONED_QD1_WRITES` a per-disk
  worker submits instead of the per-plug work.

## What only some readers got wrong

Reader B, and nobody else:

- `blk_mq_freeze_queue()` returns nothing, and the `_nomemsave` forms are the
  ones that apply NOIO. Both reversed: it returns the `memalloc_noio_save()`
  flags, `__must_check`, and `blk_mq_unfreeze_queue()` takes them back.
- `elevator_lock` is taken before freezing. The comment on the field and every
  store say freeze first.
- `sysfs_lock` serialises attribute stores and the scheduler swap, and
  `queue_lock` is vestigial. Neither is so.
- The depth callback takes a hardware context, kyber has none, and the async
  limit is a field of the scheduler. It takes the queue, all three schedulers
  have one, and the limit is `q->async_depth`.
- `queue_limits_commit_update()` is safe with requests in flight. Its
  kernel-doc requires a freeze or no outstanding I/O.
- A driver's `queue_rq` ends the request itself before returning an error. The
  core calls `blk_mq_end_request()`, so that would complete it twice. This one
  would change a verdict.
- blk_mq_tag_update_depth(), `rq->ref` as a refcount_t, loop as a bio-based
  driver, no selftests in the tree.

Readers A and B:

- `bio_integrity_prep()` takes a bio and returns bool, and its buffer
  allocation can fail. It is `void bio_integrity_prep(bio, action)`,
  `bio_integrity_action()` decides beforehand, and both allocations fall back
  to a mempool.
- The scheduler is torn down after the drain in `del_gendisk()`. It goes in
  `elevator_set_none()` inside `blk_unregister_queue()`, before
  `blk_mq_freeze_queue_wait()`; only `rq_qos_exit()` comes after.
- BLK_STS_ZONE_RESOURCE and `Documentation/block/queue-sysfs.rst` were named
  and are gone; the attributes are in `Documentation/ABI/stable/sysfs-block`.
- A plugged zone write drops its queue reference (reader A) or takes it with
  `blk_queue_enter()` (reader B). It takes one with `percpu_ref_get()` in
  `disk_zone_wplug_add_bio()` and blk-mq reuses it for the request.
- Reader A alone: `blk_mq_init_sched()` calls the depth callback (the comment
  above `dd_depth_updated()` says so and is stale), and the helper names
  blk_pm_resume_if_suspended() and __blk_crypto_bio_prep().

Reader C alone: `bio_integrity_alloc_buf()` tries `kmalloc()` without reclaim
(it passes the caller's gfp with `__GFP_NOWARN`, so reclaim is allowed), and an
ELEVATOR_FLAG_ENABLE_WBT_ON_EXIT step in the switch that is gone.

## What the readers already knew

The file map and the entry points (no reader needed more than a missing file
added); that discard, secure erase and write zeroes are writes without data and
zone append is a write with data; what `bio_has_data()` tests; that a
mempool-backed allocation cannot fail when it may block and `bio_kmalloc()`
can; one bio at a time from a bioset; freeze against quiesce, the limits update
interface and features against flags (readers A and C). These are dropped from
the build set or shrunk to a pointer.

## Where the hand-written guide is stale

- It lists `bvec_alloc()`. There is no such function in the tree.
- It says `bio_integrity_prep()` always returns `true`. It returns nothing and
  takes an action mask.
- It says `bio_integrity_alloc_buf()` tries `kmalloc()` with `GFP_NOIO` less
  direct reclaim and falls back to the mempool with `GFP_NOFS`. The function
  takes the gfp from its caller (`GFP_NOIO` from the automatic path,
  `GFP_NOFS` from the file system one) and uses it for both attempts.
- It places `async_depth` in mq-deadline and kyber and says all state derived
  from `q->nr_requests` lives in `elevator_data`. The limit is
  `q->async_depth` in `struct request_queue`, rescaled by
  `blk_mq_update_nr_requests()` and writable through its own sysfs attribute,
  whose store is a second caller of the callback. Only BFQ keeps a derived
  array.
- It says all three schedulers call their callback at the end of init. BFQ
  calls it before it writes its default `q->async_depth`.
- Its table gives `REQ_OP_FLUSH` as a bio operation with a NULL `bi_io_vec`. A
  bio cannot carry that operation (`submit_bio_noacct()` rejects it); a flush
  bio is an empty write with `REQ_PREFLUSH`.
- It lists `bio_get_first_bvec()` and `bio_get_last_bvec()` among accesses that
  need a guard. They are private to `block/blk-merge.c`.
- It says bio submission takes the usage counter through `blk_queue_enter()`.
  Bios go through `bio_queue_enter()`; `blk_queue_enter()` is the request
  allocation path, and the two fail on different conditions.
- Correct and kept as questions: the freeze returning the allocation flags,
  `op_is_write()` not being a guard for data, zone append carrying data, the
  mempool guarantee and its bvec-pool exception, and `nr_requests` being
  written before the callback.

## Left out of the build set

The hand-written guide is 629 words, so the build set holds 12 of the 35
questions, chosen by importance to someone reviewing a block layer patch and
weighted towards what the old guide was about. Left out although a reader got
them wrong: disk removal, the scheduler switch and the callbacks that carry its
resources, changing `nr_requests` and the hardware queue count, the sysfs store
path (the lock order question carries its main fact), the table of queue locks,
the rq_qos policies and zone write plugging: each is confined to a few
functions that a patch touching them has open anyway. Also left out: bio
completion, splitting, cloning and the iteration helpers (what matters from
them for a reviewer is in the question on touching data fields), submission
from a driver, the status codes and the dispatch contract (driver-side; reader
B's double completion is the one loss), the request states, one bio at a time
from a bioset, freeze against quiesce, the limits interface, features against
flags, the entry points, and the documentation and tests.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 78 corrections, 38% rewritten on average
reader B: 108 corrections, 69% rewritten on average
reader C: 68 corrections, 25% rewritten on average

question                       reader A      reader B      reader C
block.core-files                0% ( 1)       8% ( 4)       0% ( 1)
block.entry-points              0% ( 1)      14% ( 1)       0% ( 0)
block.docs-and-tests           25% ( 1)      71% ( 1)      16% ( 0)
block.usage-counter            42% ( 5)      63% ( 9)      18% ( 1)
block.freeze-api               30% ( 1)      73% ( 3)      15% ( 1)
block.freeze-reclaim           50% ( 1)      83% ( 2)      43% ( 4)
block.freeze-vs-quiesce        20% ( 1)      75% ( 1)       0% ( 0)
block.freeze-usage             32% ( 1)      77% ( 2)       2% ( 1)
block.freeze-lock-order        52% ( 2)      88% ( 2)      55% ( 6)
block.queue-locks              22% ( 4)      59% ( 7)       7% ( 3)
block.disk-teardown            66% ( 3)      88% ( 3)      26% ( 3)
block.limits-update            25% ( 3)      65% ( 2)      12% ( 0)
block.features-and-flags        4% ( 1)      53% ( 2)      16% ( 0)
block.sysfs-attrs              50% ( 3)      69% ( 4)      43% ( 2)
block.op-table                  7% ( 1)      17% ( 2)      24% ( 2)
block.op-predicates            11% ( 1)      43% ( 1)      44% ( 1)
block.data-access-usage        64% ( 2)      62% ( 1)      36% ( 3)
block.bio-iterators            32% ( 3)      60% ( 1)      19% ( 2)
block.bio-alloc                33% ( 3)      65% ( 4)      32% ( 4)
block.bioset-usage             16% ( 1)      77% ( 1)      20% ( 1)
block.integrity-alloc          68% ( 3)      86% ( 2)      39% ( 3)
block.bio-completion           37% ( 2)      86% ( 3)      60% ( 2)
block.bio-split-clone          44% ( 2)      74% ( 2)      72% ( 2)
block.stacked-submission       68% ( 2)      92% ( 2)      20% ( 2)
block.status-codes             66% ( 2)      76% ( 3)      21% ( 1)
block.request-lifecycle        35% ( 3)      68% ( 6)      28% ( 2)
block.queue-rq-contract        18% ( 3)      69% ( 4)      32% ( 4)
block.nr-hw-queues-update      52% ( 3)      82% ( 5)      47% ( 4)
block.elevator-ops             51% ( 4)      80% ( 5)      17% ( 3)
block.elevator-switch          52% ( 1)      84% ( 4)      25% ( 2)
block.depth-updated            78% ( 1)      91% ( 6)      29% ( 1)
block.nr-requests-update       48% ( 1)      90% ( 4)      15% ( 1)
block.rq-qos                   50% ( 5)      90% ( 4)      31% ( 3)
block.zone-write-plug          53% ( 4)      86% ( 2)      27% ( 3)
block.change-checklist         43% ( 3)      83% ( 3)      11% ( 0)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `block.disk-teardown`, `block.bio-completion`, `block.bio-split-clone`, `block.elevator-ops`, `block.elevator-switch`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `block.freeze-vs-quiesce`, `block.queue-locks`, `block.limits-update`, `block.bio-iterators`, `block.bioset-usage`, `block.request-lifecycle`, `block.queue-rq-contract`.

## Questions reorganised

By subject now, 25 questions where there were 26: operations and bio data; allocating bios;
completing, splitting and cloning bios; entering and freezing a queue; queue locks and limits;
schedulers; requests and dispatch. No ids changed and nothing was merged. `block.elevator-ops` is
dropped: it asked for the members of `struct elevator_mq_ops`, and the part a reviewer acts on, what is
allocated outside the freeze and how it is carried in, is asked by `block.elevator-switch`. Dead disk
against dying queue moved from `block.disk-teardown` to `block.usage-counter`. `block.queue-locks` asks
which lock covers the state a patch changes, not for a table of nine; `block.freeze-api`,
`block.op-predicates` and `block.depth-updated` ask for the contract, not for a list.
