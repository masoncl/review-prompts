- There is no dev_watchdog_down() here; `netdev_watchdog_down()` in
  `net/sched/sch_generic.c` does that, called from `dev_deactivate_many()`
  before `ndo_stop`.
- `dev_watchdog()`: holds `dev->tx_global_lock` for the whole scan and skips
  the device if `qdisc_tx_is_noop()`.
- `ndo_tx_timeout`: runs with `tx_global_lock` held and queues frozen by
  `netif_freeze_queues()`; no `_xmit_lock` is held during the call.
- `netdev_watchdog_down()`: uses `timer_delete()`, not a sync variant, under
  `netif_tx_lock_bh()`. A late `dev_watchdog()` can still run but finds noop
  qdiscs (and, on the close path, `netif_running()` false), so it does not
  call `ndo_tx_timeout`.
- `netif_tx_disable()`: takes `tx_global_lock` as well as each `_xmit_lock`,
  so it waits for a running `ndo_tx_timeout`.
- `netif_tx_stop_queue()`: stamps `trans_start`; a driver path that keeps
  queues stopped longer than `watchdog_timeo` while running, present and
  carrier-on gets `ndo_tx_timeout`.
- Netpoll transmit in `__netpoll_send_skb()`: `HARD_TX_TRYLOCK()` on one
  queue's `_xmit_lock`, then `netif_xmit_stopped()`; it does not take
  `tx_global_lock`.
- `netpoll_poll_disable()`: not exported, called only from `net/core/dev.c`;
  it blocks `netpoll_poll_dev()` and not netpoll transmit.
- On a driver's own reset or resize path `napi_disable()` is what keeps
  netpoll's poll out; `ndo_poll_controller` is not gated by NAPI state,
  `netpoll_poll_dev()` tests only `dev_lock`, `netif_running()` and
  `netif_local_xmit_active()` before it.
- **Unsafe usage**: calling `netif_tx_disable()` or `netif_tx_lock()` from
  `ndo_tx_timeout`; `dev_watchdog()` already holds `tx_global_lock`.
  - Safe: only schedule work from the callback, as `igb_tx_timeout()` does.
