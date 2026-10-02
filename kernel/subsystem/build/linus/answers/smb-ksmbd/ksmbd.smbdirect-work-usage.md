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
