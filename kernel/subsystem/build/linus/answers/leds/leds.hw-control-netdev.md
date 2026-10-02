- `can_hw_control()` has two callers: `netdev_led_attr_store()` and the
  `NETDEV_UP` case of `netdev_trig_notify()`. The result is cached in
  `trigger_data->hw_control`; `set_baseline_state()` reads only the cache.
- `set_device_name()` and `interval_store()` do not call `can_hw_control()`:
  after a `device_name` write the cached value stands until the next mode
  write or `NETDEV_UP`.
- `netdev_trig_activate()` sets `hw_control = true` without calling
  `can_hw_control()`: when `supports_hw_control()` holds and
  `hw_control_get_device()` returns non-NULL, with no mode check.
- At the end of activate, `register_netdevice_notifier()` replays
  `NETDEV_REGISTER` (and `NETDEV_UP` if the device is up) into
  `netdev_trig_notify()`; that is where `hw_control_set()` is first called,
  with the mode read by `hw_control_get()` or 0 if that failed.
- `-EOPNOTSUPP` to user space: returned only by `netdev_led_attr_store()`,
  when `brightness_set` and `brightness_set_blocking` are both NULL and
  `can_hw_control()` returned false.
- On that `-EOPNOTSUPP` the new mode and `hw_control = false` stay stored;
  nothing is rolled back and `set_baseline_state()` is not called.
- `hw_control_set()` failure: `set_baseline_state()` discards the return
  value; the write still returns `size`.
- `hw_control_is_supported()` error other than `-EOPNOTSUPP`: `dev_warn()` and
  software fallback; the error does not reach user space.
- `interval_store()`: returns `-EINVAL` as its first test while `hw_control`
  is true; `blink_set` is not consulted.
