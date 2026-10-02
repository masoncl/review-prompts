- `gpiod_configure_flags()`: calls `gpiod_direction_output_nonotify()`, not
  `gpiod_direction_output()`; the inversion is the first step there, before
  that function calls the chip.
- Kerneldoc of `enum gpiod_flags` in `include/linux/gpio/consumer.h`: says
  "drive them low" and "drive them high"; the value is logical all the same.
- First level driven: follows polarity only when polarity arrives in `lflags`,
  from the firmware or board-table lookup or a quirk of
  `drivers/gpio/gpiolib-of.c`.
- `GPIOD_FLAGS_BIT_NONEXCLUSIVE` with `-EBUSY` from `gpiod_request()`:
  `gpiod_find_and_request()` returns the descriptor without calling
  `gpiod_configure_flags()`, so this request's value and polarity are not
  applied.
- **Unsafe usage**: choosing `GPIOD_OUT_LOW` or `GPIOD_OUT_HIGH` by the
  voltage wanted on the pin, for a line whose lookup can carry
  `GPIO_ACTIVE_LOW`.
  - Safe: choose by state, `GPIOD_OUT_HIGH` for asserted, and keep that sense
    in later set calls, as `tsc200x_probe()` and `tsc200x_reset()` in
    `drivers/input/touchscreen/tsc200x-core.c` do;
    `gpiod_direction_output_nonotify()` applies `GPIOD_FLAG_ACTIVE_LOW` to
    the request value.
  - Safe: `GPIOD_OUT_LOW` for a reset line that must start released, as
    `ca8210_reset_init()` in `drivers/net/ieee802154/ca8210.c` does.
- **Potentially unsafe usage**: calling `gpiod_toggle_active_low()` after
  the request.
  - Unsafe: when the request passed `GPIOD_OUT_LOW` or `GPIOD_OUT_HIGH`; the
    line was already driven with the polarity from the lookup.
  - Safe: request with `GPIOD_ASIS`, toggle, then `gpiod_direction_output()`,
    as `matrix_keypad_init_gpio()` does for the column lines;
    `gpiod_toggle_active_low()` only flips `GPIOD_FLAG_ACTIVE_LOW` and does
    not drive the line.
  - Safe: on a line requested with `GPIOD_IN`, as `mmc_gpiod_request_cd()`
    does; nothing is driven.
