- `register_netdev()`: takes the lock with `rtnl_net_lock_killable()` and
  returns `-EINTR` without registering if the task is killed while waiting.
- `netdev->lock`: `register_netdevice()` and
  `unregister_netdevice_many_notify()` call `netdev_lock(dev)` for every
  device, ops-locked or not, to write `reg_state`; a caller that holds the
  instance lock deadlocks.
- `unregister_netdevice_queue_net()`: a form some `dellink` implementations
  use (for example `__geneve_dellink()`, and `veth_dellink()` for the peer);
  caller holds rtnl. It is an inline wrapper of
  `unregister_netdevice_queue()` unless `CONFIG_DEBUG_NET_SMALL_RTNL` is set.
- NAPI instances need not exist before registration; `__bnxt_open_nic()` adds
  them and `__bnxt_close_nic()` deletes them.
- `register_netdevice()`: `BUG_ON()` unless `reg_state` is
  `NETREG_UNINITIALIZED`, so an unregistered device cannot be registered
  again.
- `unregister_netdevice_many_notify()`: `WARN_ON(1)` and skips a device that
  is `NETREG_UNINITIALIZED`, `BUG_ON()` for any state but
  `NETREG_REGISTERED`; do not unregister after a failed registration.
- `register_netdevice()` fails or warns on incomplete ops; see its first
  checks. Easy to miss: an ops-locked device with `ndo_set_rx_mode` and no
  `ndo_set_rx_mode_async` gets a `netdev_WARN()`.
- `devm_register_netdev()`: attaches the unregister action to
  `ndev->dev.parent`, so `SET_NETDEV_DEV()` must come first.
