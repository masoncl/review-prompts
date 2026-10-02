- Bit index at or beyond `__templates_size[type]`, or a NULL slot inside the
  table: `hwmon_genattrs()` skips it with `continue`; no error, no message, and
  `hwmon_genattr()` is not called for it.
- `hwmon_genattr()`: makes no test of `template`; its `-ENOENT` comes only
  from a mode of 0, so the skip in `hwmon_genattrs()` is the only guard against
  a NULL name.
- `hwmon_chip_attrs[]`: `hwmon_chip_register_tz` is a NULL hole inside the
  table and `hwmon_chip_pec` lies past its end; neither flag creates a file.
- `info->type` at or beyond `ARRAY_SIZE(__templates)`: `hwmon_genattrs()`
  returns `-EINVAL` and registration fails, unlike an unknown bit.
