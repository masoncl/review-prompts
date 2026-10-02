# Questions: io_uring (measurement set)

- guide: io_uring.md
- title: io_uring Subsystem

A wide set of questions about io_uring: the ring and request structures, the
path a request takes from SQE to CQE, task work, the completion queue,
multishot and poll, provided and registered buffers, the networking and
passthrough opcodes, the SQPOLL and io-wq threads, cancellation, teardown and
registration. It is used to measure what a model already knows before deciding
what the built guide should spend its words on. The hand-written guide it will
replace is 1,741 words. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## uring.core-files: Source files

- section: Finding your way
- relevance: 4 - the core file has been split and new files added
- words: 150

Which files under `io_uring/` hold the core submission and completion code, task
work, waiting for completions, the opcode tables, provided buffers, registered
resources, mapped regions, poll, cancellation, timeouts, the SQPOLL thread, the
worker pool, per-task state, registration, the networking opcodes, zero-copy
send notifications, zero-copy receive, passthrough commands, message passing
between rings, the BPF hooks and the test-only file? Say which are built only
under a config option. A table. Start from `io_uring/Makefile`.

## uring.headers: Headers

- section: Finding your way
- relevance: 3 - drivers include a different header from the core
- words: 70

Which headers outside `io_uring/` declare the ring and request structures, the
user-visible ABI, the interface a driver uses to implement passthrough
commands, the hooks the rest of the kernel calls at fork, exec and exit, and the
trace events?

## uring.docs-and-tests: Documentation and tests

- section: Finding your way
- relevance: 2 - most testing lives outside the tree
- words: 60

What documentation and tests for io_uring are in the kernel tree, what do they
cover, and where does the main regression test suite live? Start from
`Documentation/networking/iou-zcrx.rst` and `tools/testing/selftests/`.

## uring.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

For each job (create a ring, submit and wait, register a resource, initialise
one request from an SQE, issue a request, run it in a worker, arm poll for a
retry, post its CQE, free it, cancel everything at task exit, tear the ring
down when the file is closed), which function do you start reading from? A
table.

## uring.ring-ctx: Ring context

- section: Core structures
- relevance: 4 - which lock covers which group of fields
- words: 110

How is `struct io_ring_ctx` laid out: what groups of fields does it have, and
for the submission state, the completion queue cache, the task work list, the
timeout lists, the overflow list, the buffer tables and the mapped regions,
which lock or rule protects each?

## uring.internal-ring-flags: Internal ring state flags

- section: Core structures
- relevance: 3 - state that used to be separate fields
- words: 80

Besides the setup flags userspace passes, what internal state flags does a ring
carry, where are they stored, what does each mean, and which are derived once at
ring creation from the setup flags? Write each flag's name in full. Start from
`io_ring_ctx_alloc()` and `io_uring_create()`.

## uring.request-struct: Request structure

- section: Core structures
- relevance: 5 - fields share storage, and using one destroys another
- words: 120

Describe `struct io_kiocb`: how per-opcode data is overlaid on it and what
limits its size, and which fields share storage in a union so that using one
mode (poll hashing, IOPOLL, RCU freeing, provided buffer, registered buffer,
completion batching, task work) rules out another.

## uring.request-flags: Request flags

- section: Core structures
- relevance: 4 - flags decide which cleanup runs
- words: 110

How are the `REQ_F_` flags defined and typed, which of them are copied straight
from the SQE, and which sets of flags send a completing request down the slow
cleanup path? Start from `IO_REQ_CLEAN_FLAGS` and `io_free_batch_list()`.

## uring.task-context: Per-task context

- section: Core structures
- relevance: 3 - task references are cached and easy to unbalance
- words: 90

What does `struct io_uring_task` hold, how does a task become attached to a
ring, how are task references taken and returned in batches, and what does the
inflight counter count? Start from `io_uring_add_tctx_node()` and
`io_task_refs_refill()`.

## uring.shared-rings: Shared ring memory

- section: Core structures
- relevance: 4 - every field in it can change under the kernel
- words: 100

What memory does the kernel share with userspace for the SQ and CQ, which side
writes which head and tail and with what ordering, and why does the context keep
two pointers to the rings structure? Start from `struct io_rings` and
`io_get_rings()`.

## uring.opcode-tables: Opcode tables

- section: Request lifecycle
- relevance: 4 - a new or changed opcode is mostly an entry here
- words: 110

