# Questions: Block layer (measurement set)

- guide: block.md
- title: Block Layer Subsystem

A wide set of questions about the block layer core under `block/`: bios,
request queues and their synchronisation, blk-mq, the I/O schedulers and the
disk lifetime. It is used to measure what a model already knows before deciding
what the built guide should spend its words on. The hand-written guide it will
replace is 629 words, so most of what is asked here cannot be in the built
guide; the point is to find which few things must be. Individual block drivers,
the device mapper and md are not covered. The trimmed set a guide is built from
is `../block.md`. Format: `../../../docs/subsystem-questions.md`.

# Where to look

## block.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

Which files hold bio allocation and completion, bio submission, splitting and
merging, the blk-mq core, tags, the scheduler glue and the three schedulers,
queue limits, the sysfs attributes, the flush machinery, zoned support,
integrity, inline encryption, the rq_qos policies, cgroup support and the disk
and block device objects? A table. Start from `block/`.

## block.entry-points: Entry points

- section: Finding your way
- relevance: 4 - the function to start reading from for each job
- words: 100

For each job (submit a bio, allocate and run a passthrough request, complete a
request from a driver, freeze a queue, change a queue limit, switch the I/O
scheduler, add a disk, remove a disk), which function do you start reading
from? A table.

## block.docs-and-tests: Documentation and tests

- section: Finding your way
- relevance: 2 - the tests are mostly outside the tree
- words: 60

Which files under `Documentation/block/` are worth reading before changing
bios, blk-mq or queue attributes, and what in the tree can exercise a block
layer change (test drivers, selftests)? Say what is not in the tree.

# Queue synchronisation and lifetime

## block.usage-counter: Queue usage counter

- section: Entering and freezing a queue
- relevance: 5 - everything a freeze guarantees rests on who holds this
- words: 90

What is the request queue's usage counter, which paths take and drop a
reference on it, and when does taking one wait, fail or succeed on a frozen,
dying or runtime-suspended queue? Start from `blk_queue_enter()`,
`bio_queue_enter()` and `blk_queue_exit()`.

## block.freeze-api: Freeze interface

- section: Entering and freezing a queue
- relevance: 5 - the signatures have changed and callers must match
- words: 90

List the functions that freeze and unfreeze a request queue in this tree, what
each takes and returns, what the start, wait and non-owner forms are for, and
how nested freezes are counted. Start from `blk_mq_freeze_queue()` in
`include/linux/blk-mq.h`.

## block.freeze-reclaim: Memory allocation while frozen

- section: Entering and freezing a queue
- relevance: 4 - a deadlock that only shows under memory pressure
- words: 80

What does the freeze interface do about memory allocations made while a queue
is frozen, and why? What usage inside a frozen section is unsafe, and what
that looks similar is correct? Name in-tree code that allocates before
freezing for this reason.

## block.freeze-vs-quiesce: Freeze and quiesce

- section: Entering and freezing a queue
- relevance: 4 - they guarantee different things and are confused
- words: 80

What does quiescing a queue guarantee that freezing does not, and the reverse?
What does each wait for, and which is needed before changing state that
`queue_rq` reads versus state that bio submission reads? Start from
`blk_mq_quiesce_queue()`.

## block.freeze-usage: Queue state and the freeze

- section: Entering and freezing a queue
- relevance: 5 - the recurring use-after-free and stale-read class
- words: 90

What usage that changes or tears down request queue state (the elevator, the
depth fields, the limits, rq_qos, the hardware contexts) without a freeze is
unsafe, and which in-tree code changes such state without freezing and is
correct? Say what makes it correct.

## block.freeze-lock-order: Lock order around a freeze

- section: Entering and freezing a queue
- relevance: 4 - lockdep reports here are frequent and hard to read
- words: 90

Which locks must be taken before a queue is frozen and which only after, and
how is a freeze modelled for lockdep? Start from the comment on
`elevator_lock` in `struct request_queue`, `blk_freeze_acquire_lock()` and
the sysfs store functions in `block/blk-sysfs.c`.

## block.queue-locks: Queue and tag set locks

- section: Locks and teardown
- relevance: 4 - each protects a different slice of the queue
- words: 110

What does each lock in `struct request_queue` and `struct blk_mq_tag_set`
protect: `queue_lock`, `sysfs_lock`, `limits_lock`, `elevator_lock`,
`rq_qos_mutex`, `debugfs_mutex`, `mq_freeze_lock`, `tag_list_lock` and
`update_nr_hwq_lock`? A table.

## block.disk-teardown: Disk removal

- section: Locks and teardown
- relevance: 4 - the order is what keeps I/O from reaching freed state
- words: 100

