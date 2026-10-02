- Non-power-of-two `a`, direction: without wrap `ALIGN(x, a)` is never below
  `x` and `ALIGN_DOWN(x, a)` is never above `x`; each differs from `x` by at
  most `a - 1`.
- Non-power-of-two `a`, value: the result has the bits of `a - 1` clear; it
  may or may not be a multiple of `a`.
- Multiple of a non-power-of-two `a`: need not be returned unchanged;
  `ALIGN(6, 6)` is `11 & ~5`, which is 10, and `ALIGN_DOWN(6, 6)` is
  `6 & ~5`, which is 2.
