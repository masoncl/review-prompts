- `up`, `moving_ns`, `nd_net`, `xdp_features`: "double protected", not protected
  by `lock` alone; writers hold `rtnl_lock` and `lock`, readers hold either.
  `netif_set_up()` in `net/core/dev.h` takes `netdev_lock()` itself when the
  device is not ops-locked.
- Field classes: the comment on `lock` in `include/linux/netdevice.h` names
  four (simply, double, ops, double ops protected); a patch that touches a
  listed field is checked against its class.
- "Ops protected" fields (`cfg`, `cfg_pending`, `ethtool`, `hwprov`): under the
  instance lock on ops-locked devices, under `rtnl_lock` on all others;
  `netdev_assert_locked_ops_compat()` is the matching assertion.
- Several instance locks at once: `netdev_lock_cmp_fn()` in
  `include/net/netdev_lock.h`, installed per lock class by
  `netdev_lockdep_set_classes()`, permits it for two locks of that class only
  while `rtnl_lock` is held, in any order; there is no upper-before-lower rule.
- Queue leasing nests two instance locks in a fixed order: the virtual
  device's lock before the physical device's; see
  `netdev_nl_queue_create_doit()`.
- `Documentation/networking/netdevices.rst` per-callback entries say "if the
  driver implements queue management or shaper API"; the code tests
  `netdev_need_ops_lock()`, so `request_ops_lock` drivers are covered too.
- Ethtool callbacks are the exception to "instance lock in addition to
  `rtnl_lock`"; see "Ethtool callback locking".
