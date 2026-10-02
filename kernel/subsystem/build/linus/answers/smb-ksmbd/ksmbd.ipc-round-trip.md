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
