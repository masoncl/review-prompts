- `round_up()`, `round_down()`, `roundup()`, `rounddown()`, `DIV_ROUND_UP()`
  and `DIV_ROUND_UP_ULL()`: `include/linux/math.h`.
- `PAGE_ALIGN_DOWN()`: exists, in `include/linux/mm.h`, as
  `ALIGN_DOWN(addr, PAGE_SIZE)`.
- `roundup_u64()`: exists, in `include/linux/math64.h`. It is a `static
  inline` function, not a macro, and takes a `u32` multiple. There is no
  rounddown_u64() here.
- `DIV_ROUND_UP_POW2()` in `include/linux/math.h`: divide-and-round-up for a
  power-of-two divisor. It does not add to `n` before dividing, so it cannot
  wrap the way `DIV_ROUND_UP()` can.
- `ALIGN` in assembly sources: the macro from `include/linux/linkage.h`, not
  the C one. Its `__ALIGN` is `.balign CONFIG_FUNCTION_ALIGNMENT` unless the
  architecture's `asm/linkage.h` defines `__ALIGN`; for example
  `arch/arm/include/asm/linkage.h` uses `.align 0`. A search for `ALIGN` hits
  both macros.
- `ALIGN()`, `IS_ALIGNED()`, `round_up()`, `round_down()`: `a`, or `y - 1`,
  is cast to `typeof(x)`, so an `a` or `y` wider than `x` is truncated.
- `ALIGN()`, `round_up()`, `round_down()`: the result has the
  integer-promoted type of `x`.
- How many times each macro evaluates its arguments (`typeof` operands are
  not counted):

| Macro | `x` or `p` | `a` or `y` |
|---|---|---|
| `ALIGN()`, `PTR_ALIGN()` | once | twice |
| `ALIGN_DOWN()`, `PTR_ALIGN_DOWN()` | once | three times |
| `IS_ALIGNED()`, `round_up()`, `round_down()` | once | once |
| `roundup()`, `rounddown()` | once | once |

- `roundup()` copies `y` into a local `__y`; `rounddown()` copies `x` into a
  local `__x` and uses `y` directly.
