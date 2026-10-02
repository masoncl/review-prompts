# SMB/ksmbd Subsystem

## Main structures

### Objects and how they relate

- `struct ksmbd_conn`: three separate counters. `refcnt` is the lifetime
  count (`ksmbd_conn_get()`, `ksmbd_conn_put()`); `r_count` counts works in
  flight and `ksmbd_conn_handler_loop()` waits for it to reach 0 before
  teardown; `req_running` feeds the idle waits and the in-flight cap.
- `conn->status`: its values are `KSMBD_SESS_NEW`, `KSMBD_SESS_GOOD` and the
  rest of that enum in `fs/smb/server/connection.h`, despite the name.
  Session state is separate: `sess->state`, with `SMB2_SESSION_EXPIRED`,
  `SMB2_SESSION_IN_PROGRESS` and `SMB2_SESSION_VALID`.
- `struct ksmbd_transport`: not embedded in the conn. `conn->transport`
  points to one embedded in `struct tcp_transport` or
  `struct smb_direct_transport`, and it points back through `conn`.
- `struct ksmbd_conn_ops`: only `process_fn` and `terminate_fn`, in one
  static `default_conn_ops` in `fs/smb/server/connection.c`;
  `conn->conn_ops` is never assigned.
- `struct smb_version_ops` (`conn->ops`): the per-dialect hooks for session
  and tree lookup, signing, encryption and credits.
  `struct smb_version_cmds` (`conn->cmds`) is the command table.
- Global containers: connections are in hashtable `conn_list` under rwsem
  `conn_list_lock`; lease tables are on list `lease_table_list` under rwlock
  `lease_list_lock` in `fs/smb/server/oplock.c`.
- `conn->sessions`: holds only sessions created on that conn;
  `ksmbd_session_register()` is the only store.
- Conn bound by multichannel: tied to the session only by its entry in
  `sess->ksmbd_chann_list`, indexed by the conn pointer; the session is
  found in `sessions_table`, see the fallback in
  `ksmbd_session_lookup_all_states()`.
- `struct channel`: created only when `conn->dialect` is at least
  `SMB30_PROT_ID`, in `register_session_channel()`; `chann->conn` is an
  uncounted pointer.
- `struct ksmbd_user`: not refcounted. The session owns it and
  `ksmbd_session_destroy()` frees it; `tree_conn->user` is a copy of the
  pointer `sess->user`.
- `work->sess` and `work->tcon`: counted references, taken by
  `smb2_check_user_session()` and `smb2_get_ksmbd_tcon()`, dropped at the end
  of `__handle_ksmbd_work()`. Later commands of a compound reuse the first
  command's pair.
- Break notification work: `request_buf` holds a
  `struct oplock_break_info` or `struct lease_break_info`, not an SMB
  header; `work->sess` is copied from `opinfo->sess` without a reference; it
  runs `__smb2_oplock_break_noti()` or `__smb2_lease_break_noti()`.
- Blocking byte-range lock: `smb2_lock()` sleeps in
  `ksmbd_vfs_posix_lock_wait()` inside the handler; the work does not outlive
  it.
- `global_ft` in `fs/smb/server/vfs_cache.c`: holds every open, not only
  durable ones; `smb2_open()` assigns a persistent id to each. An oplock
  break notification finds its open there by `opinfo->fid`.
- Detached durable handle: `fp->conn` and `fp->tcon` are `NULL` and
  `fp->volatile_id` is `KSMBD_NO_FID`; it stays in `global_ft` and on
  `m_fp_list`. `session_fd_check()` also clears `conn` and `sess` of every
  opinfo on the inode that has the same conn, and `conn` of the handle's
  locks; `ksmbd_reopen_durable_fd()` restores them for the handle's own
  opinfo and locks.
- `struct ksmbd_inode`: keyed by dentry (`m_de`), not by `struct inode`; see
  `__ksmbd_inode_lookup()`. Some walkers of `m_fp_list` compare
  `file_inode()` themselves, for example `ksmbd_smb_check_shared_mode()` and
  `ksmbd_lookup_fd_inode()`.
- `m_fp_list`: the list that share-mode checks walk, in
  `ksmbd_smb_check_shared_mode()`. `m_op_list` serves oplock and lease
  breaks.
- Stream name and size: in `struct stream` inside `struct ksmbd_file`, not in
  `struct ksmbd_inode`.
- `struct lease`: refcounted and shared, through `lease->open_list`, by the
  opinfos that `same_client_has_lease()` matched by client GUID and lease
  key on one `struct ksmbd_inode`.
- `struct lease_table`: one per client GUID; links `struct lease`, not
  `struct oplock_info`. `lb->conn` is the conn that created it, counted, and
  is the fallback route for a v2 lease break.
- `struct ksmbd_lock`: linked on `fp->lock_list` by `flist` and on
  `conn->lock_list` by `clist`, holding a conn reference while on
  `conn->lock_list`; `llist` is the request-local list inside `smb2_lock()`.

## Request dispatch and validation

**Reader thread and dispatcher**

- `handle_ksmbd_work()`: calls `__handle_ksmbd_work()` once; the per-command
  loop is inside `__handle_ksmbd_work()` in `fs/smb/server/server.c`.
- Reader throttle: `ksmbd_conn_handler_loop()` waits while `conn->req_running`
  would exceed `server_conf.max_inflight_req` (default `SMB2_MAX_CREDITS`), not
  `conn->vals->max_credits`.
- Minimum sizes in the reader: `SMB1_MIN_SUPPORTED_PDU_SIZE`,
  `SMB2_MIN_SUPPORTED_PDU_SIZE`, `SMB2_TRANSFORM_MIN_SUPPORTED_PDU_SIZE` in
  `fs/smb/server/connection.c`; there are no SMB1_MIN_SUPPORTED_HEADER_SIZE or
  SMB2_MIN_SUPPORTED_HEADER_SIZE here.
- Compressed PDU (`SMB2_COMPRESSION_TRANSFORM_ID`): the reader thread replaces
  `conn->request_buf` with the decompressed PDU in `ksmbd_decompress_request()`
  before `ksmbd_smb_request()`; failure ends the connection loop.
- `queue_ksmbd_work()`: calls `ksmbd_init_smb_server()` first; if that fails it
  returns 0, no work is queued, no response is sent, the reader keeps going.
- Once per message, before the loop, on a transform header: `decrypt_req`,
  then `ksmbd_decompress_work_request()` if the plaintext is a compression
  transform, then a re-check of `ProtocolId` and of
  `sizeof(struct smb2_pdu)`.
- Failure of decrypt, decompress or that re-check: `ksmbd_conn_abort()` and
  return; no response. Failure of `allocate_rsp_buf`: return; no response.
- Per command, in this order:
  1. `check_user_session`, for every command including the first;
  2. `get_ksmbd_tcon` when step 1 returned > 0, then `STATUS_ACCESS_DENIED` if
     the share has `KSMBD_SHARE_FLAG_ENCRYPT_DATA` and `work->encrypted` is
     false;
  3. `__process_request()`;
  4. `set_rsp_credits` under `conn->credits_lock`;
  5. `smb2_complete_request_open()`;
  6. `is_chained_smb2_message()`, which advances to the next command;
  7. `set_sign_rsp`, on the response at `ksmbd_resp_buf_curr()`.
- `__process_request()` with `work->sess->sign` set, `work->encrypted` false
  and an unsigned request: `STATUS_ACCESS_DENIED` and `SERVER_HANDLER_ABORT`,
  before `check_sign_req` is considered.
- `check_conn_state()` returning 1: `__process_request()` returns
  `SERVER_HANDLER_CONTINUE` without running the message check or the handler.
- `SERVER_HANDLER_ABORT` is returned for: failed `ksmbd_verify_smb_message()`,
  command >= `conn->max_cmds`, NULL `proc`, the two signing failures, and
  `work->send_no_response` after the handler. The dispatcher calls
  `smb2_complete_request_open()` and breaks the loop, so steps 4, 6 and 7 do
  not run for that command.
- `goto send` (skipping the rest of the loop): session failure, tree connect
  failure, the share encryption test, and `set_rsp_credits` returning < 0.
- ksmbd has no `is_chained_work()`; that name is a static function in
  `kernel/workqueue.c`. `is_chained_smb2_message()` in
  `fs/smb/server/smb2pdu.c` is the chain test.
- Once per message at `send:`, in order: `smb2_complete_request_open()`,
  release of a leftover `work->credit_charge`, `ksmbd_tree_connect_put()`,
  `smb3_preauth_hash_rsp()`, `ksmbd_compress_response()` when
  `work->compress_response`, `encrypt_resp`, `ksmbd_user_session_put()`,
  `ksmbd_conn_write()`.

**Checks before a handler runs**

- `ProtocolId`: tested by `ksmbd_verify_smb_message()` in
  `fs/smb/server/smb_common.c`, on the current command's header;
  `check_smb2_hdr()` only rejects `SMB2_FLAGS_SERVER_TO_REDIR`.
- `len` below `__SMB2_HEADER_STRUCTURE_SIZE + sizeof(__le16)`: rejected before
  `StructureSize2` is read; this matters for a small `NextCommand`.
- Accepted when `clc_len != len`, exactly these four:
  - `clc_len == len + 1`;
  - `ALIGN(clc_len, 8) == len`;
  - the command is `SMB2_NEGOTIATE_HE`, any mismatch;
  - `clc_len < len` and `len - clc_len <= 8`.
- No other command tolerates a calculated length above `len + 1`.
- NEGOTIATE: `smb2_get_data_area_len()` has no case for it, so only the fixed
  part is checked; `smb2_handle_negotiate()` bounds the dialects and contexts.
- Offsets clamped up to `offsetof(..., Buffer)` in `smb2_get_data_area_len()`:
  for example `BufferOffset`, `DataOffset`, `InputOffset`. The clamp is local;
  the field in the request is unchanged.
- A handler that adds the raw field to `req` reads a different place than the
  one checked when the field is below `Buffer`; `smb2_write()` rejects such a
  `DataOffset` itself.
- Not clamped: `SecurityBufferOffset`, `ReadChannelInfoOffset`,
  `WriteChannelInfoOffset`, `CreateContextsOffset`.
- Data length 0: `smb2_calc_size()` skips the overlap test and the offset takes
  no part in `clc_len`; the offset is only known to be <= 4096.
- `clc_len == len + 1`: the last byte of the calculated length is past what
  was received. The buffer has one spare byte (`pdu_size + 4 + 1` from
  `kvmalloc()`) that the read does not fill; in a non-final compound command
  that byte is the next header's first byte.

**Credits and message ids**

- `smb2_validate_credit_charge()`: on success adds the charge to
  `conn->outstanding_credits` and stores it in `work->credit_charge`, except
  for `SMB2_CANCEL`, where it returns 0 and takes nothing; it does not change
  `conn->total_credits`. On any failure it takes nothing.
- Gate: `conn->vals->req_capabilities & SMB2_GLOBAL_CAP_LARGE_MTU`; every
  table in `fs/smb/server/smb2ops.c` sets that bit statically. The server code
  does not use a field named `capabilities`.
- Required charge: `SMB2_QUERY_DIRECTORY` counts too, by
  `OutputBufferLength`.
- `smb2_set_rsp_credits()`: subtracts the charge from `total_credits` and
  `outstanding_credits`, clears `work->credit_charge`, then adds the grant to
  `total_credits`.
- Grant: also capped by `conn->seq_low + KSMBD_CMD_SEQ_WINDOW -
  conn->seq_high`, so it can be 0; the grant extends `seq_high` and sets the
  new bits in `seq_bitmap`.
- `CreditRequest` in the response: `smb2_set_rsp_credits()` writes the grant
  only when the command has `NextCommand == 0`, as the sum in
  `work->credits_granted`.
- `smb2_set_rsp_credits()` returns `-EINVAL` when `total_credits` exceeds
  `conn->vals->max_credits` or the charge exceeds `total_credits`; the
  dispatcher sets `STATUS_INVALID_PARAMETER` and goes to `send:`.
- Handler error with a response: `__process_request()` returns
  `SERVER_HANDLER_CONTINUE`, so `smb2_set_rsp_credits()` runs as usual.
- `SERVER_HANDLER_ABORT` (failed message check, bad command, signing failure,
  `send_no_response`): `smb2_set_rsp_credits()` does not run. At `send:`,
  `__handle_ksmbd_work()` subtracts `work->credit_charge` from
  `outstanding_credits`; `total_credits` is unchanged and nothing is granted.
