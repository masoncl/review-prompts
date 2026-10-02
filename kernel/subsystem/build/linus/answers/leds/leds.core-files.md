- `drivers/leds/leds.h`: holds only inline `led_get_brightness()`, the
  prototypes of `led_init_core()`, `led_stop_software_blink()`,
  `led_set_brightness_nopm()`, `led_set_brightness_nosleep()`,
  `led_trigger_read()`, `led_trigger_write()`, and the externs `leds_list_lock`
  and `leds_list`.
- `led_init_default_state_get()`, `led_update_brightness()`,
  `led_compose_name()`, `led_trigger_set()`, `led_trigger_remove()`: declared
  in `include/linux/leds.h`, not in `drivers/leds/leds.h`.
- `trigger_list` and `triggers_list_lock`: `static` in
  `drivers/leds/led-triggers.c`; no header declares them.
- `led_colors[]`: `static` in `drivers/leds/led-core.c`; other files reach it
  through `led_get_color_name()`.
- `drivers/leds/leds.h` users: `drivers/leds/led-class.c`,
  `drivers/leds/led-core.c`, `drivers/leds/led-triggers.c`,
  `drivers/leds/leds-ns2.c` and most files in `drivers/leds/trigger/`; no file
  outside `drivers/leds/` includes it.
- Every symbol `drivers/leds/leds.h` declares is `EXPORT_SYMBOL_GPL()`, so a
  modular trigger can call it.
