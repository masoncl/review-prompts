- `LED_INIT_DEFAULT_TRIGGER` set: only in `led_match_default_trigger()` in
  `drivers/leds/led-triggers.c`, when the trigger name equals
  `led_cdev->default_trigger` and `trigger_relevant()` passes.
- `led_classdev_register_ext()` does not set it itself, only through
  `led_trigger_set_default()`; the setter does not look at `led-pattern`.
- User space can cause it to be set: writing `default` to the sysfs `trigger`
  file makes `led_trigger_write()` call `led_trigger_set_default()`.
- Cleared in two places: by `timer_trig_activate()`, `oneshot_trig_activate()`
  and `pattern_trig_activate()` after their `pattern_init()`, and by the
  removal branch of `led_trigger_set()`.
- `led_trigger_set_default()` and `led_trigger_register()` do not clear it
  after the attach.
- Removal branch of `led_trigger_set()`: runs before the attach branch in the
  same call, so `activate` sees the flag only when the LED had no trigger
  attached.
- A default trigger whose `activate` does not clear the flag leaves it set
  for as long as that trigger stays attached.
- `cht_wc_leds_blink_set()` in `drivers/leds/leds-cht-wcove.c` relies on
  that: it reads the flag in `blink_set` to tell that the default trigger is
  still in use.