- Session or tree connect failure: reaches `send:` before the message check;
  `work->credit_charge` is 0 and nothing is released or granted.
- `smb2_send_interim_resp()`: copies the header at `ksmbd_resp_buf_next()`
  before credits are set for that command; it changes no credit state.
- `conn->credits_lock`: held for every access to `total_credits`,
  `outstanding_credits`, `seq_low`, `seq_high` and `seq_bitmap` on the SMB2
  request path; `smb2_set_rsp_credits()` runs with it held by the dispatcher.

**Message id window**

- Models take ksmbd to have no message id window. This tree has one:
  `smb2_check_sequence_number()` in `fs/smb/server/smb2misc.c`, called at the
  end of `ksmbd_smb2_check_message()`, after the credit charge check.
- State: `seq_low`, `seq_high` and `seq_bitmap` in `struct ksmbd_conn`
  (`fs/smb/server/connection.h`); the granted range is `[seq_low, seq_high)`,
  a set bit means granted and not yet used.
- Lock: `conn->credits_lock`; there is no separate sequence lock. The credit
  check and the sequence check are two separate critical sections.
- Ids consumed by a request: `CreditCharge` consecutive ids from `MessageId`,
  or 1 when `CreditCharge` is 0.
- Rejected: `MessageId + charge` wraps, any part of the range is outside
  `[seq_low, seq_high)`, or any id in it has its bit clear (already used).
- On rejection: `ksmbd_smb2_check_message()` calls `ksmbd_conn_set_exiting()`
  and returns 1; it does not call `ksmbd_conn_abort()`.
- Result for the request: `__process_request()` sets
  `STATUS_INVALID_PARAMETER` and aborts the loop; the response still goes to
  `ksmbd_conn_write()`; the reader loop ends at its next `ksmbd_conn_alive()`
  test.
- On acceptance: the bits are cleared and `seq_low` advances past used ids.
- `SMB2_CANCEL`: exempt, consumes no id.
- Compound: each command is checked with its own `MessageId`.
- Window growth: only in `smb2_set_rsp_credits()`, by the credits granted.
- Start: `ksmbd_conn_alloc()` sets the window to id 0 only. An SMB1 negotiate
  consumes id 0 in `ksmbd_verify_smb_message()`.
- `KSMBD_CMD_SEQ_WINDOW`: 8192, indexes `seq_bitmap` as a ring;
  `init_smb2_max_credits()` clamps `max_credits` to `SMB2_MAX_CREDITS` to match.
- `struct ksmbd_conn` has no req_hdr_id field and no field named `credits`.

**Compound request state**

- `smb_get_msg()` in `fs/smb/server/smb_common.h` returns the first command;
  there is no smb2_get_msg() in this tree.
- `ksmbd_req_buf_next()`, `ksmbd_resp_buf_next()`, `ksmbd_resp_buf_curr()`:
  static inlines in `fs/smb/server/ksmbd_work.h`.
- `smb2_current_req_len()` in `fs/smb/server/smb2pdu.c`: length of the current
  command (`NextCommand`, else the rest of the PDU); it is static.
- `KSMBD_NO_FID` is `INT_MAX`; `has_file_id()` is `id < KSMBD_NO_FID`.
  `SMB2_NO_FID` is the all-ones value. Both are in
  `fs/smb/server/vfs_cache.h`.
- `init_chained_smb2_rsp()` stores `compound_fid` and `compound_pfid` after a
  successful CREATE, and also after a successful FLUSH, READ or WRITE whose
  request carried a real file id.
- Failed CREATE: resets both ids to `KSMBD_NO_FID` and stores the status in
  `work->compound_status`.
- Other failed command: stores `compound_status` only if that request had
  `SMB2_FLAGS_RELATED_OPERATIONS`.
- Next request without `SMB2_FLAGS_RELATED_OPERATIONS`: ids reset to
  `KSMBD_NO_FID`, `compound_status` to `STATUS_SUCCESS`.
- `smb2_compound_has_failed()`: true for a later command when `compound_fid`
  is not a file id and `compound_status` is not `STATUS_SUCCESS`; it writes the
  stored status as the error response. Handlers call it once they have the
  request and response buffers, and return when it is true; search for its
  callers.
- Later response headers: `init_chained_smb2_rsp()` sets
  `SMB2_FLAGS_RELATED_OPERATIONS` on each, whatever the request flag.
- `is_chained_smb2_message()` stops chaining, with no response for the
  remaining commands, when the next header does not fit in the request or
  when fewer than `MAX_CIFS_SMALL_BUFFER_SIZE` bytes of `work->response_sz`
  remain.
- `work->compound_sid`: read only by `smb2_close()`;
  `smb2_check_user_session()` does not use it.
- `smb2_check_user_session()`, later command, beyond the id match:
  - NEGOTIATE, SESSION_SETUP and ECHO return 0, so `get_ksmbd_tcon` is skipped;
  - `ksmbd_conn_good()` false gives `-EIO`;
  - session state other than `SMB2_SESSION_VALID` gives `-EINVAL`, or
    `-EKEYEXPIRED` after Kerberos expiry unless
    `smb2_session_expired_cmd_allowed()` accepts the command.
- `smb2_get_ksmbd_tcon()`, later command, beyond the id match:
  - TREE_CONNECT, CANCEL and LOGOFF return 0 without a check;
  - empty `tree_conns` or `t_state != TREE_CONNECTED` gives `-ENOENT`.
- **Potentially unsafe usage**: taking the request or response with
  `smb_get_msg()`.
  - Unsafe: in a handler that runs with `work->next_smb2_rcv_hdr_off` set; it
    parses the first command and overwrites the first response.
  - Safe: in code that runs once before the loop, as `init_smb2_rsp_hdr()` and
    `smb2_allocate_rsp_buf()` do.
  - Safe: after a test of `work->next_smb2_rcv_hdr_off`, as `__wbuf()` behind
    `WORK_BUFFERS()` does.
- **Potentially unsafe usage**: passing the request's `VolatileFileId` to a
  lookup in a handler that may be a later command.
  - Unsafe: with `ksmbd_lookup_fd_fast()`, which does no substitution; the
    placeholder id finds nothing.
  - Safe: with `ksmbd_lookup_fd_slow()`, which substitutes `compound_fid` and
    `compound_pfid` when `has_file_id()` is false.
  - Safe: after substituting by hand, as `smb2_ioctl()` does before its
    `ksmbd_lookup_fd_fast()` calls.

**Client-supplied offsets and lengths**

- Bound for a field the message check did not cover: the current command's
  length from `smb2_current_req_len()`, compared as `off > len ||
  cnt > len - off`; see the channel info test in `smb2_read()`.
- `smb2_find_context_vals()` guarantees that name and data lie inside the
  context, not that the data is large enough for the caller's struct; callers
  compare `DataOffset + DataLength` with the struct size, as
  `smb2_create_sd_buffer()` does.
- `smb2_set_ea()` entry size: `sizeof(struct smb2_ea_info) + EaNameLength + 1
  + EaValueLength`; the 1 is the name terminator.
- `LockCount`: bounded against the request by `ksmbd_smb2_check_message()`,
  for which `smb2_get_data_area_len()` makes the lock array the data area, not
  by `smb2_lock()`, which only rejects 0 and values above 64.
- `parse_sec_desc()` returning 0 does not mean the offsets were checked: it
  returns 0 before validating them when `DACL_PRESENT` is clear in `type`.
- **Unsafe usage**: calling `smb2_set_ea()` with a `buf_len` that was not
  compared with `sizeof(struct smb2_ea_info)`; it reads `EaNameLength` of the
  first entry before any size test.
  - Safe: check first, as `smb2_set_info_file()` and the `ea_buf` path of
    `smb2_open()` do.
- **Unsafe usage**: testing the result of `smb2_find_context_vals()` for NULL
  only; a malformed list returns `ERR_PTR(-EINVAL)`.
  - Safe: test both `IS_ERR()` and NULL, in either order, as
    `parse_lease_state()` and `smb2_create_sd_buffer()` do.
- **Potentially unsafe usage**: reading a field of the request body in code
  that runs before `ksmbd_verify_smb_message()`, such as
  `check_user_session` or `allocate_rsp_buf`.
  - Unsafe: when nothing has compared the field's position with the received
    length; no size or layout check has run yet, and `NextCommand` of the
    current command is not yet validated either.
  - Safe: compare the field's position with `get_rfc1002_len()` of the
    request first, as `smb2_allocate_rsp_buf()` does before it reads
    `InfoType`.

## Connections and work items

**Connection lifetime**

- `ksmbd_conn_put()` in `fs/smb/server/connection.c`: NULL-safe; at zero it
  only queues `conn->release_work` on `ksmbd_conn_wq`, so it is callable from
  atomic context (`free_opinfo_rcu()`, `free_lease_table()` under
  `lease_list_lock` in `destroy_lease_table()`).
- Final free: `__ksmbd_conn_release_work()` on a `ksmbd-conn-release`
  workqueue worker; it does `ida_destroy(&conn->async_ida)`,
  `conn->transport->ops->free_transport()`, `kfree_sensitive(conn)`.
- `stop_sessions()`: the one other free site; it takes a temporary reference
  with an open-coded `atomic_inc()` and, if its `atomic_dec_and_test()` is the
  last put, does the same three steps inline.
- `ksmbd_conn_get()` holders (search for it): `struct oplock_info`,
  `struct lease_table`, `struct ksmbd_file` (`fp->conn`), `struct ksmbd_lock`
  (`smb_lock->conn`), oplock and lease break work items, and the parked
  CHANGE_NOTIFY work item (`work->owns_conn_ref`).
- `struct channel`: `chann->conn` is a raw pointer, no `refcnt` reference;
  `ksmbd_conn_sessions_cleanup()` deletes this connection's channels at
  teardown.
- `ksmbd_conn_free()`: frees `request_buf`, `preauth_info`, `mechToken`, the
  preauth sessions and `conn->sessions` unconditionally, then puts the initial
  reference; the transport and `async_ida` survive until the final free.
- After `ksmbd_conn_free()` a `refcnt` holder has only the memory, `async_ida`
  and the transport; `conn->um` and `conn->local_nls` were unloaded earlier by
  `ksmbd_conn_handler_loop()` and the conn is off `conn_list`.
- `r_count`: waited for on `r_count_q` by `ksmbd_conn_handler_loop()` only; it
  also covers the deferred notify-cancel completion (`smb2_notify_cancel_fn()`
  increments, `smb2_notify_cancel_deferred()` decrements).
- `req_running`: waited for on `req_running_q` by the receive-loop throttle and
  by `ksmbd_conn_wait_idle_sess()`; `ksmbd_conn_wait_idle()` has no caller.
- `ksmbd_conn_r_count_dec()`: `atomic_inc(&conn->refcnt)`, then the `r_count`
  decrement and `wake_up()`, then `ksmbd_conn_put()`.

**Connection teardown order**

| Step | Action in `ksmbd_conn_handler_loop()` | Needs first |
|---|---|---|
| 1 | `ksmbd_conn_set_releasing()` | receive loop left |
| 2 | `ksmbd_conn_cancel_async_requests()` | step 1; `ksmbd_conn_link_async_request()` refuses a link once it sees releasing |
| 3 | `wait_event(conn->r_count_q, ...)` for `r_count == 0` | step 2, which wakes handlers blocked in `smb2_lock()` |
| 4 | `utf8_unload()`, `unload_nls()` | step 3 |
| 5 | `default_conn_ops.terminate_fn()` | step 3 |
| 6 | `t->ops->disconnect()` | step 5 |
| 7 | `module_put(THIS_MODULE)` | step 6 |

- Step 2: sets every `KSMBD_WORK_ACTIVE` item on `conn->async_requests` to
  `KSMBD_WORK_CANCELLED` and calls its `cancel_fn`, if set, under
  `conn->request_lock`.
- Step 5 is `ksmbd_server_terminate_conn()`: `ksmbd_conn_sessions_cleanup()`
  then `destroy_lease_table()`. There is no ksmbd_sessions_deregister() here.
- `destroy_lease_table(conn)`: selects tables by `ClientGUID`, not by conn
  pointer, and puts each matching table's reference on `lb->conn`.
