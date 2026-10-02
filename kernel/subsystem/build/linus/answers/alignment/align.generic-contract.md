- The "@a is a power of 2 value" comment: in `include/vdso/align.h`, above
  `ALIGN()`.
- `roundup()` and `rounddown()` in `include/linux/math.h`: use the C `/` and
  `%` operators on the operand types, not `do_div()`.
- 64-bit value in a 32-bit build: `roundup_u64()` in
  `include/linux/math64.h` takes a `u32` multiple; `DIV_U64_ROUND_UP()` and
  `DIV64_U64_ROUND_UP()` are in the same file, `DIV_ROUND_UP_ULL()` in
  `include/linux/math.h`.
