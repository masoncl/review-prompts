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
