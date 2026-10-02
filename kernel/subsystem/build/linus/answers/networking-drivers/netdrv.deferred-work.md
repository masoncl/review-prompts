- `netdev_work_sched(dev, events)` in `net/core/netdev_work.c`: ORs
  driver-defined bits into `dev->work_pending` and schedules one global work
  item; it does not sleep.
- `ndo_work(dev, events)`: called by `netdev_work_proc()` under `rtnl_lock`,
  plus the instance lock on ops-locked devices (`netdev_lock_ops()`); may
  sleep.
- Inside `ndo_work` the `netif_*` forms apply, as in `vlan_dev_work()` in
  `net/8021q/vlan_dev.c`.
- Events coalesce: bits scheduled several times before the work runs arrive
  in one call.
- Events are dropped, not retried, when `netif_device_present()` is false at
  run time; see `netdev_work_run()`.
- Events are ignored when the device is past `NETREG_REGISTERED`
  (`dev_isalive()`), and `unregister_netdevice_many_notify()` clears what is
  pending with `netdev_work_cancel_all()`.
- The core holds a reference on the device while work is queued
  (`work_tracker`).
- `netdev_work_cancel(dev, mask)`: clears pending bits and returns those that
  were pending, so the caller can run them inline; it gives no guarantee about
  a run already in progress, except that a caller that holds `rtnl_lock`, or
  the instance lock on an ops-locked device, cannot race with one.
  `vlan_dev_open()` and `vlan_dev_stop()` use it.
- The same work item runs the core's deferred rx-mode update; see "Address
  filter callback".
