# Questions: io_uring Subsystem

- guide: io_uring.md
- title: io_uring Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/io_uring-measurement.md` is the
wider set the readers were measured on and `catalogue/io_uring-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## uring.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## uring.core-files: Source files

- relevance: 4 - task work, waiting and the BPF hooks have files no reader placed

A table and nothing else, job to file under `io_uring/`: core submission and completion; task
work; waiting for completions; the opcode tables; provided buffers; registered resources; mapped
regions; poll; cancellation; timeouts; the SQPOLL thread; the worker pool; per-task state;
registration; the networking opcodes; zero-copy send notifications; zero-copy receive;
passthrough commands; message passing between rings; the BPF hooks; the test-only file. Mark the
rows that are built only under a config option. Start from `io_uring/Makefile`.

# The ring context and its locks

## uring.internal-ring-flags: Internal ring state flags

- section: The ring context and its locks
- relevance: 4 - every reader used field names that are now bits in one word

Where does `struct io_ring_ctx` keep the ring's internal state flags, and what is the pattern of
their names? Which of them are derived once at ring creation from the setup flags, so that code
may rely on them never changing? Start from `io_ring_ctx_alloc()` and `io_uring_create()`.

## uring.ring-ctx: Ring context field locks

- section: The ring context and its locks
- relevance: 4 - which lock covers which group of fields

In `struct io_ring_ctx`, which lock or rule protects each of the submission state, the cached
range of CQEs, the task work list, the timeout lists, the overflow list, the buffer tables and
the mapped regions? A table. Say which of them have a rule and no lock.

## uring.lock-order: Lock order

- section: The ring context and its locks
- relevance: 5 - six locks and only some orders are legal

In what order do `uring_lock`, `completion_lock`, `timeout_lock`, `tctx_lock` and `mmap_lock` of
`struct io_ring_ctx` and `lock` of `struct io_sq_data` nest, and which of them may be taken from
interrupt context? What are the requirements for code that takes the `uring_lock` of a second ring
while it holds the `uring_lock` of the first, in order to assure safe usage? Name in-tree code
that shows it.

## uring.timeouts: Timeout lock

- section: The ring context and its locks
- relevance: 4 - a raw lock that must not be held across completion

What kind of lock is `timeout_lock` of `struct io_ring_ctx`, and what are the requirements for
code that holds it in order to assure safe usage? In what order is it taken with
`completion_lock`? Start from `io_kill_timeout()`.

## uring.shared-rings: Shared ring memory

- section: The ring context and its locks
- relevance: 4 - every field in it can change under the kernel

What are the requirements for kernel code that reads the fields of `struct io_rings` in order to
assure safe usage? Which of the pointers to `struct io_rings` in `struct io_ring_ctx` must code
use in which context? Start from `struct io_rings` and `io_get_rings()`.

## uring.ring-resize: Ring resize

- section: The ring context and its locks
- relevance: 4 - swaps memory that others read without the mutex

What does `io_register_resize_rings()` require of the ring's setup flags, and how does it keep
readers of the ring memory that do not hold `uring_lock` safe while it replaces the rings? Start
from `io_register_resize_rings()`.

# Request state

## uring.request-struct: Request structure unions

- section: Request state
- relevance: 4 - fields share storage, and two readers had the unions wrong

Which features of a request cannot be used together because their state shares storage in `struct
io_kiocb`, and how does code know which one is live? What limits the size of the opcode's private
data that `io_kiocb_to_cmd()` overlays on the request?

## uring.request-refs: Request reference counts

- section: Request state
- relevance: 4 - most requests are not reference counted at all

Which requests have a reference count, and what is its initial value when it is enabled? What do
the helpers in `io_uring/refs.h` do when they are called on a request whose reference count is not
enabled? Start from `io_uring/refs.h`.

## uring.sqe-reading: Reading SQE fields

- section: Request state
- relevance: 5 - the SQE is user memory that can change and be reused

