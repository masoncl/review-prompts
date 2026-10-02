- Order in `led_classdev_unregister()` (`drivers/leds/led-class.c`):
  1. return if `IS_ERR_OR_NULL(led_cdev->dev)`
  2. with `CONFIG_LEDS_TRIGGERS`: `led_trigger_set(led_cdev, NULL)` under
     `trigger_lock`, if a trigger is attached
  3. set `LED_UNREGISTERING`
  4. `led_stop_software_blink()`
  5. `led_set_brightness(led_cdev, LED_OFF)` unless `LED_RETAIN_AT_SHUTDOWN`
  6. `flush_work(&led_cdev->set_brightness_work)`
  7. `led_remove_brightness_hw_changed()` if `LED_BRIGHT_HW_CHANGED`
  8. `device_unregister()`
  9. `list_del()` under `leds_list_lock`
  10. `mutex_destroy(&led_cdev->led_access)`
- `cancel_work_sync()`: called only inside `led_trigger_set()`; unregister
  itself uses `flush_work()`, so pending work runs instead of being dropped.
- `led_access`: never locked by `led_classdev_unregister()`.
- Step 2 with `LED_RETAIN_AT_SHUTDOWN`: `led_trigger_set()` still calls
  `led_set_brightness(led_cdev, LED_OFF)`, and does so before
  `LED_UNREGISTERING` is set.
- `brightness_set()`: called directly in the caller's context from steps 2
  and 5.
- `brightness_set_blocking()`: used only when `brightness_set` is NULL; runs
  from `set_brightness_work`, which step 6 waits for.
- `LED_SUSPENDED` set: the `LED_OFF` set calls in steps 2 and 5 update
  `led_cdev->brightness` only.
- Trigger `deactivate()`: is driver code when the driver registered a private
  trigger, for example `omnia_hwtrig_deactivate()` in
  `drivers/leds/leds-turris-omnia.c`, which takes the driver's mutex and
  writes to the chip.
- `pattern_clear()`: called by `pattern_trig_deactivate()`.
- `hw_control_set()`: its only caller is `set_baseline_state()` in
  `drivers/leds/trigger/ledtrig-netdev.c`. Step 2 can reach it, with the mode
  unchanged: `unregister_netdevice_notifier()` in `netdev_trig_deactivate()`
  replays `NETDEV_DOWN` and `NETDEV_UNREGISTER` into `netdev_trig_notify()`.
  Nothing calls it to end hardware control; that is left to the `LED_OFF`
  set call in step 2.
- `blink_set()`: `led_stop_software_blink()` does not call it; it runs only if
  `LED_SET_BLINK` is still pending when `set_brightness_delayed()` runs.
- sysfs handlers: nothing in `drivers/leds/led-class.c` tests
  `LED_UNREGISTERING`, so `brightness_store()` and `brightness_show()` can
  call the set callbacks and `brightness_get()` from other tasks until step 8.
- Failed registration, value of `led_cdev->dev` after
  `led_classdev_register_ext()` returns an error:

  | Failure | `led_cdev->dev` |
  |---|---|
  | name composition, name conflict | not written |
  | `devres_alloc()` in `devm_led_classdev_register_ext()` | not written |
  | `device_create_with_groups()` | `ERR_PTR` |
  | `led_add_brightness_hw_changed()` | NULL |

- Guard on a never-registered LED: works only if the structure was zeroed;
  `asus_wmi_led_exit()` in `drivers/platform/x86/asus-wmi.c` relies on it to
  unregister LEDs that may not exist.
- After a successful unregister: `led_cdev->dev` and `LED_UNREGISTERING` are
  both left set. The guard does not catch a second call, and a later
  registration of the same structure starts with `LED_UNREGISTERING` set.