- Step 6: `ksmbd_tcp_disconnect()` and `smb_direct_disconnect()` shut the
  socket down and call `ksmbd_conn_free()`; neither releases the socket.
- Socket release: `sock_release()` in `ksmbd_tcp_free_transport()` and
  `smbdirect_socket_release()` in `smb_direct_free_transport()`, run by the
  final free after the last `ksmbd_conn_put()`.
- The final free can run after step 7; `ksmbd_server_exit()` covers it with
  `rcu_barrier()` followed by `ksmbd_conn_wq_destroy()`.
- `conn->request_lock`: orders status against async linking.
  `ksmbd_conn_link_async_request()` in `fs/smb/server/smb2pdu.c` tests
  exiting and releasing and links under it.
- Status writers that take `conn->request_lock`: `ksmbd_conn_abort()`,
  `stop_sessions()` and `ksmbd_all_conn_set_status()`; none overwrites
  `KSMBD_SESS_RELEASING`.
- `ksmbd_conn_set_releasing()` and the other setters in
  `fs/smb/server/connection.h`: plain `WRITE_ONCE()`. Step 1 holds no lock;
  the ordering comes from step 2 taking `conn->request_lock` after the store.

**Work item lifetime**

- `ksmbd_free_work_struct()` references dropped: `ksmbd_conn_put(work->conn)`
  only if `work->owns_conn_ref`; `ksmbd_fd_put()` on `work->request_open`
  (normally already cleared by `smb2_complete_request_open()`).
- `ksmbd_free_work_struct()` also frees `work->compress_buf`, and `work->iov`
  only when it is not `work->iov_inline`.
- `ksmbd_free_work_struct()` does not call `release_async_work()`: it unlinks
  the work from no list and does not free `cancel_argv`; it only releases a
  nonzero `async_id`.

| Kind | Allocated in | Freed in | Conn accounting |
|---|---|---|---|
| Client request | `queue_ksmbd_work()` | `handle_ksmbd_work()` | `req_running`, `r_count` |
| Oplock break | `smb2_oplock_break_noti()` | `__smb2_oplock_break_noti()` | `r_count` and a `refcnt` reference |
| Lease break | `smb2_lease_break_noti()` | `__smb2_lease_break_noti()` | `r_count` and a `refcnt` reference |
| Parked CHANGE_NOTIFY | `smb2_notify()` | see below | `refcnt` via `owns_conn_ref`; no counter while parked |
| Interim response | `smb2_send_interim_resp()`, `smb2_send_interim_prefix_work()` | same function | none; borrows `work->conn` |

- Break work: `smb2_oplock_break_conn_get()` or `smb2_lease_break_conn_get()`
  takes the `refcnt` reference and returns NULL when it finds no conn that is
  set and not releasing; for what the sender does then, see "Break
  notification route".
- Break worker exit order: `ksmbd_free_work_struct()`,
  `ksmbd_conn_r_count_dec()`, `ksmbd_conn_put()`; `owns_conn_ref` is not set,
  so the put is explicit.
- Parked CHANGE_NOTIFY work is freed by exactly one of: `__ksmbd_close_fd()`,
  `smb2_complete_notify_cancel()` (from `smb2_cancel()` or from
  `smb2_notify_cancel_deferred()`), or `smb2_notify_cancel_fn()` when its
  `GFP_ATOMIC` allocation fails.
- Owner of a parked work: whoever finds `work->notify_entry` non-empty under
  `fp->f_lock` and does `list_del_init()` on it.
- Deferred cancel: the only parked-work path that touches `r_count`;
  `smb2_notify_cancel_fn()` increments it and `smb2_notify_cancel_deferred()`
  calls `ksmbd_conn_r_count_dec()` after the free.

**Asynchronous requests and cancel**

- `setup_async_work()`: returns `-ESHUTDOWN`, with the id released and the
  work fields reset, when the connection is exiting or releasing; a failed id
  allocation returns that error.
- `oplock_break()` in `fs/smb/server/oplock.c`, for a non-NULL `in_work`:
  calls `setup_async_work()` with a NULL callback, sends `STATUS_PENDING`, and
  calls `release_async_work()` at once; the wait that follows cannot be
  cancelled by `AsyncId`.
- `smb2_read()` and `smb2_write()`: for the last command of a compound, they
  call `setup_async_work()` with a NULL callback and release before return;
  they never read `work->state`.
- `smb2_notify()`: does not block. It moves `async_id` to a new work item,
  links that with `ksmbd_conn_link_async_request()` and on
  `fp->notify_pendings`, and returns with `send_no_response` set.
- `work->state` is read only by `smb2_lock()`; a cancel that hits a request
  with no `cancel_fn` changes the state and has no further effect.
- `smb2_cancel()`, both branches: `cmpxchg()` from `KSMBD_WORK_ACTIVE` to
  `KSMBD_WORK_CANCELLED`; `cancel_fn`, if set, is called only when that
  succeeds, also in the `MessageId` branch.
- `smb2_cancel()` on a parked notify: compares `cancel_fn` with
  `smb2_notify_cancel_fn()`, calls `smb2_notify_cancel_claim()` instead, and
  sends `STATUS_CANCELLED` with `smb2_complete_notify_cancel()` after it drops
  `conn->request_lock`.
- `KSMBD_WORK_CLOSED` is also set without a close:
  `ksmbd_conn_wait_idle_sess()` calls `ksmbd_wake_session_blocked_works()`,
  which runs `set_close_state_blocked_works()` on every file of the session.
- `set_close_state_blocked_works()`: uses `xchg()`, so it overwrites
  `KSMBD_WORK_CANCELLED` with `KSMBD_WORK_CLOSED`; it calls `cancel_fn` only
  if the old state was `KSMBD_WORK_ACTIVE`.
- `ksmbd_conn_try_dequeue_request()`: calls `release_async_work()` for a work
  item that is still `asynchronous` when its handler returns.

**Cancel callback context**

| Caller | Thread | Spinlock held |
|---|---|---|
| `smb2_cancel()` | `ksmbd-io` worker of the CANCEL | `conn->request_lock` |
| `ksmbd_conn_cancel_async_requests()` | connection handler kthread | `conn->request_lock` |
| `set_close_state_blocked_works()` | thread that closes the file, or tears down its tree connect or session | `fp->f_lock`, inside a file-table `rwlock_t` |

- Each caller fires the callback only when it moves `work->state` out of
  `KSMBD_WORK_ACTIVE`, so a work item gets at most one call.
- `smb2_notify_cancel_fn()`: reached only from
  `ksmbd_conn_cancel_async_requests()`; `smb2_cancel()` does not call it.
- `cancel_argv`: must be NULL or come from `kmalloc()`;
  `release_async_work()` calls `kfree()` on it.
- **Unsafe usage**: a callback that sleeps or takes `conn->request_lock`, for
  example by calling `release_async_work()` or `ksmbd_conn_write()`.
  - Safe: wake the waiter only, as `smb2_remove_blocked_lock()` does with
    `ksmbd_vfs_posix_lock_unblock()` and `locks_wake_up()`.
  - Safe: defer the sleeping part with `GFP_ATOMIC` and `schedule_work()`,
    and hold `r_count` across it, as `smb2_notify_cancel_fn()` does.
- **Potentially unsafe usage**: a callback that takes `fp->f_lock`.
  - Unsafe: when the work is on `fp->blocked_works`;
    `set_close_state_blocked_works()` calls the callback with `fp->f_lock`
    held.
  - Safe: when the work is only on `fp->notify_pendings`, as in
    `smb2_notify_cancel_claim()`; its callers hold `conn->request_lock`, not
    `fp->f_lock`.
- **Unsafe usage**: linking a work item on `fp->blocked_works` with a NULL
  `cancel_fn`; `set_close_state_blocked_works()` calls it unchecked.
  - Safe: link only after `setup_async_work()` succeeded with a callback, as
    `smb2_lock()` does.
- **Unsafe usage**: freeing what `cancel_argv` points to while the work is
  still on `conn->async_requests` or `fp->blocked_works`.
  - Safe: unlink `work->fp_entry` under `fp->f_lock`, call
    `release_async_work()`, then free, as `smb2_lock()` does before
    `locks_free_lock()`.
- **Potentially unsafe usage**: a callback that frees the work item.
  - Unsafe: when a handler still runs on the work, as for a client request
    that `handle_ksmbd_work()` frees.
  - Safe: when the work is parked with no handler and the callback first
    claims it under `fp->f_lock` with `smb2_notify_cancel_claim()` and
    unlinks `async_request_entry` before the free, as
    `smb2_notify_cancel_fn()` does.

## Sessions and tree connects

**Session lifetime**

- `__session_create()` in `fs/smb/server/mgmt/user_session.c`: sets `refcnt`
  to 2 and itself adds the session to `sessions_table`.
- Table reference: one, shared by `sessions_table` and `conn->sessions`.
- Second reference: returned to `smb2_sess_setup()`, which stores it in
  `work->sess`; `smb2_sess_setup()` takes no extra get for a new session.
- There is no ksmbd_expire_session(), ksmbd_sessions_deregister() or
  SMB2_SESSION_TIMEOUT in this tree.
- `ksmbd_session_register()`: takes no reference; returns `-ENOSPC` when
  `ksmbd_too_many_session_setups()` counts `KSMBD_MAX_PENDING_SESSIONS`
  in-progress sessions on the connection.
- `ksmbd_session_register()` failure: unhashes the session and puts the table
  reference; the caller still owns its own reference.
- Paths that drop the table reference:

| Path | Condition | How |
|---|---|---|
| `ksmbd_session_register()` | its own failure | `ksmbd_user_session_put()` |
| `ksmbd_too_many_session_setups()` | `SMB2_SESSION_IN_PROGRESS`, `refcnt <= 1`, idle past `KSMBD_UNAUTHENTICATED_CONN_TIMEOUT` | `ksmbd_session_destroy()` directly |
| `ksmbd_session_unregister()` | session still hashed | `ksmbd_user_session_put()` |
| `ksmbd_conn_sessions_cleanup()` | this connection had a channel on the session or holds it in `conn->sessions`, and the channel list is empty once that channel is deleted | `atomic_dec_and_test()`, then destroy |

- `ksmbd_session_unregister()`: one caller, the failure path of
  `smb2_sess_setup()`; it also erases the session from `conn->sessions` of
  every channel connection.
- `ksmbd_expire_sessions()`: only changes `SMB2_SESSION_VALID` to
  `SMB2_SESSION_EXPIRED` once `sess->kerberos_expiry` has passed; drops no
  reference.
- `smb2_session_logoff()` and `destroy_previous_session()`: set
  `SMB2_SESSION_EXPIRED` and drop no reference; the session stays in both
  tables until one of the four paths above runs.
- `ksmbd_session_destroy()`: frees the tree connects, file table, `sess->user`,
  RPC handles, channel list and `Preauth_HashValue` along with the session.

**Session lookup functions**

- `ksmbd_session_lookup_all_states()` in
  `fs/smb/server/mgmt/user_session.c`: returns a session in any state with a
  reference taken.
- `ksmbd_session_lookup_all_states()` fallback: runs
  `ksmbd_session_lookup_slowpath()` whenever `ksmbd_session_lookup()` misses,
  and keeps the result only if `conn` is a key in `sess->ksmbd_chann_list`;
  `conn->binding` is not tested.
- `ksmbd_session_lookup_all()`: `ksmbd_session_lookup_all_states()` plus the
  `SMB2_SESSION_VALID` filter; it has no caller in this tree.
- Dispatcher: `smb2_check_user_session()` calls
  `ksmbd_session_lookup_all_states()` and filters the state itself.
- `smb2_check_user_session()` returns 0 before any lookup for
  `SMB2_NEGOTIATE_HE` and `SMB2_SESSION_SETUP_HE`; `SMB2_ECHO_HE` is not one
  of them.
- `SMB2_ECHO_HE` with a non-zero `SessionId`, as the first command: the
  session is looked up and kept if valid or Kerberos-expired; a miss is not an
  error.
- Kerberos-expired session (`smb2_session_kerberos_expired()`): the handler
  runs with `work->sess` not in `SMB2_SESSION_VALID` for the commands that
  `smb2_session_expired_cmd_allowed()` accepts; other commands that reach the
  state test get `-EKEYEXPIRED`.
