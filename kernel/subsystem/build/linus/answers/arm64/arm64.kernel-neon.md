- `kernel_neon_begin()` and `kernel_neon_end()`: each takes a
  `struct user_fpsimd_state *`; see `arch/arm64/include/asm/neon.h`.
- NULL argument: allowed only in task context that is not preemptible;
  `kernel_neon_begin()` has
  `WARN_ON((preemptible() || in_serving_softirq()) && !state)`;
  `kernel_fpu_begin()` in `arch/arm64/include/asm/fpu.h` passes NULL after
  `preempt_disable()`.
- Task-level buffer: recorded in `thread.kernel_fpsimd_state`; written only at
  context switch, by `fpsimd_save_kernel_state()`.
- Softirq caller's buffer on a non-RT kernel: receives the registers of the
  task-level section it interrupted, not its own; `kernel_neon_end()` reloads
  them from it. This is why a softirq caller needs a buffer.
- The buffer need not be initialised; `scoped_ksimd()` declares it
  `__uninitialized`.
- `kernel_neon_begin()` with `TIF_KERNEL_FPSTATE` already set: `BUG_ON()`
  unless serving a softirq on a non-RT kernel; the
  `WARN_ON(current->thread.kernel_fpsimd_state != NULL)` is reached only with
  the flag clear.
- `scoped_ksimd()`: declares a `struct user_fpsimd_state` on the stack and
  runs the following statement under guard class `ksimd`, which calls
  `kernel_neon_begin()` and `kernel_neon_end()` on that buffer.
