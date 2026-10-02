# What the io_uring measurement found

Three models were asked the 84 questions in `io_uring-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels 6.15 to 7.1), reader A a few releases behind it (6.12 to 6.18),
and reader B older again (6.7 to 6.13), with whole mechanisms out of date. The
hand-written guide was never checked against current sources, so differences
between it and the built guide are expected and are noted near the end.

io_uring moves faster than any reader's memory. All three know the design: the
rings, prep then issue, poll-driven retry, the worker pool, task work,
provided and registered buffers. What they get wrong is mostly names and
layouts that changed in the last few releases, and this tree has a great many
of those. Reader B also has rules backwards.

## What all three readers got wrong

- **The task work queues are not llists.** Both are `struct mpscq`, a lockless
  FIFO defined in `io_uring/mpscq.h`: `ctx->work_list` with its consumer cursor
  `ctx->work_head`, and `tctx->task_list` with `tctx->task_head`. Every reader
  described `work_llist`, a retry list, `llist_del_all()` and a reversal pass;
  none of that is in the tree. A pop that returns nothing while
  `mpscq_empty()` is false means a producer is half way through a push, and the
  consumer must come back, not spin with the ring mutex held.
- **The fallback paths were reworked.** There is no
  io_move_task_work_from_local(), no ctx->fallback_llist and no
  io_fallback_req_func(). Ring exit runs a deferred-taskrun ring's queue in
  cancel mode with `io_cancel_local_task_work()`; a task that can no longer run
  task work has its queue drained by `tctx->fallback_work`
  (`io_tctx_fallback_work()`). All the runners are in `io_uring/tw.c`, which is
  also the only file that creates a `struct io_tw_state`.
- **The wait counter is a countdown.** `ctx->cq_wait_nr` is armed with the
  number of lazy adds the waiter needs and counted down by
  `io_req_local_work_add()`; `IO_CQ_WAKE_INIT` is -1 and is documented in
  `io_uring/wait.h`. There is no req->nr_tw and no IO_CQ_WAKE_FORCE.
- **Ring state bits.** `task_complete`, `lockless_cq`, `drain_active`,
  `restricted`, `compat` and the rest are `IO_RING_F_*` bits in
  `ctx->int_flags`, not fields. Reader C described this correctly when asked
  directly and then used the old field names in six other answers.
- **Zero-copy send.** There is no io_send_zc(). `io_sendmsg_zc()` issues both
  opcodes, imports a registered buffer at issue through `io_send_zc_import()`,
  and skips the inline notification flush when it runs in a worker.
- **Registered buffers.** `struct io_mapped_ubuf` has no acct_pages or is_kbuf;
  it has `flags` with `IO_REGBUF_F_KBUF`, `dir`, `release` and `priv`. Huge
  pages are counted once per ring through the `ctx->hpage_acct` xarray
  (`hpage_acct_ref()`, `hpage_acct_unref()`); headpage_already_acct() is gone.
  Readers A and C described `io_buffer_register_request()` under the name
  `io_buffer_register_bvec()`, and offered an unregister function that does
  not exist (it is `io_buffer_unregister()`).
- **Zero-copy receive names.** Exit calls `io_terminate_zcrx()` once and the
  final free calls `io_unregister_zcrx()`; the names the readers gave are gone.
  DMA mapping is done when an area is created (`io_import_umem()`,
  `io_import_dmabuf()`), not in `io_pp_zc_init()`, which only validates the
  pool and takes a reference.
- **Async data at issue.** Every reader gave "allocate in prep" as the rule
  and none knew that `io_futex_wait()` allocates at issue, under the ring
  lock, and sets pointer and flag by hand.
- **Inflight tracking** also covers private futexes (`io_futex_wait_prep()`,
  `io_futexv_prep()`), not only requests on a ring file.
- **New files.** `tw.c`, `wait.c`, `loop.c`, `bpf_filter.c`, `bpf-ops.c`,
  `query.c`: no reader placed all of them, and readers A and B said the BPF
  hooks did not exist.
- Smaller things: path-taking preps use `delayed_getname()`; region creation is
  `io_create_region()` then `io_region_publish()`; the register system call
  finds its file with `io_uring_ctx_get_file()`; there is no
  IO_URING_F_TASK_DEAD; `io_fill_cqe_aux32()` passes true to `io_get_cqe()` in
  both big-CQE modes while `__io_cqring_overflow_flush()` forces false on a
  CQE32 ring.

## What only some readers got wrong

Readers A and B:

- `io_req_complete_post()` as the way to complete a request from outside task
  work. It is static, warns unless `IO_URING_F_IOWQ` is set, and only drops a
  reference. The helper for other code is `io_req_queue_tw_complete()`. This
  one would change a verdict.
- A multishot handler stays armed by returning `IOU_ISSUE_SKIP_COMPLETE`. It
  returns `IOU_RETRY`, and `io_poll_issue()` warns on the other. Both offered
  IOU_STOP_MULTISHOT, which is gone; finishing is `IOU_COMPLETE`.
- `io_uring_cmd_done()` takes a second result. It does not;
  `io_uring_cmd_done32()` does.
- Exit and exec swapped: `io_uring_files_cancel()` at exit passes false and
  waits on the tracked count, `io_uring_task_cancel()` at exec passes true.
- Neither listed `IO_URING_F_INLINE`, which `io_req_sqe_copy()` depends on.

Reader A alone: the chain of a link is changed under `timeout_lock` (it is
`completion_lock`); `req_ref_put_and_test()` warns on a request with no
reference count (it returns true, which is how such a request is freed); the
flag to `io_get_cqe()` is ignored on a CQE32 ring; `io_import_fixed()` adds the
first bvec's offset (only `io_vec_fill_bvec()` does); a message-ring cache that
does not exist; the context a zero-copy send ran in does not change where the
notification is flushed; any unlocked read of the SQPOLL thread pointer is
unsafe (`io_uring_enter()` tests it for NULL, correctly).

Reader B alone, and mostly verdict-changing:

- `io_uring_cmd_prep()` copies the SQE, so the pointer is always safe. It
  stores the ring pointer; the copy happens only through `io_req_sqe_copy()`.
- CQEs may be posted from softirq, `completion_lock` is taken from interrupt
  context, and timeouts share it. The helper asserts `in_task()`, the lock
  taken from an hrtimer is the raw `timeout_lock`, and it nests inside
  `completion_lock`, not the other way round.
- An opcode sets `REQ_F_BUFFERS_COMMIT` to skip the automatic commit. The
  selection code sets it; `io_should_commit()` decides.
- `io_kbuf_inc_commit()` touches only kernel counters and userspace can rewrite
  a ring entry only after the tail passes it. It reads and writes the shared
  entry, and userspace can rewrite it at any time.
- A multishot request is always failed in a worker; notifications are cached
  in a per-ring slot and the flush posts the CQE directly; only one ring mutex
  is ever held; multishot requests are reference counted.

Reader C alone: `IOSQE_CQE_SKIP_SUCCESS` makes drain fail in general (only an
SQE that asks for drain is refused); poll arming always starts owned (only from
a worker); `io_recv_finish()` works out the put length itself (it is passed
`consumed`).

## What the readers already knew

The two kinds of provided buffer and the rule for reading ring entries
(readers A and C, nothing to correct); clearing tags after a failed table
registration; request reference counts, CQ overflow and multishot in workers
(reader C, nothing to correct); the entry points and headers; how the SQPOLL
thread pointer must be read and how the thread is parked (reader C); links,
fixed files, partial send and receive retry, the order of request teardown
(A and C). These are dropped from the build set or shrunk to the point a reader
missed.

## Where the hand-written guide is stale

- It points at io_send_zc() for the notification flush. The function is gone;
  `io_sendmsg_zc()` serves both opcodes, and the inline flush is skipped under
  `IO_URING_F_UNLOCKED`. Its advice to compare the vectored import with the
  plain one predates `IORING_SEND_VECTORIZED`: both go through
  `io_send_zc_import()` now.
- Its task work section names `ctx->work_llist` and
  io_move_task_work_from_local(). Neither exists. The rule it states survives
  in a different form: `io_ring_exit_work()` calls
  `io_cancel_local_task_work()` before every cancel pass.
- IOU_STOP_MULTISHOT is gone. "A multishot handler must not return -EAGAIN" is
  now wrong as worded: `IOU_RETRY` is -EAGAIN and is what a handler returns to
  stay armed.
- "Allocate async data in prep, not issue" is an absolute with an in-tree
  counterexample, `io_futex_wait()`.
- It calls any bare read of `sqd->thread` a bug. `io_uring_enter()` compares it
  with NULL holding neither the lock nor RCU; what is unsafe is dereferencing
  it.
- Its CQE table says to pass false on a CQE32 ring. `io_fill_cqe_aux32()`
  passes true in both modes.
- Inflight tracking is no longer in `io_futex_prep()`; it is in
  `io_futex_wait_prep()` and `io_futexv_prep()`, for private futexes only.
- "Create DMA mappings in `io_pp_zc_init()`": mapping is done at area creation.
- `io_should_commit()` exempts both passthrough opcodes through
  `io_is_uring_cmd()`, and `io_buffers_select()` commits at selection whatever
  it says.
- The bundle quick check names a local, this_ret; `io_recv_finish()` is now
  passed `consumed` and uses that for the put.
- Its `REQ_F_NEED_CLEANUP` example uses getname(); prep calls
  `delayed_getname()`.
- "Only core io_uring.c should instantiate the token" repeats a stale comment
  in the header; only `io_uring/tw.c` does.
- Correct and kept as questions: the node of a registered buffer goes on
  whichever request is passed to the import functions; flush then clear the
  notification pointer; `REQ_F_NEED_CLEANUP` before the first early return;
  pointer and flag of async data change together; the two-phase timeout kill;
  `kfree_rcu()` for message-ring carriers; `iopoll_completed` must always be
  set.

## Left out of the build set

The hand-written guide is 1,741 words, so the build set holds 38 of the 84
questions. Left out although a reader got them wrong: zero-copy receive, the
worker pool, cancellation by key, task exit, ring teardown, waiting for
completions, the BPF filters and loop, registration dispatch and mapped regions
(a patch to any of these needs the source, and the names that moved are carried
by the source files question); pinned memory accounting, kernel-owned
registered buffers, incremental buffers, bundles and buffer ring registration
(narrow); drain, links, request recycling and reference counts, the per-task
context, shared ring memory, the opcode tables and adding an opcode (readers A
and C are close enough); eventfd, poll ownership and poll events (reader B
only); 128-byte SQEs, futex and waitid, fixed files, resource nodes. The
provided-buffer basics are left out because two readers had nothing to correct.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 236 corrections, 42% rewritten on average
reader B: 250 corrections, 79% rewritten on average
reader C: 173 corrections, 24% rewritten on average

question                            reader A      reader B      reader C
uring.core-files                    30% ( 8)      46% ( 8)       8% ( 3)
uring.headers                       10% ( 1)      38% ( 1)       7% ( 1)
uring.docs-and-tests                23% ( 1)      83% ( 1)      11% ( 1)
uring.entry-points                  22% ( 1)      11% ( 4)      11% ( 1)
uring.ring-ctx                      34% ( 6)      82% ( 9)      11% ( 2)
uring.internal-ring-flags           68% ( 1)      88% ( 2)       0% ( 1)
uring.request-struct                45% ( 1)      85% ( 3)       9% ( 1)
uring.request-flags                 15% ( 2)      79% ( 3)      19% ( 3)
uring.task-context                  43% ( 5)      77% ( 5)      55% ( 3)
uring.shared-rings                  27% ( 2)      76% ( 4)      39% ( 2)
uring.opcode-tables                 39% ( 5)      80% ( 6)      11% ( 3)
uring.adding-opcode                 22% ( 1)      72% ( 2)      28% ( 1)
uring.submission-path               32% ( 4)      77% ( 4)      18% ( 2)
uring.sqe-reading                   46% ( 2)      79% ( 3)      14% ( 1)
uring.issue-flags                   30% ( 6)      48% ( 3)      10% ( 3)
uring.issue-return-codes            42% ( 3)      87% ( 1)       6% ( 1)
uring.async-punt                    47% ( 2)      82% ( 1)       4% ( 1)
uring.completion-paths              43% ( 2)      87% ( 2)      15% ( 3)
uring.request-recycling             12% ( 3)      81% ( 2)      10% ( 2)
uring.request-refs                  79% ( 1)      85% ( 2)       0% ( 0)
uring.links                         24% ( 2)      74% ( 2)       4% ( 1)
uring.drain                         40% ( 2)      73% ( 3)      46% ( 4)
uring.cleanup-flag                  29% ( 2)      87% ( 5)       5% ( 1)
uring.async-data                    48% ( 3)      83% ( 4)      10% ( 3)
uring.alloc-caches                  36% ( 3)      86% ( 2)      26% ( 2)
uring.recycling-from-workers        65% ( 2)      91% ( 2)      40% ( 3)
uring.task-work-queues              71% ( 6)      85% ( 5)      41% ( 5)
uring.task-work-queue-rules         79% ( 1)      82% ( 2)      62% ( 1)
uring.tw-token                      59% ( 1)      81% ( 2)      10% ( 1)
uring.tw-task-exiting               57% ( 1)      78% ( 2)      44% ( 1)
uring.defer-taskrun                 65% (10)      90% ( 5)      81% ( 4)
uring.tw-add-flags                  58% ( 1)      89% ( 2)      42% ( 1)
uring.exit-cancel-loop              71% ( 2)      83% ( 2)      32% ( 2)
uring.cq-locking                    42% ( 4)      81% ( 5)      20% ( 4)
uring.cqe-posting-helpers           43% ( 2)      71% ( 3)       8% ( 2)
uring.cq-overflow                   56% ( 1)      81% ( 2)       0% ( 0)
uring.big-cqes                      45% ( 4)      81% ( 2)       5% ( 1)
uring.big-sqes                      62% ( 6)      84% ( 3)      34% ( 2)
uring.cq-waiting                    65% ( 6)      91% ( 3)      19% ( 3)
uring.eventfd                       20% ( 2)      81% ( 2)      35% ( 1)
uring.poll-ownership                25% ( 1)      72% ( 5)      29% ( 2)
uring.multishot-flags               66% ( 3)      80% ( 1)      38% ( 3)
uring.multishot-returns             52% ( 3)      88% ( 2)       6% ( 1)
uring.multishot-workers             44% ( 3)      86% ( 1)       0% ( 0)
uring.poll-events                   16% ( 1)      83% ( 1)      41% ( 3)
uring.provided-buffer-kinds          0% ( 2)      79% ( 1)       0% ( 0)
uring.buffer-ring-memory             0% ( 0)      77% ( 1)       0% ( 0)
uring.buffer-list-lifetime          17% ( 2)      71% ( 1)       9% ( 1)
uring.buffer-commit                 60% ( 4)      91% ( 1)      17% ( 2)
uring.buffer-recycle                45% ( 4)      76% ( 4)      19% ( 2)
uring.incremental-buffers           33% ( 1)      91% ( 3)      40% ( 2)
uring.bundles                       60% ( 2)      80% ( 2)      34% ( 2)
uring.buffer-ring-registration      40% ( 2)      90% ( 4)      18% ( 1)
uring.rsrc-nodes                     8% ( 3)      66% ( 5)      31% ( 3)
uring.registered-buffers            56% ( 4)      85% ( 4)      12% ( 2)
uring.registered-buffer-import      23% ( 2)      83% ( 3)      14% ( 1)
uring.kernel-registered-buffers     57% ( 1)      82% ( 3)      56% ( 4)
uring.buffer-accounting             61% ( 2)      74% ( 5)      62% ( 6)
uring.rsrc-registration-failure      1% ( 1)      74% ( 1)       0% ( 0)
uring.fixed-files                   25% ( 1)      74% ( 1)      10% ( 2)
uring.zc-send-lifetime              40% ( 4)      92% ( 3)      28% ( 3)
uring.notif-flush                   42% ( 2)      81% ( 2)       4% ( 1)
uring.net-retry                     13% ( 1)      88% ( 3)       9% ( 1)
uring.zcrx                          47% ( 4)      83% ( 3)      38% ( 3)
uring.cmd-sqe-lifetime              33% ( 2)      77% ( 1)      31% ( 2)
uring.cmd-driver-api                29% ( 4)      76% ( 3)      17% ( 2)
uring.iopoll                        57% ( 5)      81% ( 4)      27% ( 3)
uring.timeouts                      34% ( 2)      80% ( 4)      44% ( 2)
uring.msg-ring                      54% ( 7)      81% ( 5)      40% ( 4)
uring.inflight-tracking             51% ( 2)      70% ( 1)      55% ( 1)
uring.futex-waitid                  46% ( 1)      81% ( 1)      14% ( 1)
uring.cancel                        56% ( 8)      88% ( 6)      30% ( 1)
uring.task-exit-cancel              49% ( 2)      87% ( 4)      34% ( 1)
uring.ring-teardown                 52% ( 4)      86% ( 4)      49% ( 5)
uring.sqpoll-thread-pointer         58% ( 3)      78% ( 5)       1% ( 2)
uring.sqpoll-parking                19% ( 1)      65% ( 2)       8% ( 1)
uring.io-wq                         56% ( 5)      80% ( 3)      34% ( 6)
uring.register-dispatch             57% ( 5)      81% ( 6)      41% ( 7)
uring.ring-resize                   67% ( 4)      85% ( 2)      48% ( 2)
uring.memory-regions                31% ( 2)      68% ( 1)      33% ( 1)
uring.restrictions-filters          83% ( 1)      82% ( 2)      42% ( 2)
uring.bpf-loop                      94% ( 2)      96% ( 1)      62% ( 1)
uring.lock-order                    40% ( 2)      84% ( 7)      32% ( 4)
uring.change-checklist              23% ( 3)      69% ( 4)      17% ( 3)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `uring.request-refs`, `uring.cq-overflow`, `uring.cancel`, `uring.ring-teardown`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `uring.ring-ctx`, `uring.request-flags`, `uring.shared-rings`, `uring.opcode-tables`, `uring.submission-path`, `uring.async-punt`, `uring.request-recycling`, `uring.poll-ownership`, `uring.provided-buffer-kinds`, `uring.buffer-ring-memory`, `uring.rsrc-nodes`, `uring.cmd-driver-api`, `uring.task-exit-cancel`.

## Questions reorganised

By subject now, 56 questions where there were 57: the ring context and its locks; request state;
submission and issue; posting completions; task work; multishot and poll; provided buffers; registered
buffers and resource nodes; zero-copy send; passthrough commands; SQPOLL and IOPOLL rings; cancellation
and teardown; ABI and tests. `uring.request-flags` and `uring.request-recycling`, both about
`io_free_batch_list()`, are merged as `uring.request-free`; how the flags are typed is a header lookup
and is dropped. `uring.change-checklist` keeps only the ABI and the tests (relevance 4 to 3): contexts
and ring modes are asked by `uring.issue-flags` and `uring.cq-locking`. The questions on the context,
the request, the opcode tables and the resource structures no longer ask what a structure holds.
