- **Potentially unsafe usage**: doing probe work after the register call.
  - Unsafe: when the work sets up something that a `struct led_classdev`
    callback, or a handler of an attribute in `led_cdev->groups`,
    dereferences. `led_update_brightness()` calls `brightness_get()` inside
    registration; `led_trigger_set_default()` runs `activate()` inside it;
    `led_trigger_register()` can do the same from another task once the LED
    is on `leds_list`.
  - Safe: work that no callback or handler depends on, such as
    `platform_set_drvdata()` at the end of `gpio_led_probe()`; the callbacks
    use `cdev_to_gpio_led_data()` and only `gpio_led_shutdown()` reads the
    drvdata.
  - Safe: work that needs the registered device, such as
    `gpiod_set_consumer_name()` in `gpio_leds_create()`, which needs the
    final name.
- Driver sets no `default_trigger` and passes `init_data->fwnode`: firmware
  can supply one through `linux,default-trigger`, so activation during
  registration cannot be ruled out from the driver source.
- `max_brightness`: firmware `max-brightness` replaces the driver's value
  before any callback runs; callbacks that scale by it see that value.
- `led_cdev->groups` handlers: exist from `device_create_with_groups()`,
  before `brightness_get()` runs, and are not held back by `led_access`
  unless the handler takes it itself.
- `brightness_get()` returning an error during registration: ignored;
  `led_cdev->brightness` keeps what the driver set and registration
  succeeds.
- `LED_BRIGHT_HW_CHANGED` and `LED_REJECT_NAME_CONFLICT`: acted on inside
  `led_classdev_register_ext()`; set afterwards, no attribute is created and
  no name is rejected. `led_classdev_unregister()` tests
  `LED_BRIGHT_HW_CHANGED` again.
