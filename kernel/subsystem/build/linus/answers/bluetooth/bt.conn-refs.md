- Last `hci_conn_drop()` delay: `conn->disc_timeout` only for `ACL_LINK` or
  `LE_LINK` in `BT_CONNECTED`, doubled when `!conn->out`; 0 in every other
  state, `BT_CONNECT` included.
- `hci_conn_hold()`: cancels `disc_work` with `cancel_delayed_work()`; a
  `hci_conn_timeout()` already running is not stopped, and it reads `refcnt`
  once at entry.
- Last `hci_conn_drop()` after `hci_conn_del()`: queues nothing, since
  `disc_work` was disabled; it still dereferences the conn, so the caller
  needs a `hci_conn_get()` reference.
- Failed queueing: release with `hci_conn_put()`; see `hci_abort_conn()`,
  `hci_connect_le_sync()`, `hci_le_conn_update()`.
- `-EEXIST` from `hci_cmd_sync_queue_once()` or `hci_cmd_sync_run_once()`:
  also needs the `hci_conn_put()`, though the caller then returns 0.
- Successful queueing: the destroy callback owns the `hci_conn_put()`; it also
  runs with `-ECANCELED` when the entry is dequeued.