In what order does removing a disk stop new openers, mark the disk dead, drain
I/O and tear down the scheduler and rq_qos, and in what state is the queue
left afterwards? What do a dead disk and a dying queue each do to a task
submitting I/O? Start from `del_gendisk()` and `blk_mq_destroy_queue()`.

# Queue limits

## block.limits-update: Updating queue limits

- section: Limits and features
- relevance: 4 - the old setter functions are gone
- words: 90

How does a driver set limits when it creates a queue, and how does it change
them later? Which lock is held between start and commit, who validates the
values, and which commit form freezes the queue? Start from
`queue_limits_start_update()` in `include/linux/blkdev.h`.

## block.features-and-flags: Features, flags and queue flags

- section: Limits and features
- relevance: 3 - a capability has moved between these more than once
- words: 80

Queue properties live in three places: `features` and `flags` in
`struct queue_limits`, and `queue_flags` in `struct request_queue`. What kind
of property goes in each, who may change each, and how is each changed? Give
two examples of each.

## block.sysfs-attrs: Queue sysfs attributes

- section: Limits and features
- relevance: 3 - where the locking rules meet user space
- words: 80

How is a queue sysfs attribute declared, what is the difference between an
entry with a plain store and one with a limits store, and which locks and
freeze does the common store path take before calling each? Start from
`queue_attr_store()` in `block/blk-sysfs.c`.

# Bios

## block.op-table: Operations and their payload

- section: Operations and data
- relevance: 5 - which operations carry data pages decides what a driver may touch
- words: 110

Give a table of the `enum req_op` values in this tree: the number, whether
bit 0 is set, whether a bio with that operation carries data pages, and
whether its `bi_iter.bi_size` means a byte count of data or only a range.
Start from `include/linux/blk_types.h`.

## block.op-predicates: Direction and data predicates

- section: Operations and data
- relevance: 5 - the wrong predicate guards the wrong thing
- words: 90

What exactly do `op_is_write()`, `bio_data_dir()`, `bio_has_data()`,
`bio_no_advance_iter()`, `op_is_flush()` and `op_is_zone_mgmt()` test? For
which operations do "is a write" and "has data" disagree?

## block.data-access-usage: Touching bio data fields

- section: Operations and data
- relevance: 5 - a NULL dereference nothing in the diff shows
- words: 90

What usage of `bi_io_vec`, `bi_vcnt`, the bvec iterators or the first and
last bvec helpers is unsafe on a bio that may carry no data, and what guard
that looks similar is not enough? Name in-tree code that guards correctly.

## block.bio-iterators: Bio iteration helpers

- section: Operations and data
- relevance: 4 - the helper for the owner is wrong in a driver
- words: 90

Which of the bio iteration helpers may only be used by the code that built the
bio, which may a driver use on a bio it was handed, and which fields
(`bi_vcnt`, `bi_max_vecs`, `bi_io_vec`) are meaningless in a cloned or split
bio? Start from `include/linux/bio.h`.

## block.bio-alloc: Bio allocation guarantees

- section: Allocating bios
- relevance: 5 - decides whether an error path is dead code or a missing check
- words: 110

For each way of getting a bio (`bio_alloc()`, `bio_alloc_bioset()`,
`bio_alloc_clone()`, `bio_kmalloc()`, `bio_init()` on caller memory), under
which gfp flags can it return NULL, and what else can make it return NULL?
Describe the order in which `bio_alloc_bioset()` tries its sources. A table.

## block.bioset-usage: Several bios from one bioset

- section: Allocating bios
- relevance: 4 - the mempool guarantee has a precondition
- words: 80

What usage of a bioset that allocates more than one bio before submitting is
unsafe, what does the rescuer do about it and for which biosets, and what is
the correct way to carry per-bio driver data? Start from the comment above
`bio_alloc_bioset()`.

## block.integrity-alloc: Integrity payload allocation

- section: Allocating bios
- relevance: 3 - the prototypes changed and callers check the wrong thing
- words: 80

When the block layer attaches an integrity payload to a bio by itself, which
function decides whether to, what does the preparation function take and
return, and where do the payload and its buffer come from? Can either
allocation fail? Start from `bio_integrity_prep()`.

## block.bio-completion: Completion and chaining

- section: Bio life cycle
- relevance: 4 - double completion and lost errors
- words: 90

How is a bio completed: who sets `bi_status`, what does `bio_endio()` do before
calling `bi_end_io`, how does a chained bio hold off its parent, and what
usage that calls `bi_end_io` directly or completes a bio twice is unsafe?
Start from `bio_endio()` and `bio_chain()`.

## block.bio-split-clone: Splitting and cloning

- section: Bio life cycle
- relevance: 4 - what a clone shares with its source is what goes wrong
- words: 90

