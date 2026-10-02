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
