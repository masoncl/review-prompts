- `include/linux/gpio.h`: declares nothing of its own; it only includes
  `include/linux/gpio/consumer.h` under `CONFIG_GPIOLIB` and
  `include/linux/gpio/legacy.h` under `CONFIG_GPIOLIB_LEGACY`.
- `include/linux/gpio/legacy.h`: holds the integer-API declarations
  (`gpio_request()`, `gpio_is_valid()`, `devm_gpio_request_one()`) and the
  flags `GPIOF_IN`, `GPIOF_OUT_INIT_LOW`, `GPIOF_OUT_INIT_HIGH`;
  `gpio_to_desc()` and `desc_to_gpio()` are in
  `include/linux/gpio/consumer.h`.
- Code that still uses the integer calls: the opening comment of
  `include/linux/gpio.h` tells it to include `<linux/gpio/legacy.h>`, not
  `<linux/gpio.h>`, and names all three replacements; a few files still
  include `<linux/gpio.h>`, for example `drivers/gpio/gpiolib-legacy.c`.
- `include/linux/gpio/legacy.h` in new code: its own opening comment says no
  new code should use it.
- include/linux/gpio/legacy-of-mm-gpiochip.h: does not exist; neither do
  struct of_mm_gpio_chip nor of_mm_gpiochip_add_data().
- `drivers/gpio/gpiolib-of.c`: has no `EXPORT_SYMBOL`; every OF entry point is
  declared in the private `drivers/gpio/gpiolib-of.h` for gpiolib itself.
- Controller-side OF hooks: members of `struct gpio_chip` in
  `include/linux/gpio/driver.h` under `CONFIG_OF_GPIO`: `of_gpio_n_cells`,
  `of_xlate` and `of_node_instance_match`.
- `include/linux/gpio/property.h`: the board-file header for software-node
  descriptions; it defines `PROPERTY_ENTRY_GPIO()` and no flag values.
- Flags passed to `PROPERTY_ENTRY_GPIO()`: `GPIO_ACTIVE_LOW` and the rest are
  `enum gpio_lookup_flags` in `include/linux/gpio/machine.h`, so a
  software-node board file includes both headers, as
  `drivers/gpio/gpiolib-kunit.c` does.
- `include/linux/gpio/machine.h`: lookup flags and lookup tables only; there
  is no struct gpiod_hog and no gpiod_add_hogs().
- `include/linux/gpio/generic.h` and `include/linux/gpio/regmap.h`: the
  headers for users of `drivers/gpio/gpio-mmio.c` and
  `drivers/gpio/gpio-regmap.c`; `generic.h` includes `driver.h` itself,
  `regmap.h` does not.
- `include/linux/gpio/defs.h`: defines `GPIO_LINE_DIRECTION_IN` and
  `GPIO_LINE_DIRECTION_OUT`; both `consumer.h` and `driver.h` include it, so a
  consumer does not need `driver.h` for them.
