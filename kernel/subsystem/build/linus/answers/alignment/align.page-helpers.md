- `PAGE_ALIGN()` result type: the integer-promoted type of `addr`, because
  `__ALIGN_KERNEL()` in `include/uapi/linux/const.h` casts `a` to
  `__typeof__(x)`; a `u64` stays 64 bits wide on a 32-bit kernel.
- `PAGE_ALIGN_DOWN()` result type: the type of `addr - (PAGE_SIZE - 1)`, not
  the type of `addr`, because `ALIGN_DOWN()` in `include/vdso/align.h` does the
  subtraction before `__ALIGN_KERNEL()` takes the typeof.
  - Argument narrower than unsigned long, for example `u32` on a 64-bit kernel:
    result is unsigned long.
  - Signed argument of the same width as unsigned long, for example `loff_t` on
    a 64-bit kernel: result is unsigned.
  - Argument wider than unsigned long, for example `u64` or `loff_t` on a
    32-bit kernel: keeps its type and its high bits.
- Pointer argument to `PAGE_ALIGN()` or `PAGE_ALIGN_DOWN()`: does not compile,
  although the comments above them in `include/linux/mm.h` say "align the
  pointer"; the expansion adds the pointer to a mask of pointer type.
- `PAGE_ALIGNED()` on a value wider than unsigned long on a 32-bit kernel: the
  cast drops the high bits, and the result is still correct, since only bits
  below `PAGE_SHIFT` are tested.