What are the requirements for a prep or issue handler that reads fields through its `struct
io_uring_sqe` pointer in order to assure safe usage, and until what point does that pointer stay
valid? May a prep handler assume that the fields of its `struct io_kiocb` are zero? Name in-tree
code that shows each.

## uring.cleanup-flag: Opcode cleanup flag

- section: Request state
- relevance: 5 - the usual cause of leaks in prep error paths

How does `io_clean_op()` decide whether to call an opcode's cleanup handler? What are the
requirements for a prep handler whose opcode has a cleanup handler, in order to assure safe usage?
Name handlers that show it. Start from `io_clean_op()`.

## uring.async-data: Async data

- section: Request state
- relevance: 5 - pointer and flag must agree, and the usual rule has an exception

What are the requirements for code that sets or clears `async_data` of a `struct io_kiocb` and
`REQ_F_ASYNC_DATA` in order to assure safe usage? In which handlers do opcodes allocate async
data, and which code frees it or returns it to a cache? Start from `io_uring_alloc_async_data()`.

## uring.async-data-by-hand: Async data set by hand

- section: Request state
- relevance: 5 - the core frees async data in one way, and an opcode that allocates its own in another way has to match it

What are the requirements for an opcode that gets its async data by other means than
`io_uring_alloc_async_data()`, in order to assure safe usage? Name in-tree code that shows it.
Start from `io_uring_alloc_async_data()` and `io_clean_op()`.

## uring.recycling-from-workers: Async data recycling from io-wq

- section: Request state
- relevance: 4 - a worker must not touch the caches; no reader had the mechanism

What do `io_netmsg_recycle()`, `io_rw_recycle()` and `io_req_uring_cleanup()` do with a request's
async data and cached iovec when they run in an io-wq worker, how do they tell that they run in
one, and which code frees what they leave behind? Start from `io_netmsg_recycle()`,
`io_rw_recycle()` and `io_req_uring_cleanup()`.

## uring.request-free: Freeing a completed request

- section: Request state
- relevance: 4 - flags decide which cleanup runs, and the order of release matters

What does `io_free_batch_list()` skip for a request that has no flag of `IO_REQ_CLEAN_SLOW_FLAGS`
set? In what order does it release what a request holds, and where does the `struct io_kiocb` go
afterwards? Start from `IO_REQ_CLEAN_FLAGS` and `io_free_batch_list()`.

# Submission and issue

## uring.opcode-tables: Opcode tables

- section: Submission and issue
- relevance: 4 - a new or changed opcode is mostly an entry here

What decides whether a per-opcode member belongs in `struct io_issue_def` or in `struct
io_cold_def`, and what does `io_uring_optable_init()` enforce about an entry? Start from `struct
io_issue_def` and `io_uring_optable_init()`.

## uring.opcode-callbacks: Opcode callback contexts

- section: Submission and issue
- relevance: 4 - a callback that assumes a lock the core does not hold races with the rest of the ring

When does the core call each callback of `struct io_issue_def` and `struct io_cold_def`, and which
locks does it hold when it does? Start from `struct io_issue_def` and `struct io_cold_def`.

## uring.submission-path: Submission path

- section: Submission and issue
- relevance: 5 - the order of steps is what every handler relies on

Between fetching an SQE in `io_submit_sqes()` and the first issue attempt, what may a prep
handler assume has already been checked and initialised, and which of the steps run with the
ring mutex held? What happens to a request, and to the rest of its link, when prep fails part
way through a link?

## uring.issue-flags: Issue flags

- section: Submission and issue
- relevance: 5 - handlers branch on them; readers offered one that does not exist and missed one that does

