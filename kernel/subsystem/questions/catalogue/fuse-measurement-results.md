# What the fuse measurement found

Three models were asked the 90 questions in `fuse-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc5). The readers are labelled A, B and C; which
models they were does not matter here. Reader A was the most current (it
assumed kernels 6.15 to 6.19), reader B a little behind it (6.12 to 6.18), and
reader C the weakest (6.12 to 6.17): the check rewrote 26%, 35% and 63% of
their answers. The hand-written guide was never checked against current
sources, so differences between it and the built guide are expected and are
noted near the end.

All three readers know the design of FUSE: the connection, the device queues,
lookup counts and FORGET, the interrupt protocol, the attribute version, the
I/O modes. What they get wrong is mostly one reorganisation that none of them
has seen. This tree moved the transport state out of `struct fuse_conn` into a
new `struct fuse_chan`, moved the send functions into new files, and renamed
the functions that went with them. A reader that does not know this misplaces
a lock or a field in almost every answer about requests. The io-uring
transport also has commands, buffer pools and a zero-copy path that no reader
knows.

## What all three readers got wrong

- **The channel.** `struct fuse_chan` in `fs/fuse/fuse_dev_i.h` holds what the
  readers place in `struct fuse_conn`: the input queue `iq`, `devices`,
  `bg_queue`, `num_background`, `max_background`, `active_background`,
  `blocked`, `blocked_waitq`, `connected`, `initialized`, `num_waiting`,
  `no_interrupt`, `abort_with_err`, `ring`, the request timeout, and copies of
  `minor`, `max_write` and `max_pages`. Its locks are `fch->lock` and
  `fch->bg_lock`. `struct fuse_conn` keeps `chan`, and `congestion_threshold`,
  which no lock protects. Readers A and B said they did not recognise the
  structure. Reader C guessed at it and put the processing queues in it; those
  are in the `struct fuse_pqueue` of each `struct fuse_dev`.
- **Names that are gone.** Every reader used each of these names, and used
  the first two in about a dozen answers:

  | The readers wrote | This tree has |
  |---|---|
  | fuse_abort_conn() | `fuse_chan_abort()` |
  | fuse_wait_aborted() | `fuse_chan_wait_aborted()` |
  | fuse_set_initialized() | `fuse_chan_set_initialized()` |
  | fuse_queue_forget() | `fuse_chan_queue_forget()` |
  | fuse_resend(), a name that is left in one comment only | `fuse_chan_resend()` |
  | end_requests() | `fuse_dev_end_requests()` |
  | fuse_dev_free() | `fuse_dev_put()` |
  | copy_out_args() | `fuse_copy_out_args()` |

  Readers A and C also wrote fc->aborted. The field is `fch->abort_with_err`,
  which every call of `fuse_chan_abort()` stores. Readers A and B wrote
  fuse_force_creds(); `fuse_fill_creds()` does that work.

- **Files and headers.** `fuse_simple_background()`,
  `__fuse_simple_request()`, `fuse_simple_notify_reply()`, `fuse_req_prep()`
  and `fuse_fill_creds()` are in `fs/fuse/req.c`. They call `fuse_chan_send()`,
  `fuse_chan_send_bg()` and `fuse_chan_send_notify_reply()` in `fs/fuse/dev.c`.
  The timeout check is in `fs/fuse/req_timeout.c` and the notification
  handlers are in `fs/fuse/notify.c`. `struct fuse_args` is in
  `fs/fuse/args.h`, and `struct fuse_req`, `struct fuse_dev`,
  `struct fuse_iqueue` and `struct fuse_iqueue_ops` are in
  `fs/fuse/fuse_dev_i.h`, not in `fs/fuse/fuse_i.h`. `fs/fuse/dev.c`,
  `fs/fuse/dev_uring.c` and `fs/fuse/req_timeout.c` do not include
  `fs/fuse/fuse_i.h`. Every reader doubted that `fs/fuse/dev.h` and
  `fs/fuse/args.h` exist.
- **The device object.** `fuse_dev_open()` allocates the `struct fuse_dev` and
  stores it in `file->private_data`. What is published later is `fud->chan`:
  `fuse_dev_install_with_pq()` sets it with `cmpxchg()`, and
  `fuse_dev_release()` replaces it with `FUSE_DEV_CHAN_DISCONNECTED` by
  `xchg()`. `fuse_get_dev()` reads it with `smp_load_acquire()` and returns
  `ERR_PTR(-EPERM)`, or waits on `fuse_dev_waitq` when `fud->sync_init` is set.
  The readers described `private_data` as NULL until mount, a pointer fud->fc,
  a counter fc->dev_count, and a marker value for synchronous INIT. The test
  for the last device is `list_empty(&fch->devices)`.
- **Mount setup.** `fuse_opt_fd()` checks the file when the `fd=` option is
  parsed and sets `ctx->fud = fuse_dev_grab(file)`. `fuse_get_tree()` creates
  the channel with `fuse_dev_chan_new()` and does no `fget()`.
  `fuse_fill_super_common()` calls `fuse_dev_install()` last, under
  `fuse_mutex`, after it has set `sb->s_root`. There is no fudptr field, and
  `fuse_fill_super_common()` allocates no device.
- **The `end` callback takes two arguments.** `struct fuse_args` declares
  `void (*end)(struct fuse_args *args, int error)`. Every reader wrote
  end(fm, args, error). `struct fuse_req` has `chan` and no mount pointer.
- **Notifications are refused before INIT and after abort.**
  `fuse_dev_do_write()` returns `-EINVAL` for a notification unless
  `fch->initialized` and `fch->connected` are set. Readers A and B said no test
  exists, and reader C gave `-ENODEV` from `fuse_notify()`.
- **Which RELEASE is synchronous.** `fuse_file_release()` calls
  `fuse_file_put(ff, ff->fm->fc->auto_submounts)`, and only
  `fs/fuse/virtio_fs.c` sets `auto_submounts`. Readers A and B said the test is
  `fc->destroy`, which is fuseblk, and reader C did not know the test. The
  comment above the call still names fuseblk. With `fc->no_open` a regular
  file keeps `ff->args`, and `fuse_file_put()` calls `fuse_release_end()`
  without sending. `ff->args` is NULL only for a directory with
  `fc->no_opendir`.
- **A reply that fails the checks gets no FORGET.** `fuse_lookup_name()`,
  `create_new_entry()` and `fuse_create_open()` only `kfree()` the forget link
  when `fuse_invalid_attr()` or `invalid_nodeid()` rejects the reply. A FORGET
  is queued only when `fuse_iget()` returns NULL. The readdirplus path does
  send one. Every reader stated a rule that a FORGET must follow each reply
  that carries a node id. The checks of the three runs did not agree on
  whether the difference is intended, so the build set asks for the
  requirement and does not state the behaviour.
- **`nocreds` does not leave the pid unset.** `fuse_fill_creds()` sets
  `args->pid` before it tests `force` and `nocreds`. `-ECONNREFUSED` and
  `-EOVERFLOW` come from `fuse_req_prep()` and `fuse_fill_creds()`, before the
  allocation. `fuse_get_req()` returns only `-EINTR`, `-ENOTCONN` and
  `-ENOMEM`.
- **`may_block` does not decide whether an `end` callback may sleep.** Every
  reader stated that the callback must not sleep unless `may_block` is set.
  `may_block` is read only in `virtio_fs_requests_done_work()`, and
  `fuse_release_end()` calls `iput()` without it.
- **`FR_FORCE` is only tested in `request_wait_answer()`**, where it skips the
  killable wait. `fuse_chan_send()` does not set it when `args->abort_on_kill`
  is set. A forced request is still ended with `-ENOTCONN` by
  `fuse_dev_queue_req()` after an abort. No reader listed `FR_SYNC_WAKEUP`.
- **io-uring commands.** `enum fuse_uring_cmd` also has
  `FUSE_IO_URING_CMD_ADD_QUEUE` and `FUSE_IO_URING_CMD_ADD_BUFPOOL`. For both,
  `fuse_uring_cmd()` returns the result directly, never `-EIOCBQUEUED`. The
  tests in `fuse_uring_cmd()` run in this order: `fuse_get_dev()`,
  `fch->initialized` (`-EAGAIN`), `fch->abort_with_err`, `fch->connected`,
  `fch->io_uring` (`-EOPNOTSUPP`).
- **The ring is created at the INIT reply.** `fuse_chan_set_initialized()`
  calls `fuse_uring_conn_init()`, which calls `fuse_uring_create()` and sets
  `fch->io_uring`. `fuse_uring_register()` returns `-EINVAL` when there is no
  ring. Until the ring is ready, `fuse_block_alloc()` makes `fuse_get_req()`
  sleep; only forced requests go to the device queue. The readers described a
  ring made at the first REGISTER and a field fc->io_uring set by
  `process_init_reply()`.
- **Buffer pools and zero copy.** `enum fuse_queue_payload_mode` has a mode
  for one buffer for each entry and a mode for a pool,
  `fuse_uring_select_buffer()` and `fuse_uring_recycle_buffer()` take and give
  back pool buffers, and `can_zero_copy_req()` and
  `fuse_uring_set_up_zero_copy()` give the server the folios of a request.
  Every reader said the tree has one way to get a buffer and no zero-copy
  path.
- **How ring pointers are published.** `fch->ring`, `ring->queues[qid]` and
  `ring->ready` are each stored with `smp_store_release()`. The readers gave
  `WRITE_ONCE()`, a plain store or `cmpxchg()`. The loads differ by site:
  `READ_ONCE()` for the queue pointer in most places, `smp_load_acquire()` in
  `fuse_uring_register()`, `fuse_uring_add_queue()` and
  `fuse_uring_add_bufpool()`, and a plain load of `fch->ring` in
  `fuse_uring_commit_fetch()`, which runs after the `smp_load_acquire()` of
  `fch->initialized` in `fuse_uring_cmd()`.
- **A cancel frees the entry.** `fuse_uring_cancel()` unlinks the entry,
  completes the command, calls `kfree()` and drops `queue_refs`. Every reader
  said it moves the entry to another list. IO_URING_F_TASK_DEAD is not
  defined; `fuse_uring_send_in_task()` tests `tw.cancel`.
- **The epoch.** The epoch of a dentry is `epoch` in `struct fuse_dentry`, and
  the readdir cache compares `fi->rdc.epoch` with `fc->epoch` too. The readers
  said only dentries compare (A, B), or that attributes might (C).
  `fuse_dentry_tree_work()` moves expired dentries to a shrink list; it does
  not call `d_invalidate()`.

## What only some readers got wrong

In each bullet below, the first sentence is what the readers said. The rest of
the bullet is what the tree does.

Readers B and C:

- `fuse_make_bad()` removes the inode from the hash. It only sets
  `FUSE_I_BAD`; `fuse_iget()` does the unhash itself.
- While `FUSE_I_SIZE_UNSTABLE` is set, a reply updates everything except the
  size. `fuse_change_attributes_i()` returns before it applies anything.
- `fuse_set_acl()` calls `posix_acl_update_mode()`. It does not; no code under
  `fs/fuse/` does.
- An open that conflicts with the I/O mode of the inode returns `-ETXTBSY` or
  `-EINVAL`. `fuse_file_io_open()` turns every failure into `-EIO`.
- virtio-fs retries a request after a delay when the virtqueue is full.
  `dispatch_work` is a plain `struct work_struct`; `virtio_fs_send_req()` only
  parks the request, and `virtio_fs_requests_done_work()` schedules the work.

Reader B only:

- `fuse_get_attr_version()` increments the counter. It reads it.
- A reply that is older than the cached attributes marks them invalid. The
  code returns and changes nothing.
- `fuse_dentry_revalidate()` marks a stale inode bad. It only returns invalid.
- `fuse_read_folio()` waits for a WRITE of the same index. It does not.

Reader C only. The check rewrote 40% or more of 80 of reader C's 90 answers,
so this list holds only the mistakes that would change a review:

- A reply header may carry an error down to -1000. The test in
  `fuse_dev_do_write()` is `oh.error <= -512 || oh.error > 0`.
- A resent request keeps its identifier. `fuse_chan_resend()` sets
  `FUSE_UNIQUE_RESEND` in it.
- A waiter whose request was already sent returns `-EINTR` on a fatal signal.
  It falls through to an uninterruptible wait, or aborts the connection when
  `abort_on_kill` is set.
- `lock_request()` takes `fpq->lock` and is held around the page lookup. It
  takes `req->waitq.lock`; `FR_LOCKED` is held across the copy and dropped
  around the page lookup.
- `struct fuse_iqueue_ops` has callbacks that are called with `fiq->lock`
  held and release it. Its members are `send_forget`, `send_interrupt`,
  `send_req` and `release`, called without `fiq->lock`.
- `FUSE_DEV_IOC_SYNC_INIT` sends INIT from the ioctl. It only sets
  `fud->sync_init`.
- A refused INIT reply aborts the connection. It sets `fc->conn_error`, and
  `fuse_req_prep()` then fails each request that is not forced.
- Passthrough is tested before `FOPEN_DIRECT_IO`. For read, write and splice
  `FOPEN_DIRECT_IO` is tested first; only `fuse_file_mmap()` tests passthrough
  first.
- `fc->handle_killpriv` means that the kernel clears the bits. It means that
  the server does.
- `FUSE_NOWRITE` is -1 and `fuse_set_nowrite()` takes `fc->lock`. It is
  `INT_MIN`, and the lock is `fi->lock`.
- Removing the virtio device aborts the connection. `virtio_fs_remove()` waits
  for requests in flight and aborts nothing.
- `fuse_allow_current_process()` runs only without `default_permissions`. It
  runs first in both modes.

Reader A only:

- `RENAME_WHITEOUT` is refused on an idmapped mount. `fuse_rename2()` passes
  the idmap on for it.
- `fuse_setlk()` returns without sending for a lock that close removes. It has
  no such test.
- `fuse_ilookup()` walks `fc->mounts` under `rcu_read_lock()`. It is a plain
  list walk, and the caller holds `fc->killsb`.

## What the readers already knew

Readers A and B needed little or nothing on: writing a reply to the device,
the order in which a read of the device chooses among interrupts, forgets and
requests, how an INTERRUPT is queued, which I/O path a read or a write takes,
who checks permissions with and without `default_permissions`, creating and
opening a file in one request, the lists a request moves through, the readdir
cache (reader A), readdirplus, and fsync. Readers B and C needed little on the
lifetime of request arguments, and readers A and C needed little on which send
function waits. All three had the idea of the reply size check, of cloned
devices and of the control filesystem right, and had mostly names to correct
there.

## Where the hand-written guide is stale

`fuse.md` is two sections about the io-uring transport, 196 words. It uses the
current name `fch->ring`, yet the tree differs from it:

- It says `smp_load_acquire()` is not needed to read `fch->ring` and that
  `READ_ONCE()` is enough. `fuse_uring_register()`, `fuse_uring_add_queue()`
  and `fuse_uring_add_bufpool()` read `fch->ring` with `smp_load_acquire()`.
  `fuse_uring_ready()` uses `READ_ONCE()`, and `fuse_uring_commit_fetch()` and
  others use a plain load.
- It covers `fch->ring` only. The same question arises for
  `ring->queues[qid]` and `ring->ready`, which are also stored with
  `smp_store_release()` and which it does not mention.
- It says fuse reads SQE fields with `READ_ONCE(cmd->sqe->...)`.
  `fuse_uring_get_iovec_from_sqe()` reads `sqe->addr` with `READ_ONCE()` and
  `sqe->len` with a plain load.
- It says `fuse_uring_cmd()` uses `io_uring_sqe128_cmd()`. Five functions that
  run under `fuse_uring_cmd()` use it. `fuse_uring_cmd()` itself reads only
  `cmd->cmd_op`.
- It predates `FUSE_IO_URING_CMD_ADD_QUEUE`, `FUSE_IO_URING_CMD_ADD_BUFPOOL`,
  buffer pools and zero copy. `fuse_uring_cmd_index_ok()` and
  `fuse_uring_add_bufpool()` now read `cmd->sqe->buf_index` as well.
- Still true in this tree: `fch->ring` is stored with `smp_store_release()`;
  `io_req_sqe_copy()` copies the SQE before a request is punted; nothing under
  `fs/fuse/` calls `io_uring_cmd_issue_blocking()`; fuse reads `cmd->sqe` only
  in functions that `fuse_uring_cmd()` calls.

Each of its two sections ends in a "Not a bug" line. Such a line tells a
reviewer what to report, and a built guide holds no such line. The two subjects
are kept as `fuse.uring-pointer-publication` and `fuse.uring-sqe-access`, and
neither question states what the hand-written guide says. The hand-written
guide holds no text that a kernel tree cannot supply, so the build set has no
verbatim item.

## What was left out of the build set and why

The build set holds 81 of the 90 measurement questions, and the two questions
that every build set has, `fuse.overview` and `fuse.model-gaps`. A question
was left out only if the check rewrote less than half of the answer of every
reader, and then only for the reason given below. `fuse.docs-and-tests` is the
one exception.

- `fuse.main-objects`: it asks what `fuse.overview` asks, so the two are
  merged as `fuse.overview`.
- `fuse.docs-and-tests`: the answer would not change what a review concludes.
  It is left out although reader C knew almost none of the answer.
- `fuse.request-arguments`: every reader had the lifetime rules right. The
  corrections were about where the credentials are filled in, which
  `fuse.user-namespaces` and `fuse.argument-flags` ask.
- `fuse.reply-size-check`: every reader had the check right. The corrections
  were about which side sees `-EINVAL` and which sees `-EIO`.
- `fuse.device-write`: readers A and B needed one and two corrections. Reader
  C had one number and one error value wrong.
- `fuse.device-clone`: the corrections were the names that
  `fuse.device-lifetime` asks for.
- `fuse.control-fs`: the code is confined to `fs/fuse/control.c`, and every
  reader knew how a control file reaches its connection.
- `fuse.permission-checks`: readers A and B were right. What reader C got
  wrong is what `fuse.access-by-other-users` asks.
- `fuse.create-and-open`: readers A and B were right on the sequence.
  `fuse.forget` and `fuse.reply-attribute-checks` ask what is undone on
  failure.

These are kept although the check rewrote less than half of every answer,
since the corrections would change what a review concludes:

- `fuse.submounts`: every reader named the wrong code as what turns submounts
  on.
- `fuse.init-new-flag` and `fuse.send-variants`: readers stated rules more
  broadly than the code supports.
- `fuse.interrupts` and `fuse.request-lists`: reader C had the ordering and
  the lists wrong.
- `fuse.readdirplus` and `fuse.backing-files`: the check rewrote about half of
  reader C's answer.

`fuse.core-files` and `fuse.entry-points` are kept whatever the measurement
says.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A          494        26%     26     12   6.15 to 6.19
reader B          497        35%     11     31   6.12 to 6.18
reader C          470        63%      2     80   6.12 to 6.17

question                              reader A      reader B      reader C   verdict
fuse.core-files                       19% ( 6)      29% ( 5)      34% ( 7)   middling
fuse.headers                          95% ( 5)      57% ( 6)      67% ( 5)   all weak
fuse.entry-points                     29% ( 9)      34% ( 5)      44% (13)   weak: reader C
fuse.docs-and-tests                   33% ( 5)      46% ( 7)      88% ( 3)   weak: reader B, reader C
fuse.uapi-header                      35% ( 9)      34% ( 7)      69% ( 7)   weak: reader C
fuse.main-objects                     28% (10)      40% (10)      51% (11)   weak: reader B, reader C
fuse.conn-chan-split                  54% ( 3)      46% ( 4)      88% ( 2)   all weak
fuse.conn-refcount                    39% ( 5)      53% ( 2)      78% ( 3)   weak: reader B, reader C
fuse.conn-feature-bits                37% ( 3)      43% ( 5)      65% ( 4)   weak: reader B, reader C
fuse.mounts-of-connection             14% ( 2)      52% ( 2)      56% ( 3)   weak: reader B, reader C
fuse.submounts                        33% ( 3)      29% ( 2)      34% ( 3)   middling
fuse.device-lifetime                  77% ( 2)      81% ( 4)      87% ( 3)   all weak
fuse.device-clone                     23% ( 1)      30% ( 1)      48% ( 2)   weak: reader C
fuse.control-fs                       33% ( 3)      44% ( 2)      27% ( 3)   weak: reader B
fuse.mount-setup                      45% (17)      48% (13)      79% ( 6)   all weak
fuse.init-reply                       23% ( 7)      28% ( 6)      70% ( 5)   weak: reader C
fuse.init-new-flag                    33% ( 6)       4% ( 3)      39% ( 2)   middling
fuse.size-limits                      21% ( 5)      40% ( 6)      60% ( 3)   weak: reader B, reader C
fuse.unmount-order                    31% ( 5)      12% ( 2)      72% ( 5)   weak: reader C
fuse.access-by-other-users            36% ( 4)      46% ( 3)      74% ( 4)   weak: reader B, reader C
fuse.user-namespaces                  25% ( 6)      28% ( 3)      69% ( 3)   weak: reader C
fuse.request-arguments                35% (14)       8% ( 9)      14% ( 7)   middling
fuse.send-variants                    17% ( 3)      32% ( 5)       9% ( 2)   middling
fuse.argument-flags                   52% ( 7)      65% ( 8)      90% ( 6)   all weak
fuse.request-allocation-blocking      43% ( 4)      39% ( 6)      51% ( 2)   weak: reader A, reader C
fuse.background-accounting            41% ( 6)      35% ( 5)      57% ( 3)   weak: reader A, reader C
fuse.end-callback                     39% ( 5)      46% ( 5)      63% ( 3)   weak: reader B, reader C
fuse.reply-size-check                 13% ( 4)      26% ( 4)      34% ( 2)   middling
fuse.request-flag-bits                34% (13)      32% (13)      65% (17)   weak: reader C
fuse.request-lists                    12% ( 2)      12% ( 3)      43% ( 4)   weak: reader C
fuse.request-end-contract             41% ( 3)      38% ( 2)      81% ( 6)   weak: reader A, reader C
fuse.waiting-for-reply                24% ( 3)      19% ( 1)      50% ( 3)   weak: reader C
fuse.interrupts                        9% ( 2)       8% ( 1)      35% ( 3)   middling
fuse.unique-ids                       14% ( 1)      17% ( 1)      52% ( 2)   weak: reader C
fuse.forget                           29% ( 4)      31% ( 1)      63% ( 8)   weak: reader C
fuse.request-timeout                  29% ( 3)      30% ( 1)      77% ( 2)   weak: reader C
fuse.abort                            30% ( 3)      39% ( 3)      78% ( 4)   weak: reader C
fuse.device-read                       4% (10)       9% ( 5)      59% (14)   weak: reader C
fuse.device-write                      0% ( 1)       4% ( 2)      21% ( 3)   middling
fuse.copy-and-abort                   32% ( 5)      49% ( 8)      93% ( 4)   weak: reader B, reader C
fuse.splice-and-folio-move            23% ( 6)      32% ( 6)      71% ( 4)   weak: reader C
fuse.transport-callbacks              28% ( 7)      54% (10)      92% ( 4)   weak: reader B, reader C
fuse.notifications                    17% ( 7)      33% (11)      81% ( 3)   weak: reader C
fuse.uring-enabling                   34% ( 9)      48% (12)      82% ( 7)   weak: reader B, reader C
fuse.uring-commands                   31% ( 4)      36% ( 5)      74% ( 4)   weak: reader C
fuse.uring-pointer-publication        47% ( 4)      62% ( 5)      78% ( 4)   all weak
fuse.uring-sqe-access                 36% ( 3)      60% ( 5)      88% ( 1)   weak: reader B, reader C
fuse.uring-entry-states               13% ( 4)      21% ( 3)      88% ( 3)   weak: reader C
fuse.uring-queue-choice               16% ( 1)      23% ( 2)      76% ( 2)   weak: reader C
fuse.uring-commit-and-fetch           13% ( 3)      48% ( 4)      66% ( 1)   weak: reader B, reader C
fuse.uring-copy-context               15% ( 1)      30% ( 4)      80% ( 2)   weak: reader C
fuse.uring-teardown                   30% ( 2)      30% ( 3)      82% ( 3)   weak: reader C
fuse.uring-buffers                    67% ( 1)      87% ( 1)      93% ( 1)   all weak
fuse.uring-zero-copy                  69% ( 1)      92% ( 1)      91% ( 1)   all weak
fuse.uring-lock-order                 33% ( 1)      47% ( 3)      86% ( 2)   weak: reader B, reader C
fuse.inode-identity                   13% ( 9)      23% (10)      51% (10)   weak: reader C
fuse.attribute-versions               16% ( 4)      47% ( 9)      67% ( 5)   weak: reader B, reader C
fuse.attribute-cache                  16% ( 3)      33% ( 8)      57% ( 4)   weak: reader C
fuse.inode-locks                       8% ( 3)      23% ( 5)      61% ( 5)   weak: reader C
fuse.reply-attribute-checks           21% ( 4)      34% ( 5)      78% ( 6)   weak: reader C
fuse.dentry-validity                  10% ( 2)      24% (10)      70% ( 6)   weak: reader C
fuse.epoch                            56% ( 8)      46% ( 4)      68% ( 3)   all weak
fuse.reverse-invalidation             21% ( 6)      34% ( 5)      55% ( 4)   weak: reader C
fuse.permission-checks                 7% ( 2)      22% ( 2)      35% ( 2)   middling
fuse.create-and-open                   8% ( 6)      10% ( 1)      41% ( 3)   weak: reader C
fuse.readdir-cache                     4% ( 2)      36% ( 4)      64% ( 3)   weak: reader C
fuse.readdirplus                       9% ( 3)      13% ( 1)      47% ( 2)   weak: reader C
fuse.xattr-and-acl                    10% ( 4)      37% ( 3)      61% ( 5)   weak: reader C
fuse.killpriv                         22% ( 5)      42% ( 3)      77% ( 4)   weak: reader B, reader C
fuse.open-file-lifetime               28% (12)      55% (15)      43% (12)   weak: reader B, reader C
fuse.io-path-choice                    2% ( 1)       6% ( 2)      50% ( 5)   weak: reader C
fuse.inode-io-modes                   21% ( 6)      28% ( 7)      72% ( 8)   weak: reader C
fuse.buffered-read                     4% ( 9)      46% (13)      69% ( 5)   weak: reader B, reader C
fuse.buffered-write                   11% ( 3)      39% ( 6)      55% ( 5)   weak: reader C
fuse.writeback-data                   22% ( 5)      24% ( 3)      73% ( 5)   weak: reader C
fuse.write-blocking                   14% ( 2)      27% ( 2)      54% ( 6)   weak: reader C
fuse.truncate                         18% ( 4)      31% ( 4)      58% ( 6)   weak: reader C
fuse.fsync-and-syncfs                 10% ( 3)      12% ( 3)      50% ( 5)   weak: reader C
fuse.mmap                             15% ( 4)      25% ( 3)      62% ( 5)   weak: reader C
fuse.direct-io                        21% (13)      36% ( 8)      64% ( 6)   weak: reader C
fuse.backing-files                    12% ( 6)      31% ( 8)      49% ( 6)   weak: reader C
fuse.passthrough-io                   20% ( 8)      27% ( 8)      58% ( 9)   weak: reader C
fuse.file-locks                       32% (12)      16% ( 9)      64% (11)   weak: reader C
fuse.ioctl                            24% ( 6)      32% ( 6)      74% ( 8)   weak: reader C
fuse.virtiofs-requests                14% (11)      16% (10)      64% (12)   weak: reader C
fuse.virtiofs-lifetime                23% ( 7)      28% ( 8)      67% ( 7)   weak: reader C
fuse.dax                              25% (11)      38% (11)      74% ( 7)   weak: reader C
fuse.cuse                             23% (19)      49% (23)      69% (22)   weak: reader B, reader C
fuse.untrusted-server                 23% (15)      55% (15)      92% (16)   weak: reader B, reader C
fuse.reclaim-and-allocation           24% (13)      50% ( 7)      94% ( 8)   weak: reader B, reader C
```