What are the two per-opcode tables, what does each field and callback in them
mean, when is each callback called, and what checks them for consistency at
boot? Start from `struct io_issue_def` and `io_uring_optable_init()`.

## uring.adding-opcode: Adding an opcode

- section: Request lifecycle
- relevance: 3 - the steps are spread over several files
- words: 90

What does adding a new opcode involve: the ABI enum, the table entries, the
per-opcode structure, prep and issue handlers, cleanup, and anything it has to
do to work under a config option being off?

## uring.submission-path: Submission path

- section: Request lifecycle
- relevance: 5 - the order of steps is what every handler relies on
- words: 130

Trace one SQE from `io_submit_sqes()` to its first issue attempt: fetching the
SQE, initialising the request, the checks made before prep, prep, link assembly,
and inline issue. Which of those run with the ring mutex held, and what happens
to a request whose prep fails part way through a link?

## uring.sqe-reading: Reading SQE fields

- section: Request lifecycle
- relevance: 5 - the SQE is user memory that can change and be reused
- words: 90

What usage of the SQE pointer in a prep or issue handler is unsafe, and what
that looks similar is correct? Cover how fields must be read, until when the SQE
memory stays valid, and whether the fields of a freshly allocated request can be
assumed to be zero. Name in-tree code that shows each.

## uring.issue-flags: Issue flags

- section: Request lifecycle
- relevance: 5 - handlers branch on them to decide locking and completion
- words: 110

Give a table of the `IO_URING_F_` issue flags: what each tells an issue handler
and which caller sets it (inline submission, task work, poll retry, worker,
cancel). Write each flag's name in full. Start from
`enum io_uring_cmd_flags`.

## uring.issue-return-codes: Issue return codes

- section: Request lifecycle
- relevance: 5 - the wrong code double-completes or leaks a request
- words: 110

What values may an issue handler return, and what does the core do with the
request for each? Include the codes specific to requests run from poll. Start
from `io_issue_sqe()` and `io_poll_check_events()`.

## uring.async-punt: Going async

- section: Request lifecycle
- relevance: 4 - decides where a request runs next
- words: 100

When inline issue cannot complete a request without blocking, what does the
core do next, in what order, and what decides between waiting with poll and
handing the request to a worker? Start from `io_queue_async()` and
`io_arm_poll_handler()`.

## uring.completion-paths: Completion paths

- section: Request lifecycle
- relevance: 5 - each is legal only in some contexts
- words: 120

What are the ways a request's final CQE gets posted (batched under the ring
mutex, posted directly, or handed to task work), which execution context uses
which, and what usage of the batched form is unsafe? Start from
`io_req_complete_defer()`, `io_req_complete_post()` and
`io_req_queue_tw_complete()`.

## uring.request-recycling: Request recycling

- section: Request lifecycle
- relevance: 4 - the order of teardown steps matters
- words: 100

What happens to a request after its CQE is posted: in what order are its links,
poll state, opcode resources, file, resource nodes and task reference released,
and where does the request structure go? Start from `io_free_batch_list()`.

## uring.request-refs: Request reference counts

- section: Request lifecycle
- relevance: 4 - most requests are not reference counted at all
- words: 80

When does a request have a reference count, who enables it and with what
initial value, and what happens to a request that does not have one when it
completes? Start from `io_uring/refs.h`.

## uring.links: Linked requests

- section: Request lifecycle
- relevance: 3 - failure handling differs for the two kinds of link
- words: 100

How is a chain of linked requests assembled, started and continued, how does a
failure propagate for each kind of link, how does a linked timeout fit in, and
which lock covers changing a chain after submission? Start from
`io_req_find_next()` and `io_disarm_next()`.

## uring.drain: Drain

- section: Request lifecycle
- relevance: 2 - rarely touched, but it hooks the hot path
- words: 70

How is draining implemented: what state marks a ring as draining, where are
held-back requests kept, what condition releases them, and which SQE flag
disables drain for the ring? Start from `io_drain_req()` and
`io_queue_deferred()`.

## uring.cleanup-flag: Opcode cleanup flag

- section: Request state that must stay consistent
- relevance: 5 - the usual cause of leaks in prep error paths
- words: 100

How does the core decide whether to call an opcode's cleanup handler, what
usage of that mechanism in a prep handler leaks or double frees, and what that
looks similar is correct? Name handlers that show it. Start from
`io_clean_op()`.

## uring.async-data: Async data

