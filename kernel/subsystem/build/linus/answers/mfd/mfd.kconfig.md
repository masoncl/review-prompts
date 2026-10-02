- Menu dependency: `if HAS_IOMEM` in `drivers/mfd/Kconfig` encloses the whole
  menu, `MFD_CORE` and `MFD_SYSCON` included.
- `MFD_CORE`: selects `IRQ_DOMAIN` and nothing else.
- `MFD_CORE`: no Kconfig file has `depends on MFD_CORE`; every reference
  outside its definition is `select MFD_CORE`.
- `MFD_SYSCON`: users get it either way; both `select MFD_SYSCON` and
  `depends on MFD_SYSCON` are common in the tree.
- `MFD_SYSCON` with neither `select` nor `depends on`: the driver still builds.
  `include/linux/mfd/syscon.h` has inline stubs for `!CONFIG_MFD_SYSCON`; the
  lookups return `ERR_PTR(-ENOTSUPP)`, except that
  `syscon_regmap_lookup_by_phandle_optional()` returns `NULL` and
  `of_syscon_register_regmap()` returns `-EOPNOTSUPP`.
- `MFD_SIMPLE_MFD_I2C`: `tristate` with no prompt. A driver gets it with
  `select MFD_SIMPLE_MFD_I2C`, as `MFD_SL28CPLD` does.
- `drivers/mfd/bcm2835-pm.c`: built by `CONFIG_ARCH_BCM2835`, not by a symbol
  in `drivers/mfd/Kconfig`. Its `select MFD_CORE` is in
  `arch/arm/mach-bcm/Kconfig` and `arch/arm64/Kconfig.platforms`.
