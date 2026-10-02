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