- section: Request state that must stay consistent
- relevance: 5 - pointer and flag must agree or it is freed twice
- words: 110

How is a request's `async_data` allocated, returned to a cache and freed, what
keeps the pointer and its flag consistent, what usage is unsafe and what that
looks similar is correct, and in which handler should it be allocated? Start
from `io_uring_alloc_async_data()`.

## uring.alloc-caches: Allocation caches

- section: Request state that must stay consistent
- relevance: 3 - a put can fail and entries come back dirty
- words: 90

Which object types are kept in `struct io_alloc_cache` caches, what lock covers
a cache, what must a caller do when putting an object back fails, and what is
and is not cleared in an object taken from a cache? Start from
`io_uring/alloc_cache.h`.

## uring.recycling-from-workers: Recycling outside the ring mutex

- section: Request state that must stay consistent
- relevance: 4 - a worker must not touch the caches
- words: 80

When an opcode finishes in a worker thread, what happens to its async data and
cached iovec instead of being recycled, how does the code tell, and who frees
them later? Start from `io_netmsg_recycle()`, `io_rw_recycle()` and
`io_req_uring_cleanup()`.

## uring.task-work-queues: Task work queues

- section: Task work
- relevance: 5 - the data structure and its names have changed
- words: 120

What are the two places a request's task work can be queued, which ring setup
flag chooses between them, what data structure is each queue, where is each
consumer's cursor kept, and which function runs each? Start from
`__io_req_task_work_add()`.

## uring.task-work-queue-rules: Queue producer and consumer rules

- section: Task work
- relevance: 4 - a consumer that misreads the queue loses or spins on work
- words: 100

For the queue type the task work lists use: from which contexts may producers
push, how must consumers be serialised, how does a consumer tell an empty queue
from one it has to come back to, and what must it not do while it waits? If the
lists are plain lock-free lists in this tree, say so. Start from
`io_uring/mpscq.h`.

## uring.tw-token: Task work token

- section: Task work
- relevance: 4 - it is a promise about the caller's context
- words: 90

What does holding an `io_tw_token_t` guarantee, what does its one field mean
and who sets it, who may create one, and what should code that is not running
as task work call to complete a request instead? Start from
`struct io_tw_state`.

## uring.tw-task-exiting: Task work for an exiting task

- section: Task work
- relevance: 4 - the fallback has been reworked
- words: 90

What happens to queued task work when the target task can no longer run it, for
each of the two queues, and how does a task work handler learn that it should
cancel instead of proceed? Start from `io_should_terminate_tw()` and
`io_req_normal_work_add()`.

## uring.defer-taskrun: Deferred task running

- section: Task work
- relevance: 5 - only one task may run the work or post CQEs
- words: 110

With `IORING_SETUP_DEFER_TASKRUN`, who may run the ring's task work and post
CQEs, what is returned to anyone else, how does queuing work decide whether to
wake the waiter, and what do the values of the wait counter mean? Start from
`io_req_local_work_add()` and `io_uring/wait.h`.

## uring.tw-add-flags: Task work add flags

- section: Task work
- relevance: 3 - the lazy flag is unsafe for some requests
- words: 70

What flags can be passed when queuing task work, what does each do, and for
which requests must the lazy one not be used? Start from `IOU_F_TWQ_LAZY_WAKE`.

## uring.exit-cancel-loop: Ring exit and local task work

- section: Task work
- relevance: 4 - a cancel loop that leaves work queued spins forever
- words: 90

When a ring with deferred task running is torn down by something other than
its submitter task, how is its queued task work run, what usage in a loop that
cancels requests is unsafe, and what does the correct loop look like? Start from
`io_ring_exit_work()`.

## uring.cq-locking: CQ locking

- section: Completion queue
- relevance: 5 - which lock is needed depends on the ring's mode
- words: 100

What must be held, or which task must be running, to post a CQE for each kind
of ring (default, single-issuer with deferred task running, IOPOLL), which
helper asserts it, and which internal flags record the choice? Start from
`io_lockdep_assert_cq_locked()`.

## uring.cqe-posting-helpers: CQE posting helpers

- section: Completion queue
- relevance: 5 - each helper is only legal in some contexts
- words: 120

Give a table of the helpers that post a CQE other than a request's final one:
for each, the context and locks it requires, whether it handles overflow
itself, and who flushes afterwards. Start from `io_post_aux_cqe()`,
`io_add_aux_cqe()` and `io_req_post_cqe()`.

