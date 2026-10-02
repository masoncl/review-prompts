- From `pec_store()`: `write` for `hwmon_chip_pec` receives 0 or 1.
- Wording of `Documentation/hwmon/sysfs-interface.rst`, section "sysfs
  attribute writes interpretation": "do not multiply the result, and only
  add/subtract if it has been divided before the add/subtract".
- Division before the clamp is allowed: Example1 of that section divides by
  1000 and then calls `clamp_val()`.
- `DIV_ROUND_CLOSEST()` before a clamp: not safe, it adds or subtracts half
  the divisor first. `ina238_write_power_max()` clamps to `LONG_MAX / 2`
  before it.
- Scale factor known only at run time: clamp twice, as `ina238_write_in()`
  does. The first clamp, in sysfs units, keeps the multiplication from
  overflowing; the second, to `S16_MIN` / `S16_MAX`, fits the result to the
  register.
- `clamp_val()` with run-time bounds where `lo > hi`: returns `hi` or `lo`, not
  a value in a range. The check in `__clamp_once()` in
  `include/linux/minmax.h` catches only bounds known at build time.
