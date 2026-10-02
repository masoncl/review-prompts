- `include/linux/gpio.h`: its opening comment says "This header *must not*
  be included"; for what it includes and what the comment names instead, see
  "Headers by role".
- `drivers/gpio/gpiolib-legacy.c`: defines `gpio_request()`,
  `gpio_request_one()`, `gpio_free()` and `devm_gpio_request_one()`;
  `drivers/gpio/gpiolib-devres.c` holds no integer call.
- `CONFIG_GPIOLIB_LEGACY`: `def_bool y` with no prompt and no dependency in
  `drivers/gpio/Kconfig`, so a `select` or `depends on` naming it gates
  nothing, and the `#ifdef CONFIG_GPIOLIB_LEGACY` guard in both
  `include/linux/gpio.h` and `include/linux/gpio/legacy.h` is always true.
- `CONFIG_GPIOLIB` off: `drivers/Makefile` does not enter `drivers/gpio/`, so
  `drivers/gpio/gpiolib-legacy.c` is not built; `include/linux/gpio/legacy.h`
  then supplies inline stubs.

| Call a reader reaches for | In this tree |
|---|---|
| gpio_request_array(), gpio_free_array() | absent |
| devm_gpio_request(), without flags | absent; `devm_gpio_request_one()` takes flags and is present |
| gpio_set_debounce() | absent; `gpiod_set_debounce()` on a descriptor |
| of_get_named_gpio(), of_get_gpio() | absent, as is the header include/linux/of_gpio.h |

- Device tree lookup: no call returns a GPIO number; consumers use the
  `gpiod_get()` family, or `fwnode_gpiod_get_index()` for another node.
- `of_gpio_count()`: exists only as an internal function of
  `drivers/gpio/gpiolib-of.c` taking a fwnode and a `con_id`; consumers call
  `gpiod_count()`.
