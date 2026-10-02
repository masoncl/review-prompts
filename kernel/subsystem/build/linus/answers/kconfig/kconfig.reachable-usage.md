- `Documentation/process/coding-style.rst`: recommends `IS_ENABLED()` in an
  ordinary C conditional; does not mention `IS_REACHABLE()`.
- `Documentation/kbuild/kconfig-language.rst`: mentions `IS_REACHABLE()` only
  in "Optional dependencies", not under `imply`; does not mention
  `IS_ENABLED()`.
- Wording on `IS_REACHABLE()`: a "much less favorable way" than the Kconfig
  dependency and "generally discouraged", because the code is silently
  discarded when BAR=m and the caller is built in.
- Stated use for `IS_REACHABLE()`: when BAR's header provides no stubs for
  the BAR=n case.
- `if (IS_REACHABLE(CONFIG_BAR))` in C: needs only a visible declaration; the
  header does not have to test `IS_REACHABLE()`. `include/linux/hwmon.h`
  declares its functions with no configuration test and no stubs, and
  `drivers/regulator/max5970-regulator.c` calls
  `devm_hwmon_device_register_with_info()` under
  `if (IS_REACHABLE(CONFIG_HWMON))`.
- **Potentially unsafe usage**: calling into tristate BAR from code guarded
  only by `IS_ENABLED(CONFIG_BAR)`, or by header stubs selected with
  `IS_ENABLED(CONFIG_BAR)`.
  - Unsafe: when Kconfig allows the caller to be y while BAR=m; the test is
    true (`IS_ENABLED()` in `include/linux/kconfig.h` includes `IS_MODULE()`)
    and vmlinux references a symbol that exists only in the module.
  - Safe: when the caller's entry carries the optional dependency;
    `HYPERV_UTILS` in `drivers/hv/Kconfig` depends on
    `PTP_1588_CLOCK_OPTIONAL`, and `include/linux/ptp_clock_kernel.h` selects
    `ptp_clock_register()` or its stub with
    `IS_ENABLED(CONFIG_PTP_1588_CLOCK)`.
  - Safe: when the guard is `IS_REACHABLE(CONFIG_BAR)` and losing the feature
    in a built-in caller is intended, as in
    `drivers/regulator/max5970-regulator.c`.