## uring.cq-overflow: CQ overflow

- section: Completion queue
- relevance: 4 - ordering and the cached range must survive a flush
- words: 110

What happens when the CQ ring is full: where do CQEs go, what can be dropped and
how is that reported, why can a CQE not be posted directly while overflow
entries are pending, and what must the flush do to the cached CQE range before
it drops the lock? Start from `__io_cqring_overflow_flush()` and
`io_cqe_cache_refill()`.

## uring.big-cqes: 32-byte CQEs

- section: Completion queue
- relevance: 4 - two ring modes that look alike and are not
- words: 110

How do the two ring modes that allow 32-byte CQEs differ in how slots are
counted, what does the boolean that `io_get_cqe()` takes mean in each mode, what
usage of it is unsafe, and what happens when a 32-byte CQE would straddle the
end of the ring?

## uring.big-sqes: 128-byte SQEs

- section: Completion queue
- relevance: 3 - a newer mode with its own opcodes
- words: 70

How does the core handle 128-byte SQEs on a ring where only some SQEs are that
size: which opcodes need it, how is the second slot accounted for, and what is
rejected? Start from `io_init_req()`.

## uring.cq-waiting: Waiting for completions

- section: Completion queue
- relevance: 3 - several wait modes share one loop
- words: 100

How does a task wait for completions: what does it run before sleeping, how do
the minimum-wait timeout, the absolute timer and the registered wait argument
work, and how does waiting differ with deferred task running? Start from
`io_cqring_wait()`.

## uring.eventfd: Eventfd signalling

- section: Completion queue
- relevance: 3 - freed by RCU and signalled from odd contexts
- words: 90

How is the registered eventfd's lifetime managed, what usage when dropping a
reference is unsafe, when is the signal deferred instead of sent directly, and
what stops a signal when no new CQE was posted? Start from
`io_eventfd_signal()`.

## uring.poll-ownership: Poll ownership

- section: Poll and multishot
- relevance: 4 - the rule that stops two contexts touching one request
- words: 110

How does the poll code decide which context may touch a polled request: what
does `poll_refs` encode, how is ownership taken and released, what do the
cancel and retry bits do, and what may a wakeup handler that fails to take
ownership do? Start from `io_poll_get_ownership()`.

## uring.multishot-flags: Multishot flags

- section: Poll and multishot
- relevance: 5 - three flags with similar names mean different things
- words: 90

What is the difference between the two request flags that mark a multishot
request and the issue flag with a similar name, when is each set, and which one
must a handler test before it keeps a request armed?

## uring.multishot-returns: Multishot handler results

- section: Poll and multishot
- relevance: 5 - the codes have been renamed and one is gone
- words: 110

What does a multishot issue handler return to stay armed, to finish, and to be
run again at once, how does it post its intermediate CQEs and what does it do
if posting fails, and what usage on the would-block path is unsafe? Start from
`io_read_mshot()` and `io_recv_finish()`.

## uring.multishot-workers: Multishot and workers

- section: Poll and multishot
- relevance: 4 - intermediate CQEs cannot come from a worker
- words: 80

What does the worker entry point do with a multishot request, why, and which
flags must a request that posts more than one CQE carry so that this check
catches it? Start from `io_wq_submit_work()`.

## uring.poll-events: Poll event handling

- section: Poll and multishot
- relevance: 3 - generic code must not guess what an event means
- words: 80

What usage of poll event bits in the generic poll code is unsafe and where does
interpreting them belong, and what does the code do when a wakeup was caused by
the ring's own completion? Start from `io_poll_wake()`.

## uring.provided-buffer-kinds: Provided buffer kinds

- section: Provided buffers
- relevance: 4 - two implementations behind one flag
- words: 100

What are the two kinds of provided buffer, what structures and list flags
represent each, which request flags record that one has been selected, and
which of them live in memory shared with userspace?

## uring.buffer-ring-memory: Buffer ring memory access

- section: Provided buffers
- relevance: 4 - userspace can rewrite an entry between two reads
- words: 80

What usage of a buffer ring entry's fields by the kernel is unsafe, what that
looks similar is correct, and which structure needs no such care? Start from
`io_ring_buffer_select()` and `io_kbuf_inc_commit()`.

## uring.buffer-list-lifetime: Buffer list lifetime

- section: Provided buffers
- relevance: 4 - a stored pointer outlives the list
- words: 90

