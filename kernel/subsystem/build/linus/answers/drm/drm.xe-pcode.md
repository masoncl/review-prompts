- Power-limit mailbox value: two dwords, PL1 in the first and PL2 in the
  second; `attr` (`PL1_HWMON_ATTR` or `PL2_HWMON_ATTR`) selects which one
  `xe_hwmon_pcode_rmw_power_limit()` modifies.
- `xe_hwmon_pcode_read_power_limit()`: not a raw read; for
  `PL1_HWMON_ATTR` or `PL2_HWMON_ATTR` it returns one dword, and 0 unless
  `PWR_LIM_EN` is set in it.
- `xe_hwmon_pcode_rmw_power_limit()`: computes `(val & ~clr) | set`; `set`
  is not masked with `clr`.
- `hwmon->hwmon_lock`: taken with `mutex_lock()` by the sysfs callers of
  `xe_hwmon_pcode_rmw_power_limit()`; neither helper has a lockdep
  assertion, so a missing lock is not caught at run time.
- Platforms without `xe->info.has_mbx_power_limits`: the same fields live
  in a register and are updated with `xe_mmio_rmw32()` under the same
  `hwmon->hwmon_lock`.
- **Unsafe usage**: writing the two-dword power-limit value
  (`WRITE_PACKAGE_POWER_LIMIT`, `WRITE_PSYSGPU_POWER_LIMIT`) with
  `xe_pcode_write()` or `xe_pcode_write_timeout()`.
  - Unsafe: the single-dword writers pass a NULL `data1`, so
    `__pcode_mailbox_rw()` writes 0 to `PCODE_DATA1`, the PL2 dword.
  - Safe: `xe_pcode_read()` of both dwords succeeds, one field is changed,
    then `xe_pcode_write64_timeout()` sends both, the sequence in
    `xe_hwmon_pcode_rmw_power_limit()`.
  - Safe: a single-dword command, as `xe_hwmon_pcode_write_i1()` sends
    `POWER_SETUP_SUBCOMMAND_WRITE_I1` with `xe_pcode_write()`;
    `xe_hwmon_pcode_read_i1()` reads that value with a NULL second dword.
- **Potentially unsafe usage**: calling `xe_hwmon_pcode_rmw_power_limit()`
  without `hwmon->hwmon_lock`.
  - Unsafe: once the hwmon device is registered; `tile->pcode.lock` is
    dropped between the read and the write, so a concurrent sysfs store to
    another field of the same value is lost.
  - Safe: under `mutex_lock(&hwmon->hwmon_lock)`, as
    `xe_hwmon_power_max_write()` and
    `xe_hwmon_power_max_interval_store()` do.
  - Safe: before `devm_hwmon_device_register_with_info()`, as
    `xe_hwmon_get_preregistration_info()` does.
- Runtime PM for these paths: `xe_hwmon_read()` and `xe_hwmon_write()`
  take `guard(xe_pm_runtime)`; the interval show and store functions take
  their own, before `hwmon->hwmon_lock`.
