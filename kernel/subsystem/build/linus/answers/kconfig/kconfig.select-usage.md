- **Potentially unsafe usage**: `select BAR` where `BAR` has dependencies.
  - Unsafe: when some configuration lets the select term exceed `BAR`'s
    dependencies; `sym_calc_value()` warns on `dir_dep.tri < rev_dep.tri` and
    still forces `BAR`. For a tristate `BAR`, the selector at `y` with the
    dependency at `m` is such a case.
  - Safe: the selector repeats the dependency, as `SENSORS_JC42` in
    `drivers/hwmon/Kconfig` does: `depends on I2C`, `select REGMAP_I2C`.
  - Safe: the select is conditional on the dependency, as `SENSORS_LM75` does:
    `select REGMAP_I3C if I3C`.
  - Safe: the selector also selects the dependency, as `DM_CRYPT` in
    `drivers/md/Kconfig` does: `select CRYPTO` beside `select CRYPTO_CBC`.
  - Safe: selector and target sit in the same `if` block and the target has
    no other dependency, as `GPIO_PL061` and `GPIOLIB_IRQCHIP` do inside
    `if GPIOLIB` in `drivers/gpio/Kconfig`.
- `SENSORS_LM75`: has `depends on I3C_OR_I2C`, not `depends on I2C`;
  `I3C_OR_I2C` is in `drivers/i3c/Kconfig`.
- Dependencies from an enclosing `if`: count like a `depends on` line.
  `CRYPTO_CBC` has none of its own but sits in `if CRYPTO`; `MTK_SMI` sits in
  `if MEMORY`, so `MTK_IOMMU` in `drivers/iommu/Kconfig` has `select MEMORY`.
