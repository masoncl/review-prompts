# What the smb-ksmbd measurement found

Three models were asked the 36 questions in `smb-ksmbd-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels from 6.12 to 7.0), reader A a little behind it (6.12 to 6.18),
and reader B older (6.10 to 6.15) and much less exact, with invented names and
several mechanisms described as they were some releases ago. The hand-written
guide was never checked against current sources, so differences between it and
the built guide are expected and are noted near the end.

The server has changed a good deal under all three readers. Readers A and C
know the layout of `fs/smb/server/`, how a handler should bounds-check what a
client sends, how a file handle is looked up and put, and (reader C) how a
name is confined to the share. What all three get wrong is what keeps the
long-lived objects alive, because nearly all of that has been reworked: the
connection now has a real reference count with a deferred free, sessions have
a second lookup path and a starting count of two, leases are shared and
counted, message ids are checked against a window, and the whole SMB Direct
implementation has moved out of the server.

## What all three readers got wrong

- **Where SMB Direct lives.** Reader B said it is all in
  `fs/smb/server/transport_rdma.c` and that nothing is shared with the client.
  Reader A said the same with some headers under fs/smb/common/smbdirect/,
  and reader C put all of it in that directory, which does not exist. The
  protocol is in `fs/smb/smbdirect/`, its own module built by
  `CONFIG_SMBDIRECT`, which both `CONFIG_SMB_SERVER_SMBDIRECT` and the
  client's `CONFIG_CIFS_SMB_DIRECT` select. `transport_rdma.c` keeps the
  listener threads for ports 445 and 5445, the accept path and thin
  `struct ksmbd_transport_ops` wrappers over `smbdirect_connection_recvmsg()`,
  `smbdirect_connection_send_iter()` and `smbdirect_connection_rdma_xmit()`.
- **When the negotiate response goes out.** Every reader said it is sent when
  the peer's request arrives. `smbdirect_accept_negotiate_recv_work()` only
  moves the socket to the listener's ready list; the response is sent by
  `smbdirect_accept_negotiate_finish()` when the server calls
  `smbdirect_socket_accept()`, so that no credits are granted before the
  application has the socket. Readers A and B had the two work items that can
  grant credits re-enabled with enable_work() or enable_and_queue_work();
  nothing under `fs/smb/` calls either. `smbdirect_connection_negotiation_done()`
  gives `recv_io.posted.refill_work` and `idle.immediate_work` their handlers
  with `INIT_WORK()`, and it runs from the send completion of the response,
  `smbdirect_accept_negotiate_send_done()`. Reader A still named
  smb_direct_send_negotiate_response() and smb_direct_prepare(), neither of
  which is in this tree. Reader C had the mechanism right and the timing
  wrong.
- **Message ids are checked.** All three said the server keeps no window of
  message ids and no record of used ones. `smb2_check_sequence_number()`
  checks the range a request consumes against `seq_low`, `seq_high` and
  `seq_bitmap` in `struct ksmbd_conn`, under `credits_lock`, and a request
  outside the window or replayed sets the connection exiting.
  `smb2_set_rsp_credits()` extends the window.
- **The credit charge on error paths.** All three said
  `smb2_set_rsp_credits()` runs on every response. The abort, error and
  send-no-response paths skip it; the charge taken by
  `smb2_validate_credit_charge()` is kept in `work->credit_charge` and
  subtracted from `outstanding_credits` after the `send:` label in
  `__handle_ksmbd_work()`. The charge check itself applies only with
  `SMB2_GLOBAL_CAP_LARGE_MTU`.
- **What keeps a connection alive.** The readers knew `r_count` and
  `req_running`. None had the holders of `refcnt` right: `ksmbd_conn_get()` is
  used for `opinfo->conn`, `fp->conn`, the lease table's `conn`, each
  byte-range lock's `conn`, oplock and lease break work items and the change
  notify work (`owns_conn_ref`). Reader B had every work item taking one,
  which is not so. All three had the last put freeing the structure in place;
  `ksmbd_conn_put()` queues `release_work` on `ksmbd_conn_wq` and
  `__ksmbd_conn_release_work()` frees the transport and the structure in
  process context, because the last put can come from an RCU callback.
  `stop_sessions()` open-codes the final free and is the one exception.
  Reader C said it did not recognise `ksmbd_conn_put()`.
- **Connection status.** No reader knew that `conn->request_lock` orders a
  change to exiting or releasing in `ksmbd_conn_abort()`, `stop_sessions()`
  and `ksmbd_all_conn_set_status()` against
  `ksmbd_conn_link_async_request()`, or that the last of these never
  overwrites exiting or releasing. Readers A and C did not recognise
  `ksmbd_conn_abort()`; reader B had KSMBD_CONN_ names for the states.
- **Teardown.** Readers A and C named ksmbd_sessions_deregister(), which is
  gone; the terminate callback calls `ksmbd_conn_sessions_cleanup()` and
  `destroy_lease_table()`. Both missed `ksmbd_conn_cancel_async_requests()`
  between the change to releasing and the wait for `r_count`. Reader B had the
  status as exiting and the steps in the wrong order.
- **Sessions.** `__session_create()` sets the count to 2, one for the tables
  and one for the creator. The dispatcher uses
  `ksmbd_session_lookup_all_states()`, which takes a reference and accepts any
  state; `ksmbd_session_lookup_all()` accepts only valid sessions and has no
  caller left. Logoff and expiry only set `SMB2_SESSION_EXPIRED`; the table
  reference is dropped by `ksmbd_session_unregister()`,
  `ksmbd_conn_sessions_cleanup()` and `ksmbd_too_many_session_setups()`.
  Reader B said there is no global table and that `ksmbd_session_lookup()`
  takes no reference. Readers A and C used ksmbd_expire_session() and
  ksmbd_session_new(), which do not exist.
- **What an oplock object pins.** It holds a reference on the connection and
  on its lease and on nothing else: `o_fp` and `sess` are plain pointers.
  Even the connection reference does not last, because `session_fd_check()`
  puts it and clears `conn` and `sess` under `ci->m_lock` when a durable
  handle is kept. All three said that holding the oplock object makes its
  pointers safe. The correct form is `smb2_oplock_break_conn_get()` and
  `smb2_lease_break_conn_get()`, which read the connection under `ci->m_lock`
  and take their own reference.
- **Leases are shared and counted.** Readers A and C said each open has its
  own copy kept in step by copy_lease(), which does not exist. `struct lease`
  has a `refcount`, opens with the same key share one through `lease_get()`,
  the opens are on `lease->open_list` under `lease->lock`, and the per-client
  table lists leases, not opens. `lease_list_lock` is a rwlock and no walk
  uses RCU.
- **The break sequence.** A timeout in `wait_for_break_ack()` sets the holder
  to `OPLOCK_STATE_NONE` and level none, not to closing, and the caller then
  invalidates a durable handle. Only batch and exclusive oplocks and leases
  with write or handle caching wait for an acknowledgement. A lease break for
  an open that has lost its connection goes out on the lease table's
  connection, for a version 2 lease only (a version 1 lease has no fallback).
  Reader B took `smb2_oplock_break()` for the sender; it handles the
  acknowledgement.
- **Several locks are sleeping locks.** `tree_conns_lock`, `chann_lock`,
  `m_lock` and `ipc_msg_table_lock` are rw_semaphores; one reader or another
  called each a rwlock or a spinlock.
- **Compression.** Readers A and C said the server has none; reader B had it
  in the wrong place. `fs/smb/server/compress.c` decompresses a plain
  transform in the receive loop and an encrypted one after decryption, and
  compresses read responses after the pre-authentication hash and before
  encryption.
- **Signing exemptions.** Readers A and C said `smb2_is_sign_req()` exempts
  negotiate, session setup and oplock break. It exempts negotiate only.
  Unencrypted requests are refused per share
  (`KSMBD_SHARE_FLAG_ENCRYPT_DATA`) in `__handle_ksmbd_work()`.
- **Answers from the daemon.** The netlink policy lengths are minimums, and
  the RPC and SPNEGO entries have none. `ipc_validate_msg()` runs in
  `ipc_msg_send_request()` after the wait, checks four events only (RPC,
  SPNEGO, share configuration, extended login) and checks termination of the
  share name only; the account name goes to `kstrdup()` unchecked.
- **Smaller things all three missed**: a tree connect has a count of 2 after
  connect and tree disconnect closes the files before it marks the entry;
  every open gets a persistent id, not only durable ones; what decides whether
  a handle survives its session is `is_reconnectable()`; the sysfs kill switch
  runs the reset synchronously; module exit drains `ksmbd_conn_wq` after
  `rcu_barrier()`.

## What only some readers got wrong

Readers A and B, not C:

- **Path lookup.** Both had `vfs_path_lookup()` or kern_path_create() on a
  path built by convert_to_unix_name(), which is not in this tree. The lookup
  is `vfs_path_parent_lookup()` rooted at the share's `vfs_path` with
  `LOOKUP_BENEATH`, the last component through `lookup_noperm_unlocked()`, a
  final mount point crossed only with `KSMBD_SHARE_FLAG_CROSSMNT`, and creation
  through `start_creating_noperm()`. `KSMBD_SHARE_FLAG_FOLLOW_SYMLINKS` is
  never tested.
- **Credentials** are built from `prepare_kernel_cred(&init_task)`, not copied
  from the current ones; the forced ids of a share replace only the fsuid and
  fsgid.
- `struct ksmbd_inode` is keyed by dentry and shared by the streams of a file;
  delete-pending for a stream is kept per handle.

Reader B, and nobody else: a work queue per connection (there is one, global);
decryption per command of a compound (once, before the loop); handle lookups
that reject only closed handles (they require `FP_INITED`); a channel list
linked through a list head (an xarray keyed by the connection pointer); the
oplock object holding a reference on the file handle; an invented
smb2_command() dispatch table and smb2_check_message().

## What the readers already knew

Which file holds what under `fs/smb/server/` (readers A and C without error).
The pattern for walking variable-length entries in a request, with
`smb2_find_context_vals()` and `smb2_set_ea()` as the models (A and C). Lookup
and put of a file handle on every exit path, and that the lookup checks the
tree connect (A and C). The round trip to the daemon: the handle, the table,
the two-second wait, NULL on failure (A and C). The outline of the dispatcher
and of compound handling. Reader C answered path confinement and the
credential override with nothing to correct.

## Something the checker found in the tree

Two readers offered `smb2_open()` as the model for pairing
`ksmbd_override_fsids()` with `ksmbd_revert_fsids()`. It is not one: in the
durable replay and durable reconnect branches a failing `ksmbd_vfs_getattr()`
jumps to `err_out2`, which is below the revert at `err_out1`.

## Where the hand-written guide is stale

`smb-ksmbd.md` is about one invariant, that the SMB Direct negotiate response
is the first message to grant credits, and the invariant still holds. Every
name it gives for the code that keeps it is gone or has moved:

- It places the code in `fs/smb/server/transport_rdma.c` and
  fs/smb/common/smbdirect/smbdirect_socket.h. The first is now glue and the
  second does not exist; `struct smbdirect_socket` is in
  `fs/smb/smbdirect/socket.h`.
- smb_direct_send_negotiate_response(), smb_direct_create_header(),
  manage_credits_prior_sending(), smb_direct_post_recv_credits(),
  smb_direct_send_immediate_work(), smb_direct_post_send_data() and
  smb_direct_prepare_negotiation() exist nowhere in the tree.
- Its three-step sequence (give the refill work its handler and run it, then
  give the immediate work its handler, then send the response) is not what the
  tree does. Receive buffers are posted by a direct call to
  `smbdirect_connection_recv_io_refill()`, both work items keep the
  placeholder handler until the response's send completion, and the response
  waits for `smbdirect_socket_accept()`.
- `smbdirect_socket_init()`, `__smbdirect_socket_disabled_work()` and the
  `disable_work_sync()` pattern are as it describes.

The trigger for the guide in `kernel/subsystem/subsystem.md` lists
`fs/smb/server/` and the ksmbd_ and smb_direct_ prefixes; it does not match
`fs/smb/smbdirect/` or the smbdirect_ prefix, where the code it is about now
is.

## What was left out of the build set, and why

The hand-written guide is 365 words, which is under the 600-word floor, so the
build set is sized to 600: eight questions and 500 words of budget, none under
40. The first build set was held to the hand-written guide's size, six
questions and about 290 words, and at 35 to 60 words for questions that each
ask five things the answers came out as fragments. Those six were chosen by
importance to someone reviewing a server patch among the things every reader
had wrong: where SMB Direct is, the first credit grant (the old guide's
subject), what keeps a connection alive, the session's tables and count, what
an oplock object does not pin, and the message id window. They are kept and now
have 45 to 80 words each. Lease objects and the break sequence were added
back, as the next two things every reader had wrong that a lifetime bug or a
hung open can hide behind: that opens with the same key share one counted
lease, which locks cover the tables, and what a break waits for, on which
connection it goes out and what a timeout does. Four questions are worded a
little differently from the measurement run, here and in the measurement set,
so that they do not presuppose an answer or so that they ask for constant names
in full: `ksmbd.smbdirect-location`, `ksmbd.session-lifetime`,
`ksmbd.lease-objects` and `ksmbd.break-sequence`.

Left out although every reader was weak on them, for lack of room: connection
status and teardown order, the work item, asynchronous requests and cancel,
tree connects, durable handles, the oplock object's own lifetime, session
setup, the order of decryption, decompression and signing, the checks on the
daemon's answers, server start and reset, and the checklist for changing a
command. Several of these would be the next to add if the guide were allowed to
grow; the teardown order and asynchronous requests first. Left out because two
readers already answer them: the source layout, offsets and lengths from the
client, using a file handle, the netlink round trip, building the response.
Path confinement and the credential override are security-critical and two
readers had the mechanism out of date, but the most current reader had both
exactly right and a wrong answer there does not hide a bug in a diff, so they
gave way to the lifetime questions.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A          122        52%      2     28   6.12 to 6.18
reader B          134        81%      0     35   6.10 to 6.15
reader C           91        38%      7     21   6.12 to 7.0

question                            reader A      reader B      reader C
ksmbd.source-layout                  0% ( 2)      16% ( 7)       2% ( 2)
ksmbd.shared-with-client            43% ( 4)      90% ( 3)      62% ( 4)
ksmbd.smbdirect-location            80% ( 2)      87% ( 3)      55% ( 2)
ksmbd.request-path                  41% ( 2)      86% ( 7)      10% ( 6)
ksmbd.transforms-order              70% ( 4)      66% ( 3)      67% ( 4)
ksmbd.compound-state                34% ( 2)      82% ( 2)      47% ( 4)
ksmbd.response-buffers              29% ( 2)      87% ( 2)       8% ( 0)
ksmbd.message-checks                37% ( 6)      88% ( 6)      30% ( 4)
ksmbd.request-field-usage           14% ( 1)      86% ( 1)      18% ( 2)
ksmbd.credits-and-sequence          62% ( 3)      88% ( 2)      55% ( 2)
ksmbd.conn-lifetime                 49% ( 7)      79% ( 5)      65% ( 7)
ksmbd.conn-status                   84% ( 4)      80% ( 3)      61% ( 2)
ksmbd.conn-teardown-order           70% ( 3)      71% ( 2)      53% ( 2)
ksmbd.work-lifetime                 68% ( 3)      93% ( 2)      60% ( 1)
ksmbd.async-and-cancel              41% ( 3)      79% ( 3)      55% ( 1)
ksmbd.session-lifetime              59% ( 5)      79% ( 6)      44% ( 3)
ksmbd.session-pointer-usage         49% ( 1)      90% ( 2)       9% ( 1)
ksmbd.session-setup-paths           65% ( 3)      84% ( 3)      40% ( 3)
ksmbd.session-channels              59% ( 3)      88% ( 1)      31% ( 2)
ksmbd.tree-connect-lifetime         42% ( 3)      78% ( 3)      43% ( 2)
ksmbd.file-handle-lifetime          38% ( 3)      81% ( 4)      42% ( 1)
ksmbd.file-handle-usage             27% ( 1)      74% ( 2)       7% ( 1)
ksmbd.inode-object                  64% ( 2)      81% ( 3)      28% ( 1)
ksmbd.durable-handles               58% ( 4)      88% ( 5)      54% ( 1)
ksmbd.opinfo-lifetime               44% ( 7)      84% ( 6)      25% ( 4)
ksmbd.opinfo-usage                  74% ( 3)      89% ( 2)      43% ( 1)
ksmbd.lease-objects                 74% ( 5)      86% ( 5)      69% ( 3)
ksmbd.break-sequence                45% ( 4)      85% ( 6)      44% ( 5)
ksmbd.path-confinement              77% ( 5)      70% ( 6)       0% ( 0)
ksmbd.credential-override           57% ( 2)      79% ( 5)       0% ( 0)
ksmbd.ipc-round-trip                33% ( 3)      85% ( 4)      17% ( 3)
ksmbd.ipc-response-checks           59% ( 4)      88% ( 3)      55% ( 3)
ksmbd.server-state                  54% ( 3)      87% ( 4)      29% ( 3)
ksmbd.smbdirect-credit-order        64% ( 5)      80% ( 3)      48% ( 3)
ksmbd.smbdirect-work-usage          63% ( 2)      84% ( 1)      37% ( 2)
ksmbd.command-change-checklist      59% ( 6)      83% ( 9)      66% ( 6)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `ksmbd.conn-teardown-order`, `ksmbd.work-lifetime`, `ksmbd.async-and-cancel`, `ksmbd.session-setup-paths`, `ksmbd.tree-connect-lifetime`, `ksmbd.file-handle-lifetime`, `ksmbd.inode-object`, `ksmbd.path-confinement`, `ksmbd.credential-override`, `ksmbd.ipc-response-checks`, `ksmbd.smbdirect-work-usage`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `ksmbd.request-path`, `ksmbd.compound-state`, `ksmbd.message-checks`, `ksmbd.request-field-usage`, `ksmbd.session-pointer-usage`, `ksmbd.file-handle-usage`, `ksmbd.opinfo-lifetime`, `ksmbd.ipc-round-trip`.

## Questions reorganised

29 questions before and 29 after, every id kept, by subject: request dispatch and validation (5),
connections and work items (4), sessions and tree connects (4), open files (3), names and
credentials (2), oplocks and leases (4), the user-space daemon (2), SMB Direct (3). The "Where to
look" part is gone: its one question, `ksmbd.smbdirect-location`, opens the SMB Direct subject,
and `ksmbd.smbdirect-credit-order` and `ksmbd.opinfo-usage` now have a section. Nothing merged or
dropped. Most questions asked five or six things ("which fields, which lock, where, who, what
states") and were cut to the three a reviewer acts on; `ksmbd.request-path` and
`ksmbd.compound-state` no longer ask for a trace or for the fields of the work item.
