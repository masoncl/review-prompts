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
