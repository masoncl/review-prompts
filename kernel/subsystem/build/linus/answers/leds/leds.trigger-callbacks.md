- Locks held around `led_trigger_set()`, besides `led_cdev->trigger_lock` for
  write:

| Path | Also held |
|---|---|
| trigger name written to sysfs `trigger` | `led_cdev->led_access`, `triggers_list_lock` (read) |
| `none` written to `trigger`; 0 written to `brightness`; `led_trigger_remove()` from `v4l2_flash_open()` or `v4l2_subdev_get_privacy_led()` | `led_cdev->led_access` |
| `led_trigger_set_default()` from `led_classdev_register_ext()` or from `default` written to `trigger` | `led_cdev->led_access`, `triggers_list_lock` (read); only `led_cdev->led_access` when `default_trigger` is `none` |
| `led_trigger_register()`, `led_trigger_unregister()` | `leds_list_lock` (read); `triggers_list_lock` is already released |
| `led_classdev_unregister()` | none |

- **Unsafe usage**: taking `led_cdev->led_access` in `activate` or
  `deactivate`.
  - Unsafe: `led_trigger_write()`, `brightness_store()` and
    `led_classdev_register_ext()` already hold it when the callback runs.
  - Safe: a lock owned by the trigger or the driver, as
    `omnia_hwtrig_activate()` takes `leds->lock`.
- Concurrency: every lock held is per LED or taken for read, so the callbacks
  of one trigger can run at the same time for two LEDs.
- State shared across LEDs needs its own protection, as `bl_trig_activate()`
  takes `ledtrig_backlight_list_mutex` and `ieee80211_assoc_led_activate()`
  uses an atomic counter.
- `led_cdev->trigger`: set before `activate` and still set during
  `deactivate`; `power_supply_led_trigger_activate()` and
  `ieee80211_assoc_led_deactivate()` rely on it.
- `deactivate` on the `err_add_groups` path of `led_trigger_set()`: runs right
  after a successful `activate`, with the LED still on `trig->led_cdevs`, and
  without the core's `cancel_work_sync()` and `led_stop_software_blink()`.
- Detach path: the core calls `led_set_brightness()` with `LED_OFF` after
  `deactivate` returns, so `deactivate` need not turn the LED off.
- There is no del_timer_sync() here; `timer_delete_sync()` and
  `timer_shutdown_sync()` do that job, and `heartbeat_trig_deactivate()` uses
  `timer_shutdown_sync()` before `kfree()`.
