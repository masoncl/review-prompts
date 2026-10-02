- `svc_reserve()` and `svc_xprt_release_slot()`: neither calls
  `svc_xprt_enqueue()` directly. Both call `svc_xprt_resource_released()`,
  which enqueues only if `XPT_DATA` or `XPT_DEFERRED` is set and `XPT_BUSY`
  is clear.
- Barriers: `smp_rmb()` at the top of `svc_xprt_ready()`, `smp_mb()` in
  `svc_xprt_resource_released()` between the counter update and the flags
  read, `smp_mb__before_atomic()` before the clear in
  `svc_xprt_received()`. `net/sunrpc/svc_xprt.c` has no `smp_wmb()`.
- `xpt_reserved`: read only by `svc_udp_has_wspace()`. For TCP and RDMA the
  reservation is kept but does not decide readiness.
- `svc_tcp_has_wspace()`: 1 for a listener, otherwise the inverse of
  `SOCK_NOSPACE` on the socket; it does no arithmetic on send space.
- `svc_rdma_has_wspace()`: 0 while any sender waits on `sc_send_wait` or
  `sc_sq_ticket_wait`.
- Request limit: module parameter `svc_rpc_per_connection_limit`, tested
  against `xpt_nr_rqsts` in `svc_xprt_slots_in_range()`; it is not a
  transport credit count.
- `svc_handle_xprt()` adds `sv_max_mesg` to `xpt_reserved` after
  `xpo_recvfrom` or `svc_deferred_recv()` has already cleared `XPT_BUSY`, so
  a second thread can pass the write-space test before the first
  reservation is counted.
- `svc_write_space()`: calls `svc_xprt_enqueue()` without setting a bit; the
  transport is queued only if one of the five ready bits is already set.