Which functions split a bio to the queue limits and which clone one, what does
a clone share with its source, and what must the owner of the source keep
alive until the clone completes? Start from `bio_split_to_limits()` and
`bio_alloc_clone()`.

## block.stacked-submission: Submission from a driver

- section: Bio life cycle
- relevance: 3 - explains why a submitted bio has not been issued yet
- words: 80

What happens to a bio submitted from inside a driver's bio submission method:
when is it actually issued, in what order relative to others submitted there,
and what distinguishes a bio-based driver's device from a blk-mq one on this
path? Start from `submit_bio_noacct_nocheck()`.

## block.status-codes: Status codes

- section: Bio life cycle
- relevance: 3 - the resource codes change what blk-mq does next
- words: 80

What is `blk_status_t`, how is it converted to and from an errno, and what does
blk-mq do differently when `queue_rq` returns each of the resource-shortage
codes rather than an error? What status does a bio with `REQ_NOWAIT` get when
it would block?

# Requests and blk-mq

## block.request-lifecycle: Request states

- section: blk-mq
- relevance: 4 - timeouts and completions race through these
- words: 100

What states does a request move through from allocation to free, which
function makes each transition, what does the reference count on a request
protect, and how do the timeout handler and a normal completion avoid both
finishing the same request? Start from `enum mq_rq_state`.

## block.queue-rq-contract: Driver dispatch contract

- section: blk-mq
- relevance: 4 - what a driver must do before and after returning
- words: 100

What must a driver's `queue_rq` do with a request before returning each kind
of status, what do `bd->last`, `commit_rqs` and `queue_rqs` mean, and in what
context (may it sleep) is it called? Start from `struct blk_mq_ops`.

## block.nr-hw-queues-update: Changing the hardware queue count

- section: blk-mq
- relevance: 3 - touches every queue of a tag set at once
- words: 90

What are the steps of `blk_mq_update_nr_hw_queues()`: which locks, what is
allocated before any queue is frozen, what happens to each queue's scheduler,
and what is the fallback when reallocating hardware contexts fails?

# I/O schedulers

## block.elevator-ops: Scheduler callbacks

- section: Elevators
- relevance: 4 - the set of callbacks has grown
- words: 100

Which callbacks does `struct elevator_mq_ops` have in this tree, which deal
with allocating and freeing the scheduler's data and tags, and which structures
carry those resources into and out of a switch? Start from `block/elevator.h`.

## block.elevator-switch: Switching schedulers

- section: Elevators
- relevance: 4 - allocation, freeze and registration happen in a fixed order
- words: 100

What are the steps of switching a queue's scheduler from the sysfs write to
the new scheduler being registered: what is allocated before the freeze, which
locks are held at each step, what is done after the unfreeze, and what state
is the queue in if the new scheduler fails to initialise? Start from
`elv_iosched_store()`.

## block.depth-updated: Depth update callback

- section: Elevators
- relevance: 5 - a scheduler computes its limits from fields it must see updated
- words: 100

Who calls a scheduler's `depth_updated` callback, in what order relative to the
writes of the queue's depth fields, which queue fields does each in-tree
scheduler read there, and does each call it during its own initialisation?
Where does the limit on asynchronous requests live in this tree?

## block.nr-requests-update: Changing nr_requests

- section: Elevators
- relevance: 3 - tags may have to grow, and that cannot happen frozen
- words: 90

What are the steps of a write to the `nr_requests` attribute: the bounds
checked, what is allocated and when, the locks and the freeze, and what
`blk_mq_update_nr_requests()` does in each of its cases? Start from
`queue_requests_store()`.

# Other parts

## block.rq-qos: rq_qos policies

- section: Policies and zones
- relevance: 3 - attach and detach have their own lock and freeze
- words: 80

Which rq_qos policies exist, which hooks does the block layer call them
through, and which lock and what freeze do adding and removing one require?
Start from `rq_qos_add()` in `block/blk-rq-qos.c`.

## block.zone-write-plug: Zone write plugging

- section: Policies and zones
- relevance: 3 - replaced the scheduler-based zone locking
- words: 90

How does this tree keep writes to one zone of a zoned device in order: what is
a zone write plug, which bios go through one, where in submission and
completion is it hooked, and what does it do with the queue usage counter for
a plugged bio? Start from `blk_zone_plug_bio()`. If the tree has no zone write
plugs, say so and stop.

## block.change-checklist: Changing core code

- section: Policies and zones
- relevance: 3 - a core change is seen by more than blk-mq drivers
- words: 80

What must a change to bio submission, completion or the freeze code keep
working besides blk-mq drivers: bio-based drivers, stacking drivers, zoned
devices, passthrough requests, polling, runtime power management? Name the
function where each joins the common path.
