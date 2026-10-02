# Questions: Block Layer Subsystem

- guide: block.md
- title: Block Layer Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/block-measurement.md` is the
wider set the readers were measured on and `catalogue/block-measurement-results.md` says what they
got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## block.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## block.core-files: Core files

- relevance: 4 - turns a search into a lookup

A table and nothing else, job to file: bio allocation and completion; bio submission; splitting
and merging; the blk-mq core; tags; the scheduler glue and each scheduler; queue limits; the sysfs
attributes; the flush machinery; zoned support; integrity; inline encryption; the rq_qos policies;
cgroup support; the disk and block device objects. Where a reader is likely to look for a file
that does not exist in this tree, say so in the row. Start from `block/`.

# Operations and bio data

## block.op-table: Operations and their payload

- section: Operations and bio data
- relevance: 5 - which operations carry data pages decides what a driver may touch

For each `enum req_op` value in this tree, does the operation count as a write, and does a bio
with that operation carry data pages or does its `bi_iter.bi_size` give only a range? Can a bio
carry `REQ_OP_FLUSH`? Start from `include/linux/blk_types.h`.

## block.bio-iterators: Bio iteration helpers

- section: Operations and bio data
- relevance: 4 - the helper for the owner is wrong in a driver

What are the requirements for reading `bi_io_vec` and `bi_vcnt` of a bio, directly or through
`bio_for_each_segment_all()` and `bio_first_bvec_all()`, in order to assure safe usage, and what
may code that was handed a bio it did not build use in their place? Which helpers in
`include/linux/bio.h` check `BIO_CLONED`? Start from `include/linux/bio.h`.

## block.data-access-usage: Bios that carry no data

- section: Operations and bio data
- relevance: 5 - a NULL dereference nothing in the diff shows

What are the requirements for reading the bvecs of a bio that may carry no data, through
`bi_io_vec` or through `bio_for_each_segment()`, in order to assure safe usage? Which helpers that
return the first or the last bvec of a bio can a driver call? Name in-tree code that shows it.

# Allocating bios

## block.bio-alloc: Bio allocation guarantees

- section: Allocating bios
- relevance: 5 - decides whether an error path is dead code or a missing check

When can each of `bio_alloc()`, `bio_alloc_bioset()`, `bio_alloc_clone()` and `bio_kmalloc()`
return NULL? In what order does `bio_alloc_bioset()` try its sources of memory, and at which of
them may it sleep?

## block.bioset-usage: Bioset rescuer and front pad

- section: Allocating bios
- relevance: 4 - the mempool guarantee has a precondition

What are the requirements for a caller that allocates bios from one `struct bio_set` with
`bio_alloc_bioset()` in order to assure safe usage? What does the rescuer workqueue of a bioset
guarantee? How does a driver carry its own data with each bio? Start from the comment above
`bio_alloc_bioset()`.

## block.bioset-rescuer: Rescuer workqueue of a bioset

- section: Allocating bios
- relevance: 4 - the rescue applies only to a bioset that was set up for it

What decides whether a `struct bio_set` has a rescuer workqueue, and what does
`bio_alloc_bioset()` do differently for a bioset that has none? Start from `bioset_init()`.

## block.integrity-alloc: Integrity payload allocation

- section: Allocating bios
- relevance: 3 - the prototypes changed and callers check the wrong thing

When the block layer attaches an integrity payload to a bio by itself, what does
`bio_integrity_prep()` take and return, and what decides beforehand whether it is called? What do
the allocations of the payload and of its buffer guarantee to the caller?

# Completing, splitting and cloning bios

## block.bio-completion: Completion and chaining

- section: Completing, splitting and cloning bios
- relevance: 4 - double completion and lost errors

What are the requirements for completing a bio, through `bio_endio()` or through a direct call of
`bi_end_io`, in order to assure safe usage? How does a bio chained with `bio_chain()` hold off its
parent, and which `bi_status` does the parent end with? Start from `bio_endio()` and
`bio_chain()`.

## block.bio-split-clone: Splitting and cloning

- section: Completing, splitting and cloning bios
- relevance: 4 - what a clone shares with its source is what goes wrong

What does a cloned or a split bio share with its source, what must the owner of the source
therefore keep alive and leave unchanged until the clone completes, and what does a split do
with the remainder? Start from `bio_split_to_limits()` and `bio_alloc_clone()`.

# Entering and freezing a queue

## block.usage-counter: Queue usage counter

- section: Entering and freezing a queue
- relevance: 5 - everything a freeze guarantees rests on who holds this

What does holding a reference on the request queue's usage counter guarantee, and when does
taking one wait, fail or succeed on a frozen queue, a dying queue, a dead disk and a
runtime-suspended queue? Say where the bio path and the request allocation path test different
things. Start from `blk_queue_enter()`, `bio_queue_enter()` and `blk_queue_exit()`.

## block.freeze-api: Freeze interface

- section: Entering and freezing a queue
- relevance: 5 - the signatures have changed and callers must match

What does `blk_mq_freeze_queue()` return that `blk_mq_unfreeze_queue()` must be given? When is
each of `blk_freeze_queue_start()` with `blk_mq_freeze_queue_wait()`,
`blk_freeze_queue_start_non_owner()` and `blk_mq_freeze_queue_nomemsave()` used in place of
`blk_mq_freeze_queue()`? How are nested freezes counted? Start from `blk_mq_freeze_queue()` in
`include/linux/blk-mq.h`.

## block.freeze-vs-quiesce: Freeze and quiesce

- section: Entering and freezing a queue
- relevance: 4 - they guarantee different things and are confused

What does quiescing a queue guarantee that freezing does not, and the reverse? What does each
wait for, and which is needed before changing state that `queue_rq` reads and which before
changing state that bio submission reads? Start from `blk_mq_quiesce_queue()`.

## block.freeze-usage: Queue state changes under freeze

- section: Entering and freezing a queue
- relevance: 5 - the recurring use-after-free and stale-read class

What are the requirements for changing or freeing state of a `struct request_queue` that the I/O
path reads, such as the elevator and the hardware contexts, in order to assure safe usage? Which
in-tree code changes such state without `blk_mq_freeze_queue()`, and what makes that code correct?

## block.freeze-reclaim: Memory allocation while frozen

- section: Entering and freezing a queue
- relevance: 4 - a deadlock that only shows under memory pressure

What are the requirements for allocating memory between `blk_mq_freeze_queue()` and
`blk_mq_unfreeze_queue()` in order to assure safe usage? What does `blk_mq_freeze_queue()` do to
the allocation context of its caller? Name in-tree code that allocates before freezing for this
reason.

## block.disk-teardown: Disk removal

- section: Entering and freezing a queue
- relevance: 4 - the order is what keeps I/O from reaching freed state

When a disk is removed, what is torn down before I/O is drained and what only after it, where
do the scheduler and rq_qos go in that order, and in what state is the queue left once removal
returns? Start from `del_gendisk()` and `blk_mq_destroy_queue()`.

# Queue locks and limits

## block.queue-locks: Queue and tag set locks

- section: Queue locks and limits
- relevance: 4 - each protects a different slice of the queue

What does each lock of `struct request_queue` and of `struct blk_mq_tag_set` protect? Who takes
`update_nr_hwq_lock`, and in which mode?

## block.hwq-lock-sysfs: Tag set lock in sysfs

- section: Queue locks and limits
- relevance: 4 - a store function that waits for this lock can deadlock against the removal of the disk

What are the requirements for a sysfs store function that takes `update_nr_hwq_lock` in order to
assure safe usage, and what does the function return when it cannot take the lock? Name in-tree
code that shows it.

## block.freeze-lock-order: Lock order around a freeze

- section: Queue locks and limits
- relevance: 4 - lockdep reports here are frequent and hard to read

Which locks must be taken before `blk_mq_freeze_queue()` is called, and which only after it? What
does `queue_attr_store()` hold when it calls an attribute's store function? How does
`blk_freeze_acquire_lock()` model a freeze for lockdep? Start from the comment on `elevator_lock`
in `struct request_queue`, `blk_freeze_acquire_lock()` and the store functions in
`block/blk-sysfs.c`.

## block.limits-update: Updating queue limits

- section: Queue locks and limits
- relevance: 4 - the old setter functions are gone

What does a driver hold between `queue_limits_start_update()` and the commit, and what must it
call when it gives up the update? What must be true of outstanding I/O when it calls
`queue_limits_commit_update()`, and when it calls `queue_limits_commit_update_frozen()`? Start
from `queue_limits_start_update()` in `include/linux/blkdev.h`.

## block.limits-validation: Validation of queue limits

- section: Queue locks and limits
- relevance: 4 - a commit can fail, and the caller has to handle the error

What does `queue_limits_commit_update()` check in the limits that it is given, and what does it
return when the check fails? In which state are the limits of the queue and `limits_lock` after a
commit that failed? Start from `blk_validate_limits()`.

# Schedulers

## block.elevator-switch: Switching schedulers

- section: Schedulers
- relevance: 4 - allocation, freeze and registration happen in a fixed order

In a switch of a queue's scheduler, what is allocated before the queue is frozen, and which locks
are held while it is frozen? Which scheduler does the queue have when the new one fails to
initialise? Start from `elv_iosched_store()`.

## block.elevator-switch-unfreeze: Switch steps after unfreeze

- section: Schedulers
- relevance: 4 - a step that moves into the frozen part changes the lock order

In a switch of a queue's scheduler, what is done only after the queue is unfrozen, and which locks
are held for it? Start from `elevator_change()`.

## block.depth-updated: Depth update callback

- section: Schedulers
- relevance: 5 - a scheduler computes its limits from fields it must see updated

Who calls a scheduler's `depth_updated` callback, at initialisation and afterwards, and which
depth fields of the queue have been written when it runs? What must a scheduler have set before
the first call?

# Requests and dispatch

## block.request-lifecycle: Request state and timeouts

- section: Requests and dispatch
- relevance: 4 - timeouts and completions race through these

What do a request's state and its reference count each protect, and how do the timeout handler
and a normal completion avoid both finishing the same request? What may a driver's timeout
handler therefore not assume about the request it is given? Start from `enum mq_rq_state`.

## block.queue-rq-contract: Driver dispatch contract

- section: Requests and dispatch
- relevance: 4 - what a driver must do before and after returning

For each status that a driver's `queue_rq` can return, what must the driver have done with the
request, and what does the core then do with the request and with the queue? What do `bd->last`
and `commit_rqs` require of each other? Start from `struct blk_mq_ops`.

## block.queue-rq-context: Dispatch calling context

- section: Requests and dispatch
- relevance: 4 - a patch that adds a sleeping call to the dispatch callback is correct only in some drivers

In which context does the core call a driver's `queue_rq`, and what decides whether `queue_rq` may
sleep? Start from `struct blk_mq_ops`.

# Model gaps

## block.model-gaps: Other mistakes models make

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