How long is a pointer to a buffer list valid, what is `struct io_br_sel` for,
what usage of the selected list across a retry or a lock drop is unsafe, and
what do handlers do instead?

## uring.buffer-commit: Buffer commit

- section: Provided buffers
- relevance: 5 - decides whether a buffer can be handed out twice
- words: 110

When is a ring-provided buffer consumed at selection time and when is that left
to the opcode, which function decides, what must a new opcode that commits for
itself change there, and what must be captured before a commit? Start from
`io_should_commit()`.

## uring.buffer-recycle: Buffer recycle and put

- section: Provided buffers
- relevance: 4 - the wrong one loses or reuses a buffer
- words: 110

What is the difference between recycling a selected buffer and putting it, when
must each be called, what stops a recycle, and what should a handler do with its
buffer when it returns to wait for poll or retries after a partial transfer?
Start from `io_kbuf_recycle()` and `io_put_kbufs()`.

## uring.incremental-buffers: Incremental buffer consumption

- section: Provided buffers
- relevance: 3 - the commit loop reads lengths userspace controls
- words: 80

How does incremental consumption of a ring buffer work, what makes the commit
loop terminate, what decides that a partly used buffer is finished, and how is
userspace told more of the buffer remains? Start from `io_kbuf_inc_commit()`.

## uring.bundles: Bundles

- section: Provided buffers
- relevance: 3 - the count passed on completion is easy to get wrong
- words: 80

How does a send or receive use several provided buffers at once, how is the
number of buffers consumed worked out, and what length must be passed when the
buffers are put after a retried transfer? Start from `io_bundle_nbufs()` and
`io_recv_finish()`.

## uring.buffer-ring-registration: Buffer ring registration

- section: Provided buffers
- relevance: 3 - races with mmap and with requests in flight
- words: 90

What does registering and unregistering a buffer ring do, which locks cover the
lookup table against mmap, and what happens when the group id already has a
legacy list? Start from `io_register_pbuf_ring()`.

## uring.rsrc-nodes: Resource nodes

- section: Registered resources
- relevance: 4 - the reference is a plain integer
- words: 100

What is a `struct io_rsrc_node`, what protects its reference count, when is a
reference taken and dropped for a file and for a buffer, what happens when the
last one goes, and what is the tag for? Start from `io_put_rsrc_node()`.

## uring.registered-buffers: Registered buffer layout

- section: Registered resources
- relevance: 4 - offset arithmetic goes wrong on unaligned buffers
- words: 110

What does `struct io_mapped_ubuf` record, how are pages coalesced at
registration, what usage when computing an offset into the buffer is unsafe and
what is correct, and how are the pages released? Start from
`io_sqe_buffer_register()` and `io_vec_fill_bvec()`.

## uring.registered-buffer-import: Importing a registered buffer

- section: Registered resources
- relevance: 5 - the node is attached to whichever request is passed in
- words: 100

Which functions turn a registered buffer index into an iterator, to which
request do they attach the buffer's node and through which argument, what flag
records that, and what is checked about direction and range?

## uring.kernel-registered-buffers: Kernel-owned registered buffers

- section: Registered resources
- relevance: 3 - a driver can put its own pages in the table
- words: 80

How does a driver place kernel pages in a ring's buffer table, how does the
import path treat such a buffer differently, and what runs when its last
reference is dropped? Start from `io_buffer_register_bvec()`.

## uring.buffer-accounting: Pinned memory accounting

- section: Registered resources
- relevance: 3 - huge pages and clones are counted once
- words: 90

How is pinned memory for registered buffers charged and uncharged, how are huge
pages shared between buffers counted, and what must two rings have in common for
buffers to be cloned between them? Start from `io_buffer_account_pin()` and
`io_clone_buffers()`.

## uring.rsrc-registration-failure: Failed resource registration

- section: Registered resources
- relevance: 2 - one fix, but it posts stray CQEs when wrong
- words: 60

When registering a table of files or buffers fails part way, what must be done
to the entries already installed before they are released, and why? Start from
`io_clear_table_tags()`.

## uring.fixed-files: Fixed files

- section: Registered resources
- relevance: 3 - slot state is packed into the pointer
- words: 80

How is the fixed file table represented, what is packed beside the file
pointer, how is a free slot chosen, and how does a request take and drop its
reference on a fixed file? Start from `io_file_get_fixed()` and
`io_install_fixed_file()`.

