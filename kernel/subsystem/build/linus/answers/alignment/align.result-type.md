- Pointer test: `IS_ALIGNED((unsigned long)p, a)`, as `kernel/rseq.c` does;
  `include/vdso/align.h` has only `PTR_ALIGN()` and `PTR_ALIGN_DOWN()` for
  pointers.
- `ALIGN_DOWN(x, a)`: `a` is cast to the type of `(x) - ((a) - 1)`, the
  common type of `x` and `a`, so the result can be wider than `x` and a wide
  `a` is not truncated as it is in `ALIGN()`.
