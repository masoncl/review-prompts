- `validate_desc()`: has three results and never looks at the chip.
  - NULL: 0, no message.
  - Error pointer: `pr_warn()` with no stack trace, then `PTR_ERR(desc)`.
  - Anything else: 1.
- Removed chip, configuration calls: `gpio_do_set_config()` finds a NULL chip
  in `gpio_chip_guard` and returns `-ENODEV`; `validate_desc()` prints
  nothing for it. For the value calls see "Removing a chip in use".
- `gpiod_to_irq()` and `gpiod_get_direction()`: return `-EINVAL` for both NULL
  and an error pointer.
- `gpiod_cansleep()` and `gpiod_is_active_low()` on an error pointer: return
  the negative errno, which is true in a boolean test.
- `gpiod_to_chip()` and `gpiod_to_gpio_device()`: return NULL for NULL, and
  dereference an error pointer.
- Array value calls: return `-EINVAL` for a NULL `desc_array`, and test no
  element for NULL or an error pointer before dereferencing it.
- `devm_gpiod_put()` with NULL: no action was registered, so
  `devm_release_action()` hits its `WARN_ON()`. `devm_gpiod_unhinge()` accepts
  NULL and error pointers.
- `!CONFIG_GPIOLIB` stubs in `include/linux/gpio/consumer.h`: the direction
  and config stubs return `-ENOSYS` for any argument, NULL included; the value
  stubs return 0.
  - A driver that checks the return of `gpiod_direction_output()` on an
    optional line therefore fails when `CONFIG_GPIOLIB` is off.
- **Potentially unsafe usage**: passing the kept result of an optional request
  to a call that does not go through `validate_desc()`.
  - Unsafe: when the line may be absent and no NULL test precedes the call;
    `desc_to_gpio()`, `gpiod_hwgpio()` and `gpiod_is_shared()` dereference
    NULL, and `gpiod_put_array()` dereferences the NULL that
    `gpiod_get_array_optional()` returns.
  - Safe: after a NULL test, as `regulator_register()` tests
    `config->ena_gpiod` before `regulator_ena_gpio_request()` calls
    `gpiod_is_shared()`.
