- Models take `rtnl_lock` to be the only lock in the reset-work against close
  deadlock. `bnxt_lock_sp()` in `drivers/net/ethernet/broadcom/bnxt/bnxt.c`
  takes only `netdev_lock()` and clears `BNXT_STATE_IN_SP_TASK` before it
  takes the lock.
- Models take netdevice notifiers to run under `rtnl_lock` alone.
  `register_netdevice()` raises `NETDEV_REGISTER` under `netdev_lock_ops()`,
  `unregister_netdevice_many_notify()` raises `NETDEV_UNREGISTER` after
  `netdev_unlock_ops()`; the events with a stated rule are listed under
  "Notifiers and netdev instance lock" in
  `Documentation/networking/netdevices.rst`.
- Models take `dev_open()` and the other `dev_*()` wrappers in
  `net/core/dev_api.c` to be safe in any notifier handler. `dev_open()` and
  `dev_close()`, for example, call `netdev_lock_ops()`, so on an ops-locked
  device a handler for an event raised under the instance lock, such as
  `NETDEV_REGISTER`, that calls one on the device of the event takes
  `dev->lock` twice.
- Models take `xdp_set_features_flag()` to need no lock. It takes
  `netdev_lock()` itself; a caller that holds the instance lock uses
  `xdp_set_features_flag_locked()` in `net/core/xdp.c`, which also raises
  `NETDEV_XDP_FEAT_CHANGE` under that lock.
- Models take the body of a `u64_stats_fetch_begin()` loop to be forbidden
  to sleep. Usage note 5 in `include/linux/u64_stats_sync.h` allows readers
  to sleep or be preempted.
