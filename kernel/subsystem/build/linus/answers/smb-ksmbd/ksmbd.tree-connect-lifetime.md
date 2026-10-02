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
