- `__LINK_STATE_START` writers: `__dev_open()` and `__dev_close_many()` in
  `net/core/dev.c` both call `ASSERT_RTNL()` unconditionally.
- `init_dummy_netdev()`: also sets `__LINK_STATE_START`, with no open call.
- `__dev_close_many()`: has no `synchronize_net()` of its own; it does
  `clear_bit()`, `smp_mb__after_atomic()`, then `dev_deactivate_many()`.
- `dev_deactivate_many()` in `net/sched/sch_generic.c`: calls
  `synchronize_net()` only if `dev_deactivate_queue()` found a qdisc with an
  `enqueue` op, then sleeps until `some_qdisc_is_busy()` is false.
- Before `ndo_stop`, the close path waits for netpoll (`netpoll_poll_disable()`
  takes `dev_lock`) and for the qdisc layer; it has no unconditional wait for
  a driver path that read `netif_running()` as true.
- **Potentially unsafe usage**: testing `netif_running()` without RTNL, then
  using what `ndo_stop` frees.
  - Unsafe: in a work item, timer or IRQ handler that `ndo_stop` has not
    stopped; the bit can clear and `ndo_stop` can run between test and use.
  - Safe: test and use under `rtnl_lock()`, as `bnx2_reset_task()` in
    `drivers/net/ethernet/broadcom/bnx2.c` does; both writers assert RTNL.
- `napi_schedule_prep()`: takes `NAPIF_STATE_SCHED` with a `try_cmpxchg()`
  loop; `napi_watchdog()` uses `test_and_set_bit()` and `__napi_busy_loop()`
  uses `cmpxchg()`, and neither sets `NAPIF_STATE_MISSED`.
- `napi_disable_locked()`: clears `NAPI_STATE_DISABLE` before it returns; the
  disabled state is `NAPIF_STATE_SCHED | NAPIF_STATE_NPSVC` left set.
- `netif_napi_add_weight_locked()`: sets `NAPI_STATE_SCHED` and
  `NAPI_STATE_NPSVC`, so a new NAPI starts in the disabled state.
- `napi_schedule_prep()` on a disabled NAPI: returns false and sets
  `NAPIF_STATE_MISSED`; the event is dropped, nothing is queued.
- `napi_enable_locked()` on a NAPI whose SCHED bit is clear: `BUG_ON()`.
- `__napi_poll()`: when the driver used its whole budget and
  `napi_disable_pending()`, it calls `napi_complete()` itself, so a poll that
  always uses its whole budget cannot starve `napi_disable_locked()`.
- `->poll()` is not called only by the SCHED owner: `poll_one_napi()` in
  `net/core/netpoll.c` calls `napi->poll(napi, 0)` after
  `test_and_set_bit(NAPI_STATE_NPSVC)`, without SCHED.
- `poll_owner` in `struct napi_struct` is what keeps netpoll and the other
  pollers apart: `poll_napi()` takes it by `cmpxchg()`; `napi_poll()`,
  `napi_threaded_poll_loop()` and `__napi_busy_loop()` take it with
  `netpoll_poll_lock()`.
- `netpoll_poll_lock()` in `include/linux/netpoll.h`: takes `poll_owner` only
  when `dev->npinfo` is set; returns `NULL` without `CONFIG_NETPOLL`.
