- Refused with `-EINVAL`: `reg_dir_in_base` or `reg_dir_out_base` set while
  either `reg_dat_base` or `reg_set_base` is 0.
- Refused with `-EINVAL`: `reg_dir_in_base` and `reg_dir_out_base` both set.
- `reg_clr_base`: no refusal in `gpio_regmap_register()` involves it; without
  `reg_set_base` it is ignored.
- `config->regmap`: never tested and never looked up from the parent; a NULL
  one is dereferenced by `regmap_might_sleep()`.
- `ngpio` of 0: not refused as such; `gpiochip_get_ngpios()` reads `ngpios`,
  and its error code is what registration returns.
- `ngpio_per_reg` left 0: becomes `config->ngpio`, not the count read from the
  `ngpios` property.
- **Unsafe usage**: leaving `ngpio` and `ngpio_per_reg` both 0 with the default
  translation; `gpio_regmap_simple_xlate()` divides by `ngpio_per_reg`.
  - Safe: set `ngpio` in the config, as `sl28cpld_gpio_probe()` does;
    `ngpio_per_reg` then takes that value.
