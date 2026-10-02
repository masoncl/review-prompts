- System shutdown: the core does nothing; `leds_class` in
  `drivers/leds/led-class.c` sets no `shutdown_pre`, and there is no
  led_classdev_shutdown() in this tree.
- `led_classdev_register_ext()`: sets `LED_RETAIN_AT_SHUTDOWN` itself when
  `init_data->fwnode` has `retain-state-shutdown`; `led_parse_fwnode_props()`
  and `led_init_core()` do not parse it.
- Driver `.shutdown`: a driver's own shutdown callback has to test the flag,
  as `gpio_led_shutdown()` in `drivers/leds/leds-gpio.c` does before it sets
  each LED to `LED_OFF`; the flag to test is in `led_cdev->flags` after
  registration; `ncp5623_shutdown()` in `drivers/leds/rgb/leds-ncp5623.c`
  relies on the core having set the flag.
- Hibernation: `SIMPLE_DEV_PM_OPS()` in `drivers/leds/led-class.c` installs
  `led_suspend()` as `.poweroff` under `CONFIG_PM_SLEEP`; it tests only
  `LED_CORE_SUSPENDRESUME`, so when `.poweroff` runs
  (`hibernation_platform_enter()`) an LED with that flag is turned off
  whatever `LED_RETAIN_AT_SHUTDOWN` says.
