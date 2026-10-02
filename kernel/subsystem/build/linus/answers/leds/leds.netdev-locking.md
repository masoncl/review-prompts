- Order in `set_device_name()`: RTNL, then the netdev instance lock of the new
  device (`netdev_lock_ops()`), then `trigger_data->lock`.
- `netdev_lock_ops()` takes the instance lock only when
  `netdev_need_ops_lock()` is true; see `include/net/netdev_lock.h`.
- `get_device_state()` calls `netif_get_link_ksettings()`, not
  `__ethtool_get_link_ksettings()`; `netif_get_link_ksettings()` asserts
  `netdev_assert_locked_ops_compat()`: instance lock for an ops-locked device,
  RTNL otherwise.
- `__ethtool_get_link_ksettings()` takes `netdev_lock_ops()` itself, so it
  cannot replace that call: `set_device_name()` already holds the instance
  lock.
- `netdev_trig_notify()`: takes no instance lock; it relies on the caller.
  `netdev_debug_event()` in `net/core/lock_debug.c` shows which events are
  raised with it held.
- `netdev_trig_notify()` acts on six events: `NETDEV_UP`, `NETDEV_DOWN`,
  `NETDEV_CHANGE`, `NETDEV_REGISTER`, `NETDEV_UNREGISTER`,
  `NETDEV_CHANGENAME`.
- `netdev_led_attr_store()` and `interval_store()`: take neither RTNL nor
  `trigger_data->lock`; they only call `cancel_delayed_work_sync()` before
  writing `mode`, `hw_control` or `interval`.
- Hardware control callbacks run under RTNL and `trigger_data->lock` from the
  notifier and `set_device_name()`, and under neither from
  `netdev_led_attr_store()`.
- `netdev_trig_activate()` takes RTNL itself: always through
  `register_netdevice_notifier()`, and through `set_device_name()` when
  `supports_hw_control()` holds and `hw_control_get_device()` returns a
  device.
- `netdev_trig_deactivate()` takes RTNL through
  `unregister_netdevice_notifier()`.
- Every caller of `led_trigger_set()` can reach activate or deactivate, and
  so must run without RTNL when the netdev trigger is involved: for example
  `led_classdev_register_ext()` via `led_trigger_set_default()` when the
  default trigger is `"netdev"`, `led_classdev_unregister()`, and a write to
  the `trigger` attribute.
- Notifier replay: `register_netdevice_notifier()` takes RTNL and calls
  `netdev_trig_notify()` for existing devices while activate is still
  running; `call_netdevice_register_net_notifiers()` takes
  `netdev_lock_ops()` around each device.
