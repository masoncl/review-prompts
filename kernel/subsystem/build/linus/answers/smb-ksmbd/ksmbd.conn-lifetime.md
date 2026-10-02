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
