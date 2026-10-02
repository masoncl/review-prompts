- `cfg->dat`: required in every configuration, also for an output-only chip
  that gives `set`; `gpio_mmio_setup_io()` returns `-EINVAL` without it.
- `cfg->sz`: the register width in bytes, given by the caller; only
  `gpio_mmio_pdev_probe()` derives it from the size of the `dat` resource.
- Byte order: the one refusal is 64-bit registers with
  `GPIO_GENERIC_BIG_ENDIAN_BYTE_ORDER`; 8-bit registers ignore the flag.
- `gc.ngpio`: a nonzero value set before the call is kept; otherwise the
  `ngpios` property is read, and only if that fails is it `sz * 8`. See
  `gpiochip_get_ngpios()` in `drivers/gpio/gpiolib.c`.
- `gc.parent`, `gc.label`, `gc.base`, `gc.request`: assigned unconditionally,
  so a value set before the call is lost; override after the call, as
  `spacemit_gpio_add_bank()` does.
- `gc.get_direction`: set only when `dirout` or `dirin` is given.
- `sdata`: read from `dat`, then re-read from `set` when `set` is given
  without `clr` and `GPIO_GENERIC_UNREADABLE_REG_SET` is clear.
- `GPIO_GENERIC_READ_OUTPUT_REG_SET`: selects the `get` callback and plays no
  part in the initial `sdata`.
- `struct gpio_generic_chip` must be zeroed before the call: `reg_dir_out`,
  `reg_dir_in`, `pinctrl`, `dir_unreadable` and `sdir` are written only when
  the matching register or flag is given, and read later.