## uring.zc-send-lifetime: Zero-copy send lifetime

- section: Networking
- relevance: 5 - the wrong owner frees pages the network still uses
- words: 120

In a zero-copy send, what object outlives the request until the network stack
has finished with the pages, when is it allocated, what must be attached to it
and not to the request, and which functions issue the plain and the message
forms? Start from `io_send_zc_prep()` and `io_alloc_notif()`.

## uring.notif-flush: Notification flush

- section: Networking
- relevance: 4 - flushing twice is a use after free
- words: 90

What does flushing a send notification do, from which places can it happen,
what usage is unsafe, and does the context the send ran in change where the
flush is done? Start from `io_notif_flush()`.

## uring.net-retry: Partial sends and receives

- section: Networking
- relevance: 3 - retry state lives in three places
- words: 90

How does a send or receive that transferred part of its data retry: what
decides a retry is allowed, where is progress kept, and what happens to a
selected buffer before returning? Start from `io_net_retry()` and
`io_net_kbuf_recyle()`.

## uring.zcrx: Zero-copy receive

- section: Networking
- relevance: 3 - a page pool provider with user-visible references
- words: 120

Describe zero-copy receive: the interface queue and area structures, the page
pool callbacks io_uring provides and what each does, where DMA mappings are
made and undone, how buffers come back from userspace, and what is done at
ring exit before the final free. Start from `io_register_zcrx()` and
`io_pp_zc_init()`.

## uring.cmd-sqe-lifetime: Passthrough command SQE

- section: Passthrough commands
- relevance: 5 - the one opcode that keeps the SQE pointer
- words: 110

For passthrough commands, how long does the handler's SQE pointer refer to ring
memory, what makes it safe once the request goes async, what usage in a driver's
issue path is unsafe, and what that looks similar is correct? Start from
`io_uring_cmd_prep()` and `io_uring_cmd_sqe_copy()`.

## uring.cmd-driver-api: Passthrough driver interface

- section: Passthrough commands
- relevance: 4 - what a driver may call and from where
- words: 110

What does a driver implementing the passthrough file operation get and return,
how does it complete a command later or move to task context, how does it make
a command cancelable, and how much private space does it have? Start from
`include/linux/io_uring/cmd.h`.

## uring.iopoll: IOPOLL completion

- section: Reads, writes and timeouts
- relevance: 4 - a request that never marks itself done hangs the ring
- words: 110

How are requests on an IOPOLL ring tracked and reaped: what list are they on and
what protects it, how does a completion callback tell the reaper it is done,
what usage in that callback is unsafe, and how is a request that must be
reissued handled? Start from `io_do_iopoll()` and `io_complete_rw_iopoll()`.

## uring.timeouts: Timeout lock

- section: Reads, writes and timeouts
- relevance: 4 - a raw lock that must not be held across completion
- words: 90

What kind of lock protects the timeout lists, what usage while holding it is
unsafe, how does the code that kills timeouts avoid it, and in what order is it
taken with the completion lock? Start from `io_kill_timeout()`.

## uring.msg-ring: Messages between rings

- section: Other opcodes
- relevance: 4 - a request allocated outside the normal cache
- words: 100

How does posting a CQE to another ring work: when is it done directly and when
through the target's task work, how is the carrier request allocated and freed
and what usage there is unsafe, and how are the two ring mutexes taken? Start
from `io_msg_ring()` and `io_msg_data_remote()`.

## uring.inflight-tracking: Inflight tracking

- section: Other opcodes
- relevance: 3 - decides what is cancelled when files are closed
- words: 80

What does marking a request inflight do, which requests need it, when must it be
done, and how does task cancellation use the two inflight counts? Start from
`io_req_track_inflight()`.

## uring.futex-waitid: Futex and waitid requests

- section: Other opcodes
- relevance: 2 - small, but each has its own claim protocol
- words: 80

How are futex and waitid requests tracked for cancellation, how does each
settle the race between a wakeup and a cancel, and where is their async data
allocated? Start from `io_futex_wait()` and `io_waitid()`.

## uring.cancel: Cancellation

- section: Cancellation and teardown
- relevance: 4 - several tables have to be searched
- words: 110

How does cancelling a request by key work: what can be matched on, in what
order are the places a request can be waiting searched, what stops one request
being matched twice, and how does the synchronous form differ? Start from
`io_try_cancel()` and `io_cancel_req_match()`.

