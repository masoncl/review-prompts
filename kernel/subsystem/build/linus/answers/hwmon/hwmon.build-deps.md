- `include/linux/hwmon.h`: has no test of `CONFIG_HWMON` and no stub; every
  function except the inline `hwmon_is_bad_char()` is a plain prototype in
  every configuration.
- Unreachable hwmon core (`HWMON=n`, or `HWMON=m` with a built-in caller): an
  unguarded call compiles and fails at link time.
- Registration functions in `drivers/hwmon/hwmon.c`: return a device or an
  `ERR_PTR()`, never `NULL`.
- `#ifdef CONFIG_HWMON` in C: true only for `HWMON=y`, because `=m` defines
  `CONFIG_HWMON_MODULE` instead (`include/linux/kconfig.h`).
- `#ifdef CONFIG_HWMON` with no Kconfig dependency: links in every
  configuration, as `MARVELL_10G_PHY` and `drivers/net/phy/marvell10g.c` do;
  the cost is that a modular driver with `HWMON=m` gets no hwmon device.
- `ifdef CONFIG_HWMON` in a Makefile: true for `m` as well, unlike the C form.
- `drivers/net/phy/aquantia/Makefile`: builds `aquantia_hwmon.o` even when the
  driver is built in and `HWMON=m`; this links only because
  `drivers/net/phy/aquantia/aquantia_hwmon.c` wraps its whole body in
  `#if IS_REACHABLE(CONFIG_HWMON)`.
- `if (IS_REACHABLE(CONFIG_HWMON))` as a C condition around the call: valid
  with no stub, because the prototypes are unconditional; see
  `drivers/regulator/tps65185.c`.
- `NXP_TJA11XX_PHY`: `depends on HWMON`, so hwmon is mandatory there and
  `drivers/net/phy/nxp-tja11xx.c` has no guard.
- `depends on HWMON || !HWMON` (`MLX5_CORE`) and `depends on HWMON = n || HWMON`
  (`TOUCHSCREEN_ADS7846`): same effect as `depends on HWMON || HWMON=n`.
- `select HWMON`: used in this tree by drivers that need hwmon
  unconditionally, for example `DRM_AMDGPU`; `TXGBE` uses
  `select HWMON if TXGBE=y`.
- `drivers/acpi/fan.h`: the guarded functions are
  `devm_acpi_fan_create_hwmon()` and `acpi_fan_notify_hwmon()`; there is no
  acpi_fan_create_hwmon().
- `struct acpi_fan` field `hdev`: exists only under
  `IS_REACHABLE(CONFIG_HWMON)`, so only `drivers/acpi/fan_hwmon.c` may touch it.
- Registration failure: the tree has both policies. `acpi_fan_probe()` and
  `mv3310_hwmon_probe()` return the error; `sfp_hwmon_probe()` and
  `drivers/regulator/tps65185.c` log it and continue.
- Compiled-out stub: must return 0 where the caller propagates the result, as
  the stub of `devm_acpi_fan_create_hwmon()` does.
- **Potentially unsafe usage**: guarding hwmon calls with
  `IS_ENABLED(CONFIG_HWMON)` in a tristate driver.
  - Unsafe: when Kconfig allows the driver to be `y` while `HWMON=m`; the
    guard is true and the built-in call has no definition to link against.
  - Safe: with `depends on HWMON || HWMON=n` on the driver, as `SFP` with
    `drivers/net/phy/sfp.c`; the dependency caps the driver at `m` when
    `HWMON=m`.
  - Safe: with `IS_REACHABLE(CONFIG_HWMON)` instead, which needs no Kconfig
    line, as `drivers/acpi/fan.h` does for `devm_acpi_fan_create_hwmon()`.
  - Safe: with a bool sub-option that has
    `depends on HWMON && !(REALTEK_PHY=y && HWMON=m)`, as `REALTEK_PHY_HWMON`,
    tested by `rtl822x_probe()`.
- **Potentially unsafe usage**: passing a stored hwmon device pointer to
  `hwmon_device_unregister()` or `hwmon_notify_event()`.
  - Unsafe: when registration may have been skipped or its failure ignored,
    so the pointer is `NULL` or an `ERR_PTR()`; both functions dereference it
    without a test.
  - Safe: test first, as `sfp_hwmon_remove()` does with `IS_ERR_OR_NULL()`.
  - Safe: fail the probe on registration failure and install the notifier
    afterwards, as `acpi_fan_probe()` does before `acpi_fan_notify_hwmon()` can
    run.
  - Safe: for the unregister, use `devm_hwmon_device_register_with_info()`,
    which adds the release action only after registration succeeded.
