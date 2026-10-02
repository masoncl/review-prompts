- `brightness` read: `brightness_show()` returns `-ENODATA` while the attached
  trigger has a non-NULL `trigger_type`; see `led_trigger_is_hw_controlled()`
  in `drivers/leds/led-class.c`.
- `brightness_store()`: has no such test; a write of 0 still removes the
  trigger.
- `led_trigger_is_hw_controlled()`: tests `trigger_type` only, not
  `hw_control_trigger` or the `hw_control_set` family of callbacks.
- PHY LEDs with the netdev trigger: not private triggers; that trigger has no
  `trigger_type`, so `brightness` reads as usual.
- Users of `struct led_hw_trigger_type`: search for the type name; for
  example `drivers/leds/leds-cros_ec.c` and
  `drivers/leds/leds-turris-omnia.c`.
- `led_trigger_set()`: does not call `trigger_relevant()`; the test is made by
  its callers `led_trigger_write()` and `led_match_default_trigger()`.
- Duplicate names: `led_trigger_register()` returns `-EEXIST` only when the
  two types are equal or either is NULL; private triggers of different types
  may share a name.
