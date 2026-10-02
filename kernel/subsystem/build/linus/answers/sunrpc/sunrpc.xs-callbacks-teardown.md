- Order in `xs_reset_transport()`: `sk_user_data` is set to NULL first, then
  `xs_restore_old_callbacks()` runs.
- Locks: `recv_mutex`, then `lock_sock()`; `sk_callback_lock` is not used
  anywhere in `net/sunrpc`.
- Release: `__fput_sync()` on `transport->file`, after both locks are dropped;
  not `sock_release()`.
- Context: the test is `PF_WQ_WORKER`. Otherwise it warns, sets
  `XPRT_CLOSE_WAIT` and returns with the socket still open.
- `xprt_destroy()`: queues `xprt_destroy_cb()` with `schedule_work()`, so
  `xs_destroy()` runs on a system worker and may cancel `recv_worker` and
  `error_worker` synchronously.
- `xs_destroy()`: cancels `connect_worker` before `xs_close()`, and
  `recv_worker` and `error_worker` after it.
- Socket callbacks: never call `xprt_force_disconnect()` themselves; they
  queue `error_worker`, and `xs_wake_disconnect()` calls it.
- `xs_tcp_ops` has `close = xs_tcp_shutdown()`: with `xprt->reuseport` set and
  the socket in `TCP_ESTABLISHED` or `TCP_CLOSE_WAIT` it only calls
  `kernel_sock_shutdown()`. `xs_reset_transport()` runs on a later autoclose,
  triggered by `TCP_CLOSE`.
- `xs_tcp_tls_finish_connecting()`: moves the socket to the upper transport
  without `xs_reset_transport()`. It repoints `sk_user_data` under
  `lock_sock()` and clears the lower transport's `sock`, `inet` and `file`
  under `recv_mutex`, so the lower transport's later close finds nothing.
- **Unsafe usage**: a socket callback that uses the result of
  `xprt_from_sock()` without a NULL check.
  - Safe: return when it is NULL, as `xs_error_report()` and
    `xs_tcp_state_change()` do; `xs_reset_transport()` clears `sk_user_data`
    while the RPC callbacks are still installed.
