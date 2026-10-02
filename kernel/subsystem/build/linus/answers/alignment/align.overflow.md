- Unsigned operand at least as wide as `int`, power-of-two `a`: the result is
  exactly 0, not another small value.
- Signed operand at least as wide as `int`: the result is the minimum of the
  type, for example `INT_MIN`.
- Operand narrower than `int`: the sum is computed in `int` and does not
  wrap; the result is out of range for the operand type until it is stored.
- `CONFIG_UBSAN_INTEGER_WRAP` in `lib/Kconfig.ubsan`: the wrap sanitizer; it
  depends on `BROKEN`, and `scripts/integer-wrap-ignore.scl` limits it to
  `size_t`.
- `mm/mremap.c`: `do_mremap()` aligns both lengths; `check_mremap_params()`
  returns `-EINVAL` for a zero `new_len` and for `new_len > TASK_SIZE`; a
  zero `old_len` passes `check_mremap_params()`.
- `mm/madvise.c`: the wrap test is in `check_input_range()`.
- `vm_mmap()` in `mm/util.c`: its test covers the sum
  `offset + PAGE_ALIGN(len)`; it passes when `PAGE_ALIGN(len)` itself wrapped
  to 0, and `do_mmap()` rejects that case later.
- `do_mprotect_pkey()` in `mm/mprotect.c`: returns 0 for `!len` before it
  aligns, then returns `-ENOMEM` when `start + PAGE_ALIGN(len) <= start`.
- `validate_mmap_request()` in `mm/nommu.c`: rejects an aligned length of 0
  or above `TASK_SIZE` with `-ENOMEM`.
- **Potentially unsafe usage**: `ALIGN()` or `PAGE_ALIGN()` on a length or
  address from outside the kernel.
  - Unsafe: when nothing bounds the value to the type's maximum minus
    `a - 1` before the call and nothing tests the result for a wrap after
    it; `__ALIGN_KERNEL_MASK()` wraps and the result 0 is used as a size or
    an end.
  - Unsafe: when the only test is "result is 0" and a zero input is legal;
    the test cannot tell a wrap from a zero input.
  - Safe: reject a zero input, align, then reject a zero result, as
    `do_mmap()` in `mm/mmap.c` does (`-EINVAL`, then `-ENOMEM`).
  - Safe: test `len_in && !len` after aligning, as `check_input_range()`
    does.
  - Safe: test `len < request` after aligning, as `vm_brk_flags()` in
    `mm/mmap.c` does.
