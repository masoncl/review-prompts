- Models take a set on any requested line to reach the chip. A set on a line
  whose `GPIOD_FLAG_IS_OUT` is clear returns `-EPERM`, on a live chip too; see
  `gpiod_set_raw_value_commit()`. `gpiod_set_value()` and
  `gpiod_set_value_cansleep()` on an open-drain or open-source line skip that
  test; the array calls do not.
- Models limit the range check to value and direction callbacks. A positive
  return from `request()` or `set_config()` also becomes `-EBADE`; `to_irq()`
  returning 0 becomes `-ENXIO`.
- Models take the `enum gpiod_flags` a consumer passes to be what is applied.
  On ACPI, when `acpi_gpio_to_gpiod_flags()` returns other than `GPIOD_ASIS`
  for the resource, `acpi_gpio_update_gpiod_flags()` replaces direction and
  value from the resource unless `ACPI_GPIO_QUIRK_NO_IO_RESTRICTION` is set.
- Models take `gpiod_set_value()`, `gpiod_set_value_cansleep()`,
  `gpiod_set_raw_value()` and `gpiod_set_raw_value_cansleep()` to be void, as
  `Documentation/driver-api/gpio/consumer.rst` still prints. All four return
  `int` in `include/linux/gpio/consumer.h`.
- Models take a requested line to make `gpiochip_remove()` fail, as the
  comment above `gpiod_get_raw_value_commit()` in `drivers/gpio/gpiolib.c`
  still says. `gpiochip_remove()` returns `void` and has no early return.
- Models let a driver assign `of_gpio_twocell_xlate()` to `of_xlate`. It is
  `static` in `drivers/gpio/gpiolib-of.c`; `of_gpiochip_add()` installs it
  on a chip with an OF node when `of_xlate` is NULL and `of_gpio_n_cells` is
  not 3.
