- Lower half: holds only `LED_SUSPENDED` and `LED_UNREGISTERING`. Only
  `drivers/leds/led-class.c` writes them; drivers read them.
- Upper half (`LED_CORE_SUSPENDRESUME` to `LED_MULTI_COLOR`): not all
  driver-chosen. The core or an LED consumer writes these:

| Flag | Written by | Tested by |
|---|---|---|
| `LED_SYSFS_DISABLE` | `led_sysfs_disable()`, `led_sysfs_enable()`, called by LED consumers such as `drivers/video/backlight/led_bl.c` | only handlers that call `led_sysfs_is_disabled()` |
| `LED_INIT_DEFAULT_TRIGGER` | set by `led_match_default_trigger()`; cleared by `led_trigger_set()` when it removes a trigger, and by the activate of the timer, oneshot and pattern triggers | those three activates; `cht_wc_leds_blink_set()` |
| `LED_MULTI_COLOR` | `led_classdev_multicolor_register_ext()` | `led_mc_set_brightness()` logs once and returns; `led_mc_trigger_event()` skips the LED |
| `LED_RETAIN_AT_SHUTDOWN` | driver, or `led_classdev_register_ext()` from `retain-state-shutdown` | `led_classdev_unregister()` |

- `LED_SYSFS_DISABLE` scope: `brightness_store()`, `led_trigger_write()` and
  the three stores in `drivers/leds/led-class-flash.c` return `-EBUSY`; an
  attribute whose handler does not call `led_sysfs_is_disabled()` stays
  writable.
- `LED_BRIGHT_HW_CHANGED`: tested in `led_classdev_register_ext()` and again
  in `led_classdev_unregister()`.
  `led_classdev_notify_brightness_hw_changed()` tests
  `brightness_hw_changed_kn`, not the flag.
- Locks when `flags` is written after registration:

| Bit | Lock held |
|---|---|
| `LED_SUSPENDED`, `LED_UNREGISTERING` | none taken by the LED core |
| `LED_SYSFS_DISABLE` | `led_access`, by `lockdep_assert_held()` |
| `LED_INIT_DEFAULT_TRIGGER` | `trigger_lock` for write, taken by the callers of `led_match_default_trigger()` and `led_trigger_set()` |

- The locks differ per bit and every write is a plain `|=` or `&=` on the
  same `int`, so no lock excludes two writers of different bits.