## Questions reorganised

The build set is organised by subject, and every question of a part names the
part as its section: connection, channel and device; mounting and the INIT
exchange; access and credentials; sending a request; request state; device
read and write; the io-uring transport; inodes and lookup counts; attributes;
dentries and directories; open files; cached I/O and writeback; direct I/O and
passthrough; virtio-fs and DAX; CUSE. Inside a part the questions about
requirements come last.

Questions that moved to the part whose code they are about:

| Question | Moved from | Moved to |
|---|---|---|
| `fuse.uapi-header` | the subsystem | mounting and the INIT exchange |
| `fuse.access-by-other-users`, `fuse.user-namespaces` | mounting | access and credentials |
| `fuse.untrusted-server` | changing the implementation | access and credentials |
| `fuse.forget` | request state | inodes and lookup counts |
| `fuse.readdirplus` | dentries and directories | inodes and lookup counts |
| `fuse.xattr-and-acl`, `fuse.killpriv` | dentries and directories | attributes |
| `fuse.file-locks`, `fuse.ioctl` | other file operations | open files |
| `fuse.reclaim-and-allocation` | changing the implementation | cached I/O and writeback |

Two questions were reworded, and every other question keeps the text that was
measured:

- `fuse.notifications` no longer asks which notifications the server can send,
  since `enum fuse_notify_code` lists them. It asks in which states of the
  connection a notification is accepted, and which lock each kind holds.
- `fuse.untrusted-server` asked where the tree states the requirements, which
  sends the builder to the documentation. It now asks which code enforces each
  requirement.
