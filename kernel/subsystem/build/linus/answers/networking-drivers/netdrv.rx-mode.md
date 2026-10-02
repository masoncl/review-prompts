- `ndo_set_rx_mode_async` in `struct net_device_ops`: the sleeping variant;
  called from `netif_rx_mode_run()` in `net/core/dev_addr_lists.c` in process
  context, under `rtnl_lock` and `netdev_lock_ops()`, without
  `netif_addr_lock_bh()`.
- Its `uc` and `mc` arguments are snapshots of `dev->uc` and `dev->mc`.
- `__hw_addr_sync_dev()` may be run on the snapshots; the core copies the
  `sync_cnt` changes back with `__hw_addr_list_reconcile()`.
- Non-zero return: `netif_rx_mode_schedule_retry()` re-queues the update from a
  timer with doubling delay, at most `NETIF_RX_MODE_RETRY_MAX` times.
- Both callbacks set: only `ndo_set_rx_mode_async` is called.
- `__dev_set_rx_mode()` calls `ndo_set_rx_mode` inline only when the driver is
  not ops-locked and has neither `ndo_set_rx_mode_async` nor
  `ndo_change_rx_flags`; otherwise it only queues core work.
- Deferred `ndo_set_rx_mode`: `netif_rx_mode_run()` still takes
  `netif_addr_lock_bh()` around it, so it cannot sleep on any path.
- `rtnl_lock` around `ndo_set_rx_mode`: held when it runs from
  `netdev_work_proc()`; not guaranteed on the inline path.
- `netif_rx_mode_sync()`: runs a queued update inline, so the filter is
  programmed before the syscall returns; `dev_change_flags()`,
  `dev_set_promiscuity()` and `dev_set_allmulti()` call it, for example.
- `register_netdevice()`: issues `netdev_WARN()` when the driver is ops-locked
  and has `ndo_set_rx_mode` without `ndo_set_rx_mode_async`; registration
  still succeeds, and there is no other check on these callbacks.
- **Potentially unsafe usage**: walking `dev->uc` or `dev->mc`.
  - Unsafe: inside `ndo_set_rx_mode_async` without `netif_addr_lock_bh()`;
    `netif_rx_mode_run()` has dropped that lock and `dev_mc_add()` can change
    the list.
  - Safe: walking the `uc` and `mc` arguments, as `bnxt_set_rx_mode()` does;
    they are private copies made by `netif_addr_lists_snapshot()`.
  - Safe: under `netif_addr_lock_bh()`, as `fbnic_set_mac()` does; the list
    writers, for example `dev_mc_add()`, take the same lock.
