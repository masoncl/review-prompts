- Quiet case: needs all three of `-ENODEV`, `LED_UNREGISTERING` and
  `LED_HW_PLUGGABLE`; any other negative result except `-ENOTSUPP` is logged.
- Only place the core tests these flags:
  `set_brightness_delayed_set_brightness()` in `drivers/leds/led-core.c`.
- `led_set_brightness_sync()`: returns the callback's error to its caller, no
  filtering. `led_set_brightness_nosleep()`: returns void.
- `set_brightness_delayed_set_brightness()`: tries `__led_set_brightness()`
  first; `brightness_set()` returns void, so for a driver that provides it
  the result is always 0 and nothing is logged.
- Work queued by trigger removal: can run before `LED_UNREGISTERING` is set,
  so its `-ENODEV` is logged even with `LED_HW_PLUGGABLE`.
- Driver-side test of `LED_UNREGISTERING`: a callback may return 0 without
  touching the hardware to skip the final switch-off, as `kbd_led_set()` in
  `drivers/platform/x86/asus-wmi.c` and `lg_g13_kbd_led_set()` in
  `drivers/hid/hid-lg-g15.c` do.
