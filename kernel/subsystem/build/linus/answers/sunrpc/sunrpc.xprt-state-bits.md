- `XPRT_CONGESTED`: the slot table is full. Set only by `xprt_add_backlog()`,
  cleared by `xprt_wake_up_backlog()` when no waiter is left.
- `XPRT_CWND_WAIT`: the congestion window is full. Set from
  `__xprt_get_cong()`, but not when the head of `xmit_queue` already holds a
  credit; see `xprt_set_congestion_window_wait()`.
- `xprt_reserve_xprt_cong()`: takes no credit, it only tests
  `XPRT_CWND_WAIT`. The credit is taken by `xprt_request_get_cong()` in the
  send path, for example `xs_udp_send_request()` and
  `xprt_rdma_send_request()`, which return `-EBADSLT` when the window is full.
- `xprt_rdma_procs` never sets `XPRT_CONGESTED`: `xprt_rdma_alloc_slot()`
  queues with `xprt_add_backlog_noncongested()`, so
  `xprt_throttle_congested()` never diverts a reserver on that transport.
- The window is used only by ops tables that install
  `xprt_reserve_xprt_cong()`: `xs_udp_ops`, `xprt_rdma_procs` and
  `xprt_rdma_bc_procs`.
- `xprt_rdma_bc_procs` is a backchannel table that installs the congestion
  variants; `bc_tcp_ops` is the one that does not.
- `xs_tcp_ops` also serves TCP with TLS; it and `xs_local_ops` have no window.
- `XPRT_LOCKED` with `snd_task == NULL`: taken by `test_and_set_bit()` or
  `wait_on_bit_lock()` and released with `xprt_release_write(xprt, NULL)`; for
  example `xprt_autoclose()`, `rpc_sysfs_xprt_state_change()`,
  `rpc_xprt_offline()`, and `xs_tcp_tls_setup_socket()` on the lower transport.
- `xprt_destroy()`: takes `XPRT_LOCKED` and never releases it.
- `XPRT_SND_IS_COOKIE`: `snd_task` holds the connect worker's cookie, not a
  task; `xprt_schedule_autoclose_locked()` tests it before waking `snd_task`.
- `xprt_clear_locked()` with `XPRT_CLOSE_WAIT` set: leaves `XPRT_LOCKED` set
  and queues `task_cleanup`, so the lock passes to `xprt_autoclose()`.
- `XPRT_CLOSE_WAIT`: a close has been requested for any reason. Set by
  `xprt_schedule_autoclose_locked()` and by `xs_reset_transport()` when not on
  a worker; `xs_tcp_state_change()` only clears it.
- `XPRT_CLOSE_WAIT` set: `xprt_request_transmit()` returns `-ENOTCONN` and
  `xprt_connect()` does not start a connect.
- `XPRT_CLOSING` set: `xprt_conditional_disconnect()` does nothing, and
  `xprt_connect()` leaves the task asleep on `pending` without connecting.