- `smb2_check_user_session()` can return an error with `work->sess` still set:
  on `-EKEYEXPIRED`, and on `-ENOENT` for an encrypted request on an expired
  session with `sess->enc`; a later command of a compound keeps `work->sess`
  on every error.
- `smb3_decrypt_req()`: does no session lookup of its own.
- `ksmbd_get_encryption_key()` in `fs/smb/server/auth.c`: for decryption uses
  `ksmbd_session_lookup_all_states()` and accepts `SMB2_SESSION_VALID`, or
  `SMB2_SESSION_EXPIRED` with `sess->enc`; for encryption uses `work->sess`
  with no new reference.
- Re-authentication in `smb2_sess_setup()`: `ksmbd_session_lookup()`, then
  `ksmbd_session_lookup_slowpath()` accepted only if `lookup_chann_list()`
  finds this connection.

**Session setup paths**

- Binding flag: `SMB2_SESSION_REQ_FLAG_BINDING` in `fs/smb/common/smb2pdu.h`;
  there is no SMB2_SESSION_FLAG_BINDING.
- Zero `SessionId`: always takes the new-session branch, whatever the flags.
- Binding on `SMB311_PROT_ID`: `conn->cipher_type` must also equal the cipher
  of the connection in the first entry of `sess->ksmbd_chann_list`, else
  `-EINVAL`; the check sits between the dialect check and the
  `SMB2_FLAGS_SIGNED` check.
- Binding flag with a dialect below `SMB30_PROT_ID` and a non-zero
  `SessionId`: `-EACCES`.
- Binding flag on SMB3 without `KSMBD_GLOBAL_FLAG_SMB3_MULTICHANNEL`: handled
  by the re-authentication branch, not rejected with `-EACCES`.
- Re-authentication branch: has no `user_guest()` test; that test is in the
  binding branch only.
- Re-authentication of an `SMB2_SESSION_EXPIRED` session: `-EFAULT`, unless
  `sess->kerberos_expiry` is set and has passed; then
  `work->session_setup_reauth` is set and the state goes back to
  `SMB2_SESSION_IN_PROGRESS`.
- Same-user check on a valid session: done by `ksmbd_compare_user()` inside
  `ntlm_authenticate()` and `ksmbd_krb5_authenticate()`, after the branch
  checks; a mismatch returns `-EKEYREJECTED`.
- `SMB2_SESSION_VALID` and `ksmbd_conn_set_good()`: set by
  `smb2_sess_setup()` itself, after the authenticate function returns 0,
  unless `ksmbd_conn_need_reconnect()` is true.
- `register_session_channel()`: returns `-ESHUTDOWN` when `sess->tearing_down`
  is set and `-ENOSPC` at `KSMBD_MAX_CHANNELS`.
- Failure, non-binding session in `SMB2_SESSION_IN_PROGRESS`:
  `ksmbd_session_unregister()` removes it from the tables at once; the state
  is not changed.
- Failure, non-binding session not in progress: `sess->state` becomes
  `SMB2_SESSION_EXPIRED` and `sess->kerberos_expiry` 0; it stays in the tables.
- Failure, binding request: the failure path does not change the session
  state.
- Failure, `work->sess`: put and set to NULL, except for a binding request
  whose session is already in `work->sess`; that reference stays so the error
  response can be signed, and the dispatcher puts it.
- Failure, channels: the failure path does not call `ksmbd_chann_del()`; it is
  static in `fs/smb/server/mgmt/user_session.c` and called only by
  `ksmbd_conn_sessions_cleanup()`.
- Failure, `struct preauth_session`: removed only when the dialect is
  `SMB311_PROT_ID` and the request has the binding flag.
- Failure, connection state: changed only for a user with
  `KSMBD_USER_FLAG_DELAY_SESSION`; it is need-reconnect during the sleep and
  need-setup after it.
- `conn->mechToken`: freed on success too; `conn->binding` is reset to false
  on failure.

**Tree connect lifetime**

- `sess->tree_conns_lock`: a `struct rw_semaphore`, taken with `down_read()`
  and `down_write()`; holders may sleep.
- `ksmbd_tree_conn_connect()`: leaves `refcount` at 2, one for the xarray and
  one for `smb2_tree_connect()`, which puts it with
  `ksmbd_tree_connect_put()` before it returns.
- New tree connect: `t_state` is `TREE_NEW`; `smb2_tree_connect()` sets
  `TREE_CONNECTED` under the write lock, unless the state is already
  `TREE_DISCONNECTED`, so `ksmbd_tree_conn_lookup()` fails until then.
- Dispatcher reference: put by `__handle_ksmbd_work()` in
  `fs/smb/server/server.c` at `send:`, before the session put and before
  `ksmbd_conn_write()`; nothing is put when the work is freed.
- `smb2_tree_disconnect()` order:
  1. fail with `STATUS_NETWORK_NAME_DELETED` if `work->tcon` is NULL;
  2. `ksmbd_close_tree_conn_fds()`;
  3. `ksmbd_tree_conn_disconnect()`.
- `smb2_tree_disconnect()`: does not write `t_state` and does not clear
  `work->tcon`; the dispatcher's ordinary put drops its reference.
- `ksmbd_tree_conn_disconnect()` order:
  1. under one `down_write()`: return `-ENOENT` if `TREE_DISCONNECTED` or the
     xarray slot does not hold this tree connect, else set
     `TREE_DISCONNECTED` and `xa_erase()`;
  2. `ksmbd_ipc_tree_disconnect_request()`;
  3. `ksmbd_release_tree_conn_id()`;
  4. drop the xarray reference, freeing at zero.
- `ksmbd_tree_conn_disconnect()`: does not wait for other references and
  closes no files.
- `ksmbd_tree_connect_put()`: the final put does not release the tree id; the
  id is already released in step 3, while other references may remain.
- `ksmbd_tree_conn_session_logoff()`: holds the write lock across the whole
  loop, IPC request included.

**Using a session pointer**

- Dispatcher reference: put by `__handle_ksmbd_work()` in
  `fs/smb/server/server.c`, after `encrypt_resp` and before
  `ksmbd_conn_write()`; `work->sess` is not cleared afterwards.
- `ksmbd_free_work_struct()`: puts no session.
- `ksmbd_user_session_get()`: called only by the lookup functions and the
  procfs show functions; apart from the session tables, no object that
  outlives the request holds a session reference.
- `sess` in `struct oplock_info`: set by `alloc_opinfo()` with no reference;
  for where it is set to NULL and set again, see "Oplock object lifetime".
- `sess->user`: freed only by `ksmbd_session_destroy()`; a session reference
  keeps it alive.
- `smb2_sess_setup()`: assigns `work->sess` with no put of an earlier value;
  as the first command `work->sess` is NULL on entry, because
  `smb2_check_user_session()` does no lookup for `SMB2_SESSION_SETUP_HE`.
- **Unsafe usage**: putting `work->sess` in a handler and leaving the pointer
  set; `__handle_ksmbd_work()` puts it a second time.
  - Safe: put, then set `work->sess = NULL`, as the failure path of
    `smb2_sess_setup()` and `smb2_check_user_session()` do.
- **Potentially unsafe usage**: storing in `work->sess` a pointer that carries
  no reference.
  - Unsafe: on a work that reaches the put at `send:` in
    `__handle_ksmbd_work()`; the count drops below what the owners hold and
    `ksmbd_session_destroy()` runs early.
  - Safe: on a work that never passes through `__handle_ksmbd_work()`, cleared
    again while the lending work still holds its reference, as
    `smb2_send_interim_work()` does around `encrypt_resp`.
- **Unsafe usage**: using `work->sess` of a work that outlives its request;
  the dispatcher has put the reference and `ksmbd_session_destroy()` frees
  the session on the last put.
  - Safe: look the session up again by id and put it after use, as
    `smb2_send_notify_cancelled()` does with `ksmbd_session_lookup()`.
- **Potentially unsafe usage**: acting on a session from
  `ksmbd_session_lookup_slowpath()` for the current connection.
  - Unsafe: when nothing ties the session to the connection; the global table
    holds the sessions of every client.
  - Safe: after the connection is found in `sess->ksmbd_chann_list`, as the
    re-authentication branch of `smb2_sess_setup()` does with
    `lookup_chann_list()` and `ksmbd_session_lookup_all_states()` does with
    `xa_load()` under `sess->chann_lock`.

## Open files

**Open file handle lifetime**

- `ksmbd_open_fd()`: allocates only the volatile id, in
  `work->sess->file_table`.
- `ksmbd_open_durable_fd()`: allocates the persistent id in `global_ft`;
  `smb2_open()` calls it right after `ksmbd_open_fd()` and fails with
  `-ENOMEM` when `has_file_id(fp->persistent_id)` is false.
- Both idr entries share the one initial reference; registering in
  `global_ft` takes none.
- Initial reference while `FP_NEW`: belongs to the opener.
  `ksmbd_mark_fp_closed()` returns 1 for a handle that is not `FP_INITED`, so
  teardown drops only its own transient reference.
- `ksmbd_update_fstate()`: returns `int`. `FP_NEW` to `FP_INITED` fails with
  `-ENOENT` when the state is no longer `FP_NEW` or `volatile_id` was
  cleared; `smb2_open()` then puts the handle.
- `ksmbd_lookup_fd_fast()`: makes the same `fp->tcon == work->tcon` test
  (`__sanity_check()`) as `ksmbd_lookup_fd_slow()`.
- `ksmbd_lookup_foreign_fd()`: the session-table lookup with no tcon test.
- Paths that drop the table's reference, for example `ksmbd_close_fd()` and
  `__close_file_table_ids()`: remove the idr entry and set `volatile_id` to
  `KSMBD_NO_FID` under `ft->lock` first, so a later final close does no
  `idr_remove()` on the putter's table.
- `__put_fd_final()` with `fp->conn == NULL`: calls
  `__ksmbd_close_fd(NULL, fp)` and does not decrement `open_files_count`.
- `__put_fd_final()` otherwise: uses the putter's `work->sess->file_table`
  and `work->conn->stats.open_files_count`, not the opener's.
- `__ksmbd_close_fd()` with a NULL table: skips `__ksmbd_remove_fd()`, so it
  does not unlink `fp->node` from `m_fp_list`.
- `__ksmbd_remove_durable_fd()`: sets `fp->persistent_id` to `KSMBD_NO_FID`
  after `idr_remove()`.
- `set_close_state_blocked_works()`: not called from the final close; it runs
  earlier, for example from `ksmbd_close_fd()` and `ksmbd_mark_fp_closed()`.
- `__ksmbd_close_fd()`: drops the inode reference through
  `__ksmbd_inode_close()`, not `ksmbd_inode_put()`; closes the file with
  `fput()`.
- `__ksmbd_close_fd()` also: unlinks each `struct ksmbd_lock` from its
  connection and calls `ksmbd_vfs_posix_lock_unblock()`; sends and frees the
  works parked on `fp->notify_pendings`; puts `fp->conn`; frees
  `fp->owner.name`.
- Final close may sleep: it takes `m_lock`, and calls `ksmbd_conn_write()`
  for each work parked on `fp->notify_pendings`.

**Per-inode shared state**

- Key: the dentry pointer, `ci->m_de`; `__ksmbd_inode_lookup()` compares
  `ci->m_de == de`. There is no m_inode member.
- Sharing: opens through the same dentry, named streams of that file
  included; a hard link through another dentry gets its own object.
- `m_lock`: a `struct rw_semaphore`, so it sleeps.
- Nesting: `m_lock` is taken outside the table rwlocks, for example in
  `ksmbd_close_disconnected_durable_delete_on_close()` (`global_ft.lock`) and
  `ksmbd_close_fd_app_instance_id()` (`ft->lock`).
- `m_flags`: every access in `fs/smb/server/vfs_cache.c` after
  `ksmbd_inode_init()` is under `m_lock`.
- Delete-pending on a stream handle: recorded per handle in
  `fp->stream_del_pending` under `fp->f_lock`, not in `m_flags`.
- `ksmbd_fd_set_delete_pending()` and `ksmbd_fd_clear_delete_pending()`:
  what `set_file_disposition_info()` calls; they pick the per-handle flag for
  a stream and `S_DEL_PENDING` otherwise.
- `ksmbd_inode_pending_delete()`: true for `S_DEL_PENDING`; for a stream
  handle also true for `fp->stream_del_pending`.