## uring.task-exit-cancel: Task exit and exec

- section: Cancellation and teardown
- relevance: 4 - the loop must reach zero inflight or the task hangs
- words: 110

What happens to a task's requests at exit and at exec: which function loops,
what does each pass try to cancel, how does it wait, and how does the SQPOLL
thread's version differ? Start from `io_uring_cancel_generic()` and
`io_uring_try_cancel_requests()`.

## uring.ring-teardown: Ring teardown

- section: Cancellation and teardown
- relevance: 4 - the order of frees at the end is fixed
- words: 110

What happens from the last close of a ring file to freeing the context: what is
killed first, what does the exit work loop on, how are other tasks' references
to the ring removed, which RCU wait is needed, and in what order does the final
free release things? Start from `io_ring_ctx_wait_and_kill()` and
`io_ring_ctx_free()`.

## uring.sqpoll-thread-pointer: SQPOLL thread pointer

- section: Threads
- relevance: 5 - the task can exit and be freed under a reader
- words: 100

How may code read the pointer to the SQPOLL thread, what usage is unsafe, what
that looks similar is correct, which task should be signalled for a request's
task work, and who owns the task reference after the thread is started? Start
from `sqpoll_task_locked()` and `io_sq_offload_create()`.

## uring.sqpoll-parking: SQPOLL park and stop

- section: Threads
- relevance: 3 - the way to get exclusive access to the thread's rings
- words: 80

How does other code stop the SQPOLL thread from touching its rings for a while,
what does it hold afterwards, and how is the thread stopped for good? Start from
`io_sq_thread_park()`.

## uring.io-wq: Worker pool

- section: Threads
- relevance: 3 - workers are real threads of the submitting process
- words: 110

How does the worker pool run requests: what are bound and unbound work, hashed
work, how are workers created and what kind of thread are they, how is queued
and running work cancelled, and what does a request need set up before it is
queued? Start from `io_queue_iowq()` and `io_wq_enqueue()`.

## uring.register-dispatch: Registration calls

- section: Registration and memory
- relevance: 3 - locking and restrictions are applied in one place
- words: 90

How is the register system call dispatched: what is held while an opcode runs,
how are restrictions applied, which opcodes work without a ring, and how does a
disabled ring get enabled? Start from `__io_uring_register()`.

## uring.ring-resize: Ring resize

- section: Registration and memory
- relevance: 4 - swaps memory that others read without the mutex
- words: 100

What does resizing the rings require of the ring's setup, which locks does it
take and in what order, how are readers that do not hold the ring mutex kept
safe, and what would a new operation that changes ring geometry have to do?
Start from `io_register_resize_rings()`.

## uring.memory-regions: Mapped regions

- section: Registration and memory
- relevance: 3 - one abstraction now backs every shared mapping
- words: 90

What is a `struct io_mapped_region`, which shared areas are built on it, how is
one created from user or kernel memory and later mapped by userspace, and which
lock covers the lookup at mmap time? Start from `io_create_region()` and
`io_uring_mmap()`.

## uring.restrictions-filters: Restrictions and filters

- section: Registration and memory
- relevance: 3 - checked on every request once enabled
- words: 90

How can a ring's allowed operations be restricted: what can be limited, when
can restrictions be set, how do BPF filters on opcodes work and get inherited,
and where in submission are both checked?

## uring.bpf-loop: BPF-driven loop

- section: Registration and memory
- relevance: 2 - new and small, but it changes what enter does
- words: 80

What does a BPF struct_ops attached to a ring do: which callback does it
supply, what may that program call, how does the enter system call behave once
one is attached, and what is held while it runs? If this tree has none, say so.
Start from `io_run_loop()`.

## uring.lock-order: Lock order

- section: Changing the implementation
- relevance: 5 - six locks and only some orders are legal
- words: 110

Give the nesting order of the ring mutex, the completion lock, the timeout
lock, the list-of-tasks lock, the mmap lock and the SQPOLL data lock, say which
are sleeping locks and which can be taken from interrupt context, and name a
place where two rings' mutexes are held together.

## uring.change-checklist: Changing the core

- section: Changing the implementation
- relevance: 4 - the same request runs in four contexts
- words: 110

What must a change to the submission or completion core keep working: the
execution contexts a handler can be called in, the ring modes that change
locking, 32-bit compat, the ABI structures and feature flags, and where are
changes tested?
