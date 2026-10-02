- **Unsafe usage**: setting `hw_control_is_supported`, `hw_control_set` and
  `hw_control_get` while `hw_control_trigger` is NULL.
  - Unsafe: `supports_hw_control()` passes the NULL to `strcmp()` when the
    netdev trigger is activated on the LED.
  - Safe: set `hw_control_trigger` together with the three callbacks, as
    `of_phy_led()` does.
  - Safe: set `hw_control_trigger` with none of the three callbacks, as
    `drivers/leds/leds-cros_ec.c` does; `supports_hw_control()` returns false
    before the `strcmp()`.
- **Unsafe usage**: naming `"netdev"` with the three callbacks set and
  `hw_control_get_device` NULL.
  - Unsafe: `netdev_trig_activate()` and `validate_net_dev()` call it with no
    NULL test.
  - Safe: set it always, as `of_phy_led()` does even when the other callbacks
    are not set.
- **Unsafe usage**: `hw_control_get_device()` returning a device that is not
  the `dev` member of a `struct net_device`.
  - Unsafe: `validate_net_dev()` applies `to_net_dev()` to it, and
    `netdev_trig_activate()` uses its `dev_name()` as the interface name.
  - Safe: return `&ndev->dev`, or NULL when no netdev is attached, as
    `phy_led_hw_control_get_device()` does.
- **Potentially unsafe usage**: `hw_control_set()` with no check of its
  flags.
  - Unsafe: when it does not handle 0 or a flags value that
    `hw_control_is_supported()` would refuse; from activate,
    `set_baseline_state()` calls it with the flags from `hw_control_get()`,
    or 0 if that failed, with no support check.
  - Safe: validate the flags again in `hw_control_set()`, as
    `qca8k_cled_hw_control_set()` does with `qca8k_parse_netdev()`.
  - Safe: give every flags value a defined mode, as
    `igc_led_hw_control_set()` does; it starts from `IGC_LEDCTL_MODE_OFF` and
    tests only the bits it knows.
- `hw_control_set()` return value: discarded by `set_baseline_state()`, the
  only caller; only `hw_control_is_supported()` can refuse a mode.
- `hw_control_is_supported()` may change the hardware: for an LED with no
  software fallback it may switch the LED off before returning `-EOPNOTSUPP`;
  see `rtl8168_led_hw_control_is_supported()` and the header comment in
  `drivers/leds/trigger/ledtrig-netdev.c`.
- `hw_control_get()` error code: none is fixed; `netdev_trig_activate()` only
  tests for non-zero and then keeps mode 0 with `hw_control` true.
- Turning off: no call tells the driver to leave hardware control; the only
  signal is the brightness callback, which `led_trigger_set()` reaches with
  `LED_OFF` after `deactivate`.
- `netdev_trig_deactivate()` still reaches `hw_control_set()`:
  `unregister_netdevice_notifier()` replays `NETDEV_DOWN` (if the device is
  up) and `NETDEV_UNREGISTER` into `netdev_trig_notify()`, and
  `set_baseline_state()` passes the current mode while `hw_control` is true.
- Non-zero brightness must also leave hardware control: on software fallback
  `set_baseline_state()` may write the on value with no `LED_OFF` first. See
  `qca8k_led_brightness_set()` and `igc_led_brightness_set_blocking()`.
- LED with neither `brightness_set` nor `brightness_set_blocking`: the
  `led_set_brightness()` in `led_trigger_set()` reaches no driver code, so the
  LED keeps its last hardware mode after the trigger is removed.
- `blink_set`: not called by the netdev trigger's software path;
  `netdev_trig_work()` uses `led_blink_set_oneshot()`, and `led_blink_setup()`
  skips `blink_set` for one-shot blinks.