- `ksmbd_query_inode_status()`: reports
  `KSMBD_INODE_STATUS_PENDING_DELETE` for `S_DEL_PENDING` only.
- `ksmbd_fd_set_delete_on_close()`: tests only `ksmbd_stream_fd()`; the
  `file_info` argument is unused; `smb2_open()` tests
  `FILE_DELETE_ON_CLOSE_LE`.
- `__ksmbd_inode_close()` on a stream handle: removes the xattr named
  `fp->stream.name` when `S_DEL_ON_CLS_STREAM` or `fp->stream_del_pending`
  is set.
- `__ksmbd_inode_close()` on every close: turns `S_DEL_ON_CLS` into
  `S_DEL_PENDING` before it drops `m_count`.
- After that first close: `ksmbd_inode_pending_delete()` is true for the
  remaining handles, and `smb2_open()` fails a new open with `-EBUSY`.
- Unlink: `__ksmbd_inode_close()` calls `ksmbd_vfs_unlink()` when `m_count`
  reaches zero and `S_DEL_PENDING` is set.
- `ksmbd_inode_put()`: on the last reference frees the object without
  testing `m_flags`; only `__ksmbd_inode_close()` calls `ksmbd_vfs_unlink()`.

**Using a file handle**

- `smb2_set_request_open()`: takes a second reference with
  `ksmbd_file_get()` and stores it in `work->request_open`.
- `work->request_open`: put by `smb2_complete_request_open()`, which
  `__handle_ksmbd_work()` calls after each command, and by
  `ksmbd_free_work_struct()`; the handler does not put it.
- Handler after `smb2_set_request_open()`: still puts its own lookup
  reference, on the failure return too, as `smb2_set_info()` does.
- `ksmbd_fp_get()`: static in `fs/smb/server/vfs_cache.c`; code outside
  uses `ksmbd_file_get()`.
- `ksmbd_vfs_fsync()`: holds the lookup and the put for `smb2_flush()`.
- Put used after a lookup, by example:

| Lookup | Put | Example |
|---|---|---|
| `ksmbd_lookup_fd_fast()`, `ksmbd_lookup_fd_slow()` | `ksmbd_fd_put()` | `smb2_close()`, `smb2_set_info()` |
| `ksmbd_lookup_fd_inode()` | `ksmbd_fd_put()` | `ksmbd_vfs_check_rename_share()` |
| `ksmbd_lookup_global_fd()` | `ksmbd_fd_put()` | `__smb2_oplock_break_noti()` |
| `ksmbd_lookup_durable_fd()` | `ksmbd_put_durable_fd()` | `parse_durable_handle_context()` |

- `ksmbd_fd_put()` on a handle of another session: the final close skips
  `idr_remove()` on the caller's table only when `volatile_id` is already
  `KSMBD_NO_FID`; the paths that drop the table's reference set that first
  (see "Open file handle lifetime").
- **Potentially unsafe usage**: a final close that passes a NULL table to
  `__ksmbd_close_fd()`, as `ksmbd_put_durable_fd()` does on the last
  reference.
  - Unsafe: while `fp->node` is still linked on `m_fp_list`; the NULL table
    skips `__ksmbd_remove_fd()` and the handle is freed while linked.
  - Safe: after `list_del_init(&fp->node)` under
    `down_write(&fp->f_ci->m_lock)`, as `ksmbd_scavenger_dispose_dh()` and
    `__close_file_table_ids()` do.
- `m_fp_list` walk: `m_lock` is an rwsem; walk under `down_read()`, as
  `ksmbd_smb_check_shared_mode()` does.
- Entries on `m_fp_list` include `FP_NEW` handles: `smb2_open()` links the
  handle before `ksmbd_update_fstate()` sets `FP_INITED`.
- Entries on `m_fp_list` include preserved durable handles with `conn` and
  `tcon` NULL: `__close_file_table_ids()` does not unlink a handle that
  `session_fd_check()` preserved.
- `ksmbd_has_other_active_fd()`: shows the tests a walker makes on such
  entries, `f_state == FP_INITED` and `READ_ONCE()` of `conn` and `tcon`.

**File handle back pointers**

- `fp->conn`: a counted reference. `ksmbd_open_fd()` and
  `ksmbd_reopen_durable_fd()` store `ksmbd_conn_get(work->conn)`.
- `fp->tcon`: a plain pointer; both functions store `work->tcon` and take
  no reference.

| Event | Function | `conn` / `tcon` |
|---|---|---|
| handle preserved at session teardown | `session_fd_check()` | NULL / NULL, then `ksmbd_conn_put()` |
| reconnect gets no volatile id | `ksmbd_reopen_durable_fd()` | NULL / NULL, then `ksmbd_conn_put()` |
| final close | `__ksmbd_close_fd()` | `ksmbd_conn_put()`, NULL / unchanged |

- `session_fd_check()`: reached only from `ksmbd_close_session_fds()` and
  `ksmbd_destroy_file_table()`.
- `ksmbd_close_tree_conn_fds()`: uses `tree_conn_fd_check()`; it closes the
  handles of the tree and preserves none.
- `session_fd_check()` stores: plain stores with no lock held; they run
  after `__close_file_table_ids()` removed the id from the session idr.
- `smb2_session_logoff()` and `destroy_previous_session()`: call
  `ksmbd_conn_wait_idle_sess()` first and abandon the teardown if it fails.
- `ksmbd_reopen_durable_fd()`: tests both members for NULL and stores them
  under `write_lock(&global_ft.lock)`, before it publishes the volatile id.
- `ksmbd_reopen_durable_fd()`: accepts `fp->is_durable` or
  `fp->is_persistent`.
- `fp->conn == NULL`: the marker for a disconnected handle; for example
  `ksmbd_lookup_durable_fd()`, `ksmbd_durable_scavenger()` and
  `__put_fd_final()` test it.
- `fp->conn` against `work->conn`: no lookup helper compares them; a session
  bound to several connections shares one `file_table`.
- `fp->tcon` after `ksmbd_lookup_foreign_fd()`: not compared with
  `work->tcon`.
- **Potentially unsafe usage**: dereferencing `fp->conn` or `fp->tcon`.
  - Unsafe: on a handle reached through `m_fp_list` or `global_ft` while
    other references to it can exist; a preserved durable handle has both
    NULL, and nothing in the handle pins the tcon.
  - Safe: in a handler, on a handle from `ksmbd_lookup_fd_slow()` or
    `ksmbd_lookup_fd_fast()`, as `smb2_set_info_sec()` does;
    `__sanity_check()` matched `fp->tcon` to `work->tcon`, which the work
    pins, and the handle pins `fp->conn`.
  - Safe: `fp->conn` after a NULL test, by the caller whose put brought
    `refcount` to zero, as `ksmbd_close_fd_app_instance_id()` does;
    `ksmbd_fp_get()` and `__close_file_table_ids()` take no reference at
    zero, so `session_fd_check()` cannot run on the handle.
  - Safe: a NULL test with `READ_ONCE()` and no dereference under `m_lock`,
    as `ksmbd_has_other_active_fd()` does.

## Names and credentials

**Confining names to the share**

- Three places resolve a client name to the path that is used, all in
  `fs/smb/server/vfs.c`: `ksmbd_vfs_path_lookup()`,
  `ksmbd_vfs_kern_path_create()` and `ksmbd_vfs_rename()`. For a non-empty
  name each calls `vfs_path_parent_lookup()` with `&share_conf->vfs_path` as
  root and ORs in `LOOKUP_BENEATH`.
- `ksmbd_vfs_kern_path_create()`: confined on its own; it needs no earlier
  confined lookup. There is no convert_to_unix_name() and no
  kern_path_create() in this tree.
- Caller flags on create: passed to the parent walk unchanged, so
  `LOOKUP_NO_SYMLINKS` applies there too.
- `LOOKUP_NO_SYMLINKS`: supplied by the caller of `ksmbd_vfs_kern_path()` and
  `ksmbd_vfs_kern_path_create()`, never added by them; `ksmbd_vfs_rename()`
  sets it itself; `smb2_creat()` re-looks the new file up with flags 0.
- Empty name in `ksmbd_vfs_path_lookup()`: resolves `share_conf->path` with
  no root and without `LOOKUP_BENEATH`.
- Leading `/` in the name: not rejected; the walk starts at the share root
  and skips it.
- Last component: not walked by `vfs_path_parent_lookup()`.
  `ksmbd_vfs_path_lookup()` uses `lookup_noperm_unlocked()`, or
  `start_removing_noperm()` for removal; create uses
  `start_creating_noperm()`.
- Last component `.` or `..`: `vfs_path_parent_lookup()` returns `-EINVAL`,
  even when the result would stay inside the share.
- Symlink as last component: returned, not followed, no `-ELOOP`. The caller
  decides: `smb2_open()` returns `-EACCES` through `d_is_symlink()` when
  `FILE_DELETE_ON_CLOSE_LE` is not set; `ksmbd_vfs_rename()` does the same
  for the target.
- Mount point as last component: crossed by `follow_down()` only in the
  non-remove branch of `ksmbd_vfs_path_lookup()`, and only with
  `KSMBD_SHARE_FLAG_CROSSMNT`. The remove and create paths never cross it.
- `ksmbd_vfs_rename()` and `ksmbd_vfs_link()`: return `-EXDEV` when source
  and target are on different mounts.
- Caseless fallback in `__ksmbd_vfs_kern_path()`: runs only on `-ENOENT`. Its
  `vfs_path_lookup()` is rooted at the share but has no `LOOKUP_BENEATH`.
  It only finds the directory to list; the returned path always comes from
  the `retry` through `ksmbd_vfs_path_lookup()`.
- `KSMBD_SHARE_FLAG_CROSSMNT`: tested in one place,
  `ksmbd_vfs_path_lookup()`.
- `KSMBD_SHARE_FLAG_FOLLOW_SYMLINKS`: defined in
  `fs/smb/server/ksmbd_netlink.h` and named in the proc table in
  `fs/smb/server/mgmt/share_config.c`; no server code tests it.

**File name validation**

