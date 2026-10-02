- `LM75_TEMP_TO_REG()` and `LM75_TEMP_FROM_REG()` in `drivers/hwmon/lm75.h`:
  static inline functions, not macros. They do not use `DIV_ROUND_CLOSEST()`;
  the write side adds 250 or -250 by sign and divides by 500.
- Shifts of negative values: used by in-tree conversions after the clamp, for
  example `LM75_TEMP_TO_REG()`, `lm75_write_temp()` and
  `ina238_temp_to_reg()`. The top-level `Makefile` sets
  `-fno-strict-overflow`.
- `DIV_ROUND_CLOSEST()`: expands to plain `/`, so a 64-bit operand can fail to
  link on a 32-bit build. Use one of:

| Helper | Dividend | Divisor |
|---|---|---|
| `DIV_S64_ROUND_CLOSEST()` | `s64` | converted to `s32` |
| `DIV_U64_ROUND_CLOSEST()` | `u64` | converted to `u32` |
| `DIV_ROUND_CLOSEST_ULL()` | `unsigned long long` | 32-bit, uses `do_div()` |
| `DIV64_U64_ROUND_CLOSEST()` | `u64` | `u64` |

- A divisor wider than 32 bits passed to the first two helpers: truncated
  silently by the assignment inside the macro.
- A negative dividend passed to `DIV_ROUND_CLOSEST_ULL()`: converted to
  unsigned, so the result is wrong; `DIV_S64_ROUND_CLOSEST()` is the signed
  form, as in `ina228_read_voltage()`.
- Read side: a result computed in 64 bits that can exceed `LONG_MAX` must be
  clamped before the store to `*val`, as `ina238_read_power()` does.
- Product that can exceed 64 bits: `mul_u64_u64_div_u64()` as in
  `ltc4283_read_energy()`, or `check_mul_overflow()` with a fallback as in
  `ltc4282_read_energy()`.
- `FIELD_PREP()` with a run-time value: masks it silently;
  `__BF_FIELD_CHECK_MASK()` in `include/linux/bitfield.h` checks only
  build-time constants.
- `Documentation/hwmon/submitting-patches.rst`: says to avoid calculations in
  macros and macro-generated functions; one reason it gives is that such
  macros may evaluate their arguments several times.