A table of the `IO_URING_F_` issue flags: what each tells an issue handler it may or may not do,
and which caller of the handler sets it. Write each flag's name in full. Start from `enum
io_uring_cmd_flags`.

## uring.issue-return-codes: Issue return codes

- section: Submission and issue
- relevance: 5 - the wrong code double-completes or leaks a request, and the names changed

What values may an issue handler return, and what does the core do with the request for each?
Include the codes specific to requests run from poll. Start from `io_issue_sqe()` and
`io_poll_check_events()`.

## uring.async-punt: Punt to poll or io-wq

- section: Submission and issue
- relevance: 4 - decides where a request runs next

When inline issue cannot complete a request without blocking, what does the core do next and in
what order, and what decides between waiting with poll and handing the request to a worker?
Start from `io_queue_async()` and `io_arm_poll_handler()`.

# Posting completions

## uring.completion-paths: Completion paths

- section: Posting completions
- relevance: 5 - two readers recommended a helper that is legal only in a worker

Which execution contexts may call each of `io_req_complete_defer()`, `io_req_complete_post()` and
`io_req_queue_tw_complete()` to post a request's final CQE? What are the requirements for a caller
of `io_req_complete_defer()` and for a caller of `io_req_complete_post()` in order to assure safe
usage? Start from `io_req_complete_defer()`, `io_req_complete_post()` and
`io_req_queue_tw_complete()`.

## uring.cq-locking: CQ locking

- section: Posting completions
- relevance: 5 - which lock is needed depends on the ring mode

What does `io_lockdep_assert_cq_locked()` require of code that posts a CQE, for each combination
of ring setup flags it tells apart, and which flags of `struct io_ring_ctx` record which
requirement applies? Start from `io_lockdep_assert_cq_locked()`.

## uring.cqe-posting-helpers: CQE posting helpers

- section: Posting completions
- relevance: 5 - each helper is only legal in some contexts

A table of the helpers that post a CQE other than a request's final one: for each, the context
and locks it requires, whether it handles overflow itself, and who flushes afterwards. Start
from `io_post_aux_cqe()`, `io_add_aux_cqe()` and `io_req_post_cqe()`.

## uring.big-cqes: 32-byte CQEs

- section: Posting completions
- relevance: 4 - two ring modes that look alike and are not

How do rings set up with `IORING_SETUP_CQE32` and with `IORING_SETUP_CQE_MIXED` differ in how CQ
slots are counted? What are the requirements for the `cqe32` argument of `io_get_cqe()` on each,
in order to assure safe usage? What does `io_cqe_cache_refill()` do when a 32-byte CQE does not
fit before the end of the ring?

## uring.cq-overflow: CQ overflow

- section: Posting completions
- relevance: 4 - ordering and the cached range must survive a flush

When the CQ ring is full, where does a CQE go, which CQEs can be dropped, and how is a drop
reported to userspace? Start from `__io_cqring_overflow_flush()` and `io_cqe_cache_refill()`.

## uring.cq-overflow-pending: Pending overflow entries

- section: Posting completions
- relevance: 4 - a CQE posted past pending overflow entries reaches userspace out of order

What does `io_cqe_cache_refill()` do while overflow entries are pending, and what does
`__io_cqring_overflow_flush()` do to `cqe_cached` and `cqe_sentinel` of `struct io_ring_ctx`
before it drops a lock? Start from `__io_cqring_overflow_flush()` and `io_cqe_cache_refill()`.

## uring.msg-ring: Messages between rings

- section: Posting completions
- relevance: 4 - a request allocated outside the normal cache

When does `io_msg_ring()` post a CQE to the target ring directly, and when through the target's
task work? What are the requirements for allocating and freeing the `struct io_kiocb` that
`io_msg_data_remote()` sends to the target, in order to assure safe usage? How is the target
ring's `uring_lock` taken while the source ring's is held? Start from `io_msg_ring()` and
`io_msg_data_remote()`.

# Task work

## uring.task-work-queues: Task work queues

- section: Task work
- relevance: 5 - every reader described llists that are gone

What data structure holds the task work queued to a task, and what holds the task work queued to a
ring? Which ring setup flag chooses between the two queues, and which function runs each? Start
from `__io_req_task_work_add()`.

## uring.task-work-queue-rules: mpscq producers and consumers

- section: Task work
- relevance: 4 - a consumer that misreads the queue loses work or spins on it

For the queue that `io_uring/mpscq.h` defines: from which contexts may producers push, and how
must consumers be serialised? What are the requirements for a consumer that gets nothing from
`mpscq_pop()`, in order to assure safe usage? If this tree has no `io_uring/mpscq.h`, say so and
stop. Start from `io_uring/mpscq.h`.

## uring.defer-taskrun: Deferred task running

- section: Task work
- relevance: 5 - only one task may run the work, and the wake counter was reworked

With `IORING_SETUP_DEFER_TASKRUN`, which task may run the ring's task work and post CQEs, and what
does any other task get back when it tries? How does `io_req_local_work_add()` decide from
`cq_wait_nr` of `struct io_ring_ctx` whether to wake the waiter? Start from
`io_req_local_work_add()` and `io_uring/wait.h`.

## uring.tw-token: Task work token

- section: Task work
- relevance: 4 - it is a promise about the caller, and the header comment is stale

What does holding an `io_tw_token_t` guarantee to the function that receives it, and which code
may create one? What are the requirements for code that is not running as task work and has to
complete a request, in order to assure safe usage? Start from `struct io_tw_state`.

## uring.tw-task-exiting: Task work at exit

- section: Task work
- relevance: 4 - the fallback functions every reader named do not exist

What happens to queued task work when the target task can no longer run it, for each of the two
queues, and how does a task work handler learn that it should cancel instead of proceed? Start
from `io_should_terminate_tw()` and `io_req_normal_work_add()`.

## uring.exit-cancel-loop: Ring exit cancel loop

- section: Task work
- relevance: 4 - a cancel loop that leaves work queued spins forever

When a ring set up with `IORING_SETUP_DEFER_TASKRUN` is torn down by a task other than its
submitter task, how does `io_ring_exit_work()` get the ring's queued task work run? What are the
requirements for a loop that cancels a ring's requests until none is left, in order to assure safe
usage? Start from `io_ring_exit_work()`.

# Multishot and poll

## uring.poll-ownership: Poll ownership

- section: Multishot and poll
- relevance: 4 - the rule that stops two contexts touching one request

What does `poll_refs` of a `struct io_kiocb` encode, how is ownership of a polled request taken
and released, and what may a wakeup handler that fails to take ownership do to the request? Start
from `io_poll_get_ownership()`.

## uring.multishot-flags: Multishot flags

- section: Multishot and poll
- relevance: 5 - three flags with similar names mean different things

What is the difference between `REQ_F_MULTISHOT`, `REQ_F_APOLL_MULTISHOT` and
`IO_URING_F_MULTISHOT`, when is each set, and which one must a handler test before it keeps a
request armed?

## uring.multishot-returns: Multishot handler results

- section: Multishot and poll
- relevance: 5 - two readers gave a return value that the core warns on

What does a multishot issue handler return to stay armed, to finish, and to be run again at once?
What must it do when `io_req_post_cqe()` fails to post an intermediate CQE? What are the
requirements for a multishot handler whose file would block, in order to assure safe usage? Start
from `io_read_mshot()` and `io_recv_finish()`.

## uring.multishot-workers: Multishot requests in io-wq

- section: Multishot and poll
- relevance: 4 - intermediate CQEs cannot come from a worker

What does the worker entry point do with a multishot request, why, and which flags must a
request that posts more than one CQE carry so that this check catches it? Start from
`io_wq_submit_work()`.

# Provided buffers

## uring.provided-buffer-kinds: Provided buffer kinds

- section: Provided buffers
- relevance: 4 - two implementations behind one flag

How does code tell which kind of provided buffer a `struct io_buffer_list` holds, which request
flags record that a buffer of each kind has been selected, and which structures of each kind live
in memory shared with userspace?

## uring.buffer-ring-memory: Buffer ring memory access

- section: Provided buffers
- relevance: 4 - userspace can rewrite an entry between two reads

What are the requirements for kernel code that reads the fields of a `struct io_uring_buf` of a
buffer ring in order to assure safe usage? Which structures of a provided buffer list are not
shared with userspace? Start from `io_ring_buffer_select()` and `io_kbuf_inc_commit()`.

## uring.buffer-commit: Buffer commit

- section: Provided buffers
- relevance: 5 - decides whether a buffer can be handed out twice

When is a ring-provided buffer consumed at selection time, and when is that left to the opcode?
Which code sets `REQ_F_BUFFERS_COMMIT`, and what are the requirements for an opcode that commits
for itself? Start from `io_should_commit()`.

## uring.buffer-recycle: Buffer recycle and put

- section: Provided buffers
- relevance: 4 - the wrong one loses or reuses a buffer

What is the difference between `io_kbuf_recycle()` and `io_put_kbufs()`? Which of the two must a
handler call when it returns to wait for poll, and which when it retries after a partial transfer?
Start from `io_kbuf_recycle()` and `io_put_kbufs()`.

## uring.buffer-list-lifetime: Buffer list lifetime

- section: Provided buffers
- relevance: 4 - a stored pointer outlives the list

How long is a pointer to a `struct io_buffer_list` valid, and what is `struct io_br_sel` for? What
are the requirements for a handler that keeps `buf_list` of a `struct io_br_sel` in order to
assure safe usage?

# Registered buffers and resource nodes

## uring.rsrc-nodes: Resource nodes

- section: Registered buffers and resource nodes
- relevance: 4 - the reference is a plain integer

What protects the reference count of a `struct io_rsrc_node`, and when is a reference taken and
dropped for a file and for a buffer? What does `io_put_rsrc_node()` do when the last reference
goes? Start from `io_put_rsrc_node()`.

## uring.registered-buffer-import: Importing a registered buffer

- section: Registered buffers and resource nodes
- relevance: 5 - the node is attached to whichever request is passed in

To which request do `io_import_reg_buf()` and `io_import_reg_vec()` attach the buffer's `struct
io_rsrc_node`, and what are the requirements for the request that a caller passes in order to
assure safe usage? What do the two functions check about the direction and the range of the
transfer? Start from `io_import_reg_buf()` and `io_import_reg_vec()`.

## uring.registered-buffers: Registered buffer layout

- section: Registered buffers and resource nodes
- relevance: 4 - offset arithmetic goes wrong on unaligned buffers, and the structure changed

What are the requirements for code that computes an offset into `bvec` of a `struct
io_mapped_ubuf` in order to assure safe usage? Which function releases the pages of a buffer that
userspace registered, and which function those of a buffer that the kernel registered? Start from
`io_sqe_buffer_register()` and `io_vec_fill_bvec()`.

# Zero-copy send

## uring.zc-send-lifetime: Notification and buffer lifetime

- section: Zero-copy send
- relevance: 5 - the wrong owner frees pages the network still uses; the issue function every reader named is gone

What must a zero-copy send attach to the notification that `io_alloc_notif()` returns and not to
the send request, and when is the notification allocated? Which functions issue
`IORING_OP_SEND_ZC` and `IORING_OP_SENDMSG_ZC`? Start from `io_send_zc_prep()` and
`io_alloc_notif()`.

## uring.notif-flush: Notification flush

- section: Zero-copy send
- relevance: 4 - flushing twice is a use after free

What does `io_notif_flush()` do, and what are the requirements for a caller of it in order to
assure safe usage? Does the context the send ran in change where the flush is done? Start from
`io_notif_flush()`.

# Passthrough commands

## uring.cmd-sqe-lifetime: Passthrough command SQE

- section: Passthrough commands
- relevance: 5 - the one opcode that keeps the SQE pointer

For `IORING_OP_URING_CMD`, how long does `sqe` of `struct io_uring_cmd` refer to ring memory, and
what makes it safe once the request goes async? What are the requirements for a driver's issue
path that reads the SQE in order to assure safe usage? Start from `io_uring_cmd_prep()` and
`io_uring_cmd_sqe_copy()`.

## uring.cmd-driver-api: Passthrough driver interface

- section: Passthrough commands
- relevance: 4 - what a driver may call and from where

What may a driver's `uring_cmd` file operation return, and what does the core do with the command
for each value? Which helpers does a driver call to complete a command later, or to move it to
task context? Start from `include/linux/io_uring/cmd.h`.

## uring.cmd-cancelable: Cancelable commands

- section: Passthrough commands
- relevance: 4 - a command marked cancelable can be cancelled while the driver completes it

What are the requirements for a driver that calls `io_uring_cmd_mark_cancelable()` on a command,
in order to assure safe usage? On which requests does the call have no effect? Start from
`io_uring_cmd_mark_cancelable()`.

# SQPOLL and IOPOLL rings

## uring.sqpoll-thread-pointer: SQPOLL thread pointer

- section: SQPOLL and IOPOLL rings
- relevance: 5 - the task can exit and be freed under a reader

What are the requirements for code that reads and then uses `thread` of a `struct io_sq_data` in
order to assure safe usage? Which task must be signalled for a request's task work on an SQPOLL
ring, and which code owns the task reference after the thread is started? Start from
`sqpoll_task_locked()` and `io_sq_offload_create()`.

## uring.iopoll: IOPOLL completion

- section: SQPOLL and IOPOLL rings
- relevance: 4 - a request that never marks itself done hangs the ring

On an IOPOLL ring, what protects `iopoll_list` of `struct io_ring_ctx`? How does
`io_complete_rw_iopoll()` tell `io_do_iopoll()` that a request is done, and what are the
requirements for a completion callback on an IOPOLL ring in order to assure safe usage? Start from
`io_do_iopoll()` and `io_complete_rw_iopoll()`.

## uring.iopoll-reissue: Reissued requests

- section: SQPOLL and IOPOLL rings
- relevance: 4 - a request marked for reissue must not post a CQE or be freed

When does `io_complete_rw_iopoll()` mark a request to be issued again, and what does the core do
with a request that has `REQ_F_REISSUE` set? Start from `io_complete_rw_iopoll()` and
`io_free_batch_list()`.

# Cancellation and teardown

## uring.cancel: Async cancel search and matching

- section: Cancellation and teardown
- relevance: 4 - several tables have to be searched

When a request is cancelled by key, in what order are the places a request can be waiting
searched, what stops one request being matched twice, and how does the synchronous form differ?
Start from `io_try_cancel()` and `io_cancel_req_match()`.

## uring.inflight-tracking: Inflight tracking

- section: Cancellation and teardown
- relevance: 3 - every reader missed the second kind of request that needs it

Which kinds of request must be tracked with `io_req_track_inflight()`, and by what point? How does
task cancellation use `inflight` and `inflight_tracked` of `struct io_uring_task`? Start from
`io_req_track_inflight()`.

## uring.task-exit-cancel: Task exit and exec

- section: Cancellation and teardown
- relevance: 4 - the loop must reach zero inflight or the task hangs

How do exit and exec differ in what they cancel of a task's requests and in which count they
wait on, what makes the loop end, and how does the SQPOLL thread's version differ? Start from
`io_uring_cancel_generic()` and `io_uring_try_cancel_requests()`.

## uring.ring-teardown: Ring teardown

- section: Cancellation and teardown
- relevance: 4 - the order of frees at the end is fixed

What does `io_ring_exit_work()` wait for before the ring is freed, and how does it remove other
tasks' references to the ring? Which steps of `io_ring_ctx_free()` rely on an earlier step having
run? Start from `io_ring_ctx_wait_and_kill()` and `io_ring_ctx_free()`.

# ABI and tests

## uring.change-checklist: UAPI layout checks and compat

- section: ABI and tests
- relevance: 3 - what userspace was promised is easy to break without a test failing

What must a change keep as it is in the structures that io_uring shares with userspace, and which
build-time checks enforce that? Where in the tree are tests for io_uring? Start from
`io_uring_init()`.

## uring.compat-tasks: Compat tasks

- section: ABI and tests
- relevance: 3 - a structure read from a 32-bit task with the 64-bit layout is read wrong

What are the requirements for an opcode that reads a structure from userspace on a ring for which
`io_is_compat()` is true, in order to assure safe usage? Name in-tree code that shows it. Start
from `io_is_compat()`.

# Model gaps

## uring.model-gaps: Other mistakes models make

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
