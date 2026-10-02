- `of_gpio_try_fixup_polarity()` entry: `active_high` is the polarity that is
  enforced; the driver writes logical values in that sense.
- In-tree example: the `"cascoda,ca8210"` entry forces active low;
  `ca8210_reset_init()` requests with `GPIOD_OUT_LOW` and
  `ca8210_reset_send()` writes 1 then 0.
- `of_gpio_quirk_polarity()` logging: `pr_warn()` when it clears an
  active-low flag, `pr_info()` when it adds one, nothing when the tree agrees.
- Property name of the `of_gpio_try_fixup_polarity()` entry: see "Device tree
  quirks"; it must be the name the existing trees use.
- `Documentation/driver-api/gpio/consumer.rst`: names no case in which the raw
  accessors or `gpiod_toggle_active_low()` are permitted, and none in which
  they are forbidden.
- `Documentation/driver-api/gpio/consumer.rst` on raw accessors: "should be
  avoided as much as possible, especially by system-agnostic drivers".
- `Documentation/driver-api/gpio/consumer.rst` on the raw calls,
  `gpiod_is_active_low()` and `gpiod_toggle_active_low()` together: "should
  only be used with great moderation; a driver should not have to care about
  the physical line level or open drain semantics".
- `Documentation/driver-api/gpio/consumer.rst` does not mention bit-banging,
  MMC, or the quirks of `drivers/gpio/gpiolib-of.c`.
- In-tree callers of `gpiod_toggle_active_low()`: take polarity from a source
  the lookup does not carry, so a call to it is not in itself a defect.
  - Platform data on a descriptor made from a number: for example
    `gpio_led_get_legacy_gpiod()` and `gpio_keys_setup_key()`.
  - A separate property or host capability: for example
    `matrix_keypad_init_gpio()` reads `gpio-activelow`, and
    `mmc_gpiod_request_cd()` tests `MMC_CAP2_CD_ACTIVE_HIGH`.
