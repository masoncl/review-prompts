- `nl80211_pre_doit()`: calls `rtnl_lock()` unconditionally, looks up the
  device, takes the wiphy mutex, then calls `rtnl_unlock()` unless
  `NL80211_FLAG_NEED_RTNL` is set.
- Wiphy mutex in `nl80211_pre_doit()`: taken whenever an rdev was looked up
  (`NL80211_FLAG_NEED_WIPHY`, `NL80211_FLAG_NEED_NETDEV` or
  `NL80211_FLAG_NEED_WDEV`) and `NL80211_FLAG_NO_WIPHY_MTX` is clear.
- `NL80211_FLAG_NO_WIPHY_MTX`: the handler takes the mutex itself before it
  calls the op, for example `nl80211_new_interface()`.
- `nl80211_del_interface()`: unlocks the wiphy mutex around `dev_close()`
  and relocks before `del_virtual_intf` is called.
- `rdev_` wrappers in `net/wireless/rdev-ops.h`: none asserts the wiphy
  mutex.
- `cfg80211_register_netdevice()` asserts the RTNL as well as the wiphy
  mutex, so it is usable only from ops documented to hold the RTNL
  (`add_virtual_intf`, `del_virtual_intf`, `change_virtual_intf`) or from
  code that took both locks itself.
- What decides the variant is whether the caller holds the wiphy mutex, not
  whether it is inside an op; `brcmf_net_attach()` picks by a `locked`
  argument.
- **Potentially unsafe usage**: `register_netdevice()` or
  `unregister_netdevice()` with the wiphy mutex held.
  - Unsafe: when the netdev has `ieee80211_ptr` set;
    `cfg80211_netdev_notifier_call()` takes the wiphy mutex on
    `NETDEV_REGISTER` when `wdev->registered` is false, and on
    `NETDEV_UNREGISTER` when it is true and `wdev->registering` is false;
    the caller deadlocks on its own mutex.
  - Safe: `cfg80211_register_netdevice()` and
    `cfg80211_unregister_netdevice()` with RTNL and wiphy mutex held, as
    `ieee80211_if_add()` does; the first sets `wdev->registered` and
    `wdev->registering`, the second clears `wdev->registered`, so the
    notifier skips the wdev. For unregistering, the netdev must already be
    closed: the notifier takes the mutex unconditionally on
    `NETDEV_GOING_DOWN` and `NETDEV_DOWN`.
  - Safe: a netdev with no `ieee80211_ptr`, as the monitor netdev that
    `wilc_wfi_init_mon_interface()` registers; the notifier returns at once
    when `dev->ieee80211_ptr` is NULL.
  - Safe: the plain functions with the wiphy mutex not held, as
    `brcmf_net_attach()` does with `register_netdev()`; the notifier then
    takes the mutex.