- `smb2_get_name()`: returns `-EINVAL` for an empty converted name and for a
  name that starts with `\`. It does not strip a leading separator, and a
  leading `/` passes.
- The leading-`\` test is in `smb2_get_name()`, so it applies to the rename
  and link names too, not only to `smb2_open()`.
- `ksmbd_validate_filename()`: does not reject `:` or `/`. Bytes with the
  high bit set always pass.
- `ksmbd_validate_filename()`: its only caller is `smb2_open()`. The rename
  and link paths of set-info do not call it.
- `ksmbd_share_veto_filename()`: called by `smb2_open()`, `smb2_rename()`
  and `__query_dir()`; `smb2_create_link()` does not call it.
- Confinement to the share does not depend on either check; it comes from the
  lookup (see "Confining names to the share").
- POSIX create context (`posix_ctxt`, needs `tcon->posix_extensions`):
  `smb2_open()` skips the `:` handling and `ksmbd_validate_filename()`. The
  veto check still runs.
- `:` without `KSMBD_SHARE_FLAG_STREAMS`: `smb2_open()` fails with `-EBADF`.
- Zero `NameLength` in `smb2_open()`: `smb2_get_name()` and every name check
  are skipped; the name is `""`.
- Bounds: `smb2_open()` passes `NameOffset` and `NameLength` to
  `smb2_get_name()` with no check of its own; it relies on
  `ksmbd_smb2_check_message()` in `fs/smb/server/smb2misc.c`.
- Set-info names: `set_rename_info()` and `smb2_create_link()` check
  `FileNameLength` against the buffer length before `smb2_get_name()`.
  `set_rename_info()` also rejects a zero length.

**Credential override and revert**

- `__ksmbd_override_fsids()` in `fs/smb/server/smb_common.c`: base is
  `prepare_kernel_cred(&init_task)`. It changes `fsuid`, `fsgid`, the
  supplementary groups and, for a non-root `fsuid`, `cap_effective`; nothing
  else.
- Return value: an `int`. The old credentials are kept in
  `work->saved_cred`, not handed to the caller.
- `ksmbd_override_fsids()`: dereferences `work->tcon->share_conf` and
  `work->sess->user`. Before the tree connect exists, pass the share to
  `__ksmbd_override_fsids()`, as `share_config_request()` does.
- A second mechanism exists for work on an open handle:
  `override_creds(fp->filp->f_cred)` with a local saved pointer.
  `smb2_set_info()` uses it, not `ksmbd_override_fsids()`. `f_cred` is what
  `dentry_open()` recorded under the override in `smb2_open()`.
- `ksmbd_vfs_remove_file()`, `ksmbd_vfs_link()` and `ksmbd_vfs_rename()`:
  each calls `ksmbd_override_fsids()` and `ksmbd_revert_fsids()` itself.
- **Unsafe usage**: calling `ksmbd_override_fsids()`, or one of the three
  helpers above, while `work->saved_cred` is set.
  - Safe: calling them under `override_creds(fp->filp->f_cred)` only, as
    `smb2_set_info()` does through `smb2_rename()`. The requirement is
    `WARN_ON(work->saved_cred)` in `__ksmbd_override_fsids()`, which then
    overwrites the field.
- Example handlers: `smb2_query_info()` and `smb2_query_dir()` in
  `fs/smb/server/smb2pdu.c`; each has one override site.
- `smb2_open()`: has three override sites. Label `err_out2` is below the
  `ksmbd_revert_fsids()` call, so it is correct only for a path that holds no
  override. `err_out` and `err_out1` are for paths that hold it.
- `ksmbd_free_work_struct()`: does `WARN_ON(work->saved_cred != NULL)`, which
  is where a missed revert shows up.
- Share writability: `test_tree_conn_flag()` with
  `KSMBD_TREE_CONN_FLAG_WRITABLE`. No server code tests
  `KSMBD_SHARE_FLAG_WRITEABLE` or `KSMBD_SHARE_FLAG_READONLY`.
- `smb_check_perm_dacl()`: `smb2_open()` calls it for an existing file
  without testing `KSMBD_SHARE_FLAG_ACL_XATTR`. It is skipped when
  `FILE_DELETE_ON_CLOSE_LE` is set.
- `inode_permission()` in `smb2_open()`: needed because the file is opened
  with `dentry_open()`, which makes no such check. For an existing file it is
  skipped when `daccess` holds only `FILE_READ_ATTRIBUTES_LE` and
  `FILE_READ_CONTROL_LE`, and when `daccess` still holds
  `FILE_MAXIMAL_ACCESS_LE` after `smb_check_perm_dacl()`.
- Delete permission: there is no ksmbd_vfs_may_delete() here. `smb2_open()`
  calls `inode_permission()` on the parent with `MAY_EXEC | MAY_WRITE`, only
  after the `inode_permission()` check on the file above ran, and only when
  `daccess` has `FILE_DELETE_LE` or `FILE_DELETE_ON_CLOSE_LE` is set.
- `fp->daccess` for read and write is tested at two levels with different
  masks: `smb2_read()` accepts `FILE_READ_DATA_LE` or
  `FILE_READ_ATTRIBUTES_LE`; `ksmbd_vfs_read()` then requires
  `FILE_READ_DATA_LE` or `FILE_EXECUTE_LE`. `smb2_write()` accepts
  `FILE_WRITE_DATA_LE` or `FILE_READ_ATTRIBUTES_LE`; `ksmbd_vfs_write()` then
  requires `FILE_WRITE_DATA_LE` or `FILE_APPEND_DATA_LE`.

## Oplocks and leases

**Oplock object lifetime**

- Free path: `opinfo_put()` -> `free_opinfo()` -> `call_rcu()` with
  `free_opinfo_rcu()` -> `__free_opinfo()`; there is no opinfo_free_rcu() and
  `kfree_rcu()` is not used.
- `__free_opinfo()`: runs in the RCU callback, so it drops the opinfo's
  references on `conn` and on the lease only after the grace period.
- `opinfo->o_lease`: a counted reference on a `struct lease` that other opens
  may share; `free_lease()` is only `lease_put()`, see "Lease objects and
  tables".
- `opinfo->conn`: counted, taken with `ksmbd_conn_get()` in `alloc_opinfo()`,
  dropped in `__free_opinfo()` or earlier by `session_fd_check()` in
  `fs/smb/server/vfs_cache.c`.
- `session_fd_check()`: under `down_write(&ci->m_lock)` it puts `conn` and sets
  `conn` and `sess` to NULL on every opinfo of the inode whose `conn` is the
  file's connection, not only on the file's own opinfo.
- `ksmbd_reopen_durable_fd()`: sets `conn` (new reference) and `sess` again,
  under the same write lock, for opinfos with NULL `conn` and `o_fp == fp`.
- `opinfo->sess`, `opinfo->o_fp`, `o_lease->ci`: plain pointers, no reference.
- `opinfo->o_fp`: set in `smb_grant_oplock()` just before `opinfo_add()`; an
  opinfo held by another task can outlive the file.
- `close_id_del_oplock()`: first calls `smb_lazy_parent_lease_break_close()`
  when `fp->reserve_lease_break` is set.
- `close_id_del_oplock()`: sets `op_state` to `OPLOCK_CLOSING` whatever the old
  state, under `opinfo->state_lock`, clears bit 0 of `pending_break` in the same
  section, then wakes `oplock_q`, `oplock_brk` (lease only) and the bit waiters.
- `close_id_del_oplock()`: zeroes `breaking_cnt` only for a lease that was in
  `OPLOCK_ACK_WAIT`.
- `close_id_del_oplock()`: drops the file's reference with a bare
  `atomic_dec()` and its own with `opinfo_put()`.
- `opinfo_del()`: for a lease calls `lease_del_open()`, which unlinks the
  opinfo from `lease->open_list` and takes the lease off the client table only
  when that list becomes empty.
- Wait queues in `struct oplock_info`: `oplock_q` and `oplock_brk`; there is no
  op_end_wq.

**Lease objects and tables**

- `struct lease`: shared and reference counted (`refcount`, `lease_get()`,
  `lease_put()` in `fs/smb/server/oplock.c`); `lease_put()` does `kfree()` at
  the last reference.
- `smb_grant_oplock()`: allocates a lease with `alloc_lease()`, then, when
  `same_client_has_lease()` returns an opinfo, puts the new lease and takes a
  reference on that opinfo's `o_lease` instead.
- An open keeps the lease from `alloc_lease()` when `same_client_has_lease()`
  finds no match, and also when the open jumps to `set_lev` before
  `same_client_has_lease()` runs, for example the first oplock on the inode
  or a stat open.
- Lease references: one per opinfo, dropped in `__free_opinfo()`; one for the
  table, taken in `lease_add_table()` and dropped in `lease_del_table()`.
- There is no copy_lease(); `lease->state` is the shared state, and
  `lease_update_oplock_levels()` writes the mapped level into every opinfo on
  `lease->open_list`.
- `lb->lease_list`: links `struct lease` through `lease->l_entry`, not opinfos.
- `lease->open_list`: links the opinfos through `opinfo->lease_entry`, under
  the spinlock `lease->lock`.
- `lease_list_lock`: an rwlock; it protects `lease_table_list`, each
  `lb->lease_list` and `lease->l_lb`.
- Writers of `lb->lease_list`: `add_lease_global_list()`, `lease_del_open()`
  and `destroy_lease_table()`, each under `write_lock(&lease_list_lock)`.
- Readers of `lb->lease_list`: `find_same_lease_key()` and
  `lookup_lease_in_table()` use plain `list_for_each_entry()` under
  `read_lock(&lease_list_lock)`; neither takes `rcu_read_lock()` or `lb_lock`.
- `lb->lb_lock`: taken only inside `lease_add_table()` and
  `lease_del_table()`, nested in the write lock.
- `struct lease_table`: holds a counted `conn`, the connection of the open that
  created the table; `free_lease_table()` puts it.
- `add_lease_global_list()`: receives a table preallocated by
  `alloc_lease_table()` and frees it when the client already has one, so
  nothing after `opinfo_add()` can fail.
- `destroy_lease_table()`: calls `lease_del_table()` on every lease of each
  matching table, which sets `l_lb` to NULL and drops the table's reference;
  opinfos stay on `lease->open_list`.
- There is no lb_add(), lease_add_list() or lease_del_list() in this tree.

**Break sequence**

- Wait primitive: `wait_for_break_ack()` uses
  `wait_event_interruptible_timeout()` on `opinfo->oplock_q`; there is no
  op_end_wq and no OPLOCK_WAIT_BREAK.
- State constants in `fs/smb/server/oplock.h`: `OPLOCK_STATE_NONE`,
  `OPLOCK_ACK_WAIT`, `OPLOCK_CLOSING`.
- Oplock holder: the wait is called from `smb2_oplock_break_noti()`, not from
  `oplock_break()` itself.
- Lease holder with write or handle caching: `oplock_break()` sets
  `OPLOCK_ACK_WAIT` but skips `wait_for_break_ack()` when `open_trunc` is set
  and the lease state is exactly `SMB2_LEASE_READ_CACHING_LE |
  SMB2_LEASE_HANDLE_CACHING_LE`.
- Lease break chain: after an acknowledged break `oplock_break()` jumps to
  `again` and sends a further break while the lease is still incompatible;
  each step has its own 35 second wait.
- Timeout with holder in `OPLOCK_CLOSING`: `wait_for_break_ack()` changes
  nothing and returns `false`.
- Timeout on a lease: `lease_update_oplock_levels()` lowers `level` to none on
  every open that shares the lease, not only on the one that was broken.
- After a timeout the caller of `wait_for_break_ack()` calls
  `ksmbd_invalidate_durable_fd()` in `fs/smb/server/vfs_cache.c`, which sets
  `durable_reconnect_disabled` on the holder's file and returns `-ENOENT` on
  every path.
- `oplock_break()` after a timeout: returns `-ENOENT`, not 0.
- `smb_grant_oplock()` on `-ENOENT`: goes to `set_lev`; the request is capped
  at `SMB2_OPLOCK_LEVEL_II` unless the holder was a durable open, which keeps
  the requested level.
- `smb_grant_oplock()` on `-EAGAIN` (oplock holder closed during the break):
  rechecks `ksmbd_smb_check_shared_mode()` and grants the requested level.
- Other callers of `oplock_break()`, for example
  `__smb_break_all_levII_oplock()`: ignore the return value.
- Late oplock acknowledgement: `smb20_oplock_break_ack()` answers a replayed
  request (`smb3_hdr_replay()`) in `OPLOCK_STATE_NONE` with the current level
  and success; a non-replay gets an error status.
- Late lease acknowledgement: `lookup_lease_in_table()` returns only an opinfo
  whose `op_state` is `OPLOCK_ACK_WAIT`, so `smb21_lease_break_ack()` answers
  `STATUS_UNSUCCESSFUL`.

**Break notification route**

- Oplock break connection: `smb2_oplock_break_conn_get()` reads `opinfo->conn`
  under `down_read(&ci->m_lock)` and takes its own `ksmbd_conn_get()`; the
  worker drops that reference with `ksmbd_conn_put()`.
- Lease break connection: `smb2_lease_break_conn_get()` uses `opinfo->conn`
  when it is set and not `ksmbd_conn_releasing()`.
- Version 2 lease fallback: otherwise `smb2_lease_break_conn_get()` uses
  `lease->l_lb->conn`, the connection held by the client's
  `struct lease_table`, read under `read_lock(&lease_list_lock)`.
- No usable connection: the sender returns `ksmbd_invalidate_durable_fd()` for
  `opinfo->fid`, sends nothing and does not call `wait_for_break_ack()`; it
  does not change the holder's `level` or `op_state`.
- `ksmbd_invalidate_durable_fd()` on a disconnected file (`fp->conn` NULL):
  also sets `durable_timeout` to 1 and wakes `dh_wq`, which marks the handle
  expired for `ksmbd_durable_scavenger()`.
- `opinfo_get_list()`: returns NULL when the first entry of `m_op_list` has a
  NULL or releasing `conn`, so `smb_grant_oplock()` then grants as if the
  inode had no holder.
- `smb2_lease_break_noti()` with `sync` true: sends inline even in
  `OPLOCK_ACK_WAIT`; only `smb_break_all_levII_oplock_rename()` passes true.
- `smb_break_all_levII_oplock_for_delete()`: sends no notification to level II
  oplock holders, it sets their `level` to `SMB2_OPLOCK_LEVEL_NONE` directly;
  lease holders still go through `oplock_break()`.
- `__smb2_oplock_break_noti()`: looks the file up with
  `ksmbd_lookup_global_fd()` from `br_info->fid` and sends nothing when it is
  gone.

**Using an oplock object**

- `opinfo_get_list()`: static in `fs/smb/server/oplock.c`, takes `ci`,
  `skip_fp` and `snapshot`, and looks only at the first entry of `m_op_list`.
- `m_op_list` walk with deferred break: see `__smb_break_all_levII_oplock()`
  and `smb_send_parent_lease_break_noti()`.
- `smb2_open()`: reads the level through `opinfo_get()`; there is no
  smb2_lease_break_ack(), the handler is `smb21_lease_break_ack()`.
- `opinfo->o_lease`: shared with other opens, so `state`, `new_state` and
  `epoch` can change under a held opinfo reference; test `is_lease` first.
- `o_lease->l_lb`: set to NULL by `lease_del_table()`; read it under
  `read_lock(&lease_list_lock)`, as `smb2_lease_break_conn_get()` does.
- **Potentially unsafe usage**: dereferencing `fp->f_opinfo` without
  `opinfo_get()`.
  - Unsafe: outside `rcu_read_lock()`, or after `rcu_read_unlock()`;
    `opinfo_put()` frees through `call_rcu()`.
  - Safe: inside `rcu_read_lock()` with `rcu_dereference()`, for fields of the
    opinfo and of `o_lease`, as `proc_show_files()` in
    `fs/smb/server/vfs_cache.c`; `__free_opinfo()` drops the lease reference
    only in the RCU callback.
  - Safe: `opinfo_get()` paired with `opinfo_put()`, as
    `smb20_oplock_break_ack()`.
- **Potentially unsafe usage**: dereferencing `opinfo->conn` or `opinfo->sess`
  with only an opinfo reference.
  - Unsafe: outside `ci->m_lock`, while `session_fd_check()` can run; it puts
    the connection and sets both pointers to NULL under
    `down_write(&ci->m_lock)`.
  - Safe: under `down_read(&ci->m_lock)`, test `conn` for NULL and
    `ksmbd_conn_releasing()`, and take `ksmbd_conn_get()` before unlocking, as
    `smb2_oplock_break_conn_get()`.
- **Potentially unsafe usage**: dereferencing `opinfo->o_fp`.
  - Unsafe: with only an opinfo reference and no `ci->m_lock`;
    `__ksmbd_close_fd()` frees the file after `close_id_del_oplock()`.
  - Safe: under `ci->m_lock` for an opinfo found on `m_op_list`, as
    `opinfo_get_list()`; `opinfo_del()` needs the write lock before the file is
    freed.
  - Safe: look the file up by `opinfo->fid` with `ksmbd_lookup_global_fd()`, as
    `__smb2_oplock_break_noti()`.
  - Safe: in the close path of that file, as `opinfo_del()`.
  - Safe: reach the inode through the `ci` argument of `oplock_break()`, which
    the caller pins.
- **Unsafe usage**: calling `oplock_break()` while holding `ci->m_lock`; it can
  sleep for the acknowledgement, the close that ends the wait needs the write
  lock in `opinfo_del()`, and `smb2_oplock_break_conn_get()` takes the read
  lock itself.
  - Safe: take references under the lock, queue them with
    `oplock_break_add()`, and break after `up_read()`, as
    `__smb_break_all_levII_oplock()`.
- **Potentially unsafe usage**: writing `opinfo->op_state`.
  - Unsafe: on an opinfo already on `m_op_list` or in `fp->f_opinfo`, without
    `opinfo->state_lock` or over `OPLOCK_CLOSING`; `close_id_del_oplock()`
    makes that state final.
  - Safe: under `state_lock`, write only when the state is not
    `OPLOCK_CLOSING`, as `oplock_break_set_ack_wait()` and
    `smb21_lease_break_ack()`.
  - Safe: the first store before the opinfo is published, as `alloc_opinfo()`.

## The user-space daemon

**Request and response over netlink**

- Handle source: there is no ksmbd_ida_alloc(); the non-RPC helpers that wait
  for a reply call `ksmbd_acquire_id(&ipc_ida)` and release with
  `ipc_msg_handle_free()` as soon as `ipc_msg_send_request()` returns.
- RPC handle: the pipe id, taken once by `ksmbd_session_rpc_open()` in
  `fs/smb/server/mgmt/user_session.c` through `ksmbd_ipc_id_alloc()` (same
  `ipc_ida`) and reused for every request on that pipe.
- Match key: `handle` plus `entry->type + 1 == type`, nothing else; there is no
  sequence number, so a late reply to a timed-out RPC request matches the next
  request waiting on the same pipe.
- `struct ipc_msg_table_entry`: has a `wait` waitqueue, no completion; the
  waiter uses `wait_event_interruptible_timeout()`.
- `ipc_msg_send()`: `genlmsg_unicast()` to `ksmbd_tools_pid` in `init_net`; no
  multicast.
- Daemon absent: `ipc_msg_send()` fails (`-EINVAL` when `ksmbd_tools_pid` is 0,
  or the `genlmsg_unicast()` error) and the caller gets NULL without waiting.
- Daemon slow: only an unanswered, successfully sent request waits
  `IPC_WAIT_TIMEOUT`.
- Wrong type for a matching handle: `handle_response()` logs with `pr_err()`,
  keeps walking the bucket, wakes nobody and returns 0; the waiter gets NULL at
  timeout.
- Unknown or late handle: `handle_response()` returns 0, not an error.
- `handle_response()` non-zero returns: `-EINVAL` when `sz` is under
  `sizeof(unsigned int)`, `-ENOMEM` when the copy cannot be allocated; neither
  wakes the waiter.
- NULL from `ksmbd_rpc_read()`, `ksmbd_rpc_write()` or `ksmbd_rpc_ioctl()` is
  not treated as failure: `smb2_read_pipe()` and `smb2_write_pipe()` in
  `fs/smb/server/smb2pdu.c` complete the request, and
  `fsctl_pipe_transceive()` returns 0 bytes.
- NULL elsewhere, for example: `ksmbd_tree_conn_connect()` sets `status.ret`
  to `-EINVAL` and `ksmbd_krb5_authenticate()` returns `-EINVAL`;
  `ksmbd_login_user()` returns NULL.
- Freeing credentials: `ksmbd_login_user()` in
  `fs/smb/server/mgmt/user_config.c` and `ksmbd_krb5_authenticate()` in
  `fs/smb/server/auth.c` free the login or SPNEGO response with
  `kvfree_sensitive()`; both free the login-ext response with `kvfree()`, and
  other callers use `kvfree()`.
- `handle` field: `struct ksmbd_tree_disconnect_request` and
  `struct ksmbd_logout_request` have none; every struct that takes part in a
  round trip starts with it.
- RAP: there is no RAP request helper; `KSMBD_RPC_RAP_METHOD` is a method flag
  carried in `struct ksmbd_rpc_command`.
- `__ipc_heartbeat()`: clears `ksmbd_tools_pid` only when
  `ksmbd_ipc_heartbeat_request()` returns an error; the heartbeat waits for no
  reply, and the timer runs only if `server_conf.ipc_timeout` is non-zero.

**Daemon response validation**

- `ipc_validate_msg()`: called only from `ipc_msg_send_request()`, after the
  wait; not from `handle_response()` or `handle_generic_event()`.
- Size rule: the computed size must equal `entry->msg_sz` exactly; a message
  that is merely large enough is rejected.
- Every case first rejects `entry->msg_sz` below the fixed struct size.

| Request type | Checked in `ipc_validate_msg()` |
|---|---|
| `KSMBD_EVENT_RPC_REQUEST` | size = struct + `payload_sz`, with `check_add_overflow()` |
| `KSMBD_EVENT_SPNEGO_AUTHEN_REQUEST` | size = struct + `session_key_len` + `spnego_blob_len`; plain add of two `__u16` |
| `KSMBD_EVENT_SHARE_CONFIG_REQUEST` | `share_name` has a NUL inside the array; `veto_list_sz <= payload_sz`; size = struct + `payload_sz` always, also for `payload_sz` 0, with `check_add_overflow()` |
| `KSMBD_EVENT_LOGIN_REQUEST_EXT` | non-zero `ngroups` must be in 1..`NGROUPS_MAX` and size = struct + `ngroups * sizeof(gid_t)` |
| `KSMBD_EVENT_LOGIN_REQUEST`, `KSMBD_EVENT_TREE_CONNECT_REQUEST` | no case; policy minimum only, trailing bytes accepted |

- Share config, extra rule: with `flags` not `KSMBD_SHARE_FLAG_INVALID` and
  `KSMBD_SHARE_FLAG_PIPE` clear, `payload_sz <= veto_list_sz` is rejected.
- Login-ext with `ngroups` 0: any length at or above the fixed struct passes.
- `ngroups`: bounded in `ipc_validate_msg()`, not in `ksmbd_alloc_user()`,
  which uses it unchecked for `kmemdup()`.
- NUL termination: `ipc_validate_msg()` checks one string only, `share_name`
  in `struct ksmbd_share_config_response`.
- `ksmbd_nl_policy` entries for `KSMBD_EVENT_RPC_RESPONSE` and
  `KSMBD_EVENT_SPNEGO_AUTHEN_RESPONSE`: empty, so netlink sets no minimum;
  `handle_response()` requires `sizeof(unsigned int)` before it reads the
  handle.
- Permission: no op sets `GENL_ADMIN_PERM`; the only check is
  `netlink_capable(skb, CAP_NET_ADMIN)` in `handle_generic_event()` and
  `handle_startup_event()`, compiled in by
  `CONFIG_SMB_SERVER_CHECK_CAP_NET_ADMIN` (default y in
  `fs/smb/server/Kconfig`).
- Sender identity: `handle_generic_event()` does not compare the sender's port
  id with `ksmbd_tools_pid`.
- `handle_generic_event()`: rejects `type > KSMBD_EVENT_MAX` (so
  `KSMBD_EVENT_MAX` itself is allowed) and a `KSMBD_GENL_VERSION` mismatch.
- `hash_sz`: left to the caller; `ksmbd_alloc_user()` rejects
  `hash_sz > sizeof(resp->hash)`, for the plain login response and for the
  `login_response` inside `struct ksmbd_spnego_authen_response`.
- **Potentially unsafe usage**: using a length field from a response as a copy
  length.
  - Unsafe: when the source array or the destination has a fixed size and
    nothing compares the field with it; `ipc_validate_msg()` ties only the
    fields in the table above to the message length.
  - Safe: `ksmbd_alloc_user()` compares `hash_sz` with `sizeof(resp->hash)`
    (`KSMBD_REQ_MAX_HASH_SZ`) before `memcpy()`.
  - Safe: `ksmbd_krb5_authenticate()` compares `session_key_len` with
    `sizeof(sess->sess_key)` (`CIFS_KEY_SIZE`) and `spnego_blob_len` with
    `*out_len` before copying.
  - Safe: `smb2_read_pipe()` sizes its destination from `payload_sz`, and
    `fsctl_pipe_transceive()` clamps the copy to `out_buf_len`, which
    `smb2_ioctl()` took from `smb2_calc_max_out_buf_len()`.

## SMB Direct

**Location of the RDMA transport**

- Protocol code: `fs/smb/smbdirect/`, not under `fs/smb/common/`; there is no
  fs/smb/common/smbdirect/ directory in this tree.
- File names carry no prefix, for example `accept.c` and `connection.c`.
- Headers: wire formats in `fs/smb/smbdirect/pdu.h`; `struct smbdirect_socket`
  in `fs/smb/smbdirect/socket.h`; internal prototypes in
  `fs/smb/smbdirect/internal.h`; there is no smbdirect_pdu.h or
  smbdirect_socket.h.
- Public API: `include/linux/smbdirect.h`; it defines
  `struct smbdirect_socket_parameters` and only forward-declares
  `struct smbdirect_socket`, so ksmbd and cifs hold a pointer and cannot reach
  its fields.
- `CONFIG_SMBDIRECT` in `fs/smb/smbdirect/Kconfig`: promptless tristate,
  selected by `CONFIG_SMB_SERVER_SMBDIRECT` and `CONFIG_CIFS_SMB_DIRECT`;
  builds the separate module `smbdirect.o`.
- Exports: all in namespace "SMBDIRECT" (`DEFAULT_SYMBOL_NAMESPACE` in
  `fs/smb/smbdirect/internal.h`); each user needs `MODULE_IMPORT_NS()`.
- Other user: `fs/smb/client/smbdirect.c`; the move is complete on both sides,
  neither `fs/smb/server/` nor `fs/smb/client/` calls an RDMA core function
  directly.
- `fs/smb/server/transport_rdma.c`: glue only; it has no RDMA CM handler, no
  completion handler, no credit or negotiate code and no work item.
- Listener in `transport_rdma.c`: a `struct smbdirect_socket` made by
  `smbdirect_socket_create_kern()`, then `smbdirect_socket_bind()` and
  `smbdirect_socket_listen()`; see `smb_direct_listen()`.
- Two listeners, `smb_direct_ib_listener` (port 445) and
  `smb_direct_iw_listener` (port 5445); each has a kthread,
  `smb_direct_listener_kthread_fn()`, that loops on `smbdirect_socket_accept()`.
- `struct smb_direct_transport`: holds a pointer `socket`, not an embedded
  socket.
- There is no ksmbd_rdma_destroy() here; `ksmbd_rdma_stop_listening()` tears
  both listeners down.

**First credit grant**

- Work items of an accepting socket other than `connect.work` and
  `disconnect_work`, all in `fs/smb/smbdirect/`:

| Work item | Real handler | Armed in | Posts receives or grants |
|---|---|---|---|
| `recv_io.posted.refill_work` | `smbdirect_connection_recv_io_refill_work()` | `smbdirect_connection_negotiation_done()` | posts receives, then queues `idle.immediate_work` |
| `idle.immediate_work` | `smbdirect_connection_send_immediate_work()` | `smbdirect_connection_negotiation_done()` | sends an empty message that carries the grant |
| `idle.timer_work` | `smbdirect_connection_idle_timer_work()` | `smbdirect_accept_connect_request()`, after `rdma_accept()` | neither; only queues `idle.immediate_work` |

- There is no smb_direct_post_recv_credits() in this tree.
- `smbdirect_connection_negotiation_done()`: runs from
  `smbdirect_accept_negotiate_send_done()`, the send completion of the
  negotiate response, and only when the completion succeeded and the response
  status was 0.
- Until then `recv_io.posted.refill_work` and `idle.immediate_work` are still
  disabled from `smbdirect_socket_init()`; every `queue_work()` on them is
  dropped.
- `smbdirect_accept_negotiate_finish()`: arms no work item; it posts the data
  receives by calling `smbdirect_connection_recv_io_refill()` directly, takes
  the grant from `smbdirect_connection_grant_recv_credits()` and posts the
  response.
- `idle.timer_work` runs during negotiation as the negotiate timeout; it cannot
  cause a grant, because its handler returns unless status is
  `SMBDIRECT_SOCKET_CONNECTED` and `idle.immediate_work` is still disabled.
- `smbdirect_connection_put_recv_io()`: queues `recv_io.posted.refill_work`
  unconditionally; during negotiation only the disabled state stops a refill.
- **Potentially unsafe usage**: arming `recv_io.posted.refill_work` or
  `idle.immediate_work` of an accepting socket with their real handlers.
  - Unsafe: before the negotiate response is sent;
    `smbdirect_accept_negotiate_recv_work()` calls
    `smbdirect_connection_put_recv_io()`, which would start a refill that
    queues `idle.immediate_work` ahead of the response.
  - Safe: in `smbdirect_connection_negotiation_done()`, reached from
    `smbdirect_accept_negotiate_send_done()` after the response completed.

**Time of the first grant**

- The negotiate response is posted from inside `smbdirect_socket_accept()`, not
  when the negotiate request arrives.
- `smbdirect_accept_negotiate_recv_work()`: for a socket with
  `sc->accept.listener` set it parses the request, moves the socket from
  `listen.pending` to `listen.ready`, wakes the listener and returns without
  sending.
- `smbdirect_listen_connect_request()` sets `accept.listener` on every socket
  it creates, and it is the only caller of
  `smbdirect_socket_create_accepting()`.
- `smbdirect_socket_accept()`: takes the socket off `listen.ready`, sets status
  to `SMBDIRECT_SOCKET_CONNECTED`, then calls
  `smbdirect_accept_negotiate_finish()` with status 0.
- When `smbdirect_socket_accept()` returns, the data receives and the response
  are posted, or cleanup is scheduled; the send completion may not have run
  yet.
- Before the application accepts, the peer holds no credits, so no data
  transfer message can be in the reassembly queue.
- Version mismatch: `smbdirect_accept_negotiate_recv_work()` calls
  `smbdirect_accept_negotiate_finish()` at once with `STATUS_NOT_SUPPORTED`;
  that response grants 0 credits and the socket is cleaned up after it is sent.
- Waiting in `listen.ready`: no local timer ends it;
  `smbdirect_accept_negotiate_recv_work()` sets `SMBDIRECT_KEEPALIVE_NONE`, and
  `smbdirect_connection_idle_timer_work()` then returns while status is not
  `SMBDIRECT_SOCKET_CONNECTED`.
- ksmbd: `smb_direct_listener_kthread_fn()` in
  `fs/smb/server/transport_rdma.c` calls `smbdirect_socket_accept()`; there is
  no smb_direct_prepare() and `struct ksmbd_transport_ops` has no prepare
  member.

**Work item initialisation**

- Work items of `struct smbdirect_socket`: five; there is no recovery work
  member in `mr_io`.
- Placeholder: `__smbdirect_socket_disabled_work()` in
  `fs/smb/smbdirect/socket.h`; how long an item keeps it differs:

| Work item | Keeps the placeholder until |
|---|---|
| `disconnect_work` | the end of `smbdirect_socket_init_new()` or `smbdirect_socket_init_accepting()`, which set `smbdirect_socket_cleanup_work()` |
| `idle.timer_work` | `smbdirect_accept_connect_request()` after `rdma_accept()`; in `fs/smb/smbdirect/connect.c` after `rdma_connect_locked()` |
| `connect.work` | the negotiate receive completion, `smbdirect_accept_negotiate_recv_done()` or `smbdirect_connect_negotiate_recv_done()` |
| `recv_io.posted.refill_work` | `smbdirect_connection_negotiation_done()` |
| `idle.immediate_work` | `smbdirect_connection_negotiation_done()` |

- Arming: a second `INIT_WORK()` or `INIT_DELAYED_WORK()` with the real
  handler; it resets `data` to `WORK_DATA_INIT()`, which clears the disable
  count. `fs/smb/smbdirect/` does not call `enable_work()`.
- Disable count: never balanced; teardown disables the same item in
  `__smbdirect_socket_schedule_cleanup()`, `smbdirect_socket_cleanup_work()`
  and `smbdirect_socket_destroy()`.
- `queue_work()` or `mod_delayed_work()` on a disabled item: the request is
  dropped and is not replayed when the item is armed later.
- Workqueue: there is no single queue field; `sc->workqueues` has one queue
  per role, for example `refill` and `cleanup`, all copied from the
  module-wide `smbdirect_globals` in `fs/smb/smbdirect/main.c`.
- `connect.work` handlers call `disable_work()` on themselves right after the
  `sc->first_error` test, so they run once.
- `__smbdirect_socket_schedule_cleanup()` and
  `smbdirect_socket_cleanup_work()`: use `disable_work()` and
  `disable_delayed_work()`, which do not wait; a handler may still be running
  when they return.
- `smbdirect_socket_destroy()`: uses `disable_work_sync()` and
  `disable_delayed_work_sync()` on every item, before the QP and the memory
  pools are destroyed.
- **Potentially unsafe usage**: calling `INIT_WORK()` on a socket work item
  after `smbdirect_socket_init()`.
  - Unsafe: when the item was armed before, or cleanup has already run;
    `__INIT_WORK_KEY()` in `include/linux/workqueue.h` rewrites `data` and
    `entry`, which undoes the `disable_work()` that
    `__smbdirect_socket_schedule_cleanup()` relies on.
  - Safe: the first arming of an item still disabled from
    `smbdirect_socket_init()`, after a test of `sc->first_error`, as
    `smbdirect_accept_negotiate_recv_done()` does under `sc->connect.lock`;
    `__smbdirect_socket_schedule_cleanup()` does not take that lock, and the
    handler `smbdirect_accept_negotiate_recv_work()` tests `sc->first_error`
    again.
- **Potentially unsafe usage**: calling `queue_work()` on a socket work item
  that may not be armed yet.
  - Unsafe: when the caller needs the handler to run;
    `clear_pending_if_disabled()` in `kernel/workqueue.c` drops the request.
  - Safe: when another path queues the item once it is armed;
    `smbdirect_accept_rdma_event_handler()` queues `connect.work` under
    `sc->connect.lock`, and `smbdirect_accept_negotiate_recv_done()` queues it
    itself when status is already `SMBDIRECT_SOCKET_NEGOTIATE_NEEDED`.
  - Safe: when the drop is wanted; `smbdirect_connection_recv_io_done()` calls
    `disable_work()` on `recv_io.posted.refill_work` before
    `smbdirect_connection_put_recv_io()` on its error path.

## Model gaps

### Other mistakes models make

- Models take `conn->session_lock` and `sessions_table_lock` to be rwlocks.
  Here they are `struct rw_semaphore`, as are `sess->chann_lock` and
  `sess->rpc_lock`; none may be taken in a cancel callback. `conn_list` is
  keyed by `conn->inet_hash` for TCP; SMB Direct connections are added with
  key 0. `inode_hash_lock` remains an rwlock.
- Models look for ksmbd_vfs_kern_path_locked(). There is no such function
  here; `ksmbd_vfs_kern_path_start_removing()` in `fs/smb/server/vfs.c` is
  the locked lookup.
- Models take the handler's lookup reference to be all a request holds on an
  open. Here `smb2_set_request_open()` also counts the request on the handle
  by channel sequence when its caller passes `verify_chseq` and the dialect
  is `SMB30_PROT_ID` or later; `smb2_complete_request_open()` undoes the
  count.
- Models expect an interim_entry member in `struct ksmbd_work`. There is no
  interim_entry here.
- Models take CHANGE_NOTIFY to be unimplemented or an ordinary blocking
  handler. Here `__ksmbd_close_fd()` completes a parked CHANGE_NOTIFY with
  `STATUS_NOTIFY_CLEANUP`.
- Models know no compression path. Here response compression is requested
  only by `smb2_read()`, which sets `work->compress_response`.
- Models know no per-share encryption check. Here `smb2_tree_connect()`
  refuses a share with `KSMBD_SHARE_FLAG_ENCRYPT_DATA` when
  `smb3_encryption_negotiated()` is false.
- Models know no session expiry timer. Here
  `ksmbd_session_expiration_worker()` in `fs/smb/server/connection.c` runs
  `ksmbd_expire_sessions()` and aborts idle connections older than
  `KSMBD_UNAUTHENTICATED_CONN_TIMEOUT` with no valid or expired session. The
  dispatcher maps `-EKEYEXPIRED` to `STATUS_NETWORK_SESSION_EXPIRED`.
- Models take logoff to only mark the session expired. Here
  `smb2_session_logoff()` and `destroy_previous_session()` first set
  `sess->tearing_down` under `sess->chann_lock` and set the bound
  connections to `KSMBD_SESS_NEED_RECONNECT` with
  `ksmbd_all_conn_set_status()`.
- Models take a durable reconnect to need only `fp->conn == NULL` and an
  unexpired timeout. Here `ksmbd_lookup_durable_fd()` also refuses
  `durable_reconnect_disabled`, and for a handle with an opinfo
  `smb2_check_durable_oplock()` compares the owner with
  `ksmbd_vfs_compare_durable_owner()`.
- Models do not say where file ids start. Here ids start at
  `KSMBD_START_FID`; see `fs/smb/server/vfs_cache.h`.
- Models take `smb2_lock()` to link each lock on `conn->lock_list` as it is
  granted. Here it publishes the batch on `conn->lock_list` and
  `fp->lock_list` only after the response is pinned.
- Models know no procfs interface. Here `fs/smb/server/proc.c` is built under
  `CONFIG_PROC_FS`; most show functions are outside it, beside their data,
  for example `proc_show_clients()` takes `conn_list_lock`,
  `show_proc_sessions()` takes `sessions_table_lock` and `proc_show_files()`
  takes `global_ft.lock`; `ksmbd_session_destroy()` removes the per-session
  entry.
