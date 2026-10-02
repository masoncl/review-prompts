- `reg_mask_xlate`: takes six parameters; the second is an
  `enum gpio_regmap_operation`, before `base`. A five-parameter callback does
  not match the type in `struct gpio_regmap_config`.
- Operation passed: `GPIO_REGMAP_GET_OP` from `gpio_regmap_get()`,
  `GPIO_REGMAP_SET_OP` from both set paths, `GPIO_REGMAP_GET_DIR_OP` and
  `GPIO_REGMAP_SET_DIR_OP` from the direction paths.
- Use of the operation: it tells the cases apart when several bases are the
  same register; see `rtd1625_reg_mask_xlate()` in
  `drivers/gpio/gpio-rtd1625.c`.
- `value_xlate`: a second, optional callback in `struct gpio_regmap_config`;
  it runs after `reg_mask_xlate` on the set and set-direction paths and may
  change the mask and the value to be written;
  `gpio_regmap_set_with_clear()` writes only the mask.
