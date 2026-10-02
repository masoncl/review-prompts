- Pointer type: `s64 *`, not `u64 *`. `hwmon_attr_show()` passes the address of
  an `s64` and prints it with `%lld`, so a value above `S64_MAX` prints
  negative.
- The 64-bit pointer is selected by channel type, not by attribute: every
  non-string attribute declared under `HWMON_CHANNEL_INFO(energy64, ...)` gets
  it on read, `hwmon_energy_enable` included.
- `drivers/hwmon/ltc4282.c` and `drivers/hwmon/ltc4283.c`: declare
  `HWMON_E_ENABLE` under `energy` and `HWMON_E_INPUT` under `energy64`. Both
  produce `energy1_` names because both types use
  `hwmon_energy_attr_templates`.
- `val64` in `hwmon_attr_show()`: not initialised, so a store of fewer than 64
  bits prints uninitialised stack in the remaining bits.
