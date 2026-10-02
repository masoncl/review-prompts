- Field classes in the comment on `lock` apply to every device, not only
  ops-locked ones: `reg_state`, `up`, `moving_ns`, `nd_net` of a registered
  or unregistering device are written under `netdev_lock()` whether or not
  the device is ops-locked.
- `netif_set_up()` in `net/core/dev.h`: takes `netdev_lock()` itself when the
  device is not ops-locked, so `up` is always written under both locks.
- "Ops protected" fields named by the comment: `cfg`, `cfg_pending`,
  `ethtool`, `hwprov`.
- `flags`, `mtu`, `features`: not in any class of the comment.
- Notifier events and the lock, as asserted by `netdev_debug_event()` in
  `net/core/lock_debug.c` (built with `CONFIG_DEBUG_NET`):

| Event | Instance lock |
|---|---|
| `NETDEV_XDP_FEAT_CHANGE` | held, every device |
| `NETDEV_REGISTER`, `NETDEV_UP`, `NETDEV_DOWN`, `NETDEV_GOING_DOWN`, `NETDEV_CHANGE`, `NETDEV_CHANGENAME` | held if ops-locked |
| `NETDEV_UNREGISTER` | no assertion; `net/core/dev.c` sends it without the lock |
| any other, for example `NETDEV_CHANGEMTU` | no assertion; `register_netdevice()` sends `NETDEV_POST_INIT` without the lock |

- `ndo_init`, `ndo_uninit`, `priv_destructor`: called without the instance
  lock, also on ops-locked devices; see `register_netdevice()`,
  `unregister_netdevice_many_notify()` and `netdev_run_todo()`.
- ethtool ops on an ops-locked device: the default handlers in
  `net/ethtool/netlink.c` and `__dev_ethtool()` call them under the instance
  lock, and take RTNL only if `ethtool_nl_msg_needs_rtnl()` /
  `ethtool_ioctl_needs_rtnl()` (driver's `op_needs_rtnl`) or
  `ethtool_cmd_changes_features()` says so.
- An ethtool op of an ops-locked driver that reaches `ASSERT_RTNL()` code,
  for example `__netdev_update_features()`, needs its bit set in
  `op_needs_rtnl`, for example `ETHTOOL_OP_NEEDS_RTNL_SCHANNELS`.
- Order between two devices: there is no upper-before-lower rule;
  `netdev_lock_cmp_fn()` accepts any order while RTNL is held.
- Queue leasing: the virtual device's lock is taken before the physical
  device's, without RTNL; see `netdev_nl_queue_create_doit()`.
